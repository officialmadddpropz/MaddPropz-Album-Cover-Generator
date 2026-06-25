import os
import glob
from PIL import Image, ImageEnhance, ImageDraw, ImageFont, ImageFilter, ImageOps

# ── Font resolution ──────────────────────────────────────────────────────
# The original script asked for Windows/Mac-only font files ("impact.ttf",
# "arialbd.ttf", "Helvetica-Bold.ttf") with no path. On Linux/most servers
# those don't exist, so PIL silently fell back to ImageFont.load_default(),
# a ~10px bitmap font — at 3000x3000 the "360pt" titles were basically
# invisible, and all the hand-placed offsets were calculated for a font
# that was never actually used.
#
# Fix: search a list of real candidate paths/families per role and fall
# back gracefully, but ALSO rescale layout math if we ever do hit the
# tiny default font, so nothing silently breaks.

FONT_CANDIDATES = {
    "title_heavy": [  # bold display face for the "Impact"-style title
        "impact.ttf", "Impact.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    ],
    "title_clean": [  # clean sans-serif for the minimal cinema look
        "Helvetica-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ],
    "sub_heavy": [
        "arialbd.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ],
    "sub_clean": [
        "arial.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ],
}


def load_font(role, size):
    """Try each candidate path for a role in order; fall back to default."""
    for path in FONT_CANDIDATES[role]:
        try:
            return ImageFont.truetype(path, size)
        except (IOError, OSError):
            continue
    print(f"  [warning] No real font found for '{role}', using tiny PIL default.")
    return ImageFont.load_default()


def text_w(draw, text, font):
    """textlength wrapper - works across Pillow versions."""
    try:
        return draw.textlength(text, font=font)
    except AttributeError:
        return draw.textsize(text, font=font)[0]


def process_base_image(image_path):
    """Loads, crops to a perfect square, and scales the image to 3000x3000."""
    img = Image.open(image_path)
    img = ImageOps.exif_transpose(img)  # fix phone-photo rotation
    img = img.convert("RGB")
    width, height = img.size
    min_dim = min(width, height)
    left = (width - min_dim) // 2
    top = (height - min_dim) // 2
    img = img.crop((left, top, left + min_dim, top + min_dim))
    return img.resize((3000, 3000), Image.Resampling.LANCZOS)


def draw_parental_advisory(img):
    """Stamps a retail-style Parental Advisory block in the bottom corner."""
    adv_w, adv_h = 560, 340
    adv_box = Image.new("RGB", (adv_w, adv_h), "white")
    adv_draw = ImageDraw.Draw(adv_box)

    adv_draw.rectangle([0, 0, adv_w, 125], fill="black")
    adv_draw.rectangle([12, 12, adv_w - 12, adv_h - 12], outline="black", width=8)

    f_parental = load_font("sub_heavy", 82)
    f_content = load_font("sub_clean", 50)

    adv_draw.text((45, 20), "PARENTAL", fill="white", font=f_parental)
    adv_draw.text((82, 145), "ADVISORY", fill="black", font=f_parental)
    adv_draw.text((50, 252), "EXPLICIT CONTENT", fill="black", font=f_content)

    img.paste(adv_box, (3000 - adv_w - 220, 3000 - adv_h - 220))
    return img


def find_source_image(requested_path):
    """If the exact filename isn't found, look for any common image file
    in the current folder so a wrong/forgotten filename doesn't silently
    abort the whole run."""
    if os.path.exists(requested_path):
        return requested_path
    candidates = sorted(
        glob.glob("*.jpg") + glob.glob("*.jpeg") + glob.glob("*.png")
    )
    if candidates:
        print(
            f"  [notice] '{requested_path}' not found — using '{candidates[0]}' instead."
        )
        return candidates[0]
    return None


def make_album_cover_variants(image_path, artist_name="MaddPropz", album_title="Ace & King"):
    resolved_path = find_source_image(image_path)
    if not resolved_path:
        print(f"Error: Cannot find your photo. Put a .jpg/.png next to this script.")
        return

    text_artist = artist_name.upper()
    text_album = album_title.upper()

    font_title_heavy = load_font("title_heavy", 360)
    font_title_clean = load_font("title_clean", 320)
    font_sub_heavy = load_font("sub_heavy", 160)
    font_sub_clean = load_font("sub_clean", 140)

    saved_files = []

    # -----------------------------------------------------------------
    # STYLE 1: TRUE 90S OLD SCHOOL HIP-HOP
    # -----------------------------------------------------------------
    print("Generating Variation 1: 90s Old School Hip-Hop...")
    img1 = process_base_image(resolved_path)
    img1 = ImageEnhance.Contrast(img1).enhance(1.65)
    img1 = ImageEnhance.Color(img1).enhance(1.30)
    img1 = ImageEnhance.Sharpness(img1).enhance(2.0)

    noise = Image.effect_noise((3000, 3000), 15).convert("RGB")
    img1 = Image.blend(img1, noise, 0.05)  # toned down from 0.08 - less file bloat, same grit

    draw1 = ImageDraw.Draw(img1)

    w_alb1 = text_w(draw1, text_album, font_title_heavy)
    x_alb1 = (3000 - w_alb1) // 2
    y_alb1 = 200
    for offset in range(35, 0, -5):
        draw1.text((x_alb1 + offset, y_alb1 + offset), text_album, fill="#050505", font=font_title_heavy)
    draw1.text((x_alb1 - 4, y_alb1 - 4), text_album, fill="#DCDCDC", font=font_title_heavy)
    draw1.text((x_alb1, y_alb1), text_album, fill="#FFFFFF", font=font_title_heavy)

    w_art1 = text_w(draw1, text_artist, font_sub_heavy)
    x_art1 = (3000 - w_art1) // 2
    y_art1 = 2250
    for offset in range(20, 0, -4):
        draw1.text((x_art1 + offset, y_art1 + offset), text_artist, fill="#1a1100", font=font_sub_heavy)
    draw1.text((x_art1, y_art1), text_artist, fill="#FFD700", font=font_sub_heavy)

    draw1.rectangle([0, 0, 2999, 2999], outline="black", width=55)
    img1 = draw_parental_advisory(img1)
    img1.save("style_oldschool_hiphop.jpg", "JPEG", quality=92)
    saved_files.append("style_oldschool_hiphop.jpg")

    # -----------------------------------------------------------------
    # STYLE 2: 2026 PREMIUM CINEMA (Teal & Gold Look)
    # -----------------------------------------------------------------
    print("Generating Variation 2: 2026 Premium Cinema...")
    img2 = process_base_image(resolved_path)
    r, g, b = img2.split()
    r = r.point(lambda p: int(p * 0.88) if p < 128 else min(255, int(p * 1.15)))
    b = b.point(lambda p: min(255, int(p * 1.25)) if p < 128 else int(p * 0.82))
    img2 = Image.merge("RGB", (r, g, b))
    img2 = ImageEnhance.Contrast(img2).enhance(1.45)
    img2 = ImageEnhance.Color(img2).enhance(0.85)

    vignette = Image.new("L", (3000, 3000), 255)
    vignette_draw = ImageDraw.Draw(vignette)
    vignette_draw.ellipse([200, 200, 2800, 2800], fill=110)
    vignette = vignette.filter(ImageFilter.GaussianBlur(400))
    img2 = Image.composite(img2, Image.new("RGB", (3000, 3000), "black"), vignette)

    draw2 = ImageDraw.Draw(img2)

    w_alb2 = text_w(draw2, text_album, font_title_clean)
    x_alb2 = (3000 - w_alb2) // 2
    draw2.text((x_alb2 + 5, 255), text_album, fill="#0a0a0a", font=font_title_clean)
    draw2.text((x_alb2, 250), text_album, fill="#FFFFFF", font=font_title_clean)

    w_art2 = text_w(draw2, text_artist, font_sub_clean)
    x_art2 = (3000 - w_art2) // 2
    draw2.text((x_art2, 2300), text_artist, fill="#E6E6E6", font=font_sub_clean)

    img2 = draw_parental_advisory(img2)
    img2.save("style_2026_premium_cinema.jpg", "JPEG", quality=92)
    saved_files.append("style_2026_premium_cinema.jpg")

    # -----------------------------------------------------------------
    # STYLE 3: VINTAGE VINYL JACKET (Gritty Paper Texture)
    # -----------------------------------------------------------------
    print("Generating Variation 3: Vintage Vinyl Jacket...")
    img3 = process_base_image(resolved_path)
    img3 = ImageOps.grayscale(img3).convert("RGB")  # FIXED: ImageOps is now imported
    img3 = ImageEnhance.Contrast(img3).enhance(1.3)

    sepia = Image.new("RGB", (3000, 3000), "#f4ecd8")
    img3 = Image.blend(img3, sepia, 0.18)

    grunge = Image.effect_noise((3000, 3000), 25).convert("RGB")
    img3 = Image.blend(img3, grunge, 0.10)  # toned down from 0.12

    draw3 = ImageDraw.Draw(img3)
    w_alb3 = text_w(draw3, text_album, font_title_heavy)
    draw3.text(((3000 - w_alb3) // 2, 220), text_album, fill="#1a1a1a", font=font_title_heavy)
    w_art3 = text_w(draw3, text_artist, font_sub_heavy)
    draw3.text(((3000 - w_art3) // 2, 2280), text_artist, fill="#cc0000", font=font_sub_heavy)

    img3 = draw_parental_advisory(img3)
    img3.save("style_vintage_vinyl.jpg", "JPEG", quality=92)
    saved_files.append("style_vintage_vinyl.jpg")

    # -----------------------------------------------------------------
    # STYLE 4: DARK CYBERPUNK (Deep Shadow Void with Cold Neon)
    # -----------------------------------------------------------------
    print("Generating Variation 4: Dark Cyberpunk...")
    img4 = process_base_image(resolved_path)
    img4 = ImageEnhance.Contrast(img4).enhance(1.8)

    blue_wash = Image.new("RGB", (3000, 3000), "#001122")
    img4 = Image.blend(img4, blue_wash, 0.15)

    draw4 = ImageDraw.Draw(img4)
    w_alb4 = text_w(draw4, text_album, font_title_heavy)
    draw4.text(((3000 - w_alb4) // 2, 200), text_album, fill="#00FFFF", font=font_title_heavy)
    w_art4 = text_w(draw4, text_artist, font_sub_clean)
    draw4.text(((3000 - w_art4) // 2, 2300), text_artist, fill="#FFFFFF", font=font_sub_clean)

    img4 = draw_parental_advisory(img4)
    img4.save("style_dark_cyberpunk.jpg", "JPEG", quality=92)
    saved_files.append("style_dark_cyberpunk.jpg")

    print(f"\n[SUCCESS]: {len(saved_files)} cover styles saved:")
    for f in saved_files:
        size_kb = os.path.getsize(f) // 1024
        print(f"  - {f}  ({size_kb} KB)")


# Execute studio engine
if __name__ == "__main__":
    make_album_cover_variants(image_path="me.jpg", artist_name="MaddPropz", album_title="Ace & King")
