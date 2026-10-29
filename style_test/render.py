"""15-second pictogram horror test: an original scene on the premise 'crows bring gifts; don't keep the last one'.

Pure procedural drawing (Pillow + numpy) piped to ffmpeg. No sound, no subtitles.
Run: python3 render.py  ->  crows_test.mp4
"""
import math
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H, SS, FPS, DUR = 1920, 1080, 2, 30, 15.0
OUT = Path(__file__).resolve().parent / "crows_test.mp4"
FONT = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 22 * SS)

WHITE = (236, 236, 232)
GREY = (150, 150, 150)
DARK = (30, 30, 34)
FILL = (64, 64, 68)
YELLOW = (255, 206, 70)
RED = (235, 36, 36)


def ease(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


def lerp(a, b, x):
    return a + (b - a) * x


class Cam:
    """World space is 1920x1080; the camera zooms/pans and draws at SS supersampling."""

    def __init__(self, draw, cx, cy, z):
        self.d, self.cx, self.cy, self.z = draw, cx, cy, z

    def p(self, x, y):
        return (((x - self.cx) * self.z + W / 2) * SS, ((y - self.cy) * self.z + H / 2) * SS)

    def w(self, px):
        return max(1, int(px * self.z * SS))

    def rect(self, x0, y0, x1, y1, fill=None, outline=WHITE, width=3, r=0):
        a, b = self.p(x0, y0), self.p(x1, y1)
        if r:
            self.d.rounded_rectangle([a, b], radius=r * self.z * SS, fill=fill, outline=outline, width=self.w(width))
        else:
            self.d.rectangle([a, b], fill=fill, outline=outline, width=self.w(width))

    def circle(self, x, y, r, fill=None, outline=WHITE, width=3):
        a, b = self.p(x - r, y - r), self.p(x + r, y + r)
        self.d.ellipse([a, b], fill=fill, outline=outline, width=self.w(width) if outline else 0)

    def ellipse(self, x, y, rx, ry, fill=None, outline=WHITE, width=3):
        a, b = self.p(x - rx, y - ry), self.p(x + rx, y + ry)
        self.d.ellipse([a, b], fill=fill, outline=outline, width=self.w(width) if outline else 0)

    def line(self, pts, fill=WHITE, width=3):
        self.d.line([self.p(*q) for q in pts], fill=fill, width=self.w(width), joint="curve")

    def poly(self, pts, fill=None, outline=WHITE, width=3):
        self.d.polygon([self.p(*q) for q in pts], fill=fill, outline=outline, width=self.w(width) if outline else 0)

    def arc(self, x, y, r, a0, a1, fill=WHITE, width=3):
        a, b = self.p(x - r, y - r), self.p(x + r, y + r)
        self.d.arc([a, b], a0, a1, fill=fill, width=self.w(width))


# ---------------------------------------------------------------- pictograms
def crow(c, x, y, s=1.0, face=1, flap=None, eye=1.0):
    """Original crow pictogram: dark fill, white rim, yellow eye. flap: None=folded, else -1..1 wing angle."""
    def t(pts):
        return [(x + px * s * face, y + py * s) for px, py in pts]

    c.poly(t([(-62, -2), (-30, -22), (4, -28), (24, -22), (30, -6), (14, 8), (-22, 10), (-62, 6)]), DARK, WHITE, 3)
    c.line(t([(0, 8), (-4, 30)]), WHITE, 3)
    c.line(t([(12, 8), (14, 30)]), WHITE, 3)
    hx, hy = x + 32 * s * face, y - 34 * s
    c.circle(hx, hy, 15 * s, DARK, WHITE, 3)
    c.poly(t([(44, -41), (66, -33), (44, -27)]), GREY, WHITE, 2)
    if flap is None:
        c.poly(t([(-44, -6), (-6, -24), (18, -18), (-12, 2)]), FILL, WHITE, 2)
    else:
        tip = -78 * flap
        c.poly(t([(-14, -16), (16, -18), (-2, tip), (-38, tip * 0.8)]), FILL, WHITE, 2)
    if eye > 0.02:
        c.ellipse(hx + 5 * s * face, hy - 3 * s, 3.4 * s, 3.4 * s * eye, YELLOW, None)


def gift(c, kind, x, y, s=1.0, col=WHITE):
    if kind == "coin":
        c.circle(x, y - 9 * s, 9 * s, GREY, col, 2)
        c.circle(x, y - 9 * s, 5 * s, None, col, 1)
    elif kind == "button":
        c.circle(x, y - 9 * s, 9 * s, FILL, col, 2)
        for dx, dy in [(-3, -3), (3, -3), (-3, 3), (3, 3)]:
            c.circle(x + dx * s, y - 9 * s + dy * s, 1.3 * s, col, None)
    elif kind == "cap":
        pts = []
        for i in range(24):
            a = i / 24 * 2 * math.pi
            r = (10 if i % 2 else 8) * s
            pts.append((x + r * math.cos(a), y - 10 * s + r * math.sin(a)))
        c.poly(pts, FILL, col, 2)
    elif kind == "ring":
        c.ellipse(x, y - 7 * s, 9 * s, 6 * s, None, col, 3)
        c.poly([(x - 3 * s, y - 14 * s), (x, y - 19 * s), (x + 3 * s, y - 14 * s)], col, None)
    elif kind == "marble":
        c.circle(x, y - 8 * s, 8 * s, FILL, col, 2)
        c.arc(x, y - 8 * s, 4 * s, 200, 340, col, 2)
    elif kind == "key":
        c.circle(x - 13 * s, y - 8 * s, 7 * s, None, col, 3)
        c.line([(x - 6 * s, y - 8 * s), (x + 16 * s, y - 8 * s)], col, 3)
        c.line([(x + 10 * s, y - 8 * s), (x + 10 * s, y - 3 * s)], col, 3)
        c.line([(x + 15 * s, y - 8 * s), (x + 15 * s, y - 2 * s)], col, 3)


def house(c, lamp=1.0, sleeper=True):
    # night sky details
    c.arc(1700, 170, 34, 300, 120, YELLOW, 6)
    c.arc(1712, 160, 30, 300, 120, (0, 0, 0), 9)
    # wall + window
    c.rect(180, 240, 1100, 900, (16, 16, 18), WHITE, 3)
    for yy in range(300, 900, 70):
        c.line([(190, yy), (1090, yy)], (34, 34, 38), 2)
    c.rect(440, 370, 860, 690, (10, 10, 12), WHITE, 4)
    # room inside the window: lamp, nightstand, bed, sleeper
    lv = int(40 + 200 * lamp)
    c.rect(480, 580, 540, 640, FILL, WHITE, 2)
    c.line([(510, 580), (510, 552)], WHITE, 2)
    c.poly([(492, 552), (528, 552), (520, 530), (500, 530)], (lv, lv, lv - 10), WHITE, 2)
    c.rect(570, 598, 830, 640, FILL, WHITE, 2, r=6)
    c.line([(450, 640), (850, 640)], (70, 70, 74), 2)
    if sleeper:
        c.circle(605, 590, 14, (210, 210, 205), WHITE, 2)
        c.ellipse(720, 596, 95, 14, (120, 120, 124), WHITE, 2)
    c.line([(650, 370), (650, 690)], WHITE, 4)
    c.line([(440, 515), (860, 515)], WHITE, 4)
    # sill
    c.rect(410, 690, 890, 714, (200, 200, 196), WHITE, 2)
    # ground + tree
    c.line([(0, 900), (1920, 900)], (90, 90, 90), 3)
    c.poly([(1530, 900), (1570, 900), (1562, 300), (1540, 300)], DARK, WHITE, 3)
    c.line([(1545, 430), (1350, 400), (980, 392)], WHITE, 8)
    c.line([(1545, 430), (1350, 400), (980, 392)], DARK, 3)
    c.line([(1555, 320), (1680, 250)], WHITE, 6)
    c.line([(1440, 414), (1400, 360)], WHITE, 4)


SILL_Y = 690
SLOTS = {"coin": 560, "button": 512, "cap": 740, "ring": 465, "marble": 805}
APPEAR = {"coin": 2.55, "button": 4.35, "cap": 4.85, "ring": 5.35, "marble": 5.85}


def pop(t, t0):
    """Scale 0 -> overshoot -> 1 over 0.25 s."""
    k = (t - t0) / 0.25
    if k <= 0:
        return 0.0
    if k >= 1:
        return 1.0
    return math.sin(k * math.pi * 0.75) / math.sin(math.pi * 0.75)


def gifts(c, t, s=1.0, key_red=0.0, key_drop=None):
    for kind, gx in SLOTS.items():
        k = pop(t, APPEAR[kind])
        if k > 0:
            gift(c, kind, gx, SILL_Y, 1.5 * s * k)
    if key_drop is not None:
        k = ease((t - key_drop) / 0.35)
        y = lerp(540, SILL_Y, k * k) - (math.sin(min(max((t - key_drop - 0.35) / 0.25, 0), 1) * math.pi) * 8)
        col = tuple(int(lerp(a, b, key_red)) for a, b in zip(WHITE, RED))
        gift(c, "key", 612, y, s * 1.7, col)


# ---------------------------------------------------------------- shots
def shot(t):
    """Return (image, post-fx params)."""
    img = Image.new("RGB", (W * SS, H * SS), (0, 0, 0))
    d = ImageDraw.Draw(img)
    fx = {"glitch": 0.0, "flicker": 1.0, "shadow": None, "red_glow": None}

    if t < 4.0:  # 1. wide night: a crow drops the first gift
        z = lerp(1.0, 1.09, ease(t / 4))
        c = Cam(d, lerp(960, 820, ease(t / 4)), lerp(540, 590, ease(t / 4)), z)
        house(c)
        gifts(c, t)
        if t < 0.9:
            crow(c, 1300, 360, 1.3, -1)
        elif t < 2.6:
            k = ease((t - 0.9) / 1.7)
            x, y = lerp(1300, 620, k), lerp(360, 651, k) - math.sin(k * math.pi) * 120
            crow(c, x, y, 1.3, -1, flap=math.sin(t * 22))
        elif t < 3.1:
            crow(c, 620, 651, 1.3, -1)
        else:
            k = ease((t - 3.1) / 0.9)
            x, y = lerp(620, 1250, k), lerp(651, 355, k) - math.sin(k * math.pi) * 140
            crow(c, x, y, 1.3, 1, flap=math.sin(t * 22))
        if 2.55 < t < 2.9:
            fx["glint"] = (560, 676, (t - 2.55) / 0.35, c)

    elif t < 7.5:  # 2. close on the sill: the gifts keep coming; a shadow crosses
        u = t - 4.0
        c = Cam(d, lerp(650, 640, u / 3.5), 620, lerp(2.3, 2.5, u / 3.5))
        house(c)
        gifts(c, t)
        for kind in ("button", "cap", "ring", "marble"):
            if APPEAR[kind] < t < APPEAR[kind] + 0.3:
                fx["glint"] = (SLOTS[kind], 676, (t - APPEAR[kind]) / 0.3, c)
        if 6.5 < t < 7.4:
            fx["shadow"] = (t - 6.5) / 0.9

    elif t < 11.0:  # 3. wide: seven crows on the branch turn to the window, one by one
        u = t - 7.5
        c = Cam(d, lerp(1000, 1180, ease(u / 3.5)), lerp(560, 450, ease(u / 3.5)), lerp(1.02, 1.45, ease(u / 3.5)))
        flick = 1.0
        if 9.9 < t < 10.8:
            flick = 0.0 if int(t * 17) % 3 == 0 else 1.0
        house(c, lamp=flick)
        gifts(c, t)
        xs = [1040, 1112, 1184, 1256, 1328, 1400, 1472]
        for i, x in enumerate(xs):
            by = lerp(392, 400, (x - 980) / 370) if x < 1350 else lerp(400, 430, (x - 1350) / 195)
            turn = t > 8.0 + i * 0.27
            crow(c, x, by - 30 * 0.75 - 2, 0.75, -1 if turn else 1, eye=1.0)
        fx["flicker"] = 0.82 + 0.18 * flick

    elif t < 13.5:  # 4. the seventh gift: a key, which turns red
        u = t - 11.0
        c = Cam(d, 630, lerp(650, 672, ease(u / 2.5)), lerp(3.0, 4.4, ease(u / 2.5)))
        house(c, sleeper=True)
        red = ease((t - 12.1) / 0.9)
        gifts(c, t, key_red=red, key_drop=11.25)
        if red > 0:
            fx["red_glow"] = (c.p(612, 676), red * (0.75 + 0.25 * math.sin(t * 14)))

    else:  # 5. darkness: one eye opens, very close
        u = t - 13.5
        c = Cam(d, 960, 540, 1.0)
        fade = max(0.0, 1 - u / 0.5)
        if fade > 0:
            fx["red_glow"] = ((W * SS / 2, H * SS / 2 + 40 * SS), fade * 0.8)
        if u > 0.55:
            k = ease((u - 0.55) / 0.35)
            g = int(42 * k)
            crow(c, 760, 860, 9.0, 1, eye=ease((u - 0.75) / 0.25))
            if g < 42:  # keep the giant crow almost invisible: dim the frame below in post
                pass
            fx["dim_head"] = 0.22 * k
    return img, fx


# ---------------------------------------------------------------- post
yy, xx = np.mgrid[0:H, 0:W]
VIGNETTE = (1 - 0.55 * (((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2) ** 1.4).clip(0.15, 1)[..., None]


def glow(a):
    im = Image.fromarray(a)
    small = im.resize((W // 4, H // 4), Image.BILINEAR)
    g1 = np.asarray(small.filter(ImageFilter.GaussianBlur(3)).resize((W, H), Image.BILINEAR), dtype=np.float32)
    g2 = np.asarray(small.filter(ImageFilter.GaussianBlur(12)).resize((W, H), Image.BILINEAR), dtype=np.float32)
    return a.astype(np.float32) + 0.55 * g1 + 0.35 * g2


def hud(img_draw, t, frame):
    f = frame % FPS
    s = int(t)
    img_draw.text((40 * SS, 34 * SS), "FILE 07  //  TEST RENDER", font=FONT, fill=(125, 125, 125))
    tc = f"00:00:{s:02d}:{f:02d}"
    img_draw.text(((W - 40) * SS - img_draw.textlength(tc, font=FONT), 34 * SS), tc, font=FONT, fill=(125, 125, 125))


def glitch(a, amount, rng):
    a = a.copy()
    k = int(4 + 18 * amount)
    out = a.copy()
    out[..., 0] = np.roll(a[..., 0], -k, axis=1)
    out[..., 2] = np.roll(a[..., 2], k, axis=1)
    for _ in range(int(4 + 14 * amount)):
        y0 = rng.integers(0, H - 10)
        h = rng.integers(3, int(10 + 70 * amount))
        out[y0:y0 + h] = np.roll(out[y0:y0 + h], rng.integers(-int(120 * amount) - 8, int(120 * amount) + 8), axis=1)
    for _ in range(int(2 + 6 * amount)):
        y0 = rng.integers(0, H - 3)
        x0 = rng.integers(0, W - 400)
        out[y0:y0 + 2, x0:x0 + rng.integers(60, 400)] = 220
    return out


CUTS = [4.0, 7.5, 11.0, 13.5, 14.85]


def frame_at(i):
    t = i / FPS
    rng = np.random.default_rng(i)
    img, fx = shot(t)
    hud(ImageDraw.Draw(img), t, i)
    a = np.asarray(img.resize((W, H), Image.LANCZOS))

    f = glow(a)
    if fx.get("red_glow"):
        (px, py), amt = fx["red_glow"]
        px, py = px / SS, py / SS
        r2 = ((xx - px) ** 2 + (yy - py) ** 2) / (260.0 ** 2)
        f += (np.exp(-r2)[..., None] * np.array([150, 10, 10], np.float32)) * amt
    if fx.get("glint"):
        gx, gy, k, c = fx["glint"]
        px, py = c.p(gx, gy)
        px, py = px / SS, py / SS
        a_ = math.sin(min(k, 1) * math.pi)
        r2 = ((xx - px) ** 2 + (yy - py) ** 2) / (40.0 ** 2)
        f += np.exp(-r2)[..., None] * 230 * a_
    if fx.get("shadow") is not None:
        sx = lerp(-500, W + 500, fx["shadow"])
        band = np.exp(-(((xx - sx) / 380.0) ** 2) - (((yy - 520) / 600.0) ** 2))
        f *= (1 - 0.85 * band)[..., None]
    if fx.get("dim_head") is not None:
        # giant crow is drawn full-strength; crush everything but the eye down to a faint outline
        lum = f.mean(axis=2, keepdims=True)
        is_eye = (f[..., 0:1] > 200) & (f[..., 2:3] < 150)
        f = np.where(is_eye, f, f * fx["dim_head"])
        del lum

    # global flicker + per-frame breathing + vignette + grain
    f *= fx["flicker"] * (0.96 + 0.04 * math.sin(t * 9.3) + rng.normal(0, 0.012))
    f *= VIGNETTE
    f += rng.normal(0, 7, (H, W, 1)).astype(np.float32)
    out = f.clip(0, 255).astype(np.uint8)

    g = 0.0
    for ct in CUTS:
        if abs(t - ct) < 0.12:
            g = max(g, 1 - abs(t - ct) / 0.12)
    if 13.35 < t < 13.55:
        g = 1.0
    if rng.random() < 0.015:
        g = max(g, 0.25)
    if g > 0:
        out = glitch(out, g, rng)
    if t >= 14.9:
        out[:] = 0
    return out


def main():
    n = int(DUR * FPS)
    ff = subprocess.Popen(
        ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
         "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", str(OUT)],
        stdin=subprocess.PIPE)
    for i in range(n):
        ff.stdin.write(frame_at(i).tobytes())
        if i % 60 == 0:
            print(f"frame {i}/{n}", flush=True)
    ff.stdin.close()
    ff.wait()
    print("wrote", OUT)


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:  # preview stills: python3 render.py 1.5 5 9 12.5 14.4
        for s in sys.argv[1:]:
            Image.fromarray(frame_at(int(float(s) * FPS))).save(Path(OUT).with_name(f"still_{s}.png"))
    else:
        main()
