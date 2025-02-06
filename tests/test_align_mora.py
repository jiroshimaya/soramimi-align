import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from soramimi_align.align_mora import (
    align_analyzed_lyrics,
    eval_vowel_consonant_distance,
    find_correspondance,
    split_consonant_vowel,
)
from soramimi_align.schemas import AlignedMora, AnalyzedLyrics


def test_split_consonant_vowel():
    assert split_consonant_vowel("") == ("", "")
    assert split_consonant_vowel("あ") == ("", "a")
    assert split_consonant_vowel("ア") == ("", "a")
    assert split_consonant_vowel("ー") == ("", ":")
    assert split_consonant_vowel("あー") == ("", "a")
    assert split_consonant_vowel("ッ") == ("", "Q")


def test_eval_vowel_consonant_distance():
    assert eval_vowel_consonant_distance(["あ"], ["あ"]) == 0
    assert eval_vowel_consonant_distance(["あ"], ["い"]) == 1
    assert eval_vowel_consonant_distance(["あ"], ["か"]) == 1
    assert eval_vowel_consonant_distance(["あ"], [""]) == 1
    assert eval_vowel_consonant_distance(["か"], [""]) == 2
    assert eval_vowel_consonant_distance(["あ"], ["き"]) == 2


def test_find_correspondance():
    def wrapper(
        reference_moras: str | list[str], input_moras: str | list[str]
    ) -> list[tuple[str, str]]:
        """テストケースを作りやすいように、出力をテキストのペアにする"""
        dist, correspondance = find_correspondance(
            reference_moras, input_moras, eval_vowel_consonant_distance
        )

        result = []
        for input_mora, (start, end) in zip(input_moras, correspondance):
            result.append((reference_moras[start:end], input_mora))
        return result

    assert wrapper("アア", "アア") == [("ア", "ア"), ("ア", "ア")]
    assert wrapper("クドウ", "カト") == [("ク", "カ"), ("ドウ", "ト")]
    assert wrapper("ドウ", "トン") == [("ド", "ト"), ("ウ", "ン")]
    assert wrapper("トントン", "ソコ") == [("ト", "ソ"), ("ントン", "コ")]
    assert wrapper("ソコ", "トントン") == [
        ("ソ", "ト"),
        ("", "ン"),
        ("コ", "ト"),
        ("", "ン"),
    ]


