"""
Structured Clinical Entity Extraction using LangExtract
========================================================
Entry point — parses CLI args, wires together data loading,
extraction, analysis, and output modules.

Usage:
    python main.py --samples 5               # quick test
    python main.py --passes 3 --samples 20   # multi-pass
    python main.py --compare-passes           # recall comparison
    python main.py --specialty "Orthopedic"   # filter specialty
"""

import argparse
import os
import sys
import time

from dotenv import load_dotenv

load_dotenv()  # reads .env file into os.environ automatically

from config import AppConfig, ModelConfig, ExtractionConfig, DataConfig, OutputConfig
from data.loader import load_mtsamples
from extraction.engine import extract_batch
from analysis.stats import compute_stats, print_report, compare_passes
from output.export import save_results


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Clinical Entity Extraction with LangExtract"
    )
    p.add_argument("--csv", default="mtsamples.csv", help="Path to mtsamples.csv")
    p.add_argument(
        "--samples", type=int, default=None, help="Number of notes to process"
    )
    p.add_argument(
        "--specialty", type=str, default=None, help="Filter by medical specialty"
    )
    p.add_argument(
        "--passes", type=int, default=1, help="Extraction passes per document"
    )
    p.add_argument(
        "--model",
        default="gemini-2.5-flash",
        help="Gemini model ID (e.g. gemini-2.5-flash, gemini-2.5-pro, gemini-3-flash-preview)",
    )
    p.add_argument(
        "--buffer", type=int, default=4000, help="Max char buffer for chunking"
    )
    p.add_argument(
        "--workers", type=int, default=4, help="Parallel workers per document"
    )
    p.add_argument("--output", default="output", help="Output directory")
    p.add_argument(
        "--compare-passes", action="store_true", help="Run multi-pass comparison"
    )
    return p.parse_args()


def build_config(args: argparse.Namespace) -> AppConfig:
    """Map CLI args into typed config dataclasses."""
    return AppConfig(
        model=ModelConfig(model_id=args.model),
        extraction=ExtractionConfig(
            extraction_passes=args.passes,
            max_char_buffer=args.buffer,
            max_workers=args.workers,
        ),
        data=DataConfig(
            csv_path=args.csv,
            specialty=args.specialty,
            n_samples=args.samples,
        ),
        output=OutputConfig(output_dir=args.output),
    )


def main() -> None:
    args = parse_args()
    cfg = build_config(args)

    # Warn if API key is missing
    if not cfg.model.api_key:
        print("WARNING: LANGEXTRACT_API_KEY not set.")
        print("  export LANGEXTRACT_API_KEY='your-gemini-api-key'\n")

    # Load data
    df = load_mtsamples(cfg.data)

    # Multi-pass comparison mode
    if args.compare_passes:
        compare_passes(df, cfg.model, ext_cfg=cfg.extraction)
        return

    # Extract
    start = time.time()
    results = extract_batch(df, cfg.model, cfg.extraction)
    elapsed = time.time() - start

    if not results:
        print("\nNo results. Check your API key and input data.")
        sys.exit(1)

    # Analyze
    stats = compute_stats(results)
    stats["elapsed_seconds"] = round(elapsed, 1)
    print_report(stats)

    # Save
    save_results(results, stats, cfg.output)

    print(
        f"\nDone in {elapsed:.1f}s. "
        f"Run 'python visualize.py' to generate the interactive HTML viewer."
    )


if __name__ == "__main__":
    main()
