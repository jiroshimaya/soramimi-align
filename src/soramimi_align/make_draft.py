import glob
import json
import os
import re
import traceback
from typing import Hashable

import alkana
import jaconv
import neologdn
import pandas as pd
import sudachipy
from sudachipy import dictionary as sudachi_dictionary
from sudachipy import tokenizer as sudachi_tokenizer

from soramimi_align.schemas import (
    AnalyzedLyrics,
    AnalyzedWordItem,
    AthleteName,
    AthleteParodyLyrics,
    AthleteTableItem,
)


class Tokenizer:
    def __init__(self, *, user_dict: dict[str, str] | None = None):
        self.tokenizer_obj = sudachi_dictionary.Dictionary(dict="full").create()
        self.mode = sudachi_tokenizer.Tokenizer.SplitMode.A
        self.code_regex = re.compile(
            "[!\"#$%&'\\\\()*+,-./:;<=>?@[\\]^_`{|}~「」〔〕"
            "＆＊・（）＄＃＠。、？！｀＋￥％]"
        )
        self.user_dict = self.format_dict(user_dict or {})

    def format_text(self, text: str) -> str:
        # 単語のスペースを一時的に別の文字に変換。neologdnがスペースを削除するため
        tmp_space = "<sssssssss>"
        text = tmp_space.join(text.split())
        text = neologdn.normalize(text)
        text = text.replace(tmp_space, " ")
        text = self.code_regex.sub("", text)
        return text

    def tokenize(self, text: str) -> list[sudachipy.Morpheme]:
        text = self.format_text(text)
        tokens = self.tokenizer_obj.tokenize(text, self.mode)
        tokens = [
            token
            for token in tokens
            if token.part_of_speech()[0] not in ["補助記号", "記号", "空白"]
            or token.surface() in self.user_dict
        ]
        return tokens

    def format_dict(self, _dict: dict[str, str]) -> dict[str, str]:
        formatted_dict = {}
        for k, v in _dict.items():
            formatted_v = self.format_text(v)
            formatted_v = jaconv.hira2kata(formatted_v)
            formatted_dict[k] = formatted_v
        return formatted_dict

    def get_pronuncation_from_token(self, token: sudachipy.Morpheme) -> str:
        if token.surface() in self.user_dict:
            return self.user_dict[token.surface()]

        reading_form = alkana.get_kana(token.surface())
        if not reading_form:
            if token.part_of_speech()[0] == "助詞" and token.surface() == "は":
                reading_form = "ワ"
            elif token.part_of_speech()[0] == "助詞" and token.surface() == "へ":
                reading_form = "エ"
            else:
                reading_form = token.reading_form()
        reading_form = reading_form.replace("ヲ", "オ")
        return reading_form

    def parse(self, text: str) -> list[AnalyzedWordItem]:
        tokens = self.tokenize(text)
        results = []
        for i, token in enumerate(tokens):
            surface = token.surface()
            pronunciation = self.get_pronuncation_from_token(token)
            if i == 0:
                is_phrase_start = True
            else:
                is_phrase_start = self.is_phrase_start(token, tokens[i - 1])

            # surfaceからスペースを無くす
            surface = "_".join(surface.split())
            word_token = AnalyzedWordItem(
                surface=surface,
                pronunciation=pronunciation,
                is_phrase_start=is_phrase_start,
            )
            results.append(word_token)
        return results

    def is_phrase_start(
        self, token: sudachipy.Morpheme, prev_token: sudachipy.Morpheme | None = None
    ) -> bool:
        phrase_start = False
        token_pos = token.part_of_speech()[0]
        if token_pos in [
            "名詞",
            "動詞",
            "形容詞",
            "副詞",
            "接続詞",
            "感動詞",
            "形状詞",
            "連体詞",
            "代名詞",
            "接頭辞",
        ]:
            phrase_start = True
        if prev_token:
            prev_token_pos = prev_token.part_of_speech()[0]
            if prev_token_pos == "接頭辞" and token_pos == "名詞":
                phrase_start = False

        return phrase_start


