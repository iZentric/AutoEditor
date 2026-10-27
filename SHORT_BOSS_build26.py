import os, sys, subprocess, json
import numpy as np, wave
sys.path.insert(0, '/home/user/autoeditor')
import editor_pro as ep
FF = ep.FF
SB = '/home/user/autoeditor/SHORT_BOSS'
def dur(p):
    r = subprocess.run([FF,'-y','-loglevel','error','-i',p,'-ar','44100','-ac','1','-f','f32le','-'], capture_output=True)
    return len(r.stdout)//4/44100.0
def decode(p):
    r = subprocess.run([FF,'-y','-loglevel','error','-i',p,'-ar','44100','-ac','1','-f','f32le','-'], capture_output=True)
    return np.frombuffer(r.stdout, dtype=np.float32)

texts = [
    ['BOSS-UL','MI-A','FURAT','POKEMONUL!'],
    ['A','FUGIT','IN','PADUREA','INTUNECATA!'],
    ['L-AM','URMARIT','TOATA','NOAPTEA!'],
    ['MI-A','PUS','PIKACHU','INTR-O','CUSCA!'],
    ['ASA','CA','AM','SPART','CUSCA...','CU','TOT!'],
    ['SI','BOSS-UL...','A','FUGIT','PLANGAND!'],
]
vd = [dur(f'{SB}/v26_{i}.mp3') for i in range(1,7)]
V = sum(vd); TOTAL = 16.0
base_gaps = [0.30, 0.30, 0.30, 0.35, 0.35, 0.80]
scale = (TOTAL - V) / sum(base_gaps); gaps = [g*scale for g in base_gaps]
print('voce %.2fs' % V, ['%.2f'%v for v in vd], '| gaps', ['%.2f'%g for g in gaps])
words, starts = [], []
t = 0.0
for txt, v, g in zip(texts, vd, gaps):
    starts.append(t)
    n = len(txt); span = v*0.94
    for k,w in enumerate(txt):
        s = t + 0.03 + span*k/n
        words.append({'w': w, 's': round(s,2), 'e': round(s+span/n,2)})
    t += v + g
print('starts:', ['%.2f'%s for s in starts])
assert abs(t-TOTAL) < 0.06, t
voce = np.zeros(int(TOTAL*44100)+2205, dtype=np.float32)
for i,v in enumerate(vd):
    a = decode(f'{SB}/v26_{i+1}.mp3')[:int(v*44100)]
    o = int(starts[i]*44100); voce[o:o+len(a)] += a
with wave.open('/tmp/sb26/voce.wav','wb') as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(44100)
    w.writeframes((np.clip(voce,-1,1)*32767).astype('<i2').tobytes())

lines = ep.group_lines(words, maxw=3, gap=0.55)
punch = {'pokemonul!','padurea','noaptea!','cusca!','spart','plangand!'}
caps = ep.render_caption_pngs(lines, '/tmp/sb26/caps', punch_set=punch)
ep.render_text_png('MI-A FURAT POKEMONUL!', (255,230,0,255), 90, '/tmp/sb26/hook.png')
ep.render_text_png('A FUGIT!', (255,45,35,255), 110, '/tmp/sb26/big.png', popout=True)
ep.render_cta_png('DA UN LIKE!', '/tmp/sb26/like.png')
ep.make_logo_overlay('/home/user/autoeditor/assets/logo_pokecity.png', '/tmp/sb26/logo.png')

NF = [int(round((vd[i]+gaps[i])*30)) for i in range(6)]
NF[-1] = int(TOTAL*30) - sum(NF[:-1])
zooms = ["min(1+0.002*on,1.12)","min(1+0.0018*on,1.10)","min(1+0.0026*on,1.13)",
         "min(1+0.004*on,1.18)","min(1+0.005*on,1.20)","min(1+0.0026*on,1.15)"]
for i in range(6):
    subprocess.run([FF,'-y','-loglevel','error','-i',f'{SB}/S26_SCENA_{i+1}.png','-vf',
        f"scale=1180:2114:flags=lanczos,crop=1180:2098,zoompan=z='{zooms[i]}':d={NF[i]}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1180x2098:fps=30",
        '-frames:v',str(NF[i]),'-c:v','libx264','-crf','19','-preset','veryfast','-pix_fmt','yuv420p','-r','30',f'/tmp/sb26/seg{i}.mp4'], check=True)
with open('/tmp/sb26/list.txt','w') as f:
    for i in range(6): f.write(f"file '/tmp/sb26/seg{i}.mp4'\n")
subprocess.run([FF,'-y','-loglevel','error','-f','concat','-safe','0','-i','/tmp/sb26/list.txt','-c','copy','/tmp/sb26/body.mp4'], check=True)

s4, s5, s6 = starts[3], starts[4], starts[5]
line_starts = [l[0]['s'] for l in lines if l[0]['s'] > 0.08][:6]
booms = [(0.12,0.9), (s5+0.03,1.0), (s6,0.9)]
whooshes = [0.0] + [round(s-0.12,2) for s in starts[1:]]
riser = max(0.2, s5-1.5)
ep.mix_audio('/tmp/sb26/voce.wav', [(0.0,TOTAL)], TOTAL, '/tmp/sb26/mix.wav',
             pops=line_starts, booms=booms, whooshes=whooshes, riser_at=riser,
             drone_gain=0.10, pop_gain=0.16)
overlays = [('/tmp/sb26/hook.png', 150, 0.0, min(2.1, starts[1])),
            ('/tmp/sb26/like.png', 1690, 0.0, 2.0),
            ('/tmp/sb26/big.png', 700, s6+0.15, min(TOTAL-0.3, s6+1.5))]
shake = [(0.12,12), (s4,14), (s5,16), (s6,14)]
ep.render_overlays('/tmp/sb26/body.mp4', '/tmp/sb26/vid.mp4', TOTAL, overlays, '/tmp/sb26/logo.png', shake, caps)
ep.mux('/tmp/sb26/vid.mp4', '/tmp/sb26/mix.wav', '/tmp/sb26/raw.mp4')
import autoeditor
r = autoeditor.calibreaza_lufs(FF, '/tmp/sb26/raw.mp4'); print('LUFS:', r)
fin = '/home/user/autoeditor/SHORT_BOSS_FURAT.mp4'
subprocess.run(['cp', '/tmp/sb26/raw_cal.mp4' if os.path.exists('/tmp/sb26/raw_cal.mp4') else '/tmp/sb26/raw.mp4', fin], check=True)
print('FINAL:', fin, os.path.getsize(fin)//1024, 'KB')
