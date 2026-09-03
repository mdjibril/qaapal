import json
import re

QUESTION_TYPES = (
    "Direct",
    "Scenario-Based",
    "Step-by-Step Procedure",
    "Labeled Diagram",
    "Narrative Explanation",
)


def normalize_nos(nos_data):
    """Flatten fetch_nested_nos output into one record per performance criterion."""
    records = []
    for unit_key, learning_outcomes in (nos_data or {}).items():
        unit_code, _, unit_title = str(unit_key).partition(":")
        unit_code = unit_code.strip()
        unit_title = unit_title.strip()
        for lo_key, performance_criteria in (learning_outcomes or {}).items():
            lo_label, _, lo_description = str(lo_key).partition(":")
            lo_num = re.sub(r"^LO\s*", "", lo_label.strip(), flags=re.IGNORECASE).strip()
            lo_description = lo_description.strip()
            for pc_value in performance_criteria or []:
                pc_code, _, pc_description = str(pc_value).partition(":")
                pc_code = pc_code.strip()
                pc_description = pc_description.strip()
                if pc_code:
                    records.append(
                        {
                            "unit_code": unit_code,
                            "unit_title": unit_title,
                            "lo_num": lo_num,
                            "lo_description": lo_description,
                            "pc_code": pc_code,
                            "pc_description": pc_description,
                        }
                    )
    return records


def build_workbook_prompt(trade_name, level, records):
    """Build a strict JSON-only prompt for the canonical assessment item list."""
    source = json.dumps(records, ensure_ascii=True, indent=2)
    return f"""You are an expert vocational assessment designer.
Create exactly one assessment item for every source performance criterion below.
The selected trade is: {trade_name}
The selected level is: {level}

Return JSON only, with this exact top-level shape:
{{"items": [{{"pc_code": "...", "question_type": "...", "question": "...", "weight": 5, "ideal_answer": ["..."], "marking_scheme": ["..." ]}}]}}

Allowed question_type values: {', '.join(QUESTION_TYPES)}.
Use one question per pc_code. Match the selected level: foundational for Level 2,
analytical for Level 3, and supervisory, evaluative, or design-focused for higher
levels where the criterion supports it. Questions must be practical and specific
to the trade. Ideal answers must be concrete, and marking_scheme must list marks
that add up to weight. Never invent, omit, or duplicate a pc_code.

Source performance criteria:
{source}
"""


def _load_json_response(response):
    text = str(response or "").strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.IGNORECASE | re.DOTALL).strip()
    parsed = json.loads(text)
    if isinstance(parsed, dict):
        parsed = parsed.get("items")
    if not isinstance(parsed, list):
        raise ValueError("AI response must contain an items list")
    return parsed


def validate_workbook_items(response, records):
    """Validate one generated item per source PC and return normalized items."""
    try:
        items = _load_json_response(response)
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        raise ValueError(f"Invalid workbook JSON: {exc}") from exc

    source_codes = [record["pc_code"] for record in records]
    if len(source_codes) != len(set(source_codes)):
        raise ValueError("Source NOS contains duplicate PC codes")
    source_set = set(source_codes)
    seen_codes = []
    validated = []
    for item in items:
        if not isinstance(item, dict):
            raise ValueError("Each assessment item must be a JSON object")
        pc_code = str(item.get("pc_code", "")).strip()
        if pc_code not in source_set:
            raise ValueError(f"Unexpected PC code: {pc_code or '(missing)'}")
        if pc_code in seen_codes:
            raise ValueError(f"Duplicate PC code: {pc_code}")
        question = str(item.get("question", "")).strip()
        question_type = str(item.get("question_type", "")).strip()
        ideal_answer = item.get("ideal_answer")
        marking_scheme = item.get("marking_scheme")
        if not question:
            raise ValueError(f"Question is missing for PC {pc_code}")
        if question_type not in QUESTION_TYPES:
            raise ValueError(f"Invalid question type for PC {pc_code}: {question_type}")
        if not isinstance(ideal_answer, list) or not ideal_answer or not all(str(value).strip() for value in ideal_answer):
            raise ValueError(f"Ideal answer is missing for PC {pc_code}")
        if not isinstance(marking_scheme, list) or not marking_scheme or not all(str(value).strip() for value in marking_scheme):
            raise ValueError(f"Marking scheme is missing for PC {pc_code}")
        try:
            weight = int(item.get("weight"))
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Invalid weight for PC {pc_code}") from exc
        if weight <= 0:
            raise ValueError(f"Weight must be positive for PC {pc_code}")
        source = next(record for record in records if record["pc_code"] == pc_code)
        validated.append({**source, "question": question, "question_type": question_type, "weight": weight,
                          "ideal_answer": [str(value).strip() for value in ideal_answer],
                          "marking_scheme": [str(value).strip() for value in marking_scheme]})
        seen_codes.append(pc_code)

    missing = [code for code in source_codes if code not in seen_codes]
    if missing:
        raise ValueError(f"Missing PC code(s): {', '.join(missing)}")
    return validated
