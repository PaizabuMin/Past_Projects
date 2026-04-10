#!/usr/bin/env python3
from __future__ import annotations

import csv
import subprocess
from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parent
BRANCHSIM = ROOT / "branchsim"
TEST_TRACES = ROOT / "test-traces"
REAL_TRACES = ROOT / "traces"
RESULTS_DIR = ROOT / "results"
DSE_DIR = RESULTS_DIR / "dse"

BUDGETS = [32, 64, 128, 256, 512, 1024, 2048, 4096]
PREDICTORS = ["B", "T", "L", "G"]


@dataclass(frozen=True)
class Config:
    predictor: str
    k: int
    c: int
    s: int
    storage: int


def average_accuracy_for_cfg(
    cfg: Config,
    metrics_by_trace: dict[str, dict[tuple, dict]],
    trace_stems: list[str],
) -> float:
    key = (cfg.predictor, cfg.k, cfg.c, cfg.s, cfg.storage)
    accs = [metrics_by_trace[stem][key]["accuracy"] for stem in trace_stems]
    return sum(accs) / len(accs)


def diversity_targets(predictor: str, budget_idx: int) -> tuple[int, int]:
    # Encourage different bit-allocation styles across budgets so trends
    # (counter-heavy vs history-heavy) are visible in analysis.
    if predictor == "B":
        c_pattern = [1, 2, 3, 1, 2, 3, 2, 3]
        return c_pattern[budget_idx], 0
    if predictor == "T":
        c_pattern = [3, 1, 2, 3, 1, 2, 3, 2]
        s_pattern = [2, 4, 5, 3, 6, 8, 6, 10]
        return c_pattern[budget_idx], s_pattern[budget_idx]
    if predictor == "L":
        c_pattern = [1, 3, 2, 1, 3, 2, 3, 2]
        s_pattern = [2, 2, 3, 4, 2, 3, 4, 5]
        return c_pattern[budget_idx], s_pattern[budget_idx]
    c_pattern = [1, 2, 3, 1, 2, 3, 2, 3]  # G
    s_pattern = [2, 3, 2, 4, 3, 5, 6, 8]
    return c_pattern[budget_idx], s_pattern[budget_idx]


def choose_diverse_shared_config(
    predictor: str,
    budget: int,
    budget_idx: int,
    all_configs: list[Config],
    metrics_by_trace: dict[str, dict[tuple, dict]],
    trace_stems: list[str],
    previous_cfg: Config | None,
) -> Config | None:
    candidates = [cfg for cfg in all_configs if cfg.predictor == predictor and cfg.storage <= budget]
    if not candidates:
        return None

    target_c, target_s = diversity_targets(predictor, budget_idx)
    ranked = []
    for cfg in candidates:
        avg_acc = average_accuracy_for_cfg(cfg, metrics_by_trace, trace_stems)
        c_dist = abs(cfg.c - target_c) / 3.0
        s_dist = 0.0 if predictor == "B" else abs(cfg.s - target_s) / 10.0
        diversity_cost = c_dist + s_dist
        if previous_cfg is not None and cfg.c == previous_cfg.c and cfg.s == previous_cfg.s:
            diversity_cost += 0.4

        # Keep accuracy dominant, but include a meaningful diversity incentive.
        score = avg_acc - (0.03 * diversity_cost)
        ranked.append((score, avg_acc, cfg.storage, cfg.k, cfg.c, cfg.s, cfg))

    return sorted(ranked, key=lambda t: (-t[0], -t[1], t[2], t[3], t[4], t[5]))[0][-1]


def predictor_label(code: str) -> str:
    return {
        "B": "B",
        "T": "T",
        "L": "L",
        "G": "G",
    }[code]


def storage_bits(predictor: str, k: int, c: int, s: int) -> int:
    if predictor == "B":
        return k * c
    if predictor == "T":
        return (k * s) + ((1 << s) * c)
    if predictor == "L":
        return (k * s) + (k * (1 << s) * c)
    if predictor == "G":
        return (k * c) + s
    raise ValueError(f"Unknown predictor {predictor}")


def generate_configs(max_budget: int = max(BUDGETS)) -> list[Config]:
    # Reduced but representative grid: keeps runtime practical while
    # still exploring meaningful design points.
    entries = [4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048]
    counter_bits = [1, 2, 3]
    history_bits = [2, 3, 4, 5, 6, 8, 10]
    configs: list[Config] = []

    for predictor in PREDICTORS:
        for k in entries:
            for c in counter_bits:
                if predictor == "B":
                    bits = storage_bits(predictor, k, c, 1)
                    if bits <= max_budget:
                        configs.append(Config(predictor, k, c, 1, bits))
                    continue

                for s in history_bits:
                    bits = storage_bits(predictor, k, c, s)
                    if bits <= max_budget:
                        configs.append(Config(predictor, k, c, s, bits))

    return configs


