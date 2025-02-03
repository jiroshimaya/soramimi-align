import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from soramimi_align.align_mora import (
    align_analyzed_lyrics,
    eval_vowel_consonant_distance,
    find_correspondance,
    split_consonant_vowel,
)
from soramimi_align.schemas import AnalyzedLyrics


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

    assert wrapper("ああ", "ああ") == [("あ", "あ"), ("あ", "あ")]
    assert wrapper("くどう", "かと") == [("く", "か"), ("どう", "と")]
    assert wrapper("どう", "とん") == [("ど", "と"), ("う", "ん")]
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

    idx = 0
    assert results[idx].parody_mora == "ア"
    assert results[idx].original_mora == "ア"
    assert results[idx].parody_vowel == "a"
    assert results[idx].original_vowel == "a"
    assert results[idx].parody_consonant == ""
    assert results[idx].original_consonant == ""
    assert results[idx].is_parody_word_start == True
    assert results[idx].is_parody_word_end == False
    assert results[idx].is_original_phrase_start == True
    assert results[idx].is_original_phrase_end == False
    assert results[idx].line_id == "0"

    idx += 1
    assert results[idx].parody_mora == "ベ"
    assert results[idx].original_mora == "レ"
    assert results[idx].parody_vowel == "e"
    assert results[idx].original_vowel == "e"
    assert results[idx].parody_consonant == "b"
    assert results[idx].original_consonant == "r"
    assert results[idx].is_parody_word_start == False
    assert results[idx].is_parody_word_end == True
    assert results[idx].is_original_phrase_start == False
    assert results[idx].is_original_phrase_end == True
    assert results[idx].line_id == "0"

    idx += 1
    assert results[idx].parody_mora == "ク"
    assert results[idx].original_mora == "ク"
    assert results[idx].parody_vowel == "u"
    assert results[idx].original_vowel == "u"
    assert results[idx].parody_consonant == "k"
    assert results[idx].original_consonant == "k"
    assert results[idx].is_parody_word_start == True
    assert results[idx].is_parody_word_end == False
    assert results[idx].is_original_phrase_start == True
    assert results[idx].is_original_phrase_end == False
    assert results[idx].line_id == "0"

    idx += 1
    assert results[idx].parody_mora == "ル"
    assert results[idx].original_mora == "ル"
    assert results[idx].parody_vowel == "u"
    assert results[idx].original_vowel == "u"
    assert results[idx].parody_consonant == "r"
    assert results[idx].original_consonant == "r"
    assert results[idx].is_parody_word_start == False
    assert results[idx].is_parody_word_end == False
    assert results[idx].is_original_phrase_start == False
    assert results[idx].is_original_phrase_end == False
    assert results[idx].line_id == "0"

    idx += 1
    assert results[idx].parody_mora == "ー"
    assert results[idx].original_mora == ""
    assert results[idx].parody_vowel == ":"
    assert results[idx].original_vowel == ""
    assert results[idx].parody_consonant == ""
    assert results[idx].original_consonant == ""
    assert results[idx].is_parody_word_start == False
    assert results[idx].is_parody_word_end == False
    assert results[idx].is_original_phrase_start == False
    assert results[idx].is_original_phrase_end == False
    assert results[idx].line_id == "0"

    idx += 1
    assert results[idx].parody_mora == "ン"
    assert results[idx].original_mora == "ウ"
    assert results[idx].parody_vowel == "N"
    assert results[idx].original_vowel == "u"
    assert results[idx].parody_consonant == ""
    assert results[idx].original_consonant == ""
    assert results[idx].is_parody_word_start == False
    assert results[idx].is_parody_word_end == True
    assert results[idx].is_original_phrase_start == False
    assert results[idx].is_original_phrase_end == True
    assert results[idx].line_id == "0"

    idx += 1
    assert results[idx].parody_mora == "イ"
    assert results[idx].original_mora == "キ"
    assert results[idx].parody_vowel == "i"
    assert results[idx].original_vowel == "i"
    assert results[idx].parody_consonant == ""
    assert results[idx].original_consonant == "kj"
    assert results[idx].is_parody_word_start == True
    assert results[idx].is_parody_word_end == False
    assert results[idx].is_original_phrase_start == True
    assert results[idx].is_original_phrase_end == False
    assert results[idx].line_id == "0"

    idx += 1
    assert results[idx].parody_mora == "セ"
    assert results[idx].original_mora == "セ"
    assert results[idx].parody_vowel == "e"
    assert results[idx].original_vowel == "e"
    assert results[idx].parody_consonant == "s"
    assert results[idx].original_consonant == "s"
    assert results[idx].is_parody_word_start == False
    assert results[idx].is_parody_word_end == True
    assert results[idx].is_original_phrase_start == False
    assert results[idx].is_original_phrase_end == False
    assert results[idx].line_id == "0"

    idx += 1
    assert results[idx].parody_mora == "ク"
    assert results[idx].original_mora == "ツ"
    assert results[idx].parody_vowel == "u"
    assert results[idx].original_vowel == "u"
    assert results[idx].parody_consonant == "k"
    assert results[idx].original_consonant == "ts"
    assert results[idx].is_parody_word_start == True
    assert results[idx].is_parody_word_end == False
    assert results[idx].is_original_phrase_start == False
    assert results[idx].is_original_phrase_end == False
    assert results[idx].line_id == "0"
