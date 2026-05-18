from __future__ import annotations

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "mingmeng_platform_poster.jpg"

W, H = 1080, 1600


def font(path: str, size: int, index: int = 0) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(path, size=size, index=index)


PINGFANG = "/System/Library/AssetsV2/com_apple_MobileAsset_Font8/86ba2c91f017a3749571a82f2c6d890ac7ffb2fb.asset/AssetData/PingFang.ttc"
SONGTI = "/System/Library/Fonts/Supplemental/Songti.ttc"
HEITI = "/System/Library/Fonts/STHeiti Medium.ttc"

F_TITLE = font(SONGTI, 74, 0)
F_SUB = font(PINGFANG, 26, 0)
F_TAG = font(PINGFANG, 18, 0)
F_H2 = font(SONGTI, 34, 0)
F_H3 = font(PINGFANG, 28, 0)
F_BODY = font(PINGFANG, 22, 0)
F_BODY_SM = font(PINGFANG, 19, 0)
F_NUM = font(HEITI, 58, 0)
F_NUM_SM = font(HEITI, 38, 0)


def rgb(hex_color: str) -> tuple[int, int, int]:
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))


def text_size(draw: ImageDraw.ImageDraw, text: str, fnt: ImageFont.FreeTypeFont) -> tuple[int, int]:
    box = draw.textbbox((0, 0), text, font=fnt)
    return box[2] - box[0], box[3] - box[1]


