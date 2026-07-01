"""
Figure-saving utilities for paper-ready output.

Usage:
    from lib.figure_utils import save_figure
    fig, ax = plt.subplots()
    ...
    save_figure(fig, "my-figure", paper=True)  # writes to output/figures/ + paper-acm/fig/
"""

from pathlib import Path
from lib.paths import OUTPUT_FIGURES, PAPER_ACM_FIG


def save_figure(fig, name: str, *, paper: bool = True, dpi: int = 300) -> list[Path]:
    """
    Save a matplotlib figure as PNG and PDF.

    Writes to `output/figures/` and optionally copies to `paper-acm/fig/`.

    Args:
        fig: matplotlib Figure
        name: Base filename (without extension), e.g. "fig-bertopic-divergence"
        paper: If True, also copy PNG+PDF to paper-acm/fig/
        dpi: Output resolution

    Returns:
        List of paths written.
    """
    written: list[Path] = []

    OUTPUT_FIGURES.mkdir(parents=True, exist_ok=True)

    png_path = OUTPUT_FIGURES / f"{name}.png"
    pdf_path = OUTPUT_FIGURES / f"{name}.pdf"

    fig.savefig(png_path, dpi=dpi, bbox_inches="tight")
    written.append(png_path)

    fig.savefig(pdf_path, dpi=dpi, bbox_inches="tight")
    written.append(pdf_path)

    if paper:
        PAPER_ACM_FIG.mkdir(parents=True, exist_ok=True)
        import shutil
        shutil.copy2(png_path, PAPER_ACM_FIG / f"{name}.png")
        shutil.copy2(pdf_path, PAPER_ACM_FIG / f"{name}.pdf")
        written.append(PAPER_ACM_FIG / f"{name}.png")
        written.append(PAPER_ACM_FIG / f"{name}.pdf")

    return written
