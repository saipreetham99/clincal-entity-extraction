"""
Prompt description and few-shot examples defining the clinical extraction schema.

Entity classes:
    medication, dosage, route, frequency, duration, diagnosis

Relationship strategy:
    Each non-medication entity carries a 'medication_group' attribute that
    links it to its parent medication name (lowercase).
"""

import textwrap

from langextract.data import ExampleData, Extraction

# ---------------------------------------------------------------------------
# Prompt
# ---------------------------------------------------------------------------

PROMPT = textwrap.dedent("""\
    Extract clinical medication and diagnosis information from the given
    medical note. For each mention, extract the entity in the order it
    appears. Use attributes to group related entities (e.g., a dosage
    belongs to a specific medication via 'medication_group').

    Entity classes to extract:
      - medication: drug / medication name
      - dosage: numeric dose with units (e.g., 500 mg)
      - route: route of administration (e.g., PO, IV, topical, IM)
      - frequency: how often the medication is taken (e.g., BID, daily)
      - duration: length of treatment (e.g., for 7 days, x2 weeks)
      - diagnosis: disease, condition, or clinical indication

    Rules:
      1. Use exact text from the source for extraction_text.
      2. Every dosage, route, frequency, and duration MUST include a
         'medication_group' attribute linking it to the nearest preceding
         medication name.
      3. Diagnoses should include a 'severity' attribute when stated
         (e.g., mild, moderate, severe, acute, chronic).
      4. If a medication is mentioned multiple times, extract each
         occurrence separately.
""")

# ---------------------------------------------------------------------------
# Few-shot examples
# ---------------------------------------------------------------------------

EXAMPLES = [
    # Example 1 — acute treatment with two medications
    ExampleData(
        text=(
            "The patient was started on Amoxicillin 500 mg PO TID for "
            "10 days to treat acute sinusitis. She was also given "
            "Ibuprofen 400 mg PO q6h PRN for pain."
        ),
        extractions=[
            Extraction(
                extraction_class="medication",
                extraction_text="Amoxicillin",
                attributes={"medication_group": "amoxicillin"},
            ),
            Extraction(
                extraction_class="dosage",
                extraction_text="500 mg",
                attributes={"medication_group": "amoxicillin"},
            ),
            Extraction(
                extraction_class="route",
                extraction_text="PO",
                attributes={"medication_group": "amoxicillin"},
            ),
            Extraction(
                extraction_class="frequency",
                extraction_text="TID",
                attributes={"medication_group": "amoxicillin"},
            ),
            Extraction(
                extraction_class="duration",
                extraction_text="10 days",
                attributes={"medication_group": "amoxicillin"},
            ),
            Extraction(
                extraction_class="diagnosis",
                extraction_text="acute sinusitis",
                attributes={"severity": "acute"},
            ),
            Extraction(
                extraction_class="medication",
                extraction_text="Ibuprofen",
                attributes={"medication_group": "ibuprofen"},
            ),
            Extraction(
                extraction_class="dosage",
                extraction_text="400 mg",
                attributes={"medication_group": "ibuprofen"},
            ),
            Extraction(
                extraction_class="route",
                extraction_text="PO",
                attributes={"medication_group": "ibuprofen"},
            ),
            Extraction(
                extraction_class="frequency",
                extraction_text="q6h PRN",
                attributes={"medication_group": "ibuprofen"},
            ),
        ],
    ),
    # Example 2 — chronic conditions with maintenance medications
    ExampleData(
        text=(
            "Patient is a 65-year-old male with a history of chronic "
            "hypertension and type 2 diabetes mellitus, currently managed "
            "with Lisinopril 20 mg daily and Metformin 1000 mg BID."
        ),
        extractions=[
            Extraction(
                extraction_class="diagnosis",
                extraction_text="chronic hypertension",
                attributes={"severity": "chronic"},
            ),
            Extraction(
                extraction_class="diagnosis",
                extraction_text="type 2 diabetes mellitus",
                attributes={"severity": "chronic"},
            ),
            Extraction(
                extraction_class="medication",
                extraction_text="Lisinopril",
                attributes={"medication_group": "lisinopril"},
            ),
            Extraction(
                extraction_class="dosage",
                extraction_text="20 mg",
                attributes={"medication_group": "lisinopril"},
            ),
            Extraction(
                extraction_class="frequency",
                extraction_text="daily",
                attributes={"medication_group": "lisinopril"},
            ),
            Extraction(
                extraction_class="medication",
                extraction_text="Metformin",
                attributes={"medication_group": "metformin"},
            ),
            Extraction(
                extraction_class="dosage",
                extraction_text="1000 mg",
                attributes={"medication_group": "metformin"},
            ),
            Extraction(
                extraction_class="frequency",
                extraction_text="BID",
                attributes={"medication_group": "metformin"},
            ),
        ],
    ),
]
