# app/services/plotlyjs_spec_writer.py
import requests
import json
import sys

URL = "http://192.168.0.200:8002/v1/completions"   # vLLM OpenAI-compatible /v1/completions
MODEL = "google/gemma-3-27b-it"

# 프론트가 아는 스키마(실데이터는 절대 포함 X)
DEFAULT_FIELDS_META = {
    "x_field": "key",
    "available_group_bys": ["DEVICE", "ROUTE", "PARA", "MAIN_EQ", "EQ_CHAM"],
    "no_val_columns": ["NO_VAL1", "NO_VAL2", "NO_VAL3", "NO_VAL4", "NO_VAL5"],
    "spec_candidates": ["USL", "LSL", "TGT", "UCL", "LCL"],
    "filterable_fields": {
        "DEVICE": {"type": "string", "values": ["DEVICE_A", "DEVICE_B", "DEVICE_C"]},
        "ROUTE":  {"type": "string"},
        "PARA":   {"type": "number", "values": [0, 1, 2, 3]},
        "MAIN_EQ":{"type": "string"},
        "EQ_CHAM":{"type": "string"}
    },
    "alias_map": {
        "장비": "DEVICE",
        "디바이스": "DEVICE",
        "라우트": "ROUTE",
        "공정경로": "ROUTE",
        "파라": "PARA",
        "파라미터": "PARA",
        "메인EQ": "MAIN_EQ",
        "메인장비": "MAIN_EQ",
        "챔버": "EQ_CHAM"
    }
}

# -------------------------------
# Prompt Builder (문자열만 수정)
# -------------------------------
def build_prompt(user_intent: str, fields_meta: dict) -> str:
    """
    LLM이 항상 모든 필수 키를 가진 단일 JSON을 반환하도록 강제.
    - USL/LSL/TGT는 무조건 spec_lines에 포함
    - 필터는 '행 필터' 의미. 컬럼 삭제/축소, y_fields 변경이 아님.
    """
    meta_json = json.dumps(fields_meta, ensure_ascii=False)

    prompt = f"""
ROLE
You are **ChartSpecWriter**. Convert a Korean natural-language intent into a STRICT JSON spec
for a Plotly **box** chart. Return exactly ONE JSON object including ALL required keys.

USER INTENT (Korean):
\"\"\"{user_intent}\"\"\" 

FIELDS_META (use ONLY these field names; do not invent anything new):
{meta_json}

REQUIRED FIELDS (always include every key below)
- chart_type: string, must be "box"
- x_field: string, MUST equal fields_meta.x_field
- group_by: string, MUST be one of fields_meta.available_group_bys
- y_fields: array of strings, NON-EMPTY, subset of fields_meta.no_val_columns
- box: object with:
    - showpoints: boolean
    - opacity: number (0.0 ~ 1.0)
- filters: array (possibly empty) of objects with:
    - field: string (must exist in fields_meta.filterable_fields)
    - op: one of ["==","!=","in","between",">=","<="," >", " <"]
    - value: string|number|list (for in/between provide list; for between use [min,max])
- spec_lines: array of strings. MUST include ["USL", "LSL", "TGT", "UCL", "LCL"] (in that order). You MAY add others from fields_meta.spec_candidates.
- layout_patches: object (NOT an array). Include "xaxis.tickangle" (number) and "margin.t" Default is 90 (vertical labels) and margin 20.
- hover: null OR object (if unnecessary, set null)

INTERPRETATION RULES
- Map Korean aliases using alias_map (e.g., "장비"→DEVICE, "라우트"→ROUTE, "메인EQ/메인장비"→MAIN_EQ, "파라/파라미터"→PARA).
- If the intent specifies a grouping field (explicitly or via alias), use it. Otherwise choose the most relevant; if unsure prefer "DEVICE".
- IMPORTANT: User conditions describe **row filters only**. They DO NOT mean dropping columns or changing which value columns exist.
  - Example: "NO_VAL4가 120이상만 보여줘" → add a filter {{ "field":"NO_VAL4","op":">=","value":120 }} but keep y_fields as previously chosen/default.
- y_fields:
  - If the user explicitly names y fields, honor them.
  - Otherwise, default to **ALL** fields_meta.no_val_columns (do NOT reduce y_fields based only on filters).
- spec_lines:
  - Always include ["USL", "LSL", "TGT", "UCL", "LCL"], even if the user doesn't mention them.
  - You may add "UCL","LCL" if relevant, but never remove USL/LSL/TGT.
- No raw data arrays. No extra keys beyond the required schema.

DEFAULTS WHEN UNSPECIFIED
- chart_type = "box"
- x_field = fields_meta.x_field
- group_by = first relevant from available_group_bys (prefer DEVICE if available)
- y_fields = ALL items from fields_meta.no_val_columns
- box = {{ "showpoints": false, "opacity": 0.7 }}
- filters = []
- spec_lines = ["USL", "LSL", "TGT", "UCL", "LCL"]
- layout_patches = {{ "xaxis.tickangle": 90, "margin.t": 20 }}
- hover = null

OUTPUT FORMAT
- Return STRICT JSON ONLY. No code fences, no markdown, no prose.
"""
    return prompt.strip()

