from typing import Dict

PROMPT = (
    "You are a pharmacology assistant. Analyze potential interactions for the given drugs,\n"
    "list major contraindications and monitoring recommendations. \n"
    "Please consider this factor that you have to stick to the Salt of the Medicine and also alternative medicine of Same Salt"
)


def build_input(case: Dict) -> str:
    drugs = case.get("drugs", [])
    patient = case.get("patient", {})
    return (
        f"Patient: age={patient.get('age','?')}, sex={patient.get('sex','?')}, comorbidities={', '.join(patient.get('comorbidities', []))}.\n"
        f"Drugs: {', '.join(drugs)}\n"
        f"Task: {PROMPT}"
    )


def score(output: str, case: Dict) -> float:
    expected_flags = [s.lower() for s in case.get("expected_flags", [])]
    text = output.lower()
    hits = sum(1 for e in expected_flags if e in text)
    return hits / max(1, len(expected_flags) or 1)


def run_case(pipe, case: Dict, gen_defaults: Dict) -> Dict:
    inp = build_input(case)
    if pipe.task in ("text-generation",):
        resp = pipe(inp, max_new_tokens=gen_defaults.get("max_new_tokens", 128), do_sample=gen_defaults.get("do_sample", False))
        text = resp[0].get("generated_text", "")
    else:
        resp = pipe(inp, max_new_tokens=gen_defaults.get("max_new_tokens", 128))
        text = resp[0].get("generated_text", resp[0].get("summary_text", ""))
    return {"input": inp, "output": text, "score": score(text, case)}

