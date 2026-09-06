import json
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from src.benchmark import safe_extract_score
from src.judge import DEFAULT_JUDGES, run_judges
from src.utils.load_config import load_config

PANEL = ["lab-a/judge", "lab-b/judge", "lab-c/judge"]


def scored(n):
    return f"Some analysis.\n<score>{n}</score>\nJustification."


@pytest.mark.asyncio
async def test_run_judges_collects_every_judge():
    with patch("src.judge.run_judge", AsyncMock(side_effect=[scored(7), scored(8), scored(9)])):
        out = await run_judges("og", "clone", PANEL)

    assert list(out) == PANEL
    assert [safe_extract_score(r) for r in out.values()] == [7, 8, 9]


@pytest.mark.asyncio
async def test_run_judges_survives_one_failing_judge():
    """One judge going down must not sink the scenario."""
    with patch("src.judge.run_judge",
               AsyncMock(side_effect=[scored(7), RuntimeError("down"), scored(9)])):
        out = await run_judges("og", "clone", PANEL)

    assert out["lab-b/judge"] is None
    usable = [safe_extract_score(r) for r in out.values() if r is not None]
    assert usable == [7, 9]


def test_safe_extract_score_tolerates_malformed_judge_output():
    assert safe_extract_score(scored(6)) == 6
    assert safe_extract_score("I refuse to score this.") is None
    assert safe_extract_score("<score>not a number</score>") is None
    assert safe_extract_score(None) is None


def write_config(payload):
    path = Path(tempfile.mkdtemp()) / "config.json"
    path.write_text(json.dumps(payload))
    return str(path)


def test_load_config_reads_judge_panel():
    _, _, judges = load_config(
        write_config({"models": ["m"], "urls": ["u"], "judges": ["a/x", "b/y"]})
    )
    assert judges == ["a/x", "b/y"]


def test_load_config_accepts_single_judge_shorthand():
    _, _, judges = load_config(
        write_config({"models": ["m"], "urls": ["u"], "judge": "a/x"})
    )
    assert judges == ["a/x"]


def test_load_config_falls_back_to_default_panel():
    _, _, judges = load_config(write_config({"models": ["m"], "urls": ["u"]}))
    assert judges == DEFAULT_JUDGES
