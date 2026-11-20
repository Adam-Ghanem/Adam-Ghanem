#!/usr/bin/env python3
"""Render original iremcnar/eyeTutorial frames as a profile-ready looping GIF.

This exports the unchanged mathematical render_cells() frames of the original
Eye -> Space Python project. Only the display layer is changed: Tkinter cells
are drawn with Pillow so GitHub README can display the animation.
Source: https://github.com/iremcnar/eyeTutorial
"""
import hashlib
import importlib.util
import os
import pathlib
import urllib.request

from PIL import Image, ImageDraw, ImageFont

SOURCE = "https://raw.githubusercontent.com/iremcnar/eyeTutorial/main/eye.py"
EXPECTED_GIT_BLOB = "101b2bbd081779bed6b0729172992980618385a4"
OUTPUT = pathlib.Path("assets/eye_original_animation.gif")
FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"

def original_eye_module():
    data = urllib.request.urlopen(SOURCE, timeout=40).read()
    blob_sha = hashlib.sha1(("blob %d\0" % len(data)).encode() + data).hexdigest()
    if blob_sha != EXPECTED_GIT_BLOB:
        raise RuntimeError("Upstream eye.py changed; refuse to execute unexpected source")
    path = pathlib.Path("/tmp/original_iremcnar_eye.py")
    path.write_bytes(data)
    spec = importlib.util.spec_from_file_location("original_eye", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def run():
    eye = original_eye_module()
    cw, ch, rows = 9, 16, 30
    eye.init(cw, ch, rows)
    font = ImageFont.truetype(FONT_PATH, 15)
    frames = []
    last_t = 0.0

    # Preserve all phases (opening, blink, pupil zoom, nebula/heart).
    # Sample at 8 FPS; store at real-time frame duration for a loop.
    fps = 8
    end_seconds = 48
    for i in range(end_seconds * fps):
        t = i / fps
        dt = t - last_t if i else 0.0
        idx, rgb = eye.render_cells(t, dt)
        last_t = t
        frame = Image.new("RGB", (eye.W, eye.H), (1, 2, 3))
        draw = ImageDraw.Draw(frame)
        for r in range(eye.ROWS):
            for c in range(eye.COLS):
                code = int(idx[r, c])
                if code == 0:
                    continue
                clr = tuple(int(v) * 255 // (eye.QL - 1) for v in rgb[r, c])
                draw.text((c * cw + cw / 2, r * ch + ch / 2),
                          eye.RAMP[code], fill=clr, font=font, anchor="mm")
        # Adaptive palette per frame, no dithering, for compact GIF.
        frames.append(frame.quantize(colors=96, method=Image.Quantize.MEDIANCUT,
                                     dither=Image.Dither.NONE))
        if (i + 1) % 32 == 0:
            print(f"Rendered {i + 1}/{end_seconds * fps} frames", flush=True)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    frames[0].save(OUTPUT, save_all=True, append_images=frames[1:],
                   duration=int(1000 / fps), loop=0, optimize=True,
                   disposal=2)
    print(f"Wrote {OUTPUT}: {OUTPUT.stat().st_size / 1024 / 1024:.2f} MiB")

if __name__ == "__main__":
    run()