# -----------------------------------------
# Robust JSON extractor (안전 추출)
# -----------------------------------------
def extract_first_json(text: str) -> str:
    text = text.strip()
    if text.startswith("{") and text.endswith("}"):
        return text
    start = text.find("{")
    if start == -1:
        raise ValueError("No JSON object found in LLM response.")
    depth = 0
    for i in range(start, len(text)):
        ch = text[i]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[start:i+1]
    raise ValueError("Unbalanced JSON braces in LLM response.")

# -----------------------------------------
# Spec sanitizer (필수키 보강 & 교차검증)
# -----------------------------------------
def sanitize_spec(spec, meta):
    # Parse JSON if needed
    if isinstance(spec, str):
        spec = json.loads(spec)

    allowed = {
        "chart_type","x_field","group_by","y_fields","box",
        "spec_lines","layout_patches","hover","filters"
    }
    spec = {k: v for k, v in spec.items() if k in allowed}

    # chart_type & x_field
    spec["chart_type"] = "box"
    spec["x_field"] = meta["x_field"]

    # group_by
    gb = spec.get("group_by")
    if gb not in meta["available_group_bys"]:
        spec["group_by"] = "DEVICE" if "DEVICE" in meta["available_group_bys"] else meta["available_group_bys"][0]

    # y_fields (기본: 전체 NO_VAL*)
    y_in = spec.get("y_fields") or []
    y_ok = [y for y in y_in if y in meta["no_val_columns"]]
    if not y_ok:
        y_ok = list(meta["no_val_columns"])
    spec["y_fields"] = y_ok

    # spec_lines: 항상 USL, LSL, TGT 포함(순서 유지), 나머지 합치기 & 중복 제거
    baseline = [s for s in ["USL","LSL","TGT"] if s in meta["spec_candidates"]]
    existing = [s for s in (spec.get("spec_lines") or []) if s in meta["spec_candidates"]]
    merged = baseline + [s for s in existing if s not in baseline]
    spec["spec_lines"] = merged

    # # filters
    # allowed_ops = {"==","!=", "in", "between", ">=", "<=", ">", "<"}
    # flt = []
    # for f in (spec.get("filters") or []):
    #     if not isinstance(f, dict):
    #         continue
    #     field = f.get("field")
    #     op = f.get("op")
    #     val = f.get("value")
    #     if field in meta["filterable_fields"] and op in allowed_ops:
    #         flt.append({"field": field, "op": op, "value": val})
    # spec["filters"] = flt

    # box
    box = spec.get("box") or {}
    if not isinstance(box, dict):
        box = {}
    box.setdefault("showpoints", False)
    box.setdefault("opacity", 0.7)
    spec["box"] = box

    # layout_patches (dict만 허용)
    lp = spec.get("layout_patches")
    if not isinstance(lp, dict):
        lp = {}
    lp.setdefault("xaxis.tickangle", 90)
    spec["layout_patches"] = lp

    # hover
    if "hover" in spec and not (spec["hover"] is None or isinstance(spec["hover"], dict)):
        spec["hover"] = None

    return spec

# -----------------------------------------
# LLM 호출 → Spec 생성
# -----------------------------------------
def generate_plotly_spec(user_prompt: str, fields_meta: dict = None):
    fields_meta = fields_meta or DEFAULT_FIELDS_META
    prompt = build_prompt(user_prompt, fields_meta)

    payload = {
        "model": MODEL,
        "prompt": prompt,
        "max_tokens": 360,
        "temperature": 0.1,
    }

    try:
        res = requests.post(URL, headers={"Content-Type": "application/json"}, json=payload, timeout=60)
        res.raise_for_status()
        data = res.json()

        raw_text = data["choices"][0]["text"]
        print("Raw LLM Response:", raw_text)

        json_text = extract_first_json(raw_text)
        print("\nExtracted JSON:", json_text)

        spec = sanitize_spec(json_text, fields_meta)
        print("\nSanitized Spec:", json.dumps(spec, ensure_ascii=False, indent=2))
        return spec
    except Exception as e:
        print(f"Error generating plotly spec: {e}")
        # Return a default spec if LLM call fails
        return {
            "chart_type": "box",
            "x_field": fields_meta["x_field"],
            "group_by": "DEVICE",
            "y_fields": fields_meta["no_val_columns"],
            "box": {"showpoints": False, "opacity": 0.7},
            "filters": [],
            "spec_lines": ["USL", "LSL", "TGT", "UCL", "LCL"],
            "layout_patches": {"xaxis.tickangle": 90, "margin.t": 20},
            "hover": None
        }
