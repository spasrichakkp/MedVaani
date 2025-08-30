from typing import Dict

PROMPT = (
    "You are a medical assistant. Analyze the patient's symptoms and provide the 3 most likely diagnoses,\n"
    "with brief rationales and recommended initial tests. Respond in concise bullet points.\n"
)


def build_input(case: Dict) -> str:
    patient = case.get("patient", {})
    age = patient.get("age", "?")
    sex = patient.get("sex", "?")
    sx = case.get("symptoms", [])
    hx = case.get("history", [])
    meds = case.get("medications", [])
    return (
        f"Patient age {age}, sex {sex}.\n"
        f"Symptoms: {', '.join(sx)}\n"
        f"History: {', '.join(hx)}\n"
        f"Medications: {', '.join(meds)}\n"
        f"Task: {PROMPT}"
    )


def score(output: str, case: Dict) -> float:
    # Very simple keyword-based scoring vs. expected diagnoses
    expected = [s.lower() for s in case.get("expected_diagnoses", [])]
    if not expected:
        return 0.0
    text = output.lower()
    hits = sum(1 for e in expected if e in text)
    return hits / max(1, len(expected))


def run_case(pipe, case: Dict, gen_defaults: Dict) -> Dict:
    inp = build_input(case)
    if pipe.task in ("text-generation",):
        resp = pipe(inp, max_new_tokens=gen_defaults.get("max_new_tokens", 128), do_sample=gen_defaults.get("do_sample", False), temperature=gen_defaults.get("temperature", 0.2), top_p=gen_defaults.get("top_p", 0.9))
        text = resp[0].get("generated_text", "")
    else:
        # text2text
        resp = pipe(inp, max_new_tokens=gen_defaults.get("max_new_tokens", 128))
        text = resp[0].get("generated_text", resp[0].get("summary_text", ""))
    return {"input": inp, "output": text, "score": score(text, case)}

