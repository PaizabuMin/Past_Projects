#!/usr/bin/env python3
import csv
import os
from collections import defaultdict

import matplotlib.pyplot as plt
from matplotlib.ticker import StrMethodFormatter


INPUT_CSV = "experiment_results_full.csv"
OUT_DIR = "figures"


def main():
    data = defaultdict(list)
    with open(INPUT_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            data[row["benchmark"]].append(row)

    os.makedirs(OUT_DIR, exist_ok=True)

    for benchmark, rows in sorted(data.items()):
        rows.sort(key=lambda r: int(r["config"].replace("Config", "")))
        labels = [r["config"] for r in rows]
        ipc = [float(r["ipc"]) for r in rows]
        stalls = [int(r["issue_stall"]) for r in rows]

        x = list(range(len(labels)))

        fig, ax1 = plt.subplots(figsize=(10, 5.5))
        ax1.bar(x, ipc, width=0.55, color="#1f77b4", label="IPC")
        ax1.set_ylabel("IPC")
        ax1.set_xticks(x)
        ax1.set_xticklabels(labels)
        ax1.set_xlabel("Configuration")
        ax1.set_title(f"{benchmark}: IPC vs Issue Stall")
        ax1.grid(axis="y", alpha=0.25)
        if benchmark == "gen-lin-recc":
            ax1.set_ylim(0.0, 0.6)

        ax2 = ax1.twinx()
        ax2.plot(x, stalls, marker="o", linewidth=2.2, color="#ff7f0e", label="Issue Stall")
        ax2.set_ylabel("Issue Stall")
        ax2.yaxis.set_major_formatter(StrMethodFormatter("{x:,.0f}"))

        handles1, labels1 = ax1.get_legend_handles_labels()
        handles2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(handles1 + handles2, labels1 + labels2, loc="upper left")

        fig.tight_layout()
        fig.savefig(os.path.join(OUT_DIR, f"{benchmark}_ipc_issue_stall.png"), dpi=160)
        plt.close(fig)


if __name__ == "__main__":
    main()
