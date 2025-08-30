from pathlib import Path
from typing import Dict, List, Optional
import yaml
from pydantic import BaseModel, Field


class ModelEntry(BaseModel):
    repo_id: str
    task: str
    kwargs: Dict = Field(default_factory=dict)
    tokenizer_kwargs: Dict = Field(default_factory=dict)


class ModelsConfig(BaseModel):
    models: Dict[str, ModelEntry]
    defaults: Dict = Field(default_factory=dict)


class ScenariosConfig(BaseModel):
    enabled: List[str]
    thresholds: Dict[str, float] = Field(default_factory=dict)
    cases: Dict[str, str] = Field(default_factory=dict)


def load_yaml(path) -> dict:
    path = Path(path) if isinstance(path, str) else path
    with path.open("r") as f:
        return yaml.safe_load(f)


def load_model_config(path) -> ModelsConfig:
    data = load_yaml(path)
    return ModelsConfig(**data)


def load_scenarios_config(path) -> ScenariosConfig:
    data = load_yaml(path)
    return ScenariosConfig(**data)

