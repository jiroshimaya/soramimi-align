# %%
import glob
import os
from typing import Callable, Tuple

import editdistance as ed
import jamorasep
import pandas as pd

from soramimi_align.schemas import AlignedMora, AnalyzedLyrics, AnalyzedWordItem


def split_consonant_vowel(mora: str) -> Tuple[str, str]:
    if mora == "":
        return "", ""

    simpleipa = jamorasep.parse(mora, output_format="simple-ipa")[0]
    consonant, vowel = "".join(simpleipa[:-1]), simpleipa[-1]
    return consonant, vowel


def eval_vowel_consonant_distance(moras1: list[str], moras2: list[str]) -> float:
    # 本当は特殊モウラの削除コストを低くしたいが、うまくいっていない
    # if moras1 == [] and len(moras2) == 1 and moras2[0] in "ンーッ":
    #    return 0.5
    # elif moras2 == [] and len(moras1) == 1 and moras1[0] in "ンーッ":
    #    return 0.5

    vowels_consonants1 = [split_consonant_vowel(mora) for mora in moras1]
    vowels_consonants2 = [split_consonant_vowel(mora) for mora in moras2]
    vowels1 = [vowel for consonant, vowel in vowels_consonants1]
    vowels2 = [vowel for consonant, vowel in vowels_consonants2]
    consonants1 = [consonant for consonant, vowel in vowels_consonants1]
    consonants2 = [consonant for consonant, vowel in vowels_consonants2]

    vowel_dist = ed.eval(vowels1, vowels2)
    consonant_dist = ed.eval(consonants1, consonants2)
    return vowel_dist + consonant_dist


def find_correspondance(
    reference_text,
    input_segments,
    eval_func: Callable[[list[str], list[str]], float],
):
    memo = {}

    def inner_func(reference_text, input_segments):
        nonlocal memo

        memo_key = (tuple(reference_text), tuple(input_segments))
        if memo_key in memo:
            return memo[memo_key]

        if reference_text and not input_segments:
            dist = eval_func(reference_text, [])
            memo[memo_key] = (dist, [])
            return dist, []
        elif not reference_text and input_segments:
            flatten_input_segments = [x for row in input_segments for x in row]
            dist = eval_func(reference_text, flatten_input_segments)
            result = (
                dist,
                [(0, 0) for _ in range(len(input_segments))],
            )
            memo[memo_key] = result
            return result
        elif not reference_text and not input_segments:
            return 0, []
        elif reference_text and len(input_segments) == 1:
            # dist = ed.eval(reference_text, input_segments[0])
            dist = eval_func(reference_text, input_segments[0])
            memo[memo_key] = (dist, [(0, len(reference_text))])
            return dist, [(0, len(reference_text))]

        flatten_input_segments = tuple(x for row in input_segments for x in row)
        if reference_text == flatten_input_segments:
            correspondance = []
            cnt = 0
            for seg in input_segments:
                correspondance.append((cnt, cnt + len(seg)))
                cnt += len(seg)
            memo[memo_key] = (0, correspondance)
            return 0, correspondance

        text = input_segments[0]
        results = []
        window_size = 5
        for i in range(2 * window_size + 1):
            diff = i - window_size
            if len(text) + diff < 0:
                continue
            head_dist = eval_func(reference_text[0 : len(text) + diff], text)
            head_correspondance = [(0, len(text) + diff)]
            tail_dist, tail_correspondance = inner_func(
                reference_text[len(text) + diff :], input_segments[1:]
            )
            tail_correspondance = [
                (s + len(text) + diff, e + len(text) + diff)
                for s, e in tail_correspondance
            ]

            dist = head_dist + tail_dist
            correspondance = head_correspondance + tail_correspondance
            results.append((dist, correspondance))

        min_result = min(results, key=lambda x: x[0])
        memo[memo_key] = min_result
        return min_result

    if isinstance(reference_text, str):
        reference_text = tuple(reference_text)
    return inner_func(reference_text, input_segments)


