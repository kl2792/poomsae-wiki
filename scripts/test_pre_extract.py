#!/usr/bin/env python3
"""Tests for pre_extract.py — deterministic technique extraction from OCR transcripts."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from pre_extract import pre_extract, extract_key_moves, extract_sequence_steps, PRE_DIR, TRANSCRIPTS_DIR
from extract import FORM_META


def test_taegeuk_7jang_key_moves_count():
    """Taegeuk 7jang should have 13 KEY MOVES (the known count from the video)."""
    data = pre_extract("taegeuk-7jang")
    assert data is not None
    assert len(data["key_moves"]) == 13, f"Expected 13 key moves, got {len(data['key_moves'])}"


def test_taegeuk_7jang_no_hallucinated_techniques():
    """No technique name should appear that is not in the transcript.

    Specifically, 'FLAME BLOCK' and 'YEOM MAKGI' must NOT appear
    (these are known LLM hallucinations).
    """
    data = pre_extract("taegeuk-7jang")
    assert data is not None
    all_names = [m["name"] for m in data["key_moves"]]
    all_names += [s["name"] for s in data["sequence_steps"]]
    joined = " ".join(all_names).upper()
    assert "FLAME" not in joined, f"Hallucinated 'FLAME' found in: {all_names}"
    assert "YEOM" not in joined, f"Hallucinated 'YEOM' found in: {all_names}"


def test_taegeuk_7jang_key_move_names():
    """Key move names should match the video's summary list."""
    data = pre_extract("taegeuk-7jang")
    assert data is not None
    names = {m["number"]: m["name"] for m in data["key_moves"]}

    # Verify key expected techniques are present
    assert "SONAL GEODEUREO" in names.get("01", ""), f"01 should contain SONAL GEODEUREO: {names.get('01')}"
    assert "GEODEUREO BATANGSON" in names.get("02", ""), f"02 should contain GEODEUREO BATANGSON: {names.get('02')}"
    assert "BOJUMEOK" in names.get("03", ""), f"03 should be BOJUMEOK: {names.get('03')}"
    assert "GAWIMAKGI" in names.get("04", ""), f"04 should be GAWIMAKGI: {names.get('04')}"
    assert "JUCHUMSEOGI" in names.get("13", ""), f"13 should be JUCHUMSEOGI: {names.get('13')}"


def test_taegeuk_7jang_sequence_steps():
    """Taegeuk 7jang EXPLANATION sections should yield sequence steps."""
    data = pre_extract("taegeuk-7jang")
    assert data is not None
    steps = data["sequence_steps"]
    assert len(steps) >= 10, f"Expected at least 10 sequence steps, got {len(steps)}"

    # First step should be right side
    assert steps[0]["side"] == "right", f"First step should be right: {steps[0]}"


def test_taegeuk_7jang_sections():
    """Section timestamps should be detected for taegeuk-7jang."""
    data = pre_extract("taegeuk-7jang")
    assert data is not None
    sections = data["sections"]
    assert "poomsae" in sections, "poomsae section not found"
    assert "key_moves" in sections, "key_moves section not found"
    assert "explanation" in sections, "explanation section not found"
    assert "repeat" in sections, "repeat section not found"
    # Sections should be in chronological order
    assert sections["poomsae"] < sections["key_moves"] < sections["explanation"] < sections["repeat"]


def test_taegeuk_7jang_key_moves_have_timestamps():
    """Most key moves should have nonzero timestamps from breakdown headers."""
    data = pre_extract("taegeuk-7jang")
    assert data is not None
    with_ts = [m for m in data["key_moves"] if m["timestamp"] > 0]
    # At least 10 of 13 should have timestamps (some may have OCR issues)
    assert len(with_ts) >= 10, f"Expected at least 10 key moves with timestamps, got {len(with_ts)}"


def test_all_forms_produce_output():
    """Every form with a transcript should produce a pre-extraction JSON."""
    for slug in sorted(FORM_META.keys()):
        transcript = TRANSCRIPTS_DIR / f"{slug}.txt"
        if not transcript.exists():
            continue
        data = pre_extract(slug)
        assert data is not None, f"{slug}: pre_extract returned None"
        assert data["form_slug"] == slug


def test_no_noise_in_key_move_names():
    """Key move names should not consist entirely of noise words."""
    noise = {"KEY", "MOVES", "EXPLANATION", "PART", "REPEAT", "POOMSAE",
             "TAEGEUK", "KUKKIWON", "TAEKWONDO", "ACADEMY", "JANG"}
    for slug in sorted(FORM_META.keys()):
        transcript = TRANSCRIPTS_DIR / f"{slug}.txt"
        if not transcript.exists():
            continue
        data = pre_extract(slug)
        if data is None:
            continue
        for m in data["key_moves"]:
            words = set(m["name"].split())
            assert not words <= noise, f"{slug} key move #{m['number']} is pure noise: {m['name']}"


def test_output_json_structure():
    """Output JSON should have the expected top-level keys."""
    data = pre_extract("taegeuk-7jang")
    assert data is not None
    for key in ["form_slug", "key_moves", "sequence_steps", "tips", "sections"]:
        assert key in data, f"Missing key: {key}"

    # key_moves entries
    for m in data["key_moves"]:
        assert "number" in m
        assert "name" in m
        assert "timestamp" in m

    # sequence_steps entries
    for s in data["sequence_steps"]:
        assert "number" in s
        assert "name" in s
        assert "side" in s
        assert "timestamp" in s


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    failed = 0
    for test in tests:
        try:
            test()
            print(f"  PASS  {test.__name__}")
        except Exception as e:
            print(f"  FAIL  {test.__name__}: {e}")
            failed += 1
    print(f"\n{len(tests)} tests, {failed} failed")
    sys.exit(1 if failed else 0)
