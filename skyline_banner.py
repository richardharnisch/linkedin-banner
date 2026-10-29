# /// script
# requires-python = ">=3.11"
# dependencies = ["numpy", "matplotlib", "pillow"]
# ///
"""Render a compact, self-contained skyline formula as a LinkedIn banner.

Run: uv run skyline_banner.py
Add --source /path/to/Dresden_skyline.jpg to regenerate the photo overlay.
TeX rendering requires pdflatex and pdftoppm.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import subprocess

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image, ImageDraw, PngImagePlugin


HERE = Path(__file__).resolve().parent
BUILD = Path("/tmp/opencode/dresden-banner-tex")
MODEL = json.loads((HERE / "dresden-banner-model.json").read_text())
TERMS = MODEL["terms"]
CREDIT = "Adapted from Michele Vascellari's photo · CC BY-SA 4.0"


def skyline_height(x):
    """Evaluate the complete 18-term analytic formula, on all real x."""
    x = np.asarray(x, dtype=float)
    if not np.isfinite(x).all():
        raise ValueError("x must be finite")
    y = MODEL["constant"] + (MODEL["linear_change_over_domain"] / 1280) * x
    with np.errstate(over="ignore", under="ignore"):
        for amplitude, center, width, power in TERMS:
            y = y + amplitude * np.exp(-((x-center)/width)**power)
    return y


def check_model() -> dict:
    assert len(TERMS) == 18
    assert all(width > 0 and power in (2, 4, 8, 16) for _, _, width, power in TERMS)
    assert np.isfinite(skyline_height(np.array([-1e200, -5000, 0, 1280, 5000, 1e200]))).all()
    outline = np.loadtxt(HERE / "dresden-outline.csv", delimiter=",", skiprows=1)
    assert outline.shape == (1281, 2)
    assert np.array_equal(outline[:,0], np.arange(1281))
    error = skyline_height(outline[:,0]) - outline[:,1]
    landmarks = {}
    for name, left, right in [("Frauenkirche",145,185), ("Hausmannsturm",880,900), ("Hofkirche",1025,1050)]:
        xx = np.linspace(left,right,2501)
        yy = skyline_height(xx)
        index = int(np.argmax(yy))
        landmarks[name] = {"x": round(float(xx[index]),2), "photo_y": round(float(570-yy[index]),2)}
    for name, expected in [("Frauenkirche",165), ("Hausmannsturm",889), ("Hofkirche",1039)]:
        assert abs(landmarks[name]["x"]-expected) < 1
    assert abs(landmarks["Frauenkirche"]["photo_y"]-230) < 3
    assert abs(landmarks["Hausmannsturm"]["photo_y"]-317) < 3
    assert abs(landmarks["Hofkirche"]["photo_y"]-325) < 3
    metrics = {
        "smooth_terms": len(TERMS),
        "fitted_values_before_integer_rounding": 3*len(TERMS)+2,
        "fixed_even_powers": [2,4,8,16],
        "reference": "dresden-outline.csv: brightness-extracted photo outline with manual spire corrections",
        "rms_vertical_distance_to_extracted_outline_px": round(float(np.sqrt(np.mean(error**2))),3),
        "max_vertical_distance_to_extracted_outline_px": round(float(np.max(np.abs(error))),3),
        "landmarks": landmarks,
        "note": "Comparison with the extracted, manually corrected outline, not independent ground truth or a recognition test. Small roof ornaments and tree detail are intentionally omitted.",
    }
    (HERE / "dresden-banner-check.json").write_text(json.dumps(metrics, indent=2)+"\n")
    return metrics


def write_formula() -> None:
    terms = [f"{a}g(x,{c},{w},{p})" for a,c,w,p in TERMS]
    desmos = (
        "Paste each expression into a separate Desmos line:\n\n"
        r"g(x,u,v,p)=e^{-((x-u)/v)^p}" + "\n"
        "f(x)=112-37x/1280+" + "+".join(terms) + "\n"
        r"(t,f(t))\{0\le t\le1280\}" + "\n\n"
        "The function is analytic on all real x. Plot the photographed part on 0 <= x <= 1280.\n"
        "Use equal x/y scales; suggested y range: 0 to 370.\n"
        "\nAll coefficients in this file are used in the banner and plotted preview.\n"
        + CREDIT + "\n" + MODEL["source"] + "\n" + MODEL["license"] + "\n"
    )
    (HERE / "dresden-banner-formula.txt").write_text(desmos,encoding="utf-8")


def render_plot() -> None:
    x = np.linspace(0,1280,12801)
    y = skyline_height(x)
    background, ink = "#fbf9f5", "#172831"
    plt.rcParams.update({"font.family":"DejaVu Sans", "svg.fonttype":"none"})
    fig = plt.figure(figsize=(15.84,3.96),facecolor=background)
    ax = fig.add_axes([.035,.07,.93,.90],facecolor=background)
    ax.fill_between(x,0,y,color=ink,alpha=.96,linewidth=0)
    ax.plot(x,y,color=ink,lw=1)
    ax.set(xlim=(0,1280),ylim=(0,370),aspect="equal")
    ax.axis("off")
    fig.text(.035,.023,CREDIT,size=6,color="#5e7078")
    for suffix in ["png","svg"]:
        options = {"dpi":100} if suffix == "png" else {}
        fig.savefig(HERE/f"dresden-banner-plot.{suffix}",facecolor=background,**options)
    plt.close(fig)


def render_overlay(source: Path) -> None:
    """Draw only the photo crop and fitted line, without margins or labels."""
    with Image.open(source) as original:
        photo = original.convert("RGB").resize((1280,850), Image.Resampling.LANCZOS)
    crop = photo.crop((0,210,1280,570))
    x = np.linspace(0,1280,12801)
    photo_y = MODEL["height_reference_photo_y"] - skyline_height(x) - 210
    # Antialias only the line; leave the underlying photo pixels unchanged.
    scale = 4
    mask = Image.new("L",(crop.width*scale,crop.height*scale),0)
    points = list(zip((x*scale).tolist(),(photo_y*scale).tolist()))
    ImageDraw.Draw(mask).line(points,fill=255,width=6)
    mask = mask.resize(crop.size,Image.Resampling.LANCZOS)
    crop.paste("#55ffe5",(0,0,crop.width,crop.height),mask)
    metadata = PngImagePlugin.PngInfo()
    metadata.add_text("Description",f"{CREDIT}; {MODEL['source']}; {MODEL['license']}")
    crop.save(HERE/"dresden-fit-overlay.png",pnginfo=metadata)


def render_tex() -> None:
    def term(row):
        a,c,w,p = row
        return rf"{a}\,E^{{{p}}}_{{{c},{w}}}"

    # Three complete rows, not an omitted coefficient list. The header defines
    # E as an expression at the same x as f(x), making it an exact abbreviation.
    rows = [TERMS[:5], TERMS[5:11], TERMS[11:]]
    equation = r"f(x)={}&112-\frac{37x}{1280}+"+"+".join(map(term,rows[0]))
    for row in rows[1:]:
        equation += r"\\[5pt]&+"+"+".join(map(term,row))

    template = r"""\documentclass[tikz,border=0pt]{standalone}