def align(
    parody_line: list[AnalyzedWordItem], original_line: list[AnalyzedWordItem]
) -> list[AlignedMora]:
    input_moras = []
    is_parody_word_starts = []
    is_parody_word_ends = []
    parody_word_surfaces = []
    for word in parody_line:
        moras = jamorasep.parse(word.pronunciation)
        input_moras += moras
        is_parody_word_starts += [True] + [False] * (len(moras) - 1)
        is_parody_word_ends += [False] * (len(moras) - 1) + [True]
        parody_word_surfaces += [word.surface] * len(moras)
    reference_moras = []
    is_original_phrase_starts = []
    is_original_phrase_ends = []
    is_original_word_starts = []
    is_original_word_ends = []
    original_word_surfaces = []
    for word in original_line:
        moras = jamorasep.parse(word.pronunciation)
        reference_moras += moras
        original_word_surfaces += [word.surface] * len(moras)
        if word.is_phrase_start:
            is_original_phrase_starts += [True] + [False] * (len(moras) - 1)
        else:
            is_original_phrase_starts += [False] * len(moras)

        # 基本的に単語の末尾をphraseの末尾としておいて、直後がphraseの始まりでないならFalseに修正する。
        if not word.is_phrase_start and len(is_original_phrase_starts) > 0:
            is_original_phrase_ends[-1] = False
        is_original_phrase_ends += [False] * (len(moras) - 1) + [True]

        is_original_word_starts += [True] + [False] * (len(moras) - 1)
        is_original_word_ends += [False] * (len(moras) - 1) + [True]
    dist, correspondance = find_correspondance(
        reference_moras, input_moras, eval_vowel_consonant_distance
    )
    results = []
    for i, (start, end) in enumerate(correspondance):
        parody_mora = input_moras[i]
        is_parody_word_start = is_parody_word_starts[i]
        is_parody_word_end = is_parody_word_ends[i]
        parody_word_surface = ""
        if is_parody_word_start and parody_mora:
            parody_word_surface = parody_word_surfaces[i]
        original_mora = reference_moras[start:end]
        if start == end:
            is_original_phrase_start = False
            is_original_phrase_end = False
            is_original_word_start = False
            is_original_word_end = False
        else:
            is_original_phrase_start = is_original_phrase_starts[start]
            is_original_phrase_end = is_original_phrase_ends[end - 1]
            is_original_word_start = is_original_word_starts[start]
            is_original_word_end = is_original_word_ends[end - 1]

        original_word_surface = ""
        if is_original_word_start and original_mora:
            original_word_surface = original_word_surfaces[start]

        obj = AlignedMora(
            parody_mora=parody_mora,
            is_parody_word_start=is_parody_word_start,
            is_parody_word_end=is_parody_word_end,
            original_mora="".join(original_mora),
            is_original_phrase_start=is_original_phrase_start,
            is_original_phrase_end=is_original_phrase_end,
            is_original_word_start=is_original_word_start,
            is_original_word_end=is_original_word_end,
            original_word_surface=original_word_surface,
            parody_word_surface=parody_word_surface,
        )
        results.append(obj)

    # 空文字の修正
    # startは直後の情報と同じにする。
    for i in range(len(results) - 2, -1, -1):
        if results[i].original_mora == "":
            results[i].is_original_phrase_start = results[
                i + 1
            ].is_original_phrase_start
            results[i].is_original_word_start = results[i + 1].is_original_word_start
    # endは直前の情報と同じにする
    for i in range(1, len(results)):
        if results[i].original_mora == "":
            results[i].is_original_phrase_end = results[i - 1].is_original_phrase_end
            results[i].is_original_word_end = results[i - 1].is_original_word_end
    return results


def align_analyzed_lyrics(analyzed_lyrics: AnalyzedLyrics) -> list[AlignedMora]:
    all_results = []
    for line_id, (parody_line, original_line) in enumerate(
        zip(analyzed_lyrics.parody, analyzed_lyrics.original)
    ):
        results = align(parody_line, original_line)
        for result in results:
            result.line_id = str(line_id)

            parody_consonant, parody_vowel = split_consonant_vowel(result.parody_mora)
            original_consonant, original_vowel = split_consonant_vowel(
                result.original_mora
            )
            result.parody_vowel = parody_vowel
            result.parody_consonant = parody_consonant
            result.original_vowel = original_vowel
            result.original_consonant = original_consonant
        all_results.extend(results)
    return all_results


def align_files(input_dir: str):
    all_results = []
    if os.path.isdir(input_dir):
        files = sorted(glob.glob(os.path.join(input_dir, "*.txt")))
    else:
        files = [input_dir]
    for input_file_path in files:
        print(input_file_path)
        with open(input_file_path, "r") as f:
            input_text = f.read()
        analyzed_lyrics = AnalyzedLyrics.from_text(input_text)
        results = align_analyzed_lyrics(analyzed_lyrics)
        for result in results:
            result.input_file_path = input_file_path
        all_results.extend(results)
    return all_results


def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input_dir", type=str, default="data/lyrics")
    parser.add_argument("-o", "--output_file_path", type=str, default="output.csv")
    args = parser.parse_args()
    all_results = align_files(args.input_dir)
    df = pd.DataFrame(all_results)
    df.to_csv(args.output_file_path, index=False)


if __name__ == "__main__":
    main()