def test_align_analyzed_lyrics():
    text = """
    阿部 クルーン 伊勢 工藤 中野
    アベ クルーン イセ クドウ ナカノ
    荒れ 狂う 季節 の 中 を
    アレ/p クルウ/p キセツ/p ノ ナカ/p オ"""
    analyzed_lyrics = AnalyzedLyrics.from_text(text)
    results = align_analyzed_lyrics(analyzed_lyrics)

    assert results[0] == AlignedMora(
        parody_mora="ア",
        original_mora="ア",
        parody_vowel="a",
        original_vowel="a",
        parody_consonant="",
        original_consonant="",
        is_parody_word_start=True,
        is_parody_word_end=False,
        is_original_phrase_start=True,
        is_original_phrase_end=False,
        is_original_word_start=True,
        is_original_word_end=False,
        line_id="0",
        parody_word_surface="阿部",
        original_word_surface="荒れ",
    )

    assert results[1] == AlignedMora(
        parody_mora="ベ",
        original_mora="レ",
        parody_vowel="e",
        original_vowel="e",
        parody_consonant="b",
        original_consonant="r",
        is_parody_word_start=False,
        is_parody_word_end=True,
        is_original_phrase_start=False,
        is_original_phrase_end=True,
        is_original_word_start=False,
        is_original_word_end=True,
        line_id="0",
        parody_word_surface="",
        original_word_surface="",
    )

    assert results[2] == AlignedMora(
        parody_mora="ク",
        original_mora="ク",
        parody_vowel="u",
        original_vowel="u",
        parody_consonant="k",
        original_consonant="k",
        is_parody_word_start=True,
        is_parody_word_end=False,
        is_original_phrase_start=True,
        is_original_phrase_end=False,
        is_original_word_start=True,
        is_original_word_end=False,
        line_id="0",
        parody_word_surface="クルーン",
        original_word_surface="狂う",
    )

    assert results[3] == AlignedMora(
        parody_mora="ル",
        original_mora="ル",
        parody_vowel="u",
        original_vowel="u",
        parody_consonant="r",
        original_consonant="r",
        is_parody_word_start=False,
        is_parody_word_end=False,
        is_original_phrase_start=False,
        is_original_phrase_end=False,
        is_original_word_start=False,
        is_original_word_end=False,
        line_id="0",
        parody_word_surface="",
        original_word_surface="",
    )

    assert results[4] == AlignedMora(
        parody_mora="ー",
        original_mora="",
        parody_vowel=":",
        original_vowel="",
        parody_consonant="",
        original_consonant="",
        is_parody_word_start=False,
        is_parody_word_end=False,
        is_original_phrase_start=False,
        is_original_phrase_end=False,
        is_original_word_start=False,
        is_original_word_end=False,
        line_id="0",
        parody_word_surface="",
        original_word_surface="",
    )

    assert results[5] == AlignedMora(
        parody_mora="ン",
        original_mora="ウ",
        parody_vowel="N",
        original_vowel="u",
        parody_consonant="",
        original_consonant="",
        is_parody_word_start=False,
        is_parody_word_end=True,
        is_original_phrase_start=False,
        is_original_phrase_end=True,
        is_original_word_start=False,
        is_original_word_end=True,
        line_id="0",
        parody_word_surface="",
        original_word_surface="",
    )

    assert results[6] == AlignedMora(
        parody_mora="イ",
        original_mora="キ",
        parody_vowel="i",
        original_vowel="i",
        parody_consonant="",
        original_consonant="kj",
        is_parody_word_start=True,
        is_parody_word_end=False,
        is_original_phrase_start=True,
        is_original_phrase_end=False,
        is_original_word_start=True,
        is_original_word_end=False,
        line_id="0",
        parody_word_surface="伊勢",
        original_word_surface="季節",
    )

    assert results[7] == AlignedMora(
        parody_mora="セ",
        original_mora="セ",
        parody_vowel="e",
        original_vowel="e",
        parody_consonant="s",
        original_consonant="s",
        is_parody_word_start=False,
        is_parody_word_end=True,
        is_original_phrase_start=False,
        is_original_phrase_end=False,
        is_original_word_start=False,
        is_original_word_end=False,
        line_id="0",
        parody_word_surface="",
        original_word_surface="",
    )

    assert results[8] == AlignedMora(
        parody_mora="ク",
        original_mora="ツ",
        parody_vowel="u",
        original_vowel="u",
        parody_consonant="k",
        original_consonant="ts",
        is_parody_word_start=True,
        is_parody_word_end=False,
        is_original_phrase_start=False,
        is_original_phrase_end=False,
        is_original_word_start=False,
        is_original_word_end=True,
        line_id="0",
        parody_word_surface="工藤",
        original_word_surface="",
    )

    assert results[9] == AlignedMora(
        parody_mora="ド",
        original_mora="ノ",
        parody_vowel="o",
        original_vowel="o",
        parody_consonant="d",
        original_consonant="n",
        is_parody_word_start=False,
        is_parody_word_end=False,
        is_original_phrase_start=False,
        is_original_phrase_end=True,
        is_original_word_start=True,
        is_original_word_end=True,
        line_id="0",
        parody_word_surface="",
        original_word_surface="の",
    )

    assert results[10] == AlignedMora(
        parody_mora="ウ",
        original_mora="",
        parody_vowel="u",
        original_vowel="",
        parody_consonant="",
        original_consonant="",
        is_parody_word_start=False,
        is_parody_word_end=True,
        is_original_phrase_start=True,
        is_original_phrase_end=True,
        is_original_word_start=True,
        is_original_word_end=True,
        line_id="0",
        parody_word_surface="",
        original_word_surface="",
    )

    assert results[11] == AlignedMora(
        parody_mora="ナ",
        original_mora="ナ",
        parody_vowel="a",
        original_vowel="a",
        parody_consonant="n",
        original_consonant="n",
        is_parody_word_start=True,
        is_parody_word_end=False,
        is_original_phrase_start=True,
        is_original_phrase_end=False,
        is_original_word_start=True,
        is_original_word_end=False,
        line_id="0",
        parody_word_surface="中野",
        original_word_surface="中",
    )

    assert results[12] == AlignedMora(
        parody_mora="カ",
        original_mora="カ",
        parody_vowel="a",
        original_vowel="a",
        parody_consonant="k",
        original_consonant="k",
        is_parody_word_start=False,
        is_parody_word_end=False,
        is_original_phrase_start=False,
        is_original_phrase_end=False,
        is_original_word_start=False,
        is_original_word_end=True,
        line_id="0",
        parody_word_surface="",
        original_word_surface="",
    )

    assert results[13] == AlignedMora(
        parody_mora="ノ",
        original_mora="オ",
        parody_vowel="o",
        original_vowel="o",
        parody_consonant="n",
        original_consonant="",
        is_parody_word_start=False,
        is_parody_word_end=True,
        is_original_phrase_start=False,
        is_original_phrase_end=True,
        is_original_word_start=True,
        is_original_word_end=True,
        line_id="0",
        parody_word_surface="",
        original_word_surface="を",
    )

    text = """
    丼丼 藤
    ドンドン ト
    外 夜
    ソト/p ヨ/p"""
    analyzed_lyrics = AnalyzedLyrics.from_text(text)
    results = align_analyzed_lyrics(analyzed_lyrics)
    print(results)
    idx = 0
    assert results[idx].parody_mora == "ド"
    assert results[idx].original_mora == "ソ"
    assert results[idx].is_original_phrase_start
    assert not results[idx].is_original_phrase_end
    assert results[idx].is_original_word_start
    assert not results[idx].is_original_word_end

    idx = 1
    assert results[idx].parody_mora == "ン"
    assert results[idx].original_mora == ""
    assert not results[idx].is_original_phrase_start
    assert not results[idx].is_original_phrase_end
    assert not results[idx].is_original_word_start
    assert not results[idx].is_original_word_end

    idx = 2
    assert results[idx].parody_mora == "ド"
    assert results[idx].original_mora == "ト"
    assert not results[idx].is_original_phrase_start
    assert results[idx].is_original_phrase_end
    assert not results[idx].is_original_word_start
    assert results[idx].is_original_word_end

    idx = 3
    assert results[idx].parody_mora == "ン"
    assert results[idx].original_mora == ""
    assert results[idx].is_original_phrase_start
    assert results[idx].is_original_phrase_end
    assert results[idx].is_original_word_start
    assert results[idx].is_original_word_end

    idx = 4
    assert results[idx].parody_mora == "ト"
    assert results[idx].original_mora == "ヨ"
    assert results[idx].is_original_phrase_start
    assert results[idx].is_original_phrase_end
    assert results[idx].is_original_word_start
    assert results[idx].is_original_word_end
