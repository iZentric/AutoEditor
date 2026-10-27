import os, sys, subprocess, math, json
import numpy as np
sys.path.insert(0, '/home/user/autoeditor')
os.environ.setdefault('FFMPEG', '')  # las engine-ul sa-si gaseasca ffmpeg-ul
import editor_pro as ep
from PIL import Image

FF = ep.FF
SB = '/home/user/autoeditor/SHORT_BOSS'
def dur(p):
    r = subprocess.run([FF,'-y','-loglevel','error','-i',p,'-ar','44100','-ac','1','-f','f32le','-'], capture_output=True)
    return len(r.stdout)//4/44100.0
def decode(p):
    r = subprocess.run([FF,'-y','-loglevel','error','-i',p,'-ar','44100','-ac','1','-f','f32le','-'], capture_output=True)
    return np.frombuffer(r.stdout, dtype=np.float32)

# ---------- 1) timpi reali ai vocii ----------
texts = [
    ['AM','GASIT','BOSS-UL','DIN','POKECITY!'],
    ['ZICEAU','TOTI','CA','NU','SE','POATE','BATE!'],
    ['AM','INTRAT','LA','EL','CU','PIKACHU!'],
    ['M-A','LOVIT','CU','TOT','CE','AVEA!'],
    ['DAR','EU','AM','AVUT','PLANUL','SECRET...'],
    ['L-AM','BATUT...','SI','A','INCEPUT','SA','PLANGA!'],
]
vd = [dur(f'{SB}/voce_{i}.mp3') for i in range(1,7)]
V = sum(vd)
print('voce totala %.2fs' % V, ['%.2f'%v for v in vd])
TOTAL = 16.0
base_gaps = [0.30, 0.30, 0.30, 0.45, 0.45, 0.85]   # aer natural + tail pt loop
scale = (TOTAL - V) / sum(base_gaps)
gaps = [g*scale for g in base_gaps]
print('gaps:', ['%.2f'%g for g in gaps])

# ---------- 2) cuvinte cu timpi pe timeline ----------
words, starts = [], []
t = 0.0
for i,(txt,v,g) in enumerate(zip(texts, vd, gaps)):
    starts.append(t)
    n = len(txt); span = v*0.94
    for k,w in enumerate(txt):
        s = t + 0.03 + span*k/n
        words.append({'w': w, 's': round(s,2), 'e': round(s + span/n, 2)})
    t += v + g
print('starts:', ['%.2f'%s for s in starts], 'TOTAL %.2f' % t)
assert abs(t-TOTAL) < 0.05

# ---------- 3) voce.wav pe timeline ----------
voce = np.zeros(int(TOTAL*44100)+2205, dtype=np.float32)
for i,v in enumerate(vd):
    a = decode(f'{SB}/voce_{i+1}.mp3')[:int(v*44100)]
    o = int(starts[i]*44100)
    voce[o:o+len(a)] += a
import wave
with wave.open('/tmp/sb/voce.wav','wb') as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(44100)
    w.writeframes((np.clip(voce,-1,1)*32767).astype('<i2').tobytes())

# ---------- 4) captions sloturi (motorul lui) ----------
lines = ep.group_lines(words, maxw=3, gap=0.55)
punch = {'boss-ul','pokecity!','pikachu!','lovit','planga!','secret...'}
caps = ep.render_caption_pngs(lines, '/tmp/sb/caps', punch_set=punch)
print('caption pngs:', len(caps))

# ---------- 5) hook / big popout / CTA / logo ----------
ep.render_text_png('L-AM GASIT PE BOSS!', (255,230,0,255), 92, '/tmp/sb/hook.png')
ep.render_text_png('A PLANS!', (255,45,35,255), 110, '/tmp/sb/big.png', popout=True)
ep.render_cta_png('DA UN LIKE!', '/tmp/sb/like.png')
ep.make_logo_overlay('/home/user/autoeditor/assets/logo_pokecity.png', '/tmp/sb/logo.png')

# ---------- 6) body cinematic: zoompan per scena @1180x2098 (loc pt shake) ----------
NF = [int(round((vd[i]+gaps[i])*30)) for i in range(6)]
NF[-1] = int(TOTAL*30) - sum(NF[:-1])
zooms = ["min(1+0.0018*on,1.13)","min(1+0.0014*on,1.10)","min(1+0.0022*on,1.14)",
         "min(1+0.005*on,1.20)","min(1+0.003*on,1.15)","min(1+0.0026*on,1.16)"]
for i in range(6):
    subprocess.run([FF,'-y','-loglevel','error','-i',f'{SB}/SCENA_{i+1}.png','-vf',
        f"scale=1180:2114:flags=lanczos,crop=1180:2098,zoompan=z='{zooms[i]}':d={NF[i]}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1180x2098:fps=30",
        '-frames:v',str(NF[i]),'-c:v','libx264','-crf','19','-preset','veryfast','-pix_fmt','yuv420p','-r','30',f'/tmp/sb/seg{i}.mp4'], check=True)
    print('seg', i+1, NF[i]/30, 's')
with open('/tmp/sb/list.txt','w') as f:
    for i in range(6): f.write(f"file '/tmp/sb/seg{i}.mp4'\n")
subprocess.run([FF,'-y','-loglevel','error','-f','concat','-safe','0','-i','/tmp/sb/list.txt','-c','copy','/tmp/sb/body.mp4'], check=True)

# ---------- 7) SFX INTELIGENT (mixul lui: drone ducked + whoosh + boom + riser + pop) ----------
line_starts = [l[0]['s'] for l in lines if l[0]['s'] > 0.08][:6]
s4, s6 = starts[3], starts[5]
booms = [(0.12,0.9), (s4+0.03,0.9), (s6,1.0)]
whooshes = [0.0] + [round(s-0.12,2) for s in starts[1:]]
riser = max(0.2, s6-1.6)
ep.mix_audio('/tmp/sb/voce.wav', [(0.0,TOTAL)], TOTAL, '/tmp/sb/mix.wav',
             pops=line_starts, booms=booms, whooshes=whooshes, riser_at=riser,
             drone_gain=0.10, pop_gain=0.16)
print('mix OK | pops', ['%.1f'%p for p in line_starts], '| riser@%.2f'%riser)

# ---------- 8) overlay-uri + shake + randare ----------
overlays = [('/tmp/sb/hook.png', 150, 0.0, min(2.1, starts[1])),
            ('/tmp/sb/like.png', 1690, 0.0, 2.0),
            ('/tmp/sb/big.png', 700, s6+0.15, min(TOTAL-0.3, s6+1.5))]
shake = [(0.12,12), (s4,16), (s6,14)]
ep.render_overlays('/tmp/sb/body.mp4', '/tmp/sb/vid.mp4', TOTAL, overlays, '/tmp/sb/logo.png', shake, caps)
ep.mux('/tmp/sb/vid.mp4', '/tmp/sb/mix.wav', '/tmp/sb/raw.mp4')

# ---------- 9) LUFS -14 (calibrul repo-ului) ----------
import autoeditor
r = autoeditor.calibreaza_lufs(FF, '/tmp/sb/raw.mp4')
print('LUFS calib:', r)
fin = '/home/user/autoeditor/SHORT_BOSS_PLANS.mp4'
subprocess.run(['cp','/tmp/sb/raw_cal.mp4' if os.path.exists('/tmp/sb/raw_cal.mp4') else '/tmp/sb/raw.mp4', fin], check=True)
print('FINAL:', fin, os.path.getsize(fin)//1024, 'KB')
json.dump({'starts':[round(s,2) for s in starts], 'total':TOTAL}, open('/tmp/sb/meta.json','w'))
