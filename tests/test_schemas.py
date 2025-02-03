import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from soramimi_align.schemas import (
    AnalyzedLyrics,
    AnalyzedWordItem,
    AthleteName,
    AthleteParodyLyrics,
)


def test_lyrics_from_text():
    text = """
    イチロー 大谷 ダルビッシュ
    いちろう おおたに だるびっしゅ
    
    選手一覧
    イチロー
    大谷
    ダルビッシュ
    """
    lyrics = AthleteParodyLyrics.from_text(text)
    assert lyrics.parody_lines == ["イチロー 大谷 ダルビッシュ"]
    assert lyrics.original_lines == ["いちろう おおたに だるびっしゅ"]
    assert lyrics.athlete_names == ["イチロー", "大谷", "ダルビッシュ"]


def test_athlete_name_from_text():
    raw_text = "山田(やまだ)"
    name = AthleteName.from_text(raw_text)
    assert name.raw == raw_text
    assert name.pronounced_surface == "山田"
    assert name.pre_silent_surface == ""
    assert name.post_silent_surface == ""
    assert name.pronunciation == "ヤマダ"

    raw_text = "山田（やまだ）"
    name = AthleteName.from_text(raw_text)
    assert name.raw == raw_text
    assert name.pronounced_surface == "山田"
    assert name.pre_silent_surface == ""
    assert name.post_silent_surface == ""
    assert name.pronunciation == "ヤマダ"

    raw_text = "(山田)太郎"
    name = AthleteName.from_text(raw_text)
    assert name.raw == raw_text
    assert name.pronounced_surface == "太郎"
    assert name.pre_silent_surface == "山田"
    assert name.post_silent_surface == ""
    assert name.pronunciation == ""

    raw_text = "(山田)太郎(たろう)"
    name = AthleteName.from_text(raw_text)
    assert name.raw == raw_text
    assert name.pronounced_surface == "太郎"
    assert name.pre_silent_surface == "山田"
    assert name.post_silent_surface == ""
    assert name.pronunciation == "タロウ"

    raw_text = "(山田太郎)"
    name = AthleteName.from_text(raw_text)
    assert name.raw == raw_text
    assert name.pronounced_surface == "山田太郎"
    assert name.pre_silent_surface == ""
    assert name.post_silent_surface == ""
    assert name.pronunciation == ""

    raw_text = "(山田"
    name = AthleteName.from_text(raw_text)
    assert name.raw == raw_text
    assert name.pronounced_surface == "山田"
    assert name.pre_silent_surface == ""
    assert name.post_silent_surface == ""
    assert name.pronunciation == ""

    raw_text = "山田)"
    name = AthleteName.from_text(raw_text)
    assert name.raw == raw_text
    assert name.pronounced_surface == "山田"
    assert name.pre_silent_surface == ""
    assert name.post_silent_surface == ""
    assert name.pronunciation == ""

    raw_text = "ウィリー(ウィリアム・テル)"
    name = AthleteName.from_text(raw_text)
    assert name.raw == raw_text
    assert name.pronounced_surface == "ウィリー"
    assert name.pre_silent_surface == ""
    assert name.post_silent_surface == "ウィリアム・テル"
    assert name.pronunciation == ""


def test_analyzed_lyrics_from_text():
    text = """
    イチロー 大谷 有
    イチロー オオタニ ユウ
    風 の 中 の すばる
    カゼ/p ノ ナカ/p ノ スバル/p"""

    analyzed_lyrics = AnalyzedLyrics.from_text(text)

    assert analyzed_lyrics.parody[0][0] == AnalyzedWordItem(
        surface="イチロー", pronunciation="イチロー", is_phrase_start=False, memo={}
    )
    assert analyzed_lyrics.parody[0][1] == AnalyzedWordItem(
        surface="大谷", pronunciation="オオタニ", is_phrase_start=False, memo={}
    )
    assert analyzed_lyrics.parody[0][2] == AnalyzedWordItem(
        surface="有", pronunciation="ユウ", is_phrase_start=False, memo={}
    )
    assert analyzed_lyrics.original[0][0] == AnalyzedWordItem(
        surface="風", pronunciation="カゼ", is_phrase_start=True, memo={}
    )
    assert analyzed_lyrics.original[0][1] == AnalyzedWordItem(
        surface="の", pronunciation="ノ", is_phrase_start=False, memo={}
    )
    assert analyzed_lyrics.original[0][2] == AnalyzedWordItem(
        surface="中", pronunciation="ナカ", is_phrase_start=True, memo={}
    )
    assert analyzed_lyrics.original[0][3] == AnalyzedWordItem(
        surface="の", pronunciation="ノ", is_phrase_start=False, memo={}
    )
    assert analyzed_lyrics.original[0][4] == AnalyzedWordItem(
        surface="すばる", pronunciation="スバル", is_phrase_start=True, memo={}
    )
