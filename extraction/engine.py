"""
Extraction engine — single-note and batch processing via LangExtract.
"""

from __future__ import annotations

import pandas as pd

from langextract.extraction import extract

from config import ModelConfig, ExtractionConfig
from extraction.schema import PROMPT, EXAMPLES


def extract_note(
    text: str,
    model_cfg: ModelConfig,
    ext_cfg: ExtractionConfig,
    char_len: int | None = None,
):
    """
    Run LangExtract on a single clinical note.

    If char_len exceeds the long-document threshold, the buffer is
    automatically reduced for better recall.
    """
    buf = ext_cfg.max_char_buffer
    if char_len and char_len > ext_cfg.long_doc_threshold:
        buf = min(buf, ext_cfg.long_doc_buffer)

    try:
        return extract(
            text_or_documents=text,
            prompt_description=PROMPT,
            examples=EXAMPLES,
            model_id=model_cfg.model_id,
            extraction_passes=ext_cfg.extraction_passes,
            max_char_buffer=buf,
            max_workers=ext_cfg.max_workers,
        )
    except Exception as e:
        print(f"  [ERROR] {e}")
        return None


def extract_batch(
    df: pd.DataFrame,
    model_cfg: ModelConfig,
    ext_cfg: ExtractionConfig,
) -> list:
    """
    Process every clinical note in the dataframe.

    Returns a list of AnnotatedDocuments (failed notes are skipped).
    """
    results = []
    total = len(df)

    for idx, row in df.iterrows():
        specialty = row.get("medical_specialty", "Unknown")
        char_len = row["char_len"]
        print(
            f"\n[{idx + 1}/{total}] {specialty} | "
            f"{char_len:,} chars | "
            f"{ext_cfg.extraction_passes} pass(es)"
        )

        result = extract_note(
            text=row["transcription"],
            model_cfg=model_cfg,
            ext_cfg=ext_cfg,
            char_len=char_len,
        )
        if result is not None:
            n = len(result.extractions) if result.extractions else 0
            print(f"  → {n} entities extracted")
            results.append(result)

    print(f"\nBatch complete: {len(results)}/{total} notes succeeded")
    return results
