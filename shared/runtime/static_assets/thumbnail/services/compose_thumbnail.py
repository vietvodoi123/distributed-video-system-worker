from pathlib import Path

from PIL import (
    Image,
    ImageDraw,
    ImageFont,
    ImageFilter
)

import re


# =========================================
# HELPERS
# =========================================

def load_font(
    font_path: str,
    size: int
):

    return ImageFont.truetype(
        font_path,
        size
    )


def split_title(
    title: str
):

    separators = [

        " - ",

        " – ",

        " — ",

        ":",

        "|"
    ]

    for sep in separators:

        if sep in title:

            parts = title.split(
                sep,
                1
            )

            return (

                parts[0].strip(),

                parts[1].strip()
            )

    # fallback

    words = title.split()

    mid = len(words) // 2

    return (

        " ".join(words[:mid]),

        " ".join(words[mid:])
    )


# =========================================
# STROKE TEXT
# =========================================

def draw_text_with_stroke(

    draw,

    position,

    text,

    font,

    fill,

    stroke_fill="black",

    stroke_width=5,
):

    draw.text(

        position,

        text,

        font=font,

        fill=fill,

        stroke_width=stroke_width,

        stroke_fill=stroke_fill,
    )


# =========================================
# GRADIENT
# =========================================

def apply_bottom_gradient(
    image: Image.Image
):

    width, height = image.size

    gradient = Image.new(
        "L",
        (1, height),
        color=0
    )

    for y in range(height):

        alpha = 0

        if y > height * 0.45:

            progress = (
                (y - height * 0.45)
                /
                (height * 0.55)
            )

            alpha = int(
                progress * 230
            )

        gradient.putpixel(
            (0, y),
            alpha
        )

    alpha_gradient = (
        gradient.resize(
            (width, height)
        )
    )

    black_image = Image.new(
        "RGBA",
        (width, height),
        (0, 0, 0, 255)
    )

    black_image.putalpha(
        alpha_gradient
    )

    image.paste(
        black_image,
        (0, 0),
        black_image
    )


# =========================================
# BADGE
# =========================================

def draw_episode_badge(

    image: Image.Image,

    text: str,

    font_path: str,
):

    draw = ImageDraw.Draw(
        image
    )

    width, height = image.size

    font = load_font(
        font_path,
        int(height * 0.12)
    )

    badge_text = (
        f"TẬP {text}"
    )

    bbox = draw.textbbox(
        (0, 0),
        badge_text,
        font=font
    )

    text_width = (
        bbox[2] - bbox[0]
    )

    text_height = (
        bbox[3] - bbox[1]
    )

    padding_x = 45
    padding_y = 25

    box_width = (
        text_width
        + padding_x * 2
    )

    box_height = (
        text_height
        + padding_y * 2
    )

    x = width - box_width - 40
    y = 40

    overlay = Image.new(
        "RGBA",
        image.size,
        (0, 0, 0, 0)
    )

    overlay_draw = ImageDraw.Draw(
        overlay
    )

    overlay_draw.rounded_rectangle(

        [
            x,
            y,
            x + box_width,
            y + box_height
        ],

        radius=22,

        fill=(0, 0, 0, 170)
    )

    image.alpha_composite(
        overlay
    )

    draw.text(

        (
            x + padding_x,
            y + padding_y - 4
        ),

        badge_text,

        font=font,

        fill=(255, 215, 0),

        stroke_width=5,

        stroke_fill="black",
    )

import textwrap


def fit_title(
    draw: ImageDraw.ImageDraw,
    title: str,
    font_path: str,
    start_size: int,
    max_width: int,
    max_height: int,
):
    size = start_size

    while size >= 20:

        main_font = load_font(font_path, size)
        sub_font = load_font(font_path, int(size * 0.82))

        words = title.split()

        best_main = title
        best_sub = ""

        # tìm cách chia đẹp nhất thành đúng 2 dòng
        if len(words) > 1:

            best_score = 1e9

            for i in range(1, len(words)):
                line1 = " ".join(words[:i])
                line2 = " ".join(words[i:])

                w1 = draw.textbbox((0, 0), line1, font=main_font)[2]
                w2 = draw.textbbox((0, 0), line2, font=sub_font)[2]

                score = abs(w1 - w2)

                if score < best_score:
                    best_score = score
                    best_main = line1
                    best_sub = line2

        main_bbox = draw.textbbox((0, 0), best_main, font=main_font)
        sub_bbox = draw.textbbox((0, 0), best_sub, font=sub_font)

        main_width = main_bbox[2] - main_bbox[0]
        sub_width = sub_bbox[2] - sub_bbox[0]

        main_height = main_bbox[3] - main_bbox[1]
        sub_height = sub_bbox[3] - sub_bbox[1]

        spacing = int(main_height * 0.35)

        total_height = main_height + sub_height + spacing

        if (
            main_width <= max_width
            and sub_width <= max_width
            and total_height <= max_height
        ):
            return (
                best_main,
                best_sub,
                main_font,
                sub_font,
                main_height,
                sub_height,
                spacing,
                total_height,
            )

        size -= 2

    raise RuntimeError("Cannot fit title")
# =========================================
# MAIN
# =========================================

def compose_thumbnail(

    input_path: Path,

    output_path: Path,

    title: str,

    thumbnail_hook: str,

    episode_text: str,

    font_path: str,
):

    image = (
        Image
        .open(input_path)
        .convert("RGBA")
    )

    width, height = image.size

    apply_bottom_gradient(
        image
    )

    draw = ImageDraw.Draw(
        image
    )

    # =====================================
    # SPLIT TITLE
    # =====================================

    max_text_width = int(width * 0.88)  # chừa lề trái/phải
    max_total_height = int(height * 0.36)  # khoảng 36% ảnh

    main_size = int(height * 0.12)

    (
        main_title,
        sub_title,
        main_font,
        sub_font,
        main_height,
        sub_height,
        spacing,
        total_height,
    ) = fit_title(
        draw=draw,
        title=title,
        font_path=font_path,
        start_size=main_size,
        max_width=max_text_width,
        max_height=max_total_height,
    )

    # =====================================
    # POSITION
    # =====================================

    x = int(width * 0.05)

    y = int(
        height
        - total_height
        - height * 0.045
    )

    # =====================================
    # MAIN TITLE
    # =====================================

    draw_text_with_stroke(

        draw=draw,

        position=(x, y),

        text=main_title,

        font=main_font,

        fill=(255, 255, 255),

        stroke_width=7,
    )

    # =====================================
    # SUB TITLE
    # =====================================

    sub_y = (
        y
        + main_height
        + spacing
    )

    draw_text_with_stroke(

        draw=draw,

        position=(x, sub_y),

        text=sub_title,

        font=sub_font,

        fill=(255, 215, 0),

        stroke_width=5,
    )

    # =====================================
    # BADGE
    # =====================================

    draw_episode_badge(

        image=image,

        text=episode_text,

        font_path=font_path,
    )

    # =====================================
    # EXPORT
    # =====================================

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    image.convert("RGB").save(

        output_path,

        quality=95
    )

    return output_path