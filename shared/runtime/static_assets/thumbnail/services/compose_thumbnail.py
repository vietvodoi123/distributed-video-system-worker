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
        int(height * 0.07)
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

    padding_x = 35
    padding_y = 18

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

        stroke_width=3,

        stroke_fill="black",
    )


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

    main_title, sub_title = (
        split_title(title)
    )

    # =====================================
    # FONT SIZES
    # =====================================

    main_size = int(
        height * 0.12
    )

    sub_size = int(
        main_size * 0.82
    )

    spacing = int(
        height * 0.018
    )

    # =====================================
    # FIT HEIGHT
    # =====================================

    max_total_height = (
            height / 2
    )

    while True:

        main_font = load_font(
            font_path,
            main_size
        )

        sub_font = load_font(
            font_path,
            sub_size
        )

        main_bbox = (
            draw.textbbox(

                (0, 0),

                main_title,

                font=main_font
            )
        )

        sub_bbox = (
            draw.textbbox(

                (0, 0),

                sub_title,

                font=sub_font
            )
        )

        main_height = (
            main_bbox[3]
            - main_bbox[1]
        )

        sub_height = (
            sub_bbox[3]
            - sub_bbox[1]
        )

        total_height = (
            main_height
            + sub_height
            + spacing
        )

        if total_height <= max_total_height:
            break

        main_size -= 2
        sub_size -= 2

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