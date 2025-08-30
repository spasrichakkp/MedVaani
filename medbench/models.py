from typing import Optional, Dict
from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM, AutoModelForSeq2SeqLM, AutoModelForTokenClassification
from transformers import AutoProcessor, AutoModelForImageClassification
from .config import ModelEntry, ModelsConfig


def load_pipeline(model_key: str, models_cfg: ModelsConfig):
    if model_key not in models_cfg.models:
        raise ValueError(f"Unknown model key: {model_key}")
    me: ModelEntry = models_cfg.models[model_key]

    task = me.task
    repo = me.repo_id
    kwargs = me.kwargs or {}
    tok_kwargs = me.tokenizer_kwargs or {}

    # Resolve model classes to avoid pipeline guessing where beneficial
    model = None
    tokenizer = None
    processor = None

    if task in ("text-generation",):
        tokenizer = AutoTokenizer.from_pretrained(repo, **tok_kwargs)
        model = AutoModelForCausalLM.from_pretrained(repo, **kwargs)
    elif task in ("text2text-generation",):
        tokenizer = AutoTokenizer.from_pretrained(repo, **tok_kwargs)
        model = AutoModelForSeq2SeqLM.from_pretrained(repo, **kwargs)
    elif task in ("token-classification",):
        tokenizer = AutoTokenizer.from_pretrained(repo, **tok_kwargs)
        model = AutoModelForTokenClassification.from_pretrained(repo, **kwargs)
    elif task in ("image-classification",):
        processor = AutoProcessor.from_pretrained(repo)
        model = AutoModelForImageClassification.from_pretrained(repo, **kwargs)
    else:
        # Fallback to generic pipeline
        return pipeline(task=task, model=repo, **kwargs)

    if task == "image-classification":
        return pipeline(task=task, model=model, feature_extractor=processor)
    else:
        return pipeline(task=task, model=model, tokenizer=tokenizer)

