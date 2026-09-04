"""
generate_carousel.py — generates a branded 5-slide carousel (LinkedIn/Instagram) as PNGs.

Posting carousels via API is more fragile than single images (Instagram's carousel
endpoint needs multiple pre-uploaded media containers, LinkedIn's requires a different
flow entirely) — this script generates the finished slide images and saves them to
carousel_drafts/, for manual upload. That 2-minute manual upload is a reasonable
trade-off versus a much more brittle auto-post integration for a format used ~weekly.

Run weekly via .github/workflows/weekly-growth.yml
"""
import os
import sys
import datetime
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from common import generate_text_json, pick_alternating

FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_REG = "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
FONT_BOLD_LIB = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"

C_DARK = (12, 14, 28)
C_MID = (35, 22, 74)
C_VIOLET = (88, 42, 168)
C_TEAL = (45, 212, 191)
C_WHITE = (255, 255, 255)
C_MUTED = (188, 182, 214)

W, H = 1080, 1350  # LinkedIn/IG carousel portrait ratio
OUT_DIR = "carousel_drafts"

BUYER_TOPICS = [
    "How to evaluate an AI provider before you hire one",
    "5 signs your business is ready for AI automation",
]
PROVIDER_TOPICS = [
    "How to build an AI case study that wins clients",
    "5 things every high-converting provider profile needs",
]


def vertical_gradient(w, h, top, bottom):
    base = Image.new("RGB", (w, h), top)
    draw = ImageDraw.Draw(base)
    for y in range(h):
        t = y / h
        r = int(top[0] + (bottom[0] - top[0]) * t)
        g = int(top[1] + (bottom[1] - top[1]) * t)
        b = int(top[2] + (bottom[2] - top[2]) * t)
        draw.line([(0, y), (w, y)], fill=(r, g, b))
    return base


def add_glow(img, cx, cy, r, color, alpha=100):
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color + (alpha,))
    overlay = overlay.filter(ImageFilter.GaussianBlur(120))
    img.paste(Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB"), (0, 0))
    return img


def wrap_text(draw, text, font, max_width):
    words = text.split()
    lines, cur = [], ""
    for w in words:
        test = (cur + " " + w).strip()
        if draw.textlength(test, font=font) <= max_width:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def make_slide(index, total, headline, subtext, is_cover=False):
    img = vertical_gradient(W, H, C_DARK, C_MID)
    img = add_glow(img, W - 150, 150, 380, C_VIOLET, 110)
    img = add_glow(img, 100, H - 150, 320, C_TEAL, 70)
    draw = ImageDraw.Draw(img)

    logo_font = ImageFont.truetype(FONT_BOLD, 36)
    draw.text((60, 50), "BIZLANCE", font=logo_font, fill=C_WHITE)
    draw.text((60, 50), "BIZ", font=logo_font, fill=C_TEAL)

    if not is_cover:
        page_font = ImageFont.truetype(FONT_BOLD_LIB, 28)
        page_text = f"{index}/{total}"
        pw = draw.textlength(page_text, font=page_font)
        draw.text((W - 60 - pw, 55), page_text, font=page_font, fill=C_MUTED)

    headline_font = ImageFont.truetype(FONT_BOLD, 64 if is_cover else 54)
    lines = wrap_text(draw, headline, headline_font, W - 140)
    line_h = (64 if is_cover else 54) + 14
    total_h = line_h * len(lines)
    y = (H - total_h) // 2 - (40 if subtext else 0)
    for line in lines:
        draw.text((70, y), line, font=headline_font, fill=C_WHITE)
        y += line_h

    if subtext:
        sub_font = ImageFont.truetype(FONT_REG, 32)
        y += 20
        for line in wrap_text(draw, subtext, sub_font, W - 160):
            draw.text((70, y), line, font=sub_font, fill=C_MUTED)
            y += 44

    if is_cover:
        badge_font = ImageFont.truetype(FONT_BOLD_LIB, 26)
        badge_text = "SWIPE →"
        bw = draw.textlength(badge_text, font=badge_font) + 50
        draw.rounded_rectangle([70, H - 140, 70 + bw, H - 90], radius=25, fill=C_TEAL)
        draw.text((95, H - 128), badge_text, font=badge_font, fill=C_DARK)

    return img


def main():
    segment, topic = pick_alternating(BUYER_TOPICS, PROVIDER_TOPICS)
    print(f"Segment: {segment} | Topic: {topic}")

    prompt = (
        f"Create a 5-slide LinkedIn/Instagram carousel outline for Bizlance about: {topic}. "
        "Slide 1 is a punchy cover/hook (under 8 words). Slides 2-4 are each one clear point "
        "(under 12 words headline + one short supporting sentence under 15 words). "
        "Slide 5 is a call-to-action pointing toward Bizlance (under 10 words headline + "
        "one supporting sentence). "
        'Return ONLY valid JSON: {"slides": [{"headline": "...", "subtext": "..."}, ...]} '
        "with exactly 5 items, slide 1's subtext can be empty string. No commentary, no code fences."
    )
    parsed = generate_text_json(prompt)
    slides = parsed.get("slides", [])
    if len(slides) != 5:
        print("Model didn't return 5 clean slides, aborting.", file=sys.stderr)
        sys.exit(1)

    date_str = datetime.date.today().isoformat()
    out_path = os.path.join(OUT_DIR, date_str)
    os.makedirs(out_path, exist_ok=True)

    for i, slide in enumerate(slides, start=1):
        img = make_slide(i, 5, slide["headline"], slide.get("subtext", ""), is_cover=(i == 1))
        fname = os.path.join(out_path, f"slide{i}.png")
        img.save(fname)
        print(f"Saved {fname}")

    print(f"Carousel ready in {out_path}/ — upload manually to LinkedIn/Instagram.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"FAILED: {e}", file=sys.stderr)
        sys.exit(1)