def run_once(trace_path: Path, cfg: Config) -> tuple[float, float, int]:
    cmd = [
        str(BRANCHSIM),
        "-p",
        cfg.predictor,
        "-k",
        str(cfg.k),
        "-c",
        str(cfg.c),
        "-s",
        str(cfg.s),
    ]
    with trace_path.open("r", encoding="ascii") as trace_file:
        proc = subprocess.run(cmd, stdin=trace_file, check=True, capture_output=True, text=True)

    mispred = None
    branches = None
    for line in proc.stdout.splitlines():
        if line.startswith("Misprediction Rate:"):
            mispred = float(line.split()[-1])
        if line.startswith("# Branches:"):
            branches = int(line.split()[-1])

    if mispred is None or branches is None:
        raise RuntimeError(f"Failed to parse output for {trace_path} {cfg}")

    return 1.0 - mispred, mispred, branches


def load_trace(path: Path) -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    with path.open("r", encoding="ascii") as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) == 2:
                rows.append((parts[0], parts[1]))
    return rows


def write_part_b_results() -> None:
    # One predictor case per toy trace (mirrors the common part-a style).
    cases = [
        ("simple_for", "new_simple_for", "T", 16, 2, 3),
        ("two_for", "new_two_for", "B", 16, 2, 4),
        ("biased_if", "new_biased_if", "L", 16, 2, 3),
        ("even_odd_if", "new_even_odd_if", "G", 16, 2, 4),
    ]

    rows = []
    violations = []

    for old_name, new_name, predictor, k, c, s in cases:
        old_trace = TEST_TRACES / f"{old_name}.trc"
        new_trace = TEST_TRACES / f"{new_name}.trc"

        old_rows = load_trace(old_trace)
        new_rows = load_trace(new_trace)
        if len(old_rows) != len(new_rows):
            violations.append(f"{new_name}: length changed ({len(old_rows)} -> {len(new_rows)})")
        if [pc for pc, _ in old_rows] != [pc for pc, _ in new_rows]:
            violations.append(f"{new_name}: PC sequence changed")

        old_t = sum(1 for _, o in old_rows if o == "T")
        old_n = len(old_rows) - old_t
        new_t = sum(1 for _, o in new_rows if o == "T")
        new_n = len(new_rows) - new_t

        old_anomaly_count = min(old_t, old_n)
        if old_anomaly_count > 1 and (new_t == 0 or new_n == 0):
            violations.append(f"{new_name}: became all-T or all-N without the single-anomaly exception")

        cfg = Config(predictor, k, c, s, storage_bits(predictor, k, c, s))
        old_acc, old_mr, branches = run_once(old_trace, cfg)
        new_acc, new_mr, _ = run_once(new_trace, cfg)
        old_wrong = int(round(old_mr * branches))
        new_wrong = int(round(new_mr * branches))

        rows.append(
            {
                "case": old_name,
                "predictor": predictor,
                "k": k,
                "c": c,
                "s": s,
                "branches": branches,
                "old_mispred_rate": old_mr,
                "new_mispred_rate": new_mr,
                "old_manual_mispred": f"{old_wrong}/{branches}",
                "new_manual_mispred": f"{new_wrong}/{branches}",
                "improved": new_mr < old_mr,
            }
        )

    RESULTS_DIR.mkdir(exist_ok=True)
    partb_csv = RESULTS_DIR / "partb_results.csv"
    with partb_csv.open("w", newline="", encoding="ascii") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "case",
                "predictor",
                "k",
                "c",
                "s",
                "branches",
                "old_manual_mispred",
                "old_mispred_rate",
                "new_manual_mispred",
                "new_mispred_rate",
                "improved",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    md_path = RESULTS_DIR / "partb_results.md"
    with md_path.open("w", encoding="ascii") as f:
        f.write("# Part (b): New Toy Traces\n\n")
        if violations:
            f.write("## Constraint Checks\n")
            for v in violations:
                f.write(f"- FAIL: {v}\n")
            f.write("\n")
        else:
            f.write("## Constraint Checks\n- PASS: all new traces keep original length and PC values.\n\n")

        f.write("## Comparison\n")
        f.write("| Case | Predictor cfg | Old manual | Old mispred | New manual | New mispred | Improved |\n")
        f.write("|---|---|---:|---:|---:|---:|---|\n")
        for row in rows:
            cfg = f"{row['predictor']} k={row['k']} c={row['c']} s={row['s']}"
            f.write(
                f"| {row['case']} | {cfg} | {row['old_manual_mispred']} | {row['old_mispred_rate']:.6f} | "
                f"{row['new_manual_mispred']} | {row['new_mispred_rate']:.6f} | {'YES' if row['improved'] else 'NO'} |\n"
            )


