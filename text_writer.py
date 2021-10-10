from PIL import Image, ImageDraw, ImageFont, ImageFilter
import textwrap


def add_text(image_path, title, subtitle=""):
    background_layer = Image.open(image_path).convert("RGBA")
    shadow_layer = Image.new("RGBA", background_layer.size)
    text_layer = Image.new("RGBA", background_layer.size)

    shadow_draw = ImageDraw.Draw(shadow_layer)
    text_draw = ImageDraw.Draw(text_layer)

    header = ImageFont.truetype("resources/roboto/Roboto-Light.ttf", size=90)
    subheader = ImageFont.truetype("resources/roboto/Roboto-Regular.ttf", size=50)

    w, h = background_layer.size
    margin_left = 80
    margin_bottom = 80
    margin_right = w / 6
    margin_between = 80

    header_w, header_h = text_draw.textsize(title, header)
    subheader_w, subheader_h = text_draw.textsize(subtitle, subheader)
    chars = max(len(title), len(subtitle))

    while chars > 0 and (w - margin_right < header_w or w - margin_right < subheader_w):
        title = textwrap.fill(title, chars)
        subtitle = textwrap.fill(subtitle, chars)
        header_w, header_h = shadow_draw.textsize(title, header)
        subheader_w, subheader_h = shadow_draw.textsize(subtitle, subheader)
        chars = int(chars / 1.8)

    x = margin_left
    y1 = h - margin_bottom - subheader_h - margin_between - header_h
    y2 = h - margin_bottom - subheader_h

    shadow_fill = (0, 0, 0, 220)
    text_fill = (255, 255, 255)

    for x_off in range(-5, 5):
        for y_off in range(-5, 5):
            shadow_draw.text(
                (x + x_off, y1 + y_off), title, font=header, fill=shadow_fill
            )
            shadow_draw.text(
                (x + x_off, y2 + y_off), subtitle, font=subheader, fill=shadow_fill
            )
    shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(10))

    text_draw.text((x, y1), title, font=header, fill=text_fill)
    text_draw.text((x, y2), subtitle, font=subheader, fill=text_fill)

    composite = Image.alpha_composite(background_layer, shadow_layer)
    composite = Image.alpha_composite(composite, text_layer)

    try:
        composite.save(image_path)
    except OSError:
        composite.convert("RGB").save(image_path)