\usepackage[T1]{fontenc}
\usepackage{lmodern,amsmath,amssymb,graphicx,xcolor}
\definecolor{paper}{HTML}{FBF9F5}
\definecolor{ink}{HTML}{172831}
\definecolor{muted}{HTML}{60717A}
\begin{document}
\begin{tikzpicture}[x=1cm,y=1cm,text=ink]
\path[use as bounding box] (0,0) rectangle (40,10);
\begin{pgfinterruptboundingbox}
\fill[paper] (0,0) rectangle (40,10);
\node[inner sep=0pt] at (24,8.65) {\resizebox{22cm}{!}{$\displaystyle
  E^p_{\mu,w}:=\exp\!\left[-\left(\frac{x-\mu}{w}\right)^p\right],
  \qquad p\in\{2,4,8,16\},\qquad f:\mathbb{R}\to\mathbb{R}
$}};
\node[inner sep=0pt] at (22.6,4.75) {\resizebox{32.5cm}{!}{$\displaystyle
  \begin{aligned}
EQUATION
  \end{aligned}
$}};
\node[inner sep=0pt,text=muted] at (24,0.85) {\resizebox{13.5cm}{!}{$\displaystyle
  \gamma(t)=\bigl(t,f(t)\bigr),\quad 0\leq t\leq1280
$}};
\node[anchor=east,inner sep=0pt,text=muted] at (39,0.25)
  {\fontsize{5.3}{6}\selectfont\sffamily Adapted from Michele Vascellari's photo\quad\textbar\quad CC BY-SA 4.0};
\end{pgfinterruptboundingbox}
\end{tikzpicture}
\end{document}
"""
    source = HERE / "dresden-linkedin-banner.tex"
    source.write_text(template.replace("EQUATION",equation),encoding="utf-8")
    BUILD.mkdir(parents=True,exist_ok=True)
    result = subprocess.run(
        ["pdflatex","-interaction=nonstopmode","-halt-on-error","-no-shell-escape",
         f"-output-directory={BUILD}",str(source)],capture_output=True,text=True
    )
    if result.returncode:
        raise RuntimeError(result.stdout[-5000:])
    pdf = HERE / "dresden-linkedin-banner.pdf"
    shutil.copyfile(BUILD/pdf.name,pdf)
    for width,height,stem in [(1584,396,"dresden-linkedin-banner"),(3168,792,"dresden-linkedin-banner-2x")]:
        subprocess.run(["pdftoppm","-singlefile","-png","-scale-to-x",str(width),
                        "-scale-to-y",str(height),str(pdf),str(HERE/stem)],check=True)
        with Image.open(HERE/f"{stem}.png") as image:
            assert image.size == (width,height)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, help="Exact source photo, to regenerate dresden-fit-overlay.png")
    args = parser.parse_args()
    metrics = check_model()
    write_formula()
    render_plot()
    render_tex()
    if args.source is not None:
        render_overlay(args.source)
    print(json.dumps(metrics,indent=2))
    print(HERE/"dresden-linkedin-banner.png")


if __name__ == "__main__":
    main()
