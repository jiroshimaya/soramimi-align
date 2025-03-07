from pydantic import BaseModel

from soramimi_align.evaluate_phonetic_search_dataset import (
    get_default_output_path,
    get_structured_outputs,
)


def test_get_structured_outputs():
    # テストデータの準備
    class Person(BaseModel):
        name: str
        age: int

    model_name = "gpt-4o-mini"
    messages = [
        [{"role": "user", "content": "Taro is 20 years old"}],
        [{"role": "user", "content": "Jiro's age is 10"}],
    ]

    responses = get_structured_outputs(
        model_name=model_name,
        messages=messages,
        response_format=Person,
        temperature=0.0,
        max_tokens=1000,
    )

    # 結果の検証
    assert responses[0] == Person(name="Taro", age=20)
    assert responses[1] == Person(name="Jiro", age=10)


def test_get_default_output_path():
    # 基本的なケース（rerankなし）
    assert (
        get_default_output_path(
            input_path="data/test.json",
            rank_func="vowel_consonant",
            topn=10,
            rerank=False,
        )
        == "data/test_vowel_consonant_top10.json"
    )

    # rerankありのケース
    assert (
        get_default_output_path(
            input_path="data/test.json",
            rank_func="vowel_consonant",
            topn=10,
            rerank=True,
            rerank_topn=50,
            rerank_model_name="gpt-4",
        )
        == "data/test_vowel_consonant_top10_reranked_top50_modelgpt-4.json"
    )
