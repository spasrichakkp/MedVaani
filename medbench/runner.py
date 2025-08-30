from pathlib import Path
from typing import Dict, Any, Optional
import json
import csv
from rich.console import Console
from rich.table import Table

from .config import ModelsConfig, ScenariosConfig
from .models import load_pipeline
from .scenarios import run_diagnosis, run_drug, run_summarization, run_cds, run_imaging, has_imaging_deps

console = Console()


def load_cases(path: Path, limit: Optional[int] = None):
    cases = []
    if not path.exists():
        return cases
    with path.open("r") as f:
        for i, line in enumerate(f):
            if line.strip():
                cases.append(json.loads(line))
            if limit and len(cases) >= limit:
                break
    return cases


def evaluate_scenario(pipe, scenario: str, cases_path: Path, defaults: Dict) -> Dict:
    cases = load_cases(cases_path, defaults.get("limit"))
    results = []
    for case in cases:
        try:
            if scenario == "diagnosis":
                r = run_diagnosis(pipe, case, defaults)
            elif scenario == "drug_interactions":
                r = run_drug(pipe, case, defaults)
            elif scenario == "summarization":
                r = run_summarization(pipe, case, defaults)
            elif scenario == "cds":
                r = run_cds(pipe, case, defaults)
            elif scenario == "imaging":
                r = run_imaging(pipe, case, defaults)
            else:
                raise ValueError(f"Unknown scenario {scenario}")
            results.append({"status": "ok", **r})
        except Exception as e:
            results.append({"status": "error", "error": str(e), "input": str(case)})
    return {"results": results}


def summarize(results: Dict, threshold: float) -> Dict:
    scores = [r.get("score", 0.0) for r in results.get("results", []) if r.get("status") == "ok"]
    if not scores:
        return {"mean": 0.0, "pass_rate": 0.0, "n": 0}
    mean = sum(scores) / len(scores)
    passed = sum(1 for s in scores if s >= threshold)
    return {"mean": mean, "pass_rate": passed / len(scores), "n": len(scores)}


def write_results(out_dir: Path, model_key: str, scenario: str, results: Dict):
    out_dir.mkdir(parents=True, exist_ok=True)
    jsonl = out_dir / f"{model_key}__{scenario}__results.jsonl"
    with jsonl.open("w") as f:
        for r in results["results"]:
            f.write(json.dumps(r) + "\n")


def write_summary_csv_md(out_dir: Path, rows):
    # CSV
    csv_path = out_dir / "summary.csv"
    with csv_path.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["model", "scenario", "mean", "pass_rate", "n", "threshold"])
        for r in rows:
            w.writerow([r["model"], r["scenario"], r["mean"], r["pass_rate"], r["n"], r["threshold"]])
    # Markdown
    md = out_dir / "summary.md"
    with md.open("w") as f:
        f.write("| model | scenario | mean | pass_rate | n | threshold |\n")
        f.write("|---|---:|---:|---:|---:|---:|\n")
        for r in rows:
            f.write(f"| {r['model']} | {r['scenario']} | {r['mean']:.3f} | {r['pass_rate']:.2%} | {r['n']} | {r['threshold']} |\n")


def run_single_scenario(model_key: str, scenario: str, models_cfg: ModelsConfig, scen_cfg: ScenariosConfig, out_dir: Path, max_cases: Optional[int] = None) -> Optional[Dict]:
    # Validate imaging deps
    if scenario == "imaging" and not has_imaging_deps():
        console.print("[yellow]Imaging dependencies not present. Skipping imaging scenario.[/yellow]")
        return None

    # Load model pipeline with robust error handling
    try:
        pipe = load_pipeline(model_key, models_cfg)
    except Exception as e:
        console.print(f"[red]Failed to load model {model_key}: {e}[/red]")
        return None

    cases_path = Path(scen_cfg.cases.get(scenario, ""))
    defaults = models_cfg.defaults.get("generation", {}).copy()
    if max_cases:
        defaults["limit"] = max_cases

    results = evaluate_scenario(pipe, scenario, cases_path, defaults)
    summ = summarize(results, scen_cfg.thresholds.get(scenario, 0.5))
    write_results(out_dir, model_key, scenario, results)

    # Present table
    table = Table(title=f"{model_key} — {scenario}")
    table.add_column("mean")
    table.add_column("pass_rate")
    table.add_column("n")
    table.add_row(f"{summ['mean']:.3f}", f"{summ['pass_rate']:.2%}", str(summ['n']))
    console.print(table)

    return {"summary": summ, "results": results}


def run_batch(models_cfg: ModelsConfig, scen_cfg: ScenariosConfig, out_dir: Path, max_cases: Optional[int] = None):
    rows = []
    for model_key in models_cfg.models.keys():
        for scenario in scen_cfg.enabled:
            r = run_single_scenario(model_key, scenario, models_cfg, scen_cfg, out_dir, max_cases)
            if r is None:
                continue
            summ = r["summary"]
            rows.append({
                "model": model_key,
                "scenario": scenario,
                "mean": summ["mean"],
                "pass_rate": summ["pass_rate"],
                "n": summ["n"],
                "threshold": scen_cfg.thresholds.get(scenario, 0.5),
            })
    write_summary_csv_md(out_dir, rows)
    console.print(f"Wrote batch summary to {out_dir}")

