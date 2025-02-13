import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from soramimi_align.align_word import align_analyzed_lyrics
from soramimi_align.schemas import AnalyzedLyrics


def test_align_analyzed_lyrics():
    text = """
    阿部 クルーン 伊勢 工藤 中野
    アベ クルーン イセ クドウ ナカノ
    荒れ 狂う 季節 の 中 を
    アレ/p クルウ/p キセツ/p ノ ナカ/p オ"""
    analyzed_lyrics = AnalyzedLyrics.from_text(text)
    results = align_analyzed_lyrics(analyzed_lyrics)

    idx = 0
    assert results[idx].parody_mora == "アベ"
    assert results[idx].original_mora == "アレ"
    assert results[idx].is_original_phrase_start is True
    assert results[idx].is_original_phrase_end is True
    assert results[idx].is_original_word_start is True
    assert results[idx].is_original_word_end is True
    assert results[idx].parody_word_surface == "阿部"
    assert results[idx].original_word_surface == "荒れ"

    idx = 1
    assert results[idx].parody_mora == "クルーン"
    assert results[idx].original_mora == "クルウ"
    assert results[idx].is_original_phrase_start is True
    assert results[idx].is_original_phrase_end is True
    assert results[idx].is_original_word_start is True
    assert results[idx].is_original_word_end is True
    assert results[idx].parody_word_surface == "クルーン"
    assert results[idx].original_word_surface == "狂う"

    idx = 2
    assert results[idx].parody_mora == "イセ"
    assert results[idx].original_mora == "キセ"
    assert results[idx].is_original_phrase_start is True
    assert results[idx].is_original_phrase_end is False
    assert results[idx].is_original_word_start is True
    assert results[idx].is_original_word_end is False
    assert results[idx].parody_word_surface == "伊勢"
    assert results[idx].original_word_surface == "季節"

    idx = 3
    assert results[idx].parody_mora == "クドウ"
    assert results[idx].original_mora == "ツノ"
    assert results[idx].is_original_phrase_start is False
    assert results[idx].is_original_phrase_end is True
    assert results[idx].is_original_word_start is False
    assert results[idx].is_original_word_end is True
    assert results[idx].parody_word_surface == "工藤"
    assert results[idx].original_word_surface == "季節の"

    idx = 4
    assert results[idx].parody_mora == "ナカノ"
    assert results[idx].original_mora == "ナカオ"
    assert results[idx].is_original_phrase_start is True
    assert results[idx].is_original_phrase_end is True
    assert results[idx].is_original_word_start is True
    assert results[idx].is_original_word_end is True
    assert results[idx].parody_word_surface == "中野"
    assert results[idx].original_word_surface == "中を"
