"""
Dan-Koe-style card renderer for PropReport Instagram posts.
1080x1080, minimalist, alternating dark/light backgrounds, bold statements.
"""
from PIL import Image, ImageDraw, ImageFont
import os

FONT_DIR = os.path.join(os.path.dirname(__file__), "fonts")

W = H = 1080
BG_LIGHT = (247, 246, 242)
TEXT_DARK = (26, 25, 22)
BG_DARK = (23, 22, 20)
TEXT_LIGHT = (247, 246, 242)
MUTED = (122, 121, 116)


def font(name, size):
    return ImageFont.truetype(os.path.join(FONT_DIR, name), size)


def draw_wrapped(draw, text, xy, fnt, fill, max_width, line_spacing=1.25, align="left"):
    """Wrap on explicit newlines first, then word-wrap each paragraph to max_width."""
    paragraphs = text.split("\n")
    all_lines = []
    for para in paragraphs:
        if para == "":
            all_lines.append("")
            continue
        words = para.split()
        cur = ""
        for w in words:
            test = (cur + " " + w).strip()
            bbox = draw.textbbox((0, 0), test, font=fnt)
            if bbox[2] - bbox[0] <= max_width:
                cur = test
            else:
                if cur:
                    all_lines.append(cur)
                cur = w
        if cur:
            all_lines.append(cur)

    ascent, descent = fnt.getmetrics()
    line_h = int((ascent + descent) * line_spacing)
    x, y = xy
    for line in all_lines:
        if line:
            bbox = draw.textbbox((0, 0), line, font=fnt)
            lw = bbox[2] - bbox[0]
            if align == "center":
                draw.text((x - lw / 2, y), line, font=fnt, fill=fill)
            elif align == "right":
                draw.text((x - lw, y), line, font=fnt, fill=fill)
            else:
                draw.text((x, y), line, font=fnt, fill=fill)
        y += line_h
    return y - xy[1]


def measure_wrapped_height(text, fnt, max_width):
    tmp = Image.new("RGB", (10, 10))
    td = ImageDraw.Draw(tmp)
    return draw_wrapped(td, text, (0, 0), fnt, (0, 0, 0), max_width)


def brand_tag(draw, dark_bg=False):
    color = TEXT_LIGHT if dark_bg else TEXT_DARK
    f_small = font("Inter-SemiBold.ttf", 26)
    draw.text((72, H - 100), "PROPREPORT.COM.AU", font=f_small, fill=color)
    f_tiny = font("Inter-Regular.ttf", 24)
    draw.text((72, H - 64), "AI property reports, in minutes", font=f_tiny, fill=MUTED)


def render_statement(headline, filename, tag=None, dark_bg=True):
    bg = BG_DARK if dark_bg else BG_LIGHT
    fg = TEXT_LIGHT if dark_bg else TEXT_DARK
    tag_color = (140, 138, 132) if dark_bg else (120, 118, 113)

    img = Image.new("RGB", (W, H), bg)
    d = ImageDraw.Draw(img)

    word_count = len(headline.split())
    f_size = 76 if word_count <= 12 else 62
    f_head = font("InterDisplay-Bold.ttf", f_size)
    max_w = W - 144

    h = measure_wrapped_height(headline, f_head, max_w)
    start_y = (H - h) / 2 - 40
    draw_wrapped(d, headline, (72, start_y), f_head, fg, max_w, align="left")

    if tag:
        f_tag = font("Inter-SemiBold.ttf", 28)
        d.text((72, start_y - 70), tag.upper(), font=f_tag, fill=tag_color)

    brand_tag(d, dark_bg=dark_bg)
    img.save(filename)


def render_stat(big_number, sub_line, filename, dark_bg=True):
    bg = BG_DARK if dark_bg else BG_LIGHT
    fg = TEXT_LIGHT if dark_bg else TEXT_DARK
    sub_color = (190, 189, 184) if dark_bg else (90, 89, 84)

    img = Image.new("RGB", (W, H), bg)
    d = ImageDraw.Draw(img)

    f_num = font("InterDisplay-Black.ttf", 220)
    bbox = d.textbbox((0, 0), big_number, font=f_num)
    num_h = bbox[3] - bbox[1]

    f_sub = font("Inter-Medium.ttf", 42)
    max_w = W - 144
    sub_h = measure_wrapped_height(sub_line, f_sub, max_w)

    total_h = num_h + 40 + sub_h
    start_y = (H - total_h) / 2 - 40

    d.text((72, start_y), big_number, font=f_num, fill=fg)
    draw_wrapped(d, sub_line, (72, start_y + num_h + 40), f_sub, sub_color, max_w)

    brand_tag(d, dark_bg=dark_bg)
    img.save(filename)


def render_post(post, out_dir):
    filename = os.path.join(out_dir, f"{post['id']}.png")
    if post["style"] == "dark_statement":
        render_statement(post["headline"], filename, tag=post.get("tag"), dark_bg=True)
    elif post["style"] == "light_statement":
        render_statement(post["headline"], filename, tag=post.get("tag"), dark_bg=False)
    elif post["style"] == "stat":
        render_stat(post["big_number"], post["sub_line"], filename, dark_bg=post.get("dark_bg", True))
    else:
        raise ValueError(f"Unknown style: {post['style']}")
    return filename
