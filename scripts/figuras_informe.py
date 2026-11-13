"""Figuras del informe (docs/figuras/).

Uso: uv run --with matplotlib python scripts/figuras_informe.py

Figura 1: flujo del entorno y del verificador.
Figura 2: pass@1 y pass@5 por dificultad y modelo, en ambas condiciones. Las cifras son las
de la tabla por dificultad del informe (sección 5), calculadas por scripts/analyze_results.py.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch  # noqa: E402

OUT = Path(__file__).resolve().parents[1] / "docs" / "figuras"
SURFACE = "#fcfcfb"
INK = "#1f1f1e"
MUTED = "#6b6a63"
GRID = "#e4e3de"

# Paleta categórica validada (orden fijo); el modelo objetivo usa el slot 1.
MODELS = [
    ("Qwen3-1.7B con thinking (objetivo)", "#2a78d6"),
    ("Qwen3-4B sin thinking", "#eb6834"),
    ("Qwen3-1.7B sin thinking", "#1baf7a"),
    ("Qwen3-0.6B con thinking (parcial)", "#eda100"),
    ("Llama-3.2-1B", "#e87ba4"),
]
# (pass@1, pass@5) en % por dificultad: easy, medium, hard.
DATA = {
    "Con datos visibles": {
        "Qwen3-1.7B con thinking (objetivo)": [(90, 100), (60, 93), (43, 73)],
        "Qwen3-4B sin thinking": [(100, 100), (87, 97), (37, 40)],
        "Qwen3-1.7B sin thinking": [(63, 93), (23, 57), (3, 20)],
        "Qwen3-0.6B con thinking (parcial)": [(12, 46), (4, 17), (4, 13)],
        "Llama-3.2-1B": [(0, 0), (0, 0), (0, 0)],
    },
    "Con herramientas": {
        "Qwen3-1.7B con thinking (objetivo)": [(63, 100), (43, 73), (17, 33)],
        "Qwen3-4B sin thinking": [(93, 100), (83, 97), (37, 47)],
        "Qwen3-1.7B sin thinking": [(40, 77), (23, 40), (10, 23)],
        "Qwen3-0.6B con thinking (parcial)": [(17, 50), (17, 22), (4, 4)],
        "Llama-3.2-1B": [(0, 0), (0, 0), (0, 0)],
    },
}
LEVELS = ["Easy", "Medium", "Hard"]


def _style(ax) -> None:
    ax.set_facecolor(SURFACE)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(MUTED)
        ax.spines[side].set_linewidth(0.8)
    ax.tick_params(colors=MUTED, labelsize=9, length=3)
    ax.grid(axis="y", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)


def figure_pass_at_k() -> None:
    fig, axes = plt.subplots(1, 2, figsize=(9.5, 3.9), sharey=True, facecolor=SURFACE)
    offsets = [-0.28, -0.14, 0.0, 0.14, 0.28]
    for ax, (title, rows) in zip(axes, DATA.items()):
        _style(ax)
        for (name, color), dx in zip(MODELS, offsets):
            for level, (p1, p5) in enumerate(rows[name]):
                x = level + dx
                ax.plot([x, x], [p1, p5], color=color, linewidth=2, solid_capstyle="round", zorder=2)
                ax.scatter([x], [p5], s=42, facecolor=SURFACE, edgecolor=color, linewidth=2, zorder=3)
                ax.scatter([x], [p1], s=42, color=color, edgecolor=SURFACE, linewidth=1.5, zorder=4)
        ax.set_title(title, color=INK, fontsize=11, loc="left")
        ax.set_xticks(range(3), LEVELS)
        ax.set_xlim(-0.5, 2.5)
        ax.set_ylim(-4, 104)
    axes[0].set_ylabel("Instancias resueltas (%)", color=INK, fontsize=10)
    handles = [Line2D([], [], color=c, marker="o", linewidth=2, markersize=6, label=n) for n, c in MODELS]
    handles += [
        Line2D([], [], color=MUTED, marker="o", linestyle="", markersize=6, label="pass@1 (relleno)"),
        Line2D([], [], color=MUTED, marker="o", linestyle="", markersize=6, markerfacecolor=SURFACE,
               markeredgewidth=2, label="pass@5 (hueco)"),
    ]
    fig.legend(handles=handles, loc="lower center", ncol=4, frameon=False, fontsize=8.5,
               labelcolor=INK, bbox_to_anchor=(0.5, -0.02))
    fig.tight_layout(rect=(0, 0.13, 1, 1))
    fig.savefig(OUT / "figura2_pass_por_dificultad.png", dpi=200, facecolor=SURFACE)
    plt.close(fig)


def _box(ax, x, y, w, h, title, body, color):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.01,rounding_size=0.015",
                                facecolor=SURFACE, edgecolor=color, linewidth=1.6))
    ax.text(x + w / 2, y + h - 0.035, title, ha="center", va="top", fontsize=9.5,
            color=INK, weight="bold")
    ax.text(x + w / 2, y + h - 0.10, body, ha="center", va="top", fontsize=8, color=MUTED,
            linespacing=1.35)


def _arrow(ax, start, end, label=None, rad=0.0):
    ax.add_patch(FancyArrowPatch(start, end, arrowstyle="-|>", mutation_scale=11, color=MUTED,
                                 linewidth=1.2, connectionstyle=f"arc3,rad={rad}"))
    if label:
        mx, my = (start[0] + end[0]) / 2, (start[1] + end[1]) / 2
        ax.text(mx, my + 0.025, label, ha="center", va="bottom", fontsize=7.5, color=MUTED)


def figure_flow() -> None:
    fig, ax = plt.subplots(figsize=(9.5, 3.8), facecolor=SURFACE)
    ax.set_facecolor(SURFACE)
    ax.set_xlim(-0.02, 1.02)
    ax.set_ylim(0, 1)
    ax.axis("off")
    blue, orange, aqua = "#2a78d6", "#eb6834", "#1baf7a"
    pad = 0.012

    # Fila superior: generación e interacción.
    top_y, top_h = 0.62, 0.34
    _box(ax, 0.00, top_y, 0.20, top_h, "Generador",
         "objetivos → inventario\nsolver independiente\ncalcula expected\n(protegido)", aqua)
    _box(ax, 0.26, top_y, 0.18, top_h, "Prompt",
         "reglas + solicitud\nvisible: tabla\ntools: catálogo", aqua)
    _box(ax, 0.50, top_y, 0.18, top_h, "Modelo", "razona en <think>\nllama o responde\ncon <answer>", blue)
    _box(ax, 0.80, top_y, 0.20, top_h, "get_inventory",
         "devuelve físico\ny reservado\n(nunca el disponible)\nmáx. 2 rondas", orange)
    _arrow(ax, (0.20 + pad, 0.79), (0.26 - pad, 0.79))
    _arrow(ax, (0.44 + pad, 0.79), (0.50 - pad, 0.79))
    _arrow(ax, (0.68 + pad, 0.84), (0.80 - pad, 0.84), "llamadas")
    _arrow(ax, (0.80 - pad, 0.72), (0.68 + pad, 0.72), "resultados")

    # Fila inferior: verificador.
    ax.text(1.00, 0.45, "Verificador: reward(prompt, completion) → 0 o 1", fontsize=9.5,
            color=INK, weight="bold", ha="right")
    steps = [
        ("1. Instancia", "sha256(prompt)\n→ expected"),
        ("2. Trayectoria", "re-ejecuta llamadas,\nexige los datos\nnecesarios"),
        ("3. Bloque", "quita <think>,\nexige un solo\n<answer>"),
        ("4. Valores", "interpreta por tipo;\nlo ambiguo\nse rechaza"),
        ("5. Compara", "cada campo\ncontra expected\n→ 1 si todos"),
    ]
    width, gap, x = 0.164, 0.045, 0.0
    for i, (title, body) in enumerate(steps):
        _box(ax, x, 0.06, width, 0.30, title, body, MUTED)
        if i < len(steps) - 1:
            _arrow(ax, (x + width + pad, 0.21), (x + width + gap - pad, 0.21))
        x += width + gap
    _arrow(ax, (0.59, top_y - pad), (0.08, 0.36 + pad), "trayectoria", rad=-0.12)
    fig.tight_layout()
    fig.savefig(OUT / "figura1_flujo.png", dpi=200, facecolor=SURFACE)
    plt.close(fig)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    figure_flow()
    figure_pass_at_k()
    print("figuras en", OUT)
