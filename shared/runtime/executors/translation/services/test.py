import asyncio
from pprint import pprint

from deepseek_translate_service import DeepSeekTranslateService


async def main():
    translator = DeepSeekTranslateService(
        api_key="sk-1541545e3b8e4170ab347f31909df26d",   # hoặc bỏ nếu dùng biến môi trường
    )

    text = """
你好
我是中国人
今天天气很好。
"""

    response = await translator._client.chat.completions.create(
        model=translator._model,
        temperature=0.3,
        max_tokens=8192,
        messages=[
            {
                "role": "system",
                "content": "Bạn là một dịch giả chuyên dịch tiếng Trung sang tiếng Việt. Chỉ trả về bản dịch tiếng Việt."
            },
            {
                "role": "user",
                "content": text
            }
        ]
    )

    print("=" * 80)
    print("MODEL:")
    print(response.model)

    print("=" * 80)
    print("FULL RESPONSE:")
    pprint(response.model_dump())

    print("=" * 80)
    print("CONTENT:")
    print(response.choices[0].message.content)


if __name__ == "__main__":
    asyncio.run(main())