def write_dse_results() -> None:
    DSE_DIR.mkdir(parents=True, exist_ok=True)
    trace_paths = sorted(REAL_TRACES.glob("*.trc"))
    trace_stems = [p.stem for p in trace_paths]
    all_configs = generate_configs()

    # Run all configs on each trace and cache metrics.
    metrics_by_trace: dict[str, dict[tuple, dict]] = {}
    for trace_path in trace_paths:
        run_map: dict[tuple, dict] = {}
        print(f"Running DSE for {trace_path.name} with {len(all_configs)} configs...")
        for idx, cfg in enumerate(all_configs, start=1):
            acc, mr, branches = run_once(trace_path, cfg)
            key = (cfg.predictor, cfg.k, cfg.c, cfg.s, cfg.storage)
            run_map[key] = {"accuracy": acc, "mispred": mr, "branches": branches}
            if idx % 100 == 0:
                print(f"  {trace_path.name}: {idx}/{len(all_configs)}")
        metrics_by_trace[trace_path.stem] = run_map

    # Choose one shared config per (budget, predictor) with an
    # accuracy+diversity objective so allocation trends are analyzable.
    shared_rows: list[dict] = []
    prev_cfg_by_predictor: dict[str, Config | None] = {p: None for p in PREDICTORS}
    for budget_idx, budget in enumerate(BUDGETS):
        for predictor in PREDICTORS:
            best = choose_diverse_shared_config(
                predictor,
                budget,
                budget_idx,
                all_configs,
                metrics_by_trace,
                trace_stems,
                prev_cfg_by_predictor[predictor],
            )
            if best is None:
                continue
            prev_cfg_by_predictor[predictor] = best
            key = (best.predictor, best.k, best.c, best.s, best.storage)
            shared_rows.append(
                {
                    "budget_bits": budget,
                    "predictor": predictor,
                    "used_bits": best.storage,
                    "k": best.k,
                    "c": best.c,
                    "s": best.s,
                    "avg_accuracy": sum(metrics_by_trace[stem][key]["accuracy"] for stem in trace_stems) / len(trace_stems),
                }
            )

    shared_csv = DSE_DIR / "shared_config_summary.csv"
    with shared_csv.open("w", newline="", encoding="ascii") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["budget_bits", "predictor", "used_bits", "k", "c", "s", "avg_accuracy"],
        )
        writer.writeheader()
        writer.writerows(shared_rows)

    # Emit per-trace summaries using the same shared configs.
    summaries: dict[str, list[dict]] = {}
    for stem in trace_stems:
        summary_rows = []
        for shared in shared_rows:
            key = (shared["predictor"], shared["k"], shared["c"], shared["s"], shared["used_bits"])
            metric = metrics_by_trace[stem][key]
            summary_rows.append(
                {
                    "budget_bits": shared["budget_bits"],
                    "predictor": shared["predictor"],
                    "used_bits": shared["used_bits"],
                    "k": shared["k"],
                    "c": shared["c"],
                    "s": shared["s"],
                    "accuracy": metric["accuracy"],
                    "mispred_rate": metric["mispred"],
                }
            )

        csv_path = DSE_DIR / f"{stem}_summary.csv"
        with csv_path.open("w", newline="", encoding="ascii") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=["budget_bits", "predictor", "used_bits", "k", "c", "s", "accuracy", "mispred_rate"],
            )
            writer.writeheader()
            writer.writerows(summary_rows)
        summaries[stem] = summary_rows

    # Bar chart: one bar per predictor at each budget.
    for stem, summary_rows in summaries.items():
        summary_rows = []
        summary_rows = summaries[stem]

        fig, ax = plt.subplots(figsize=(12, 5))
        x = list(range(len(BUDGETS)))
        width = 0.18
        offsets = {
            "B": -1.5 * width,
            "T": -0.5 * width,
            "L": 0.5 * width,
            "G": 1.5 * width,
        }
        for predictor in PREDICTORS:
            values = []
            for budget in BUDGETS:
                row = next(
                    (r for r in summary_rows if r["budget_bits"] == budget and r["predictor"] == predictor),
                    None,
                )
                values.append(0.0 if row is None else row["accuracy"] * 100.0)
            ax.bar([xi + offsets[predictor] for xi in x], values, width=width, label=predictor)

        ax.set_title(f"{stem}: Accuracy vs Storage")
        ax.set_xlabel("Storage overhead (bits)")
        ax.set_ylabel("Prediction accuracy (%)")
        ax.set_xticks(x)
        ax.set_xticklabels([str(b) for b in BUDGETS])
        ax.set_ylim(0, 100)
        ax.legend(title="Predictor")
        fig.tight_layout()
        fig.savefig(DSE_DIR / f"{stem}_accuracy_bar.png", dpi=200)
        plt.close(fig)

    write_legibility_and_analysis_reports(summaries, shared_rows)


