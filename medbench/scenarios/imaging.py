from typing import Dict
from pathlib import Path

PROMPT = "Describe notable medical findings in the image and suggest next steps if concerning."


def has_imaging_deps() -> bool:
    try:
        import PIL  # noqa: F401
        return True
    except Exception:
        return False


def build_input(case: Dict) -> Dict:
    img_path = case.get("image_path")
    if not img_path or not Path(img_path).exists():
        raise FileNotFoundError(f"Image not found: {img_path}")
    return {"images": img_path, "text": PROMPT}


def score(output: str, case: Dict) -> float:
    expected = [s.lower() for s in case.get("expected_keywords", [])]
    text = output.lower()
    hits = sum(1 for e in expected if e in text)
    return hits / max(1, len(expected) or 1)


def run_case(pipe, case: Dict, gen_defaults: Dict) -> Dict:
    inputs = build_input(case)
    # CLIP classification pipeline returns labels; we adapt by joining labels
    res = pipe(inputs["images"])  # type: ignore
    if isinstance(res, list) and res and isinstance(res[0], dict) and "label" in res[0]:
        text = ", ".join([r["label"] for r in res[:5]])
    else:
        text = str(res)
    return {"input": str(inputs), "output": text, "score": score(text, case)}

