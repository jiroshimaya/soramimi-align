# %%
import glob
import os

import jamorasep
import pandas as pd

from soramimi_align.align_mora import eval_vowel_consonant_distance, find_correspondance
from soramimi_align.schemas import AlignedMora, AnalyzedLyrics, AnalyzedWordItem


def align_parody_word_to_original(
    parody_line: list[AnalyzedWordItem], original_line: list[AnalyzedWordItem]
) -> list[AlignedMora]:
    parody_word_pronunciations = []
    parody_word_surfaces = []
    for word in parody_line:
        moras = jamorasep.parse(word.pronunciation)
        parody_word_pronunciations.append(moras)
        parody_word_surfaces.append(word.surface)

    original_moras = []
    is_original_phrase_starts = []
    is_original_phrase_ends = []
    is_original_word_starts = []
    is_original_word_ends = []
    original_word_surfaces = []
    for word in original_line:
        moras = jamorasep.parse(word.pronunciation)
        original_moras += moras
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
        original_moras,
        parody_word_pronunciations,
        eval_vowel_consonant_distance,
    )
    results = []
    for i, (start, end) in enumerate(correspondance):
        parody_word_pronunciation = parody_word_pronunciations[i]
        parody_word_surface = parody_word_surfaces[i]
        original_mora = original_moras[start:end]
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
        if original_mora:
            original_word_surface += original_word_surfaces[start]
            for i in range(start + 1, end):
                if is_original_word_starts[i]:
                    original_word_surface += original_word_surfaces[i]

        obj = AlignedMora(
            parody_mora="".join(parody_word_pronunciation),
            is_parody_word_start=True,
            is_parody_word_end=True,
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
        results = align_parody_word_to_original(parody_line, original_line)
        for result in results:
            result.line_id = str(line_id)

            result.parody_vowel = ""
            result.parody_consonant = ""
            result.original_vowel = ""
            result.original_consonant = ""
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
