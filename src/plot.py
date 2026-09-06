"""Plot benchmark results as a percentage of the maximum achievable score.

    python -m src.plot [results.csv] [-o output.png]

The judge scores each clone 1-10, so a model's score is its mean across tasks
expressed as a percentage of 10. That is comparable across runs of different
sizes - unlike a total, which just rewards whoever attempted more URLs.
"""
import argparse

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

MAX_JUDGE_SCORE = 10


def normalised_scores(df: pd.DataFrame) -> pd.DataFrame:
    """Mean judge score per model, as a percentage of the maximum."""
    scores = (
        df.groupby("model_name")["judge_score"]
        .agg(mean_score="mean", tasks="count")
        .reset_index()
    )
    scores["pct"] = scores["mean_score"] / MAX_JUDGE_SCORE * 100
    return scores.sort_values("pct", ascending=False)


def plot(scores: pd.DataFrame, output_path: str):
    height = 2.4 + 0.85 * len(scores)
    fig, ax = plt.subplots(figsize=(14, height))

    # Title offsets are in figure fractions, so convert from inches to keep the
    # header spacing constant however many models are plotted.
    def frac(inches):
        return 1 - inches / height

    # Colour by the score itself rather than by rank, so a model keeps its shade
    # if the ordering changes and the ramp actually encodes magnitude.
    norm = plt.Normalize(0, 100)
    colors = plt.cm.plasma(norm(scores["pct"]) * 0.8 + 0.1)

    bars = ax.barh(
        range(len(scores)),
        scores["pct"],
        color=colors,
        edgecolor="white",
        linewidth=1.2,
        height=0.8,
    )

    fig.suptitle(
        "Model Performance Benchmark\nSingle Page UI Cloning",
        fontsize=18,
        fontweight="bold",
        color="#1a1a1a",
        ha="center",
        y=frac(0.45),
    )
    fig.text(
        0.5,
        frac(1.15),
        "Mean judge score as % of maximum  (Higher is Better)",
        fontsize=12,
        style="italic",
        color="#666666",
        ha="center",
    )

    ax.set_yticks(range(len(scores)))
    ax.set_yticklabels(
        [f"{m}  (n={n})" for m, n in zip(scores["model_name"], scores["tasks"])],
        fontsize=11,
        color="#333333",
    )
    ax.invert_yaxis()

    ax.set_xlim(0, 100)
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x:.0f}%"))
    ax.tick_params(axis="x", labelsize=11, colors="#333333")

    for bar, pct in zip(bars, scores["pct"]):
        ax.text(
            bar.get_width() + 1.2,
            bar.get_y() + bar.get_height() / 2,
            f"{pct:.1f}%",
            ha="left",
            va="center",
            fontsize=10,
            fontweight="bold",
            color="#1a1a1a",
        )

    ax.grid(True, linestyle="--", alpha=0.6, color="lightgray", axis="x")
    ax.set_axisbelow(True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#CCCCCC")
    ax.spines["bottom"].set_color("#CCCCCC")

    fig.patch.set_facecolor("#FFFFFF")
    ax.set_facecolor("#FFFFFF")

    plt.tight_layout(rect=[0, 0, 1, frac(1.6)])
    fig.savefig(output_path, dpi=150, facecolor=fig.get_facecolor())
    print(f"saved {output_path}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("results", nargs="?", default="data/results.csv")
    parser.add_argument("-o", "--output", default="resources/image.png")
    args = parser.parse_args()

    df = pd.read_csv(args.results)
    scores = normalised_scores(df)
    print(scores[["model_name", "mean_score", "pct", "tasks"]].to_string(index=False))
    plot(scores, args.output)


if __name__ == "__main__":
    main()
