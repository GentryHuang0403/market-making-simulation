from __future__ import annotations

import argparse
from pathlib import Path

from .experiments import (
    run_default_outputs,
    run_parameter_sweep,
    run_sample_simulation,
    save_sample_outputs,
    save_sweep_outputs,
)
from .metrics import compute_metrics


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the market-making simulation sample path or parameter sweep."
    )
    parser.add_argument(
        "--mode",
        choices=["sample", "sweep", "all"],
        default="sample",
        help="Run a single sample path, the parameter sweep, or both.",
    )
    parser.add_argument("--steps", type=int, default=500, help="Number of time steps.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for sample mode.")
    parser.add_argument(
        "--output-dir",
        default="outputs",
        help="Directory where CSV files and figures are saved.",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    output_dir = Path(args.output_dir)

    if args.mode == "sample":
        sample = run_sample_simulation(steps=args.steps, seed=args.seed)
        save_sample_outputs(sample, output_dir)
        metrics = compute_metrics(sample)
        print(f"Saved sample path to {output_dir / 'sample_path.csv'}")
        print(f"Final PnL: {metrics['final_pnl']:.4f}")
        print(f"Fill rate: {metrics['fill_rate']:.4f}")
        return

    if args.mode == "sweep":
        sweep = run_parameter_sweep(steps=args.steps)
        save_sweep_outputs(sweep, output_dir)
        print(f"Saved sweep results to {output_dir / 'sweep_results.csv'}")
        print(f"Rows: {len(sweep)}")
        return

    sample, sweep = run_default_outputs(output_dir)
    print(f"Saved sample path to {output_dir / 'sample_path.csv'}")
    print(f"Saved sweep results to {output_dir / 'sweep_results.csv'}")
    print(f"Sample rows: {len(sample)}")
    print(f"Sweep rows: {len(sweep)}")


if __name__ == "__main__":
    main()
