import re
from dataclasses import dataclass, field
from typing import Any, Hashable

import jaconv
import neologdn


@dataclass
class AthleteTableItem:
    id: Hashable
    original: str
    surface: str
    pronunciation: str


@dataclass
class AthleteParodyLyrics:
    raw: str
    parody_lines: list[str] = field(default_factory=list)
    original_lines: list[str] = field(default_factory=list)
    athlete_names: list[str] = field(default_factory=list)

    def __post_init__(self):
        if len(self.parody_lines) != len(self.original_lines):
            raise ValueError("パロディ歌詞と元の歌詞の行数が一致しません")

    @classmethod
    def from_text(cls, text: str) -> "AthleteParodyLyrics":
        # テキストを行ごとに分割
        lines = text.splitlines()
        # 空行を削除
        lines = [line.strip() for line in lines if line.strip()]
        # 記号だけの行を削除
        lines = [line for line in lines if not re.match(r"^[\W_]+$", line)]

        # 選手一覧を探す
        try:
            separator_index = next(
                i
                for i, line in enumerate(lines)
                if "選手一覧" in line or "起用選手" in line or "使用選手" in line
            )
        except StopIteration:
            raise ValueError("選手一覧が見つかりません")

        # 選手一覧より上をパロディと元の歌詞部分に分割
        lyrics_part = lines[:separator_index]
        athlete_names_part = lines[separator_index + 1 :]
        # lyrics_partの始まりを探す
        lyrics_start_index = -1
        athlete_names_str = "\n".join(athlete_names_part)
        for i, line in enumerate(lyrics_part):
            words = line.split()
            try:
                for word in words:
                    name = AthleteName.from_text(word)
                    if name.pronounced_surface in athlete_names_str:
                        lyrics_start_index = i
                        break
                else:
                    continue
                break
            except Exception:
                continue
        if lyrics_start_index == -1:
            raise ValueError("lyrics_partの始まりが見つかりません")

        # パロディ歌詞と元の歌詞を抽出
        lyrics_part = lyrics_part[lyrics_start_index:]

        parody_lines = []
        original_lines = []
        for i, line in enumerate(lyrics_part):
            if i % 2 == 0:
                parody_lines.append(line)
            else:
                original_lines.append(line)
        if len(parody_lines) != len(original_lines):
            raise ValueError("パロディ歌詞と元の歌詞の行数が一致しません")

        # パロディ用の単語を抽出
        athlete_names = athlete_names_part

        return cls(
            raw=text,
            parody_lines=parody_lines,
            original_lines=original_lines,
            athlete_names=athlete_names,
        )


@dataclass
class AthleteName:
    raw: str
    pre_silent_surface: str = ""
    pronounced_surface: str = ""
    post_silent_surface: str = ""
    pronunciation: str = ""

    @classmethod
    def from_text(cls, text: str) -> "AthleteName":
        normalized_raw = neologdn.normalize(text)
        pre_silent_surface, pronounced_surface, post_silent_surface, pronunciation = (
            cls._parse_name_text(normalized_raw)
        )
        return cls(
            raw=text,
            pre_silent_surface=pre_silent_surface,
            pronounced_surface=pronounced_surface,
            post_silent_surface=post_silent_surface,
            pronunciation=pronunciation,
        )

    @staticmethod
    def _parse_name_text(input_str) -> tuple[str, str, str, str]:
        """
        `(pre_silent_surface)pronounced_surface(post_silent_surface)(pronounciation)`
        という形式のtextをparseする。

        args:
            input_str (str): 入力テキスト

        returns:
            tuple[str, str, str, str]: pre_silent_surface, pronounced_surface, post_silent_surface, pronunciation
        """
        # 入力全体が最初または最後だけにカッコをもつ場合、カッコを削除
        if (
            input_str.startswith("(")
            and input_str.endswith(")")
            and input_str[1:-1].count("(") == input_str[1:-1].count(")") == 0
        ):
            input_str = input_str[1:-1]
        elif input_str.startswith("(") and ")" not in input_str:
            input_str = input_str[1:]
        elif input_str.endswith(")") and "(" not in input_str:
            input_str = input_str[:-1]

        # 正規表現パターンを定義
        pattern = r"(\(.*?\))?([^\(\)]+)(\([^\(\)]+\)){0,2}"

        match = re.fullmatch(pattern, input_str)
        if not match:
            raise ValueError(f"入力形式が正しくありません: {input_str}")

        # 各部分を取得
        pre = match.group(1)  # pre部分（0または1個）
        pronounced_surface = match.group(2)  # pronounced_surface部分（1個）
        post = re.findall(
            r"\([^\(\)]+\)", input_str[len(pre or "") + len(pronounced_surface) :]
        )  # post部分（0,1,2個）

        # preの括弧を除去して返す。空の場合は '' を返す
        pre_silent_surface = pre[1:-1] if pre else ""

        # postの処理
        post_silent_surface = ""
        pronunciation = ""
        if len(post) == 1:
            # 1つの場合
            post_content = post[0][1:-1]  # カッコを除去
            if re.fullmatch(
                r"[ぁ-んァ-ヶー・]+", post_content
            ):  # 全てがひらがなまたはカタカナ
                # pronounced_surfaceが外国人名らしき場合は、post_contentがpost_silent_surfaceである可能性を検討する
                # pronounced_surfaceがカナで、かつ、post_contentと異なる場合は、post_contentはpost_silent_surfaceであるとみなす
                if (
                    re.fullmatch(r"[ぁ-んァ-ヶー・]+", pronounced_surface)
                    and pronounced_surface != post_content
                ):
                    post_silent_surface = post_content
                else:
                    pronunciation = jaconv.hira2kata(post_content)
            else:
                post_silent_surface = post_content
        elif len(post) == 2:
            # 2つの場合
            post_silent_surface = post[0][
                1:-1
            ]  # 1つ目をpost_not_pronounced_surfaceとして扱う
            pronunciation = post[1][1:-1]  # 2つ目をpronunciationとして扱う

        return (
            pre_silent_surface,
            pronounced_surface,
            post_silent_surface,
            pronunciation,
        )


