from pydantic import BaseModel

from soramimi_align.evaluate_phonetic_search_dataset import get_structured_outputs


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
