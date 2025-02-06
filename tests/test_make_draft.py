import os
import sys
import tempfile

import pandas as pd
import pytest

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from soramimi_align.make_draft import (
    AthleteNameDetector,
    AthleteParodyLyrics,
    Tokenizer,
    parse_lyrics,
    summarize_parsed_lyrics,
)


@pytest.fixture
def athlete_name_detector():
    athlete_table = [
        {
            "id": 1,
            "original": "イチロー",
            "surface": "イチロー",
            "pronunciation": "イチロー",
        },
        {"id": 1, "original": "イチロー", "surface": "鈴木", "pronunciation": "スズキ"},
        {
            "id": 1,
            "original": "イチロー",
            "surface": "一郎",
            "pronunciation": "イチロー",
        },
        {
            "id": 1,
            "original": "イチロー",
            "surface": "鈴木一郎",
            "pronunciation": "スズキイチロー",
        },
        {
            "id": 2,
            "original": "大谷有",
            "surface": "大谷",
            "pronunciation": "オオタニ",
        },
        {
            "id": 2,
            "original": "大谷有",
            "surface": "有",
            "pronunciation": "アル",
        },
        {
            "id": 3,
            "original": "ダルビッシュ有",
            "surface": "有",
            "pronunciation": "ユウ",
        },
        {
            "id": 3,
            "original": "ダルビッシュ有",
            "surface": "ダルビッシュ",
            "pronunciation": "ダルビッシュ",
        },
        {
            "id": 3,
            "original": "ダルビッシュ有",
            "surface": "有",
            "pronunciation": "ユウ",
        },
    ]

    # テスト用の一時ファイルを作成
    with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp_file:
        athlete_table_df = pd.DataFrame(athlete_table)
        athlete_table_df.to_csv(tmp_file.name, index=False)
        tmp_file_path = tmp_file.name

    return AthleteNameDetector(tmp_file_path)


@pytest.fixture
def tokenizer():
    user_dict = {
        "○": "マル",
    }
    return Tokenizer(user_dict=user_dict)


def test_parse_lyrics(athlete_name_detector, tokenizer):
    text = """
    イチロー 大谷 （ダルビッシュ）有
    風の中のすばる
    
    # コメントアウト
    
    選手一覧
    イチロー
    大谷有
    ダルビッシュ有
    """
    lyrics = AthleteParodyLyrics.from_text(text)
    parsed_lyrics = parse_lyrics(lyrics, athlete_name_detector, tokenizer)
    summarized_text = summarize_parsed_lyrics(parsed_lyrics)
    print(summarized_text)
    summaized_tokens = summarized_text.split()
    expected_tokens = """
    イチロー 大谷 有
    イチロー オオタニ ユウ
    風 の 中 の すばる
    カゼ/p ノ ナカ/p ノ スバル/p""".split()

    assert summaized_tokens == expected_tokens


def test_tokenizer_format_text(tokenizer):
    text = "イチロー) 大谷 ダルビッシュ"
    assert tokenizer.format_text(text) == "イチロー 大谷 ダルビッシュ"


def test_tokenizer_is_phrase_start(tokenizer):
    text = "お先に失礼します"
    tokens = tokenizer.tokenize(text)

    assert tokenizer.is_phrase_start(tokens[0]) is True  # お
    assert tokenizer.is_phrase_start(tokens[1], tokens[0]) is False  # 先
    assert tokenizer.is_phrase_start(tokens[2], tokens[1]) is False  # に
    assert tokenizer.is_phrase_start(tokens[3], tokens[2]) is True  # 失礼
    assert tokenizer.is_phrase_start(tokens[4], tokens[3]) is True  # し
    assert tokenizer.is_phrase_start(tokens[5], tokens[4]) is False  # ます
