"""
Aggregate statistics and reporting over extraction results.
"""

from __future__ import annotations

from collections import Counter


def compute_stats(results: list) -> dict:
    """
    Build a summary dict: entity class distribution, top medications,
    top diagnoses, per-document counts.
    """
    class_counts: Counter = Counter()
    medication_names: Counter = Counter()
    diagnosis_names: Counter = Counter()
    entities_per_doc: list[int] = []
    docs_with_entities = 0

    for doc in results:
        extractions = doc.extractions if doc.extractions else []
        n = len(extractions)
        entities_per_doc.append(n)
        if n > 0:
            docs_with_entities += 1

        for ext in extractions:
            cls = ext.extraction_class
            txt = ext.extraction_text.strip().lower()
            class_counts[cls] += 1
            if cls == "medication":
                medication_names[txt] += 1
            elif cls == "diagnosis":
                diagnosis_names[txt] += 1

    total = len(results)
    total_ent = sum(entities_per_doc)

    return {
        "total_documents": total,
        "documents_with_entities": docs_with_entities,
        "total_entities": total_ent,
        "avg_entities_per_document": round(total_ent / total, 1) if total else 0,
        "entity_class_distribution": dict(class_counts.most_common()),
        "top_medications": dict(medication_names.most_common(20)),
        "top_diagnoses": dict(diagnosis_names.most_common(20)),
    }


def print_report(stats: dict) -> None:
    """Pretty-print the extraction summary to stdout."""
    w = 65
    print("\n" + "=" * w)
    print("  CLINICAL ENTITY EXTRACTION — SUMMARY REPORT")
    print("=" * w)
    print(f"  Documents processed:      {stats['total_documents']}")
    print(f"  Documents with entities:  {stats['documents_with_entities']}")
    print(f"  Total entities extracted: {stats['total_entities']}")
    print(f"  Avg entities / document:  {stats['avg_entities_per_document']}")
    print("-" * w)

    print("\n  Entity Class Distribution:")
    for cls, count in stats["entity_class_distribution"].items():
        bar = "█" * min(count, 50)
        print(f"    {cls:<16} {count:>5}  {bar}")

    print("\n  Top 10 Medications:")
    for med, count in list(stats["top_medications"].items())[:10]:
        print(f"    {med:<30} {count:>4}")

    print("\n  Top 10 Diagnoses:")
    for dx, count in list(stats["top_diagnoses"].items())[:10]:
        print(f"    {dx:<40} {count:>4}")

    print("=" * w)


def compare_passes(
    df,
    model_cfg,
    pass_counts: list[int] = [1, 2, 3],
    ext_cfg=None,
) -> None:
    """
    Run extraction at different pass counts on long documents
    and print a side-by-side recall comparison.
    """
    from extraction.engine import extract_batch
    from dataclasses import replace

    long_docs = df[df["char_len"] > 5000].head(3)
    if long_docs.empty:
        long_docs = df.head(3)

    print("\n" + "=" * 65)
    print("  MULTI-PASS EXTRACTION COMPARISON")
    print("=" * 65)

    for passes in pass_counts:
        cfg = replace(ext_cfg, extraction_passes=passes) if ext_cfg else None
        if cfg is None:
            from config import ExtractionConfig

            cfg = ExtractionConfig(extraction_passes=passes)

        print(f"\n--- {passes} pass(es) ---")
        results = extract_batch(long_docs, model_cfg, cfg)
        s = compute_stats(results)
        print(f"  Total entities:  {s['total_entities']}")
        print(f"  Avg / document:  {s['avg_entities_per_document']}")
        for cls, cnt in s["entity_class_distribution"].items():
            print(f"    {cls}: {cnt}")
