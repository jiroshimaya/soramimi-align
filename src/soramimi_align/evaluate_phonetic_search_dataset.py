import argparse
import json
from typing import Callable

import editdistance as ed
import jamorasep
import pyopenjtalk
from kanasim import create_kana_distance_calculator

from soramimi_align.schemas import PhoneticSearchDataset


def load_phonetic_search_dataset(path: str) -> PhoneticSearchDataset:
    with open(path, "r") as f:
        dataset = json.load(f)
    return PhoneticSearchDataset.from_dict(dataset)


def rank_by_mora_editdistance(
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


def rank_by_vowel_consonant_editdistance(
    query_texts: list[str], wordlist_texts: list[str]
) -> list[list[str]]:
    query_moras = [
        jamorasep.parse(text, output_format="simple-ipa") for text in query_texts
    ]
    query_vowels = [[m[-1] for m in mora] for mora in query_moras]
    query_consonants = [
        [m[:-1] if m[:-1] else "sp" for m in mora] for mora in query_moras
    ]
    wordlist_moras = [
        jamorasep.parse(text, output_format="simple-ipa") for text in wordlist_texts
    ]
    wordlist_vowels = [[m[-1] for m in mora] for mora in wordlist_moras]
    wordlist_consonants = [
        [m[:-1] if m[:-1] else "sp" for m in mora] for mora in wordlist_moras
    ]

    filnal_results = []
    for query_vowel, query_consonant in zip(query_vowels, query_consonants):
        scores = []
        for wordlist_vowel, wordlist_consonant in zip(
            wordlist_vowels, wordlist_consonants
        ):
            vowel_distance = ed.eval(query_vowel, wordlist_vowel)
            consonant_distance = ed.eval(query_consonant, wordlist_consonant)
            distance = vowel_distance * 10 + consonant_distance
            scores.append(distance)

        ranked_wordlist = [
            word for word, _ in sorted(zip(wordlist_texts, scores), key=lambda x: x[1])
        ]
        filnal_results.append(ranked_wordlist)
    return filnal_results


def rank_by_phoneme_editdistance(
    query_texts: list[str], wordlist_texts: list[str]
) -> list[list[str]]:
    query_phonemes = [pyopenjtalk.g2p(text).split() for text in query_texts]
    wordlist_phonemes = [pyopenjtalk.g2p(text).split() for text in wordlist_texts]

    filnal_results = []
    for query_phoneme in query_phonemes:
        scores = []
        for wordlist_phoneme in wordlist_phonemes:
            distance = ed.eval(query_phoneme, wordlist_phoneme)
            scores.append(distance)

        ranked_wordlist = [
            word for word, _ in sorted(zip(wordlist_texts, scores), key=lambda x: x[1])
        ]
        filnal_results.append(ranked_wordlist)
    return filnal_results


def rank_by_kanasim(
    query_texts: list[str], wordlist_texts: list[str]
) -> list[list[str]]:
    kana_distance_calculator = create_kana_distance_calculator()

    all_scores = kana_distance_calculator.calculate_batch(query_texts, wordlist_texts)

    ranked_wordlists = []
    for query_text, scores in zip(query_texts, all_scores):
        ranked_wordlist = [
            word for word, _ in sorted(zip(wordlist_texts, scores), key=lambda x: x[1])
        ]
        ranked_wordlists.append(ranked_wordlist)

    return ranked_wordlists


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
    topn_wordlists = rank_dataset(dataset, rank_by_kanasim)
    # topn_wordlists = rank_dataset(dataset, rank_by_vowel_consonant_editdistance)
    # topn_wordlists = rank_dataset(dataset, rank_by_phoneme_editdistance)

    positive_texts = [query.positive for query in dataset.queries]
    recall = calculate_recall(topn_wordlists, positive_texts)
    if args.verbose:
        for query, topn_wordlist in zip(dataset.queries, topn_wordlists):
            print(f"Query: {query.query}")
            print(f"Top {len(topn_wordlist)}: {topn_wordlist}")
            print(f"Positive: {query.positive}")
            print()

    print("Recall: ", recall)


if __name__ == "__main__":
    main()