@dataclass
class AnalyzedWordItem:
    surface: str
    pronunciation: str
    is_phrase_start: bool = False
    memo: dict[str, Any] = field(default_factory=dict)


@dataclass
class AnalyzedLyrics:
    parody: list[list[AnalyzedWordItem]]
    original: list[list[AnalyzedWordItem]]

    def __post_init__(self):
        if len(self.parody) != len(self.original):
            raise ValueError("parodyとoriginalの行数が一致しません")

    @classmethod
    def from_text(cls, text: str) -> "AnalyzedLyrics":
        lines = text.splitlines()
        # 空行を削除
        lines = [line.strip() for line in lines if line.strip()]

        assert len(lines) % 4 == 0

        parody_surface_lines = lines[::4]
        parody_pronunciation_lines = lines[1::4]
        original_surface_lines = lines[2::4]
        original_pronunciation_lines = lines[3::4]

        analyzed_parody_words = [
            cls._parse_parody_line(surface_line, pronunciation_line)
            for surface_line, pronunciation_line in zip(
                parody_surface_lines, parody_pronunciation_lines
            )
        ]
        analyzed_original_words = [
            cls._parse_original_line(surface_line, pronunciation_line)
            for surface_line, pronunciation_line in zip(
                original_surface_lines, original_pronunciation_lines
            )
        ]
        return cls(parody=analyzed_parody_words, original=analyzed_original_words)

    @classmethod
    def _parse_parody_line(
        cls, surface_line: str, pronunciation_line: str
    ) -> list[AnalyzedWordItem]:
        surfaces = surface_line.split()
        pronunciations = pronunciation_line.split()

        assert len(surfaces) == len(pronunciations)

        analyzed_words = []
        for surface, pronunciation in zip(surfaces, pronunciations):
            analyzed_word = AnalyzedWordItem(
                surface=surface, pronunciation=pronunciation
            )
            analyzed_words.append(analyzed_word)

        return analyzed_words

    @classmethod
    def _parse_original_line(
        cls, surface_line: str, pronunciation_line: str
    ) -> list[AnalyzedWordItem]:
        surfaces = surface_line.split()
        pronunciations = pronunciation_line.split()

        assert len(surfaces) == len(pronunciations)

        analyzed_words = []
        for surface, pronunciation in zip(surfaces, pronunciations):
            pronunciation_tokens = pronunciation.split("/")
            if len(pronunciation_tokens) > 1 and pronunciation_tokens[1] == "p":
                is_phrase_start = True
            else:
                is_phrase_start = False

            analyzed_word = AnalyzedWordItem(
                surface=surface,
                pronunciation=pronunciation_tokens[0],
                is_phrase_start=is_phrase_start,
            )
            analyzed_words.append(analyzed_word)
        return analyzed_words


@dataclass
class AlignedMora:
    parody_mora: str
    is_parody_word_start: bool
    is_parody_word_end: bool
    original_mora: str
    is_original_phrase_start: bool
    is_original_phrase_end: bool
    line_id: str = ""
    input_file_path: str = ""
    parody_vowel: str = ""
    original_vowel: str = ""
    parody_consonant: str = ""
    original_consonant: str = ""