class AthleteNameDetector:
    def __init__(self, athlete_table_path: str):
        self.athlete_table_items = self._load_athlete_table(athlete_table_path)
        self.surface_to_id_dict = self._create_surface_to_id_dict(
            self.athlete_table_items
        )
        self.id_to_pronunciation_dict = self._create_id_to_pronunciation_dict(
            self.athlete_table_items
        )
        self.tokenizer_obj = sudachi_dictionary.Dictionary(dict="full").create()
        self.mode = sudachi_tokenizer.Tokenizer.SplitMode.A

    def _load_athlete_table(self, athlete_table_path: str) -> list[AthleteTableItem]:
        athlete_table_df = pd.read_csv(athlete_table_path)
        athlete_table_items = []
        for index, row in athlete_table_df.iterrows():
            # pronunciationはカタカナのみにする
            pronunciation = "".join(row["pronunciation"].split()).replace("・", "")
            athlete_table_items.append(
                AthleteTableItem(
                    id=row["id"],
                    original=row["original"],
                    surface=row["surface"],
                    pronunciation=pronunciation,
                )
            )
        return athlete_table_items

    def _create_surface_to_id_dict(
        self, athlete_table_items: list[AthleteTableItem]
    ) -> dict[str, set[int]]:
        surface_to_id_dict = {}
        for athlete_table_item in athlete_table_items:
            if athlete_table_item.original not in surface_to_id_dict:
                surface_to_id_dict[athlete_table_item.original] = set()
            surface_to_id_dict[athlete_table_item.original].add(athlete_table_item.id)

            if athlete_table_item.surface not in surface_to_id_dict:
                surface_to_id_dict[athlete_table_item.surface] = set()
            surface_to_id_dict[athlete_table_item.surface].add(athlete_table_item.id)
        return surface_to_id_dict

    def _create_id_to_pronunciation_dict(
        self, athlete_table_items: list[AthleteTableItem]
    ) -> dict[Hashable, dict[str, set[str]]]:
        id_to_pronunciation_dict = {}
        for athlete_table_item in athlete_table_items:
            if athlete_table_item.id not in id_to_pronunciation_dict:
                id_to_pronunciation_dict[athlete_table_item.id] = {}
            if (
                athlete_table_item.surface
                not in id_to_pronunciation_dict[athlete_table_item.id]
            ):
                id_to_pronunciation_dict[athlete_table_item.id][
                    athlete_table_item.surface
                ] = set()
            id_to_pronunciation_dict[athlete_table_item.id][
                athlete_table_item.surface
            ].add(athlete_table_item.pronunciation)
        return id_to_pronunciation_dict

    def get_ids_from_surface(self, surface: str) -> set[int]:
        # 完全一致で検索
        ids = self.surface_to_id_dict.get(surface, set())
        # 完全一致がなければ部分一致で検索
        if not ids:
            for k, v in self.surface_to_id_dict.items():
                if surface in k:
                    ids.update(v)
        return ids

    def _format_name(self, name: str) -> str:
        name = neologdn.normalize(name)
        if name in self.surface_to_id_dict:
            return name
        name = "".join(name.split())
        if name in self.surface_to_id_dict:
            return name
        # 箇条書きの中黒を削除
        if name.startswith("・"):
            name = name[1:]
        if name in self.surface_to_id_dict:
            return name
        # 「1.」などの番号を削除
        name = re.sub(r"^\d+\.", "", name)
        if name in self.surface_to_id_dict:
            return name
        name = name.split("(")[0]
        if name in self.surface_to_id_dict:
            return name
        return name

    def set_athlete_names(self, names: list[str]) -> None:
        formatted_names = []
        for name in names:
            formatted_names.append(self._format_name(name))
        self.athlete_names = formatted_names

    def get_pronunciation_candidates(self, name: AthleteName) -> tuple[set[str], str]:
        """
        以下の流れで名前の読みの候補を取得する。

        Args:
            name (AthleteName): 名前

        Returns:
            set[str]: _description_
        """
        pronunciation_candidates = set()
        method = "athlete_names_full_surface"
        for athlete_name in self.athlete_names:
            if (
                name.pre_silent_surface in athlete_name
                and name.post_silent_surface in athlete_name
                and name.pronounced_surface in athlete_name
            ):
                ids = self.get_ids_from_surface(athlete_name)
                for id in ids:
                    pronunciation_candidates.update(
                        self.id_to_pronunciation_dict[id].get(
                            name.pronounced_surface, set()
                        )
                    )
                # if "哲" in name.pronounced_surface:
                #    print(name, player_name)
                #    print(id_candidates)

        if (
            not pronunciation_candidates
            and not name.pre_silent_surface
            and not name.post_silent_surface
        ):
            method = "athlete_names_pronounced_surface"
            for athlete_name in self.athlete_names:
                if name.pronounced_surface in athlete_name:
                    ids = self.get_ids_from_surface(athlete_name)
                    for id in ids:
                        pronunciation_candidates.update(
                            self.id_to_pronunciation_dict[id].get(
                                name.pronounced_surface, set()
                            )
                        )
        if not pronunciation_candidates:
            method = "athlete_table"
            ids = self.get_ids_from_surface(name.pronounced_surface)
            for id in ids:
                pronunciation_candidates.update(
                    self.id_to_pronunciation_dict[id].get(
                        name.pronounced_surface, set()
                    )
                )
        if len(pronunciation_candidates) != 1 and name.pronunciation:
            method = "definition"
            pronunciation_candidates = set()
            pronunciation_candidates.add(name.pronunciation)
        if not pronunciation_candidates and re.fullmatch(
            r"[ぁ-んァ-ヶー・]+", name.pronounced_surface
        ):
            method = "allkana"
            pronunciation_candidates.add(jaconv.hira2kata(name.pronounced_surface))
        if not pronunciation_candidates:
            method = "sudachi"
            pronunciation_candidates.add(
                self.get_pronunciation_by_sudachi(name.pronounced_surface)
            )
        if len(pronunciation_candidates) > 1:
            print(method, name, pronunciation_candidates)
        return pronunciation_candidates, method

    def get_pronunciation_by_sudachi(self, text: str) -> str:
        tokens = self.tokenizer_obj.tokenize(text, self.mode)
        prons = ""
        for token in tokens:
            pron = alkana.get_kana(token.surface())
            if not pron:
                pron, surface, pos = (
                    token.reading_form(),
                    token.surface(),
                    token.part_of_speech()[0],
                )
                if pos == "補助記号":  # 記号は発音しないので結果に含めない
                    continue
                if surface == "は" and pos == "助詞":  # 助詞の「は」は「わ」になおす
                    pron = "ワ"
                elif surface == "へ" and pos == "助詞":  # 助詞の「へ」は「え」になおす
                    pron = "エ"
            prons += pron
        prons = prons.replace("ヲ", "オ")
        return prons