def draw_center(draw: ImageDraw.ImageDraw, xy: tuple[int, int], text: str, fnt, fill, max_width: int | None = None) -> None:
    x, y = xy
    if max_width:
        size = fnt.size
        while size > 12 and text_size(draw, text, fnt)[0] > max_width:
            fnt = font(PINGFANG, size - 1, 0)
            size -= 1
    tw, _ = text_size(draw, text, fnt)
    draw.text((x - tw // 2, y), text, font=fnt, fill=fill)


def wrap(draw: ImageDraw.ImageDraw, text: str, fnt, max_width: int) -> list[str]:
    lines: list[str] = []
    current = ""
    for ch in text:
        test = current + ch
        if text_size(draw, test, fnt)[0] <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = ch
    if current:
        lines.append(current)
    return lines


def paragraph(draw: ImageDraw.ImageDraw, x: int, y: int, text: str, fnt, fill, max_width: int, leading: int) -> int:
    for line in wrap(draw, text, fnt, max_width):
        draw.text((x, y), line, font=fnt, fill=fill)
        y += leading
    return y


def rounded(draw: ImageDraw.ImageDraw, box, radius: int, fill, outline=None, width: int = 1) -> None:
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def shadowed_card(base: Image.Image, box, radius: int, fill, shadow=(0, 0, 0, 42)) -> ImageDraw.ImageDraw:
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    x1, y1, x2, y2 = box
    ld.rounded_rectangle((x1, y1 + 12, x2, y2 + 12), radius=radius, fill=shadow)
    layer = layer.filter(ImageFilter.GaussianBlur(18))
    base.alpha_composite(layer)
    d = ImageDraw.Draw(base)
    rounded(d, box, radius, fill)
    return d


def make_background() -> Image.Image:
    img = Image.new("RGBA", (W, H), rgb("#f4ebd8") + (255,))
    px = img.load()
    top = rgb("#fbf7ee")
    bottom = rgb("#e8ddc8")
    for y in range(H):
        t = y / (H - 1)
        col = tuple(int(top[i] * (1 - t) + bottom[i] * t) for i in range(3))
        for x in range(W):
            px[x, y] = col + (255,)
    d = ImageDraw.Draw(img, "RGBA")
    for x in range(0, W, 48):
        d.line((x, 0, x, H), fill=(126, 113, 91, 23), width=1)
    for y in range(0, H, 48):
        d.line((0, y, W, y), fill=(126, 113, 91, 23), width=1)
    return img


def main() -> None:
    img = make_background()
    d = ImageDraw.Draw(img, "RGBA")

    deep = rgb("#0d3f36")
    deep2 = rgb("#102a43")
    gold = rgb("#c9a15a")
    ink = rgb("#17231d")
    muted = rgb("#625b50")
    paper = rgb("#fffaf0")

    d.rectangle((0, 0, W, 420), fill=deep + (255,))
    d.polygon([(0, 300), (220, 258), (472, 332), (730, 274), (1080, 330), (1080, 470), (0, 470)], fill=deep2 + (235,))
    for y in (84, 142, 206):
        d.arc((70, y, 1040, y + 210), 190, 350, fill=gold + (78,), width=2)

    rounded(d, (74, 72, 430, 112), 20, fill=(255, 250, 235, 230), outline=gold + (125,))
    d.text((96, 82), "ARCHIVAL RESEARCH PLATFORM", font=F_TAG, fill=(73, 68, 57, 255))

    draw_center(d, (W // 2, 148), "民盟历史文献研究库", F_TITLE, (255, 248, 232, 255), max_width=920)
    draw_center(d, (W // 2, 245), "海外一手档案 · 中英全文 · 页码引用 · 多源互证", F_SUB, (230, 216, 185, 255), max_width=880)
    draw_center(d, (W // 2, 296), "1941–1950年代中国民主同盟研究平台", F_TAG, (209, 196, 166, 255), max_width=780)

    shadowed_card(img, (74, 390, 1006, 570), 14, paper + (255,))
    d.rectangle((74, 390, 1006, 398), fill=gold + (255,))
    draw_center(d, (W // 2, 432), "把散落在海外档案中的民盟史料", F_H2, ink + (255,), max_width=850)
    draw_center(d, (W // 2, 482), "整理成可检索、可引用、可复核的证据库", F_H2, ink + (255,), max_width=850)
    draw_center(d, (W // 2, 532), "面向学术研究、专题写作与公共展示", F_BODY, deep + (255,), max_width=820)

    d.text((74, 660), "当前规模", font=F_H2, fill=ink + (255,))
    shadowed_card(img, (74, 700, 1006, 890), 14, (255, 255, 255, 235))
    stats = [("496", "篇海外文献"), ("710", "个全文页段"), ("5", "类海外来源"), ("100%", "中文译文覆盖")]
    for i, (num, lab) in enumerate(stats):
        cx = 74 + 116 + i * 232
        draw_center(d, (cx, 744), num, F_NUM if num != "100%" else F_NUM_SM, deep + (255,), max_width=190)
        draw_center(d, (cx, 820), lab, F_BODY_SM, muted + (255,), max_width=180)

    d.text((74, 980), "来源矩阵", font=F_H2, fill=ink + (255,))
    shadowed_card(img, (74, 1020, 1006, 1254), 14, deep2 + (255,))
    sources = [
        ("FRUS", "美国外交文件集"),
        ("CIA FOIA", "情报系统视角"),
        ("Wilson Center", "冷战档案视角"),
        ("HathiTrust / IA", "港媒与公开出版物"),
        ("Hoover", "私人档案线索"),
        ("JACAR / HKPRO / NARA", "下一阶段扩展"),
    ]
    for i, (name, desc) in enumerate(sources):
        col = i % 2
        row = i // 2
        x = 120 + col * 438
        y = 1062 + row * 64
        d.ellipse((x, y, x + 16, y + 16), fill=gold + (255,))
        d.text((x + 32, y - 8), name, font=F_BODY, fill=(255, 248, 232, 255))
        d.text((x + 32, y + 23), desc, font=F_BODY_SM, fill=(204, 191, 158, 255))

    d.text((74, 1340), "平台能力", font=F_H2, fill=ink + (255,))
    cards = [("全文检索", "原文与译文并行检索"), ("页码引用", "保留来源链接与定位"), ("专题白皮书", "多源叙事与证据链")]
    for i, (head, body) in enumerate(cards):
        x1 = 74 + i * 318
        shadowed_card(img, (x1, 1380, x1 + 296, 1504), 12, paper + (255,), shadow=(0, 0, 0, 28))
        draw_center(d, (x1 + 148, 1418), head, F_H3, deep + (255,), max_width=250)
        draw_center(d, (x1 + 148, 1464), body, F_BODY_SM, muted + (255,), max_width=250)

    d.line((74, 1538, 1006, 1538), fill=(170, 155, 123, 255), width=1)
    d.text((74, 1568), "民盟历史文献研究库", font=F_BODY_SM, fill=muted + (255,))
    right = "FRUS · CIA · Wilson · HathiTrust/IA · Hoover"
    tw, _ = text_size(d, right, F_BODY_SM)
    d.text((1006 - tw, 1568), right, font=F_BODY_SM, fill=rgb("#926820") + (255,))

    img = img.convert("RGB")
    img.save(OUT, "JPEG", quality=95, subsampling=0, optimize=True)
    print(OUT)


if __name__ == "__main__":
    main()
