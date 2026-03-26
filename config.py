"""
Centralized configuration — model settings, paths, and extraction defaults.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ModelConfig:
    """LLM provider settings."""

    model_id: str = "gemini-2.5-flash"
    api_key_env: str = "LANGEXTRACT_API_KEY"

    @property
    def api_key(self) -> str | None:
        return os.environ.get(self.api_key_env)


@dataclass
class ExtractionConfig:
    """Controls for the extraction engine."""

    extraction_passes: int = 1
    max_char_buffer: int = 4000
    long_doc_buffer: int = 2000  # reduced buffer for notes > long_doc_threshold
    long_doc_threshold: int = 10_000  # characters
    max_workers: int = 4


@dataclass
class DataConfig:
    """Dataset loading parameters."""

    csv_path: str = "mtsamples.csv"
    specialty: str | None = None
    n_samples: int | None = None
    min_char_length: int = 200


@dataclass
class OutputConfig:
    """Paths for saved artifacts."""

    output_dir: str = "output"

    @property
    def jsonl_path(self) -> str:
        return str(Path(self.output_dir) / "clinical_extractions.jsonl")

    @property
    def html_path(self) -> str:
        return str(Path(self.output_dir) / "clinical_extractions.html")

    @property
    def stats_path(self) -> str:
        return str(Path(self.output_dir) / "extraction_stats.json")


@dataclass
class AppConfig:
    """Top-level config aggregating all sub-configs."""

    model: ModelConfig = field(default_factory=ModelConfig)
    extraction: ExtractionConfig = field(default_factory=ExtractionConfig)
    data: DataConfig = field(default_factory=DataConfig)
    output: OutputConfig = field(default_factory=OutputConfig)
