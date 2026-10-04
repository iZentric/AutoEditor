#!/usr/bin/env python3
"""Finalizare miniatura YouTube la SPECul corect + verificare.
SPEC: 1280x720 (16:9), JPG, < 2MB (limita YouTube: 2MB).
Folosire: python3 finalizare_miniatura.py intrare.png iesire.jpg [offset_y]
  offset_y = 0..1 (0=top, 0.5=centru) — unde cade fereastra 16:9 pe imaginea sursa."""
import subprocess, sys, os

W, H = 1280, 720

def spec(cale_in, cale_out, offset=0.25):
    # dimensiuni sursa
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0",
                        "-show_entries", "stream=width,height", "-of", "csv=p=0", cale_in],
                       capture_output=True, text=True).stdout.strip()
    w0, h0 = (int(x) for x in r.split(","))
    # fereastra 16:9 maxima in sursa
    if w0 / h0 > W / H:                 # sursa mai lata -> taie din stanga/dreapta
        win_h, win_w = h0, int(h0 * W / H)
        x = (w0 - win_w) // 2
        y = 0
    else:                               # sursa mai inalta -> taie sus/jos (offset controleaza unde)
        win_w, win_h = w0, int(w0 * H / W)
        x = 0
        y = int((h0 - win_h) * max(0.0, min(1.0, offset)))
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", cale_in,
                    "-vf", f"crop={win_w}:{win_h}:{x}:{y},scale={W}:{H}:flags=lanczos",
                    "-q:v", "2", cale_out], check=True)
    mb = os.path.getsize(cale_out) / 1024 / 1024
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0",
                        "-show_entries", "stream=width,height", "-of", "csv=p=0", cale_out],
                       capture_output=True, text=True).stdout.strip()
    ok_dim = r == f"{W},{H}"
    ok_mb = mb < 2.0
    print(f"[{'OK' if ok_dim and ok_mb else 'FAIL'}] {cale_out}: {r}, {mb:.2f}MB "
          f"(spec 1280x720, <2MB) | fereastra crop: {win_w}x{win_h} la y={y}")
    return ok_dim and ok_mb

if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit("folosire: finalizare_miniatura.py intrare.png iesire.jpg [offset_y=0.25]")
    off = float(sys.argv[3]) if len(sys.argv) > 3 else 0.25
    sys.exit(0 if spec(sys.argv[1], sys.argv[2], off) else 1)
