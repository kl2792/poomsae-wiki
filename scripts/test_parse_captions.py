#!/usr/bin/env python3
"""Tests for parse_captions.py — VTT auto-caption parsing."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from parse_captions import (
    parse_vtt_timestamp,
    strip_vtt_tags,
    parse_vtt,
    merge_segments,
    find_vtt_file,
    parse_captions,
    CAPTIONS_DIR,
)


def test_parse_vtt_timestamp_basic():
    """Timestamps should convert HH:MM:SS.mmm to seconds."""
    assert parse_vtt_timestamp("00:00:00.000") == 0.0
    assert parse_vtt_timestamp("00:01:00.000") == 60.0
    assert parse_vtt_timestamp("00:00:26.800") == 26.8
    assert parse_vtt_timestamp("01:02:03.456") == 3723.456


def test_strip_vtt_tags():
    """VTT inline tags should be removed, leaving clean text."""
    raw = "tango<00:00:26.800><c> refers</c><00:00:27.279><c> to</c><00:00:27.439><c> the</c>"
    assert strip_vtt_tags(raw) == "tango refers to the"

    # Already clean text passes through
    assert strip_vtt_tags("hello world") == "hello world"

    # Empty tags
    assert strip_vtt_tags("<c></c>") == ""


def test_parse_vtt_skips_music():
    """[Music] annotations should be filtered out."""
    vtt = """WEBVTT

00:00:15.180 --> 00:00:23.340
[Music]

00:00:26.240 --> 00:00:28.150
tango refers to the source of
"""
    segments = parse_vtt(vtt)
    assert len(segments) == 1
    assert segments[0]["text"] == "tango refers to the source of"


def test_parse_vtt_extracts_timestamps():
    """Segment timestamps should be parsed correctly."""
    vtt = """WEBVTT

00:00:26.240 --> 00:00:28.150 align:start position:0%
hello world
"""
    segments = parse_vtt(vtt)
    assert len(segments) == 1
    assert abs(segments[0]["start"] - 26.24) < 0.01
    assert abs(segments[0]["end"] - 28.15) < 0.01


def test_parse_vtt_multiline_text():
    """Multi-line caption text within a segment should be joined."""
    vtt = """WEBVTT

00:00:26.240 --> 00:00:28.150
line one
line two
"""
    segments = parse_vtt(vtt)
    assert len(segments) == 1
    assert segments[0]["text"] == "line one line two"


def test_merge_segments_dedup_prefix():
    """Segments where one is a prefix of the other should merge."""
    segments = [
        {"start": 0.0, "end": 1.0, "text": "hello"},
        {"start": 0.5, "end": 2.0, "text": "hello world"},
        {"start": 1.0, "end": 3.0, "text": "hello world today"},
    ]
    merged = merge_segments(segments)
    assert len(merged) == 1
    assert merged[0]["text"] == "hello world today"
    assert merged[0]["start"] == 0.0
    assert merged[0]["end"] == 3.0


def test_merge_segments_distinct():
    """Segments with different text should stay separate."""
    segments = [
        {"start": 0.0, "end": 2.0, "text": "first sentence about blocking"},
        {"start": 5.0, "end": 7.0, "text": "second sentence about striking"},
    ]
    merged = merge_segments(segments)
    assert len(merged) == 2


def test_merge_segments_word_overlap():
    """Segments sharing trailing/leading words should merge."""
    segments = [
        {"start": 0.0, "end": 2.0, "text": "the blocking arm should"},
        {"start": 1.5, "end": 3.0, "text": "arm should be straightened"},
    ]
    merged = merge_segments(segments)
    assert len(merged) == 1
    # Should keep the longer text
    assert "straightened" in merged[0]["text"]


def test_merge_segments_empty():
    """Empty input should return empty output."""
    assert merge_segments([]) == []


def test_find_vtt_taegeuk_1jang():
    """Should find the existing VTT file for taegeuk-1jang."""
    path = find_vtt_file("taegeuk-1jang")
    if path is not None:
        assert path.suffix == ".vtt"
        assert "WhkjRruCBTo" in path.name
    # If no VTT exists, test is informational (not a failure)


def test_parse_captions_taegeuk_1jang():
    """If VTT exists for taegeuk-1jang, should produce non-empty captions."""
    path = find_vtt_file("taegeuk-1jang")
    if path is None:
        print("    (skipped: no VTT file for taegeuk-1jang)")
        return

    result = parse_captions("taegeuk-1jang")
    assert result is not None
    assert result["form_slug"] == "taegeuk-1jang"
    assert len(result["captions"]) > 0

    # Each caption should have required fields
    for cap in result["captions"]:
        assert "start" in cap
        assert "end" in cap
        assert "text" in cap
        assert isinstance(cap["start"], float)
        assert cap["end"] >= cap["start"]
        assert len(cap["text"]) > 0

    # Merged captions should be far fewer than raw VTT segments
    vtt_text = path.read_text()
    raw_count = len(parse_vtt(vtt_text))
    assert len(result["captions"]) < raw_count, (
        f"Merging should reduce segment count: {len(result['captions'])} merged vs {raw_count} raw"
    )


def test_parse_captions_nonexistent():
    """Nonexistent slug should return None gracefully."""
    result = parse_captions("nonexistent-form")
    assert result is None


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
