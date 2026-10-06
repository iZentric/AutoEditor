# ELEMENTELE DE BRAND (extrase din masterul aprobat — thumbnail-ul cu bebe Pikachu)
PNG cu FUNDAL TRANSPARENT — se lipesc peste ORICE scenă (în Pillow, Photoshop, Canva, CapCut).

| Fișier | Ce e | Unde se pune (recomandare 1280x720) |
|---|---|---|
| **BALON_JH_real_CE.png** | **balonul REAL cu „CE?" — copiat 1:1 din clipul exact I0NiXn_YVCQ** (refăcut 06-10 după ce originalul a căzut la migrare) | sus-stânga/dreapta, latime ~430px |
| bula_FUGI.png | bula albă + „FUGI!" roșu, contur negru gros | sus-centru (530,10), codita spre cine strigă |
| bula_GOLA.png | bula FĂRĂ text — scrii ce vrei (CE?, NU!, SST!, BĂĂ) | idem |
| nametag_iZentric.png | nametag Minecraft al canalului | deasupra capului personajului tău |
| nametag_Mocivanu.png | nametag Minecraft Mocivanu | deasupra capului lui Mocivanu |
| cerc_rosu.png | inel roșu gros de highlight | pe elementul-mister (rotit/redimensionat liber) |
| sageata_rosie.png | săgeata groasă cu coadă rotundă | dintr-un colț liber, spre acțiune |
| inimi_rosii.png | 4 inimioare (formula Cadres 31M) | între personaje la teme de dragoste |
| PREVIZUALIZARE.jpg | toate pe fond șah | doar ca să le vezi |

REGULI (PROTOCOL_MINIATURI_BRAND.md): bulă = UN cuvânt scurt · nametag NU pe fețe ·
logo de serie DOAR la serie (assets/logo_pokecity_clear.png) · textul NICIODATĂ generat de AI.
Pentru aplicare automată: python tools/thumb_brand.py (le desenează procedural, la fel).

## CUM REFACI ORICE ELEMENT PIERDUT (1:1, fără AI, fără ochi)
1. Găsește textul în bibliotecă:   `python3 tools/ocr_biblioteca.py CE`
   (îți dă fișierul + caseta exactă, ex. `530,41,752,165`)
2. Extrage elementul cu alpha:     `python3 tools/crop_balon.py refs/brand_1la1/FISIER.jpg --box 530,41,752,165 --out elemente_brand/NUME.png --verifica-ocr`
3. Lipește-l pe thumbnail:          `python3 tools/thumb_brand.py SCENA.jpg --out … --balon elemente_brand/NUME.png:x:y:latime`
