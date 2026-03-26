"""
MTSamples dataset loading and filtering.
"""

import sys

import pandas as pd

from config import DataConfig


def load_mtsamples(cfg: DataConfig) -> pd.DataFrame:
    """
    Load mtsamples.csv, clean transcription text, and apply filters.

    Returns a DataFrame with columns: transcription, medical_specialty, char_len
    """
    df = pd.read_csv(cfg.csv_path, index_col=0)
    df = df.dropna(subset=["transcription"])
    df["transcription"] = df["transcription"].astype(str).str.strip()
    df["char_len"] = df["transcription"].str.len()
    df = df[df["char_len"] >= cfg.min_char_length].copy()

    if cfg.specialty:
        mask = df["medical_specialty"].str.contains(cfg.specialty, case=False, na=False)
        df = df[mask]
        if df.empty:
            available = sorted(
                pd.read_csv(cfg.csv_path, index_col=0)["medical_specialty"]
                .dropna()
                .unique()
                .tolist()
            )
            print(f"No notes found for specialty '{cfg.specialty}'.")
            print(f"Available specialties: {available[:20]}")
            sys.exit(1)

    df = df.reset_index(drop=True)

    if cfg.n_samples:
        df = df.head(cfg.n_samples)

    print(f"Loaded {len(df)} clinical notes (avg {df['char_len'].mean():.0f} chars)")
    return df
