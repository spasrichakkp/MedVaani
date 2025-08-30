from typing import Dict

PROMPT = (
    "Summarize the clinical note focusing on diagnoses, medications, allergies, and follow-up plans."
)


def build_input(case: Dict) -> str:
    return f"Clinical note:\n{case.get('note','')}\n\nTask: {PROMPT}"


def score(output: str, case: Dict) -> float:
    expected_keywords = [s.lower() for s in case.get("expected_keywords", [])]
    text = output.lower()
    hits = sum(1 for e in expected_keywords if e in text)
    return hits / max(1, len(expected_keywords) or 1)


def run_case(pipe, case: Dict, gen_defaults: Dict) -> Dict:
    inp = build_input(case)
    if pipe.task in ("text-generation",):
        resp = pipe(inp, max_new_tokens=gen_defaults.get("max_new_tokens", 128), do_sample=gen_defaults.get("do_sample", False))
        text = resp[0].get("generated_text", "")
    else:
        resp = pipe(inp, max_new_tokens=gen_defaults.get("max_new_tokens", 128))
        text = resp[0].get("generated_text", resp[0].get("summary_text", ""))
    return {"input": inp, "output": text, "score": score(text, case)}

