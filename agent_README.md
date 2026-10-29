# linkedin-banner

A complete smooth-function LinkedIn banner. Plot the function to reveal the skyline.

![Formula banner](./dresden-linkedin-banner.png)

The banner contains the complete formula. There is no hidden coefficient table.
The final model does not depend on the superseded Fourier fit.

## Files

- [`dresden-linkedin-banner.png`](./dresden-linkedin-banner.png): 1584 × 396, 4:1.
- [`dresden-linkedin-banner-2x.png`](./dresden-linkedin-banner-2x.png): 3168 × 792.
- [`dresden-linkedin-banner.tex`](./dresden-linkedin-banner.tex): editable TeX.
- [`dresden-linkedin-banner.pdf`](./dresden-linkedin-banner.pdf): vector version.
- [`dresden-banner-plot.png`](./dresden-banner-plot.png): the actual formula plotted
  with equal horizontal and vertical scales.
- [`dresden-fit-overlay.png`](./dresden-fit-overlay.png): the exact final banner
  function plotted over the source photograph.
- [`dresden-banner-formula.txt`](./dresden-banner-formula.txt): Desmos expressions.
- [`dresden-banner-model.json`](./dresden-banner-model.json): all numeric values.
- [`dresden-outline.csv`](./dresden-outline.csv): the measured photo outline used
  for numerical checks.

## How the shorter formula works

For the current value of x, the banner defines this abbreviation:

```text
E^p_(mu,w) = exp(-((x-mu)/w)^p)
```

The function is a linear baseline plus 18 of these terms. Powers 2, 4, 8, and
16 give rounded domes or steeper tower walls. Every power is a positive even
integer, so this is one analytic function on all of R, not a piecewise function.

The 18-term model used 56 fitted values: 18 amplitudes, 18 centers, 18 widths,
plus a baseline and a slope. The powers were additional fixed design choices,
not fitted coefficients. All fitted values were rounded to integers for the
banner. Centers, widths, and powers are printed explicitly; they are not omitted
from the formula.

The photographed portion is 0 <= x <= 1280. Heights are measured in image pixels
above the horizontal line y = 570. The parametric form is (t, f(t)). Outside the
photographed portion, the formula tends toward its linear baseline; unlike the
earlier cosine fit, it is not periodic.

## Trade-off and checks

The main dome, lantern, towers, and roof groups remain. Small statues, roof
ornaments, sharp cornice details, and leaves were deliberately simplified.

The rounded formula is checked directly against the brightness-extracted,
manually corrected photo outline. The three main peak positions
remain within one pixel horizontally, and their heights remain within about
1.1 pixels of the corresponding photo-read values. See
[`dresden-banner-check.json`](./dresden-banner-check.json).

These are numerical comparisons with the extracted outline, not an independent test
that every viewer will recognize Dresden. The banner was inspected at its native
1584 × 396 size; actual LinkedIn display scaling and cropping were not tested.
The lower-left area is largely clear to reduce profile-photo overlap.

## Reproduce

```sh
uv run skyline_banner.py
```

The script reads only the compact JSON model to evaluate the function, and uses
the retained CSV outline for numerical checks. TeX rendering requires `pdflatex`
and `pdftoppm`.

To also regenerate the photo overlay, provide the exact source photograph:

```sh
uv run skyline_banner.py --source /path/to/Dresden_skyline.jpg
```

The source photograph is available through the attribution link below. It is
not bundled with these files.

## Attribution

Outline adapted from Michele Vascellari's
[Dresden skyline photograph](https://commons.wikimedia.org/wiki/File:Dresden_skyline.jpg).
Source and derived outline/renders:
[CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).
Changes: outline extraction, analytic fitting, simplification, rounding, and
formula/plot rendering.