def parse_lyrics(
    lyrics: AthleteParodyLyrics,
    athlete_name_detector: AthleteNameDetector,
    tokenizer: Tokenizer,
) -> AnalyzedLyrics:
    athlete_name_detector.set_athlete_names(lyrics.athlete_names)

    analyzed_parody_lines = []
    analyzed_original_lines = []
    for parody_line, original_line in zip(lyrics.parody_lines, lyrics.original_lines):
        analyzed_parody_line = []
        for parody_word in parody_line.split():
            name = AthleteName.from_text(parody_word)
            pronunciation_candidates, method = (
                athlete_name_detector.get_pronunciation_candidates(name)
            )
            pronunciation = ""
            if pronunciation_candidates:
                pronunciation = list(pronunciation_candidates)[0]
            memo = {
                "method": method,
                "pronunciation_candidate_num": len(pronunciation_candidates),
                "pronunciation_candidates": list(pronunciation_candidates),
            }
            # pronunciationはカタカナのみにする
            # pronunciation = "".join(pronunciation.split()).replace("・", "")

            analyzed_parody_line.append(
                AnalyzedWordItem(
                    surface=name.pronounced_surface,
                    pronunciation=pronunciation,
                    memo=memo,
                )
            )
        analyzed_original_line = []
        original_tokens = tokenizer.parse(original_line)
        for original_token in original_tokens:
            analyzed_original_line.append(
                AnalyzedWordItem(
                    surface=original_token.surface,
                    pronunciation=original_token.pronunciation,
                    is_phrase_start=original_token.is_phrase_start,
                )
            )

        analyzed_parody_lines.append(analyzed_parody_line)
        analyzed_original_lines.append(analyzed_original_line)
    return AnalyzedLyrics(
        parody=analyzed_parody_lines, original=analyzed_original_lines
    )