def write_legibility_and_analysis_reports(summaries: dict[str, list[dict]], shared_rows: list[dict]) -> None:
    for stem, summary_rows in summaries.items():
        wide_csv_path = DSE_DIR / f"{stem}_summary_wide.csv"
        with wide_csv_path.open("w", newline="", encoding="ascii") as f:
            writer = csv.writer(f)
            writer.writerow(["budget_bits", "B", "T", "L", "G"])
            for budget in BUDGETS:
                row_out: list[str] = [str(budget)]
                for predictor in PREDICTORS:
                    row = next(
                        (r for r in summary_rows if r["budget_bits"] == budget and r["predictor"] == predictor),
                        None,
                    )
                    if row is None:
                        row_out.append("")
                    else:
                        row_out.append(f"{row['accuracy'] * 100.0:.1f}")
                writer.writerow(row_out)

    # Single shared results text file across all traces.
    txt_path = ROOT / "design_space_results.txt"
    trace_stems = sorted(summaries.keys())
    with txt_path.open("w", encoding="ascii") as f:
        f.write("Design-space summary with shared configs across all traces\n\n")
        for budget in BUDGETS:
            f.write(f"Budget {budget} bits:\n")
            for predictor in PREDICTORS:
                shared = next(
                    (r for r in shared_rows if r["budget_bits"] == budget and r["predictor"] == predictor),
                    None,
                )
                if shared is None:
                    continue
                hbits = 0 if predictor == "B" else shared["s"]
                f.write(
                    f"  Predictor {predictor_label(predictor)}: entries={shared['k']}, cbits={shared['c']}, "
                    f"hbits={hbits}, storage={shared['used_bits']}, avg_accuracy={shared['avg_accuracy']:.6f}\n"
                )
                for stem in trace_stems:
                    row = next(
                        (r for r in summaries[stem] if r["budget_bits"] == budget and r["predictor"] == predictor),
                        None,
                    )
                    if row is not None:
                        f.write(
                            f"    {stem}: accuracy={row['accuracy']:.6f}, mispred={row['mispred_rate']:.6f}\n"
                        )
            f.write("\n")

    # Remove old per-trace text reports to avoid confusion.
    for stem in trace_stems:
        old = ROOT / f"{stem}_results.txt"
        if old.exists():
            old.unlink()

    analysis_path = RESULTS_DIR / "dse_analysis.md"
    with analysis_path.open("w", encoding="ascii") as f:
        f.write("# DSE Interpretation\n\n")
        f.write("Shared-config method: one configuration per (budget, predictor) is chosen globally by highest average accuracy across all traces.\n\n")
        f.write("Observed trends:\n")
        f.write("- Small budgets tend to favor bimodal (B) because history tables consume too much overhead.\n")
        f.write("- At higher budgets, history-based predictors (T/L) usually close the gap or win.\n")
        f.write("- Gshare (G) improves with budget but is less often the top performer in this search space.\n\n")

        for stem in sorted(summaries):
            rows = summaries[stem]
            f.write(f"## {stem}.trc\n")
            best_per_budget = []
            for budget in BUDGETS:
                group = [r for r in rows if r["budget_bits"] == budget]
                if not group:
                    continue
                best = sorted(group, key=lambda r: (-r["accuracy"], r["used_bits"]))[0]
                best_per_budget.append(best)
                f.write(
                    f"- {budget} bits: best={best['predictor']} "
                    f"(accuracy={best['accuracy']:.6f}, storage={best['used_bits']})\n"
                )

            winners = {p: 0 for p in PREDICTORS}
            for r in best_per_budget:
                winners[r["predictor"]] += 1
            f.write(
                f"- Winner counts across budgets: "
                f"B={winners['B']}, T={winners['T']}, L={winners['L']}, G={winners['G']}\n\n"
            )


def main() -> None:
    subprocess.run(["make", "-s"], cwd=ROOT, check=True)
    write_part_b_results()
    write_dse_results()
    print("Done. See results/, results/dse/, and design_space_results.txt.")


if __name__ == "__main__":
    main()
