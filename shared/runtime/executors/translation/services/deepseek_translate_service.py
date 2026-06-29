import os

from openai import AsyncOpenAI
import re
def contains_chinese(text: str) -> bool:
    return bool(re.search(r'[\u4e00-\u9fff\u3400-\u4dbf]', text))

class DeepSeekTranslateService:

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "deepseek-v4-flash",
    ):
        self._client = AsyncOpenAI(
            api_key=api_key or os.environ["DEEPSEEK_API_KEY"],
            base_url="https://api.deepseek.com",
            timeout=120,
        )

        self._model = model

    async def translate(self, text: str) -> str:
        """Phiên bản tối giản - ép DeepSeek phải dịch"""

        # QUAN TRỌNG: Gửi text dưới dạng 1 message DUY NHẤT
        response = await self._client.chat.completions.create(
            model="deepseek-v4-flash",  # Thử "deepseek-chat" nếu vẫn lỗi
            messages=[
                {
                    "role": "system",
                    "content": "You are a translation engine. ONLY output Vietnamese text."
                },
                {
                    "role": "user",
                    "content": f"Translate to Vietnamese:\n{text}"
                }
            ],
            max_tokens=4096,
            temperature=0,
            top_p=0.1,  # Giảm randomness
            frequency_penalty=0,
            presence_penalty=0,
            # THÊM DÒNG NÀY:
            stop=["\n```", "【"],  # Dừng khi gặp định dạng linh tinh
        )

        result = response.choices[0].message.content

        # Nếu vẫn còn chữ Hán, ép buộc bằng regex
        import re
        if re.search(r'[\u4e00-\u9fff]', result):
            # Gọi lại với instruction mạnh hơn
            response = await self._client.chat.completions.create(
                model="deepseek-v4-flash",
                messages=[
                    {"role": "user", "content": f"CHỈ DỊCH, KHÔNG GIỮ CHỮ HÁN. Dịch:\n{text}"}
                ],
                temperature=0,
                top_p=0.1,  # Giảm randomness
                frequency_penalty=0,
                presence_penalty=0,
                max_tokens=4096,
            )
            result = response.choices[0].message.content

        return result