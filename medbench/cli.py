import argparse
import sys
from pathlib import Path
from datetime import datetime
from rich.console import Console
from rich.table import Table

from .config import load_model_config, load_scenarios_config
from .models import load_pipeline
from .runner import run_single_scenario, run_batch

console = Console()


def cmd_list(args):
    models_cfg = load_model_config(Path(args.models))
    scen_cfg = load_scenarios_config(Path(args.scenarios))

    table = Table(title="Configured Models")
    table.add_column("Key")
    table.add_column("Repo")
    table.add_column("Task")
    for k, m in models_cfg.models.items():
        table.add_row(k, m.repo_id, m.task)
    console.print(table)

    table2 = Table(title="Enabled Scenarios")
    table2.add_column("Scenario")
    table2.add_column("Cases Path")
    table2.add_column("Threshold")
    for scen in scen_cfg.enabled:
        table2.add_row(scen, scen_cfg.cases.get(scen, ""), str(scen_cfg.thresholds.get(scen, "")))
    console.print(table2)


def cmd_run(args):
    models_cfg = load_model_config(Path(args.models))
    scen_cfg = load_scenarios_config(Path(args.scenarios))

    out_dir = Path(args.out_dir) if args.out_dir else Path("runs") / datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir.mkdir(parents=True, exist_ok=True)

    result = run_single_scenario(
        model_key=args.model_key,
        scenario=args.scenario,
        models_cfg=models_cfg,
        scen_cfg=scen_cfg,
        out_dir=out_dir,
        max_cases=args.max_cases,
    )
    if result is None:
        console.print("[red]Run failed[/red]")
        sys.exit(1)


def cmd_batch(args):
    models_cfg = load_model_config(Path(args.models))
    scen_cfg = load_scenarios_config(Path(args.scenarios))

    out_dir = Path(args.out_dir) if args.out_dir else Path("runs") / datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir.mkdir(parents=True, exist_ok=True)

    run_batch(models_cfg=models_cfg, scen_cfg=scen_cfg, out_dir=out_dir, max_cases=args.max_cases)


def build_parser():
    p = argparse.ArgumentParser(prog="medbench", description="Evaluate Hugging Face medical models across scenarios")
    p.add_argument("--models", default="configs/models.yaml", help="Path to models.yaml")
    p.add_argument("--scenarios", default="configs/scenarios.yaml", help="Path to scenarios.yaml")
    p.add_argument("--out-dir", default=None, help="Output directory (default runs/<timestamp>)")
    p.add_argument("--max-cases", type=int, default=None, help="Limit number of cases per scenario")

    sub = p.add_subparsers(dest="cmd", required=True)

    s1 = sub.add_parser("list", help="List configured models and scenarios")
    s1.set_defaults(func=cmd_list)

    s2 = sub.add_parser("run", help="Run a single scenario with one model")
    s2.add_argument("--model-key", required=True, help="Model key from models.yaml")
    s2.add_argument("--scenario", required=True, choices=["diagnosis", "drug_interactions", "summarization", "cds", "imaging"], help="Scenario to run")
    s2.add_argument("--max-cases", type=int, default=None, help="Limit number of cases per scenario")
    s2.set_defaults(func=cmd_run)

    s3 = sub.add_parser("batch", help="Run all scenarios across all models")
    s3.add_argument("--max-cases", type=int, default=None, help="Limit number of cases per scenario")
    s3.set_defaults(func=cmd_batch)

    return p


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()

