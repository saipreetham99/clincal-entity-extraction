# Structured Clinical Entity Extraction using LangExtract

Extract structured biomedical entities from unstructured clinical notes using Google's [LangExtract](https://github.com/google/langextract) — no labeled training data or model fine-tuning required.

## Overview

This project processes clinical notes from the [MTSamples](https://www.kaggle.com/datasets/tboyle10/medicaltranscriptions) dataset and extracts:

| Entity Class | Description | Example |
|---|---|---|
| `medication` | Drug / medication name | Amoxicillin, Lisinopril |
| `dosage` | Numeric dose with units | 500 mg, 20 mg |
| `route` | Route of administration | PO, IV, topical, IM |
| `frequency` | Dosing schedule | BID, daily, q6h PRN |
| `duration` | Treatment length | for 10 days, x2 weeks |
| `diagnosis` | Disease or condition | acute sinusitis, type 2 diabetes |

Every extraction is **character-level grounded** back to the source text, enabling interactive HTML visualization for error analysis.

---

## Results

Full dataset extraction on **4,999 clinical notes** from MTSamples using `gemini-2.5-flash` (configurable via `--model`) with single-pass extraction:

<!-- REPLACE the numbers below after running: python main.py -->

| Metric | Value |
|---|---|
| Documents processed | 20 |
| Documents with entities | 18 |
| Total entities extracted | 401 |
| Avg entities / document | 20.1 |
| Runtime | 20m 8s | Value |
|---|---|
| Documents processed | X,XXX |
| Documents with entities | X,XXX |
| Total entities extracted | XX,XXX |
| Avg entities / document | XX.X |
| Runtime | XXm XXs |

### Entity Class Distribution

| Class | Count |
|---|---|
| diagnosis | 277 |
| medication | 73 |
| dosage | 25 |
| route | 17 |
| frequency | 5 |
| duration | 4 | Count |
|---|---|
| diagnosis | X,XXX |
| medication | X,XXX |
| dosage | X,XXX |
| frequency | X,XXX |
| route | XXX |
| duration | XXX |

### Top 10 Medications Extracted

| Medication | Count |
|---|---|
| epinephrine | 4 |
| allegra | 3 |
| crestor | 3 |
| general | 3 |
| normal saline solution | 3 |
| xylocaine | 3 |
| zyrtec | 2 |
| marcaine | 2 |
| anesthesia | 2 |
| lidocaine | 2 | Count |
|---|---|
| ... | ... |

### Top 10 Diagnoses Extracted

| Diagnosis | Count |
|---|---|
| asthma | 4 |
| hypertension | 4 |
| pulmonary embolism | 4 |
| bleeding | 4 |
| infection | 4 |
| morbid obesity | 4 |
| diabetes | 3 |
| obesity | 3 |
| high cholesterol | 3 |
| deep venous thrombosis | 3 | Count |
|---|---|
| ... | ... |

### Multi-Pass Recall Comparison

Tested on documents exceeding 10K characters with `--compare-passes`:

| Passes | Avg Entities / Document |
|---|---|
| 1 | XX.X |
| 2 | XX.X |
| 3 | XX.X |

---

## Project Structure

```
clinical-entity-extraction/
├── main.py                  # CLI entry point
├── config.py                # Dataclass configs (model, extraction, data, output)
├── visualize.py             # Custom multi-document HTML visualization
├── update_readme.py         # Auto-fill README results from stats JSON
├── requirements.txt
├── .env.example             # Copy to .env with your API key
├── .gitignore
├── data/
│   └── loader.py            # MTSamples CSV loading and filtering
├── extraction/
│   ├── __init__.py
│   ├── schema.py            # Prompt + few-shot examples (extraction schema)
│   └── engine.py            # Single-note and batch extraction
├── analysis/
│   ├── __init__.py
│   └── stats.py             # Aggregate metrics, reporting, pass comparison
└── output/
    ├── __init__.py
    └── export.py            # JSONL save, HTML visualization, stats JSON
```

**Module responsibilities:**

- **`config.py`** — All tunables in typed dataclasses. CLI args map directly into these.
- **`data/loader.py`** — Reads `mtsamples.csv`, cleans text, filters by specialty/length/sample count.
- **`extraction/schema.py`** — The prompt and two few-shot `ExampleData` objects defining the 6-class entity schema with `medication_group` relationship attributes.
- **`extraction/engine.py`** — `extract_note()` for single documents (with adaptive chunking for long notes) and `extract_batch()` for the full dataframe.
- **`analysis/stats.py`** — `compute_stats()` aggregates entity counts. `compare_passes()` benchmarks recall across pass counts.
- **`output/export.py`** — Saves JSONL, generates LangExtract's built-in HTML, writes stats JSON.
- **`visualize.py`** — Reads the JSONL and generates a custom multi-document HTML viewer with sidebar navigation, color-coded highlights, and a click-to-inspect entity panel.

---

## Setup

### 1. Clone this repo

```bash
git clone https://github.com/YOUR_USERNAME/clinical-entity-extraction.git
cd clinical-entity-extraction
```

### 2. Install LangExtract

```bash
git clone https://github.com/google/langextract.git
cd langextract && pip install -e . && cd ..
```

### 3. Install remaining dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure API key

```bash
cp .env.example .env
# Edit .env and paste your Gemini API key
# Get one free at: https://aistudio.google.dev/apikey
```

Then load it in your shell:

```bash
export $(cat .env | xargs)
```

### 5. Get the MTSamples dataset

```bash
curl -L -o mtsamples.csv \
  "https://raw.githubusercontent.com/salgadev/medical-nlp/master/data/mtsamples.csv"
```

---

## Usage

```bash
# Quick test — 5 notes with default model (gemini-2.5-flash)
python main.py --samples 5

# Use a specific model
python main.py --model gemini-3-flash-preview --samples 5
python main.py --model gemini-2.5-pro --samples 10

# Full dataset — all notes, single pass
python main.py

# Multi-pass for higher recall
python main.py --passes 3

# Filter by specialty
python main.py --specialty "Orthopedic" --passes 2

# Compare 1 vs 2 vs 3 pass recall
python main.py --compare-passes

# Combine options
python main.py --model gemini-3-flash-preview --passes 2 --specialty "Cardiovascular" --workers 2
```

## Output

Results are saved to `output/`:

| File | Description |
|---|---|
| `clinical_extractions.jsonl` | Structured extractions with character offsets |
| `clinical_extractions.html` | LangExtract's built-in visualization |
| `visualization.html` | Custom multi-document visualization (recommended) |
| `extraction_stats.json` | Aggregate statistics |

### Visualization

After running extraction, generate the custom visualization:

```bash
python visualize.py
```

Open `output/visualization.html` in a browser to:
- Browse all documents in the **sidebar** (click to switch)
- See **color-coded entity highlights** in the clinical text
- **Click any entity** to inspect its class, attributes, and character span
- Use **← →** arrow keys or Previous/Next buttons to navigate

---

## Architecture

```
mtsamples.csv
      │
      ▼
┌──────────────────┐
│  data/loader.py   │  Filter by specialty, min length, sample count
└────────┬─────────┘
         ▼
┌──────────────────────┐
│  extraction/engine.py │  Few-shot prompt + schema enforcement
│  extraction/schema.py │  Chunking → Parallel → Multi-pass merge
└────────┬─────────────┘
         ▼
┌──────────────────┐
│  analysis/stats.py│  Entity distribution, top meds/diagnoses
└────────┬─────────┘
         ▼
┌──────────────────┐
│  output/export.py │  JSONL + stats JSON
└────────┬─────────┘
         ▼
┌──────────────────┐
│  visualize.py     │  Custom multi-document HTML viewer
└──────────────────┘
```

## Key Design Decisions

**Few-shot prompting over fine-tuning** — Two `ExampleData` objects in `schema.py` teach Gemini the full entity schema via controlled generation, eliminating the need for labeled training data.

**Adaptive chunking for long documents** — `engine.py` automatically reduces `max_char_buffer` for notes exceeding 10K characters so the model processes smaller, focused contexts with better recall.

**Multi-pass extraction** — Each pass processes the text independently. Results merge with "first-pass wins" for overlapping entities, adding unique non-overlapping entities from later passes.

**Relationship grouping via attributes** — The `medication_group` attribute links dosages, routes, frequencies, and durations to their parent medication, preserving clinical relationships.

## License

This project uses LangExtract under the [Apache 2.0 License](https://www.apache.org/licenses/LICENSE-2.0). The MTSamples dataset is public domain (CC0).
