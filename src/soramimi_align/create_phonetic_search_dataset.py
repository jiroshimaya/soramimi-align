import argparse
import json
import re
from collections import Counter, defaultdict

import pandas as pd

from soramimi_align.schemas import AlignedMora

# argparseを使ってコマンドライン引数を処理
parser = argparse.ArgumentParser(
    description="Process CSV files for phonetic search dataset."
)
parser.add_argument(
    "-w",
    "--word_table_path",
    type=str,
    required=True,
    help="Path to the word_table.csv file",
)
parser.add_argument(
    "-a",
    "--aligned_words_path",
    type=str,
    required=True,
    help="Path to the aligned_words.csv file",
)
args = parser.parse_args()


# baseball.csvの処理
def load_unique_wordlist(
    word_table_path: str, allowed_types: list[str] = ["full", "family", "registered"]
) -> list[str]:
    df = pd.read_csv(word_table_path)
    df = df[df["type"].isin(allowed_types)]
    df["pronunciation"] = df["pronunciation"].apply(
        lambda x: re.sub(r"[^ァ-ンー]", "", x)
    )
    return list(df["pronunciation"].unique())


def load_aligned_words(aligned_words_path: str) -> list[AlignedMora]:
    df = pd.read_csv(aligned_words_path)
    aligned_words = []
    for _, row in df.iterrows():
        aligned_word = AlignedMora(
            original_mora=row["original_mora"],
            is_original_word_start=row["is_original_word_start"],
            is_original_phrase_start=row["is_original_phrase_start"],
            is_original_word_end=row["is_original_word_end"],
            is_original_phrase_end=row["is_original_phrase_end"],
            parody_mora=row["parody_mora"],
            is_parody_word_start=True,
            is_parody_word_end=True,
        )
        aligned_words.append(aligned_word)
    return aligned_words


# 全体出力の確認用。あまり使わない。
def count_conversion(aligned_words: list[AlignedMora]) -> dict[tuple, Counter]:
    count_dict = defaultdict(Counter)

    for aligned_word in aligned_words:
        k = (
            aligned_word.original_mora,
            aligned_word.is_original_word_start,
            aligned_word.is_original_phrase_start,
            aligned_word.is_original_word_end,
            aligned_word.is_original_phrase_end,
        )
        count_dict[k]["total"] += 1
        count_dict[k][aligned_word.parody_mora] += 1

    return count_dict


def create_query_dataset(count_dict: dict[tuple, Counter]) -> dict[str, list[str]]:
    filtered_count_dict = {}
    for (
        original_word,
        is_original_word_start,
        is_original_phrase_start,
        is_original_word_end,
        is_original_phrase_end,
    ), v in count_dict.items():
        if not (is_original_phrase_start and is_original_word_end):
            continue
        if len(original_word) < 2:
            continue

        v.pop("total")
        parody_words = sorted(v.items(), key=lambda item: item[1], reverse=True)
        parody_words = [parody_word for parody_word, count in parody_words if count > 1]

        if not parody_words:
            continue

        filtered_count_dict[original_word] = parody_words

    return filtered_count_dict


def combine_query_and_words(
    query_dataset: dict[str, list[str]], wordlist: list[str]
) -> dict[str, list]:
    wordset = set(wordlist)
    queries = []
    for idx, (query, parody_words) in enumerate(query_dataset.items()):
        # wordsetに含まれるものだけ取得
        positive_words = [w for w in parody_words if w in wordset and w != query]

        # queryと同一のparody_wordは無条件で1位にする
        if query in wordset:
            words = [query] + positive_words

        queries.append(
            {
                "query_id": idx,
                "query": query,
                "positive": positive_words,
            }
        )

    return {"queries": queries, "wordlist": wordlist}


def create_phonetic_search_dataset(
    word_table_path: str, aligned_words_path: str
) -> dict[str, list]:
    wordlist = load_unique_wordlist(word_table_path)
    aligned_words = load_aligned_words(aligned_words_path)
    count_dict = count_conversion(aligned_words)
    query_dataset = create_query_dataset(count_dict)
    return combine_query_and_words(query_dataset, wordlist)


def main():
    parser = argparse.ArgumentParser(description="Create phonetic search dataset.")
    parser.add_argument(
        "-w",
        "--word_table_path",
        type=str,
        required=True,
        help="Path to the word_table.csv file",
    )
    parser.add_argument(
        "-a",
        "--aligned_words_path",
        type=str,
        required=True,
        help="Path to the aligned_words.csv file",
    )
    parser.add_argument(
        "-o",
        "--output_path",
        type=str,
        help="Path to the output file",
        default="output.json",
    )
    args = parser.parse_args()

    dataset = create_phonetic_search_dataset(
        args.word_table_path, args.aligned_words_path
    )

    with open(args.output_path, "w") as f:
        json.dump(dataset, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
