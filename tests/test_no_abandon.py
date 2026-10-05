"""The playbook must not suggest abandoning cargo (fee is at most half the cargo value in this data)."""
from pathlib import Path

import yaml


def test_playbook_has_no_cancel_booking():
    dom = yaml.safe_load(Path("domains/freight-demurrage/domain.yaml").read_text())
    actions = [step["action"] for step in dom.get("playbook", [])]
    assert "cancel_booking" not in actions
    assert actions[0] == "divert"
