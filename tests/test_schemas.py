import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from soramimi_align.schemas import AthleteName, AthleteParodyLyrics


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


test_athlete_name_from_text()
