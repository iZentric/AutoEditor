#!/usr/bin/env python3
# EXEMPLU OFICIAL — thumbnail generat integral prin overlay_engine (protocolul bossului)
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from overlay_engine import Engine

e = Engine(
    baza='refs/brand_1la1/UC8Ekc_ZSdRv9kNl3o.jpg',   # baza ytarului (neatinsa)
    scena='scena_swap.png',                           # swap AI fara text
    swap_poly=[(868,370),(1280,370),(1280,720),(868,720)],  # DOAR personajul
)
GURA_RECHIN = (640, 385)   # tinta cercului — centrul geometric
GURA_BOSS   = (1082, 525)  # gura vorbitorului — tinta cozii bulei

e.cerc(tinta=GURA_RECHIN, marime=385)                       # inel centrat geometric
e.sageata(tinta=GURA_RECHIN, start=(1060, 330), lungime=300) # capul -> centrul cercului
e.bula(nume='bula_8BxmOBKt84I_1', tinta_gura=GURA_BOSS,
       start=(1265, 260), marime=215, rot_max=40)            # coada -> centrul gurii
e.nametag('iZentric', poz=(928, 392))                        # nu acopera fata

e.salveaza('thumbnaili/THUMB_RECHIN_ENGINE')
print('OK — vezi thumbnaili/THUMB_RECHIN_ENGINE.png')
