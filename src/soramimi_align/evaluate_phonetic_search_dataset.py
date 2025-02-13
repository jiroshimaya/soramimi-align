import argparse
import json
from typing import Callable

import editdistance as ed
import jamorasep

from soramimi_align.schemas import PhoneticSearchDataset


def load_phonetic_search_dataset(path: str) -> PhoneticSearchDataset:
    with open(path, "r") as f:
        dataset = json.load(f)
    return PhoneticSearchDataset.from_dict(dataset)


def rank_by_editdistance(
    query_texts: list[str], wordlist_texts: list[str]
) -> list[list[str]]:
    query_moras = [jamorasep.parse(text) for text in query_texts]
    wordlist_moras = [jamorasep.parse(text) for text in wordlist_texts]

    filnal_results = []
    for query_mora in query_moras:
        scores = []
        for wordlist_mora in wordlist_moras:
            distance = ed.eval(query_mora, wordlist_mora)
            scores.append(distance)

        ranked_wordlist = [
            word for word, _ in sorted(zip(wordlist_texts, scores), key=lambda x: x[1])
        ]
        filnal_results.append(ranked_wordlist)
    return filnal_results


def rank_dataset(
    phonetic_search_dataset: PhoneticSearchDataset,
    rank_func: Callable[[list[str], list[str]], list[list[str]]],
    topn: int = 10,
) -> list[list[str]]:
    query_texts = [query.query for query in phonetic_search_dataset.queries]
    wordlist_texts = phonetic_search_dataset.words

    ranked_wordlists = rank_func(query_texts, wordlist_texts)
    topn_wordlists = [ranked_wordlist[:topn] for ranked_wordlist in ranked_wordlists]

    return topn_wordlists


def calculate_recall(
    ranked_wordlists: list[list[str]],
    positive_texts: list[list[str]],
) -> float:
    recalls = []
    for topn_wordlist, positive_text in zip(ranked_wordlists, positive_texts):
        positive_text_count = len(positive_text)
        hit_count = len(set(topn_wordlist) & set(positive_text))
        recall = hit_count / positive_text_count
        recalls.append(recall)

    return sum(recalls) / len(recalls)


def main():
    parser = argparse.ArgumentParser(description="Evaluate phonetic search dataset.")
    parser.add_argument(
        "-i",
        "--input_path",
        type=str,
        required=True,
        help="Path to the input file",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Verbose output",
    )
    args = parser.parse_args()

    dataset = load_phonetic_search_dataset(args.input_path)
    topn_wordlists = rank_dataset(dataset, rank_by_editdistance)
    positive_texts = [query.positive for query in dataset.queries]
    recall = calculate_recall(topn_wordlists, positive_texts)
    if args.verbose:
        for query, topn_wordlist in zip(dataset.queries, topn_wordlists):
            print(f"Query: {query.query}")
            print(f"Top {len(topn_wordlist)}: {topn_wordlist}")
            print(f"Positive: {query.positive}")
            print("Recall: ", recall)
            print()
    else:
        print(f"Recall: {recall}")


if __name__ == "__main__":
    main()
