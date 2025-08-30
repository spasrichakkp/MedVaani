from typing import Dict

PROMPT = (
    "Provide guideline-based initial management recommendations and red flags for the described case."
)


def build_input(case: Dict) -> str:
    return (
        f"Chief complaint: {case.get('chief_complaint','')}\n"
        f"Vitals: {', '.join([f"{k}:{v}" for k,v in case.get('vitals',{}).items()])}\n"
        f"Key findings: {', '.join(case.get('findings', []))}\n"
        f"Task: {PROMPT}"
    )


def score(output: str, case: Dict) -> float:
    must_mentions = [s.lower() for s in case.get("expected_recs", [])]
    text = output.lower()
    hits = sum(1 for e in must_mentions if e in text)
    return hits / max(1, len(must_mentions) or 1)


def run_case(pipe, case: Dict, gen_defaults: Dict) -> Dict:
    inp = build_input(case)
    if pipe.task in ("text-generation",):
        resp = pipe(inp, max_new_tokens=gen_defaults.get("max_new_tokens", 128), do_sample=gen_defaults.get("do_sample", False))
        text = resp[0].get("generated_text", "")
    else:
        resp = pipe(inp, max_new_tokens=gen_defaults.get("max_new_tokens", 128))
        text = resp[0].get("generated_text", resp[0].get("summary_text", ""))
    return {"input": inp, "output": text, "score": score(text, case)}

