"""
Auto-populate README.md Results section from extraction_stats.json.

Usage:
    python main.py                  # run full extraction first
    python update_readme.py         # then fill in the README
"""

import json
from pathlib import Path


def fmt(n: int) -> str:
    """Format integer with commas."""
    return f"{n:,}"


def build_table(rows: list[tuple[str, str | int]], headers: tuple = ("", "")) -> str:
    """Build a markdown table from a list of (col1, col2) tuples."""
    lines = [
        f"| {headers[0]} | {headers[1]} |",
        "|---|---|",
    ]
    for k, v in rows:
        lines.append(f"| {k} | {fmt(v) if isinstance(v, int) else v} |")
    return "\n".join(lines)


def main():
    stats_path = Path("output/extraction_stats.json")
    readme_path = Path("README.md")

    if not stats_path.exists():
        print(f"ERROR: {stats_path} not found. Run 'python main.py' first.")
        return

    if not readme_path.exists():
        print(f"ERROR: {readme_path} not found.")
        return

    stats = json.loads(stats_path.read_text())
    readme = readme_path.read_text()

    # --- Summary table ---
    elapsed = stats.get("elapsed_seconds", 0)
    mins, secs = divmod(int(elapsed), 60)
    summary = build_table(
        [
            ("Documents processed", stats["total_documents"]),
            ("Documents with entities", stats["documents_with_entities"]),
            ("Total entities extracted", stats["total_entities"]),
            ("Avg entities / document", str(stats["avg_entities_per_document"])),
            ("Runtime", f"{mins}m {secs}s"),
        ],
        headers=("Metric", "Value"),
    )

    # --- Entity class distribution ---
    dist = build_table(
        [(cls, count) for cls, count in stats["entity_class_distribution"].items()],
        headers=("Class", "Count"),
    )

    # --- Top medications ---
    meds = build_table(
        list(stats["top_medications"].items())[:10],
        headers=("Medication", "Count"),
    )

    # --- Top diagnoses ---
    diags = build_table(
        list(stats["top_diagnoses"].items())[:10],
        headers=("Diagnosis", "Count"),
    )

    # --- Replace placeholder sections ---
    # Each section is identified by its heading + the next heading/---
    import re

    def replace_section(text, after_heading, replacement_table):
        """Replace the markdown table that follows a given heading."""
        # Match: heading line, optional blank, then a markdown table block
        pattern = (
            r"(###? " + re.escape(after_heading) + r".*?\n\n)"
            r"(\|.*?\|(?:\n\|.*?\|)*)"
        )
        match = re.search(pattern, text, re.DOTALL)
        if match:
            return text[: match.start(2)] + replacement_table + text[match.end(2) :]
        return text

    # Replace each section
    readme = replace_section(readme, "Entity Class Distribution", dist)
    readme = replace_section(readme, "Top 10 Medications Extracted", meds)
    readme = replace_section(readme, "Top 10 Diagnoses Extracted", diags)

    # Replace the summary table (first table after "## Results")
    results_pattern = (
        r"(<!-- REPLACE the numbers below after running: python main.py -->\n\n)"
        r"(\|.*?\|(?:\n\|.*?\|)*)"
    )
    match = re.search(results_pattern, readme, re.DOTALL)
    if match:
        readme = readme[: match.start(2)] + summary + readme[match.end(2) :]

    readme_path.write_text(readme)
    print(f"README.md updated with results from {stats_path}")


if __name__ == "__main__":
    main()
