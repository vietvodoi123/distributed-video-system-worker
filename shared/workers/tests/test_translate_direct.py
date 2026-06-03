import asyncio

from shared.runtime.executors.refine.services.ollama_translate_service import (
    OllamaTranslateService
)


async def main():

    service = (
        OllamaTranslateService(model="gemma3:12b")
    )

    text = """
“Hô hô hô......”
Thiên Sơn Tuyết Hậu gió biển lạnh, sáo lệch thổi đi đường khó.
Gió tuyết đầy trời bay múa, một bóng người tại trong cuồng phong bạo tuyết gian nan tiến lên.
Trương Tố Huyền.
Trẻ tuổi nhất Đạo Giáo Thiên Sư, được vinh dự “Đạo Tổ chuyển thế”, hiện đại Đạo Giáo bên trong duy nhất được trao tặng “Thiên Tôn” danh hiệu Thiên Sư.
Trương Tố Huyền trời sinh gần “Đạo”, tại năm gần 10 tuổi liền đọc xong Đạo Giáo tất cả điển tàng, khẩu chiến quần hùng, biện tất cả trưởng bối á khẩu không trả lời được.
15 tuổi liền được phá cách thụ lục « Thượng Thanh lỗ lớn trải qua lục », thuộc Thiên Sư hàm.
Sau, một đường cầu đạo, muốn hỏi Tiên Lộ.
Một cỗ xe đạp chia sẻ, du lịch cả nước danh sơn đại xuyên.
Phí thời gian mười năm, không thu hoạch được gì.
"""

    result = await service.translate(
        text
    )

    print(result)

    await service.unload_model()


if __name__ == "__main__":

    asyncio.run(main())