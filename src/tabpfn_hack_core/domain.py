"""Load and validate domain.yaml packs."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field


class ActionThresholds(BaseModel):
    high: float = 0.75
    mid_high: float | None = None
    mid: float = 0.45
    mid_low: float | None = None


class PlaybookStep(BaseModel):
    action: str
    min_proba: float = 0.0
    when_col: str | None = None
    when_equals: str | None = None
    reason: str = ""


class DomainConfig(BaseModel):
    name: str = "generic-messy-table"
    label_col: str = "target"
    group_col: str | None = None
    time_col: str | None = None
    text_cols: list[str] = Field(default_factory=list)
    high_card_cols: list[str] = Field(default_factory=list)
    id_col: str | None = "row_id"
    action_thresholds: ActionThresholds = Field(default_factory=ActionThresholds)
    actions: dict[str, str] = Field(
        default_factory=lambda: {"high": "escalate", "mid": "review", "low": "monitor"}
    )
    playbook: list[PlaybookStep] = Field(default_factory=list)
    disclaimer: str = "Synthetic demo only."
    data_path: str | None = None
    feature_exclude: list[str] = Field(default_factory=list)
    secondary_label_col: str | None = None

    @property
    def group_time_col(self) -> str | None:
        """Alias used by TabPFN Thinking mode."""
        return self.time_col


def load_domain(path: str | Path | None = None) -> DomainConfig:
    """Load domain.yaml from path, or search common locations."""
    candidates: list[Path] = []
    if path is not None:
        candidates.append(Path(path))
    else:
        cwd = Path.cwd()
        candidates.extend(
            [
                cwd / "domain.yaml",
                cwd / "domain.yml",
                Path(__file__).resolve().parents[2] / "domain.yaml",
            ]
        )
    for p in candidates:
        if p.is_file():
            with p.open(encoding="utf-8") as f:
                raw: dict[str, Any] = yaml.safe_load(f) or {}
            return DomainConfig.model_validate(raw)
    return DomainConfig()


def find_project_root(start: Path | None = None) -> Path:
    """Walk up looking for domain.yaml or pyproject.toml."""
    cur = (start or Path.cwd()).resolve()
    for p in [cur, *cur.parents]:
        if (p / "domain.yaml").is_file() or (p / "pyproject.toml").is_file():
            if (p / "src" / "tabpfn_hack_core").is_dir() or (p / "domain.yaml").is_file():
                return p
    return Path.cwd()