def summarize_parsed_lyrics(parsed_lyrics: AnalyzedLyrics) -> str:
    summary_lines = []
    for analyzed_parody_line, analyzed_original_line in zip(
        parsed_lyrics.parody, parsed_lyrics.original
    ):
        parody_word_surfaces = [word.surface for word in analyzed_parody_line]
        parody_word_pronunciations = []
        for word in analyzed_parody_line:
            pronunciation = word.pronunciation
            if word.memo.get("method") == "sudachi":
                pronunciation += "/sudachi"
                print(f"sudachi: {word}")
            if int(word.memo.get("pronunciation_candidate_num", 0)) > 1:
                pronunciation += f"/{word.memo.get('pronunciation_candidates')}"
                print(
                    f"{word.memo.get('pronunciation_candidate_num')} candidate: {word}"
                )
            parody_word_pronunciations.append(pronunciation)
        original_word_surfaces = [word.surface for word in analyzed_original_line]
        # 空白を含んだ表層があるとpronunciationと要素数が合わなくなるので、表層の空白をハイフンに変換
        original_word_surfaces = [
            word.replace(" ", "_") for word in original_word_surfaces
        ]
        original_word_pronunciations = []
        for word in analyzed_original_line:
            pronunciation = word.pronunciation
            if word.is_phrase_start:
                pronunciation += "/p"
            original_word_pronunciations.append(pronunciation)

        summary_lines.append(" ".join(parody_word_surfaces))
        summary_lines.append(" ".join(parody_word_pronunciations))
        summary_lines.append(" ".join(original_word_surfaces))
        summary_lines.append(" ".join(original_word_pronunciations))
        summary_lines.append("")

    full_text = "\n".join(summary_lines)

    return full_text


def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input_file", type=str)
    parser.add_argument("-o", "--output_file", type=str, default=None)
    parser.add_argument(
        "-w", "--word_dict_path", type=str, default="data/worddict/baseball.csv"
    )
    parser.add_argument("-u", "--user_dict_path", type=str, default=None)
    parser.add_argument("-c", "--check_only", action="store_true")
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="tracebackを出力するかのフラグ"
    )
    parser.add_argument(
        "-pree",
        "--pre_errata_dict_path",
        type=str,
        default=None,
        help="入力replaceで修正するための辞書",
    )
    parser.add_argument(
        "-poste",
        "--post_errata_dict_path",
        type=str,
        default=None,
        help="出力をreplaceで修正するための辞書",
    )
    parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="出力ファイルが既に存在しても上書きするフラグ",
    )
    args = parser.parse_args()

    if not args.output_file:
        if os.path.isfile(args.input_file):
            args.output_file = "output.txt"
        elif os.path.isdir(args.input_file):
            args.output_file = "output"

    athlete_name_detector = AthleteNameDetector(args.word_dict_path)
    user_dict = None
    if args.user_dict_path:
        with open(args.user_dict_path, "r") as f:
            user_dict = json.load(f)
    tokenizer = Tokenizer(user_dict=user_dict)

    if args.pre_errata_dict_path:
        with open(args.pre_errata_dict_path, "r") as f:
            pre_errata_dict = json.load(f)
    else:
        pre_errata_dict = None

    if args.post_errata_dict_path:
        with open(args.post_errata_dict_path, "r") as f:
            post_errata_dict = json.load(f)
    else:
        post_errata_dict = None

    if os.path.isfile(args.input_file):
        with open(args.input_file, "r") as f:
            text = f.read()

        if pre_errata_dict:
            for k, v in pre_errata_dict.items():
                text = text.replace(k, v)
        # print(text)
        lyrics = AthleteParodyLyrics.from_text(text)
        parsed_lyrics = parse_lyrics(lyrics, athlete_name_detector, tokenizer)
        summary = summarize_parsed_lyrics(parsed_lyrics)
        if post_errata_dict:
            for k, v in post_errata_dict.items():
                summary = summary.replace(k, v)
        with open(args.output_file, "w") as f:
            f.write(summary)
    elif os.path.isdir(args.input_file):
        os.makedirs(args.output_file, exist_ok=True)
        txt_files = glob.glob(
            os.path.join(args.input_file, "**", "*.txt"), recursive=True
        )
        txt_files.sort()
        # for file_path in tqdm.tqdm(txt_files):
        for file_path in txt_files:
            output_file_path = os.path.join(
                args.output_file, os.path.basename(file_path)
            )
            print(file_path, end="")
            try:
                with open(file_path, "r") as f:
                    text = f.read()
                if pre_errata_dict:
                    for k, v in pre_errata_dict.items():
                        text = text.replace(k, v)
                lyrics = AthleteParodyLyrics.from_text(text)
                parsed_lyrics = parse_lyrics(lyrics, athlete_name_detector, tokenizer)
                summary = summarize_parsed_lyrics(parsed_lyrics)
                if post_errata_dict:
                    for k, v in post_errata_dict.items():
                        summary = summary.replace(k, v)
                if not args.check_only:
                    if os.path.exists(output_file_path) and not args.force:
                        print(" skip")
                    else:
                        print(" write")
                        with open(output_file_path, "w") as f:
                            f.write(summary)
            except Exception as e:
                print(f"Error:{e}")
                if args.verbose:
                    traceback.print_exc()


if __name__ == "__main__":
    main()
