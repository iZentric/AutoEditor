# ELEMENTELE LUATE 1:1 DE LA JOCURI HORROR SKY (iei, nu refaci)

Toate sunt **decupaje din thumbnail-urile lui REALE** (originalele byte-cu-byte sunt in
`refs/brand_1la1/JocuriHorrorSky_*.jpg`). NU sunt regenerate, NU sunt redesenate, NU sunt AI.
Fundal transparent (PNG RGBA), gata de lipit peste orice scena.

Continut: **12 bule cu cuvinte** · **13 sageti/„linii"** · **4 cercuri rosii** · 30 semne/logouri
(OHIO, WELCOME TO, STRICT, TikTok = semnatura lui repetata).

## CE CUVINTE FOLOSESTE EL (bulele lui, verificate cu OCR)
| Cuvant | Din thumbnail-ul | Fisier |
|---|---|---|
| **AJUTOR** | JocuriHorrorSky_F2S4d-wedWM.jpg | `BULA_AJUTOR_-wedWM.png` |
| **CE?** | JocuriHorrorSky_MerQRetwZKM.jpg | `BULA_CE?_etwZKM.png` |
| **COPIL** | JocuriHorrorSky_cP2H14-G_Wk.jpg | `BULA_COPIL_4-G_Wk.png` |
| **FILM** | JocuriHorrorSky_jWsJyQ9yKHQ.jpg | `BULA_FILM_Q9yKHQ.png` |
| **FINAL** | JocuriHorrorSky_hSfHO5r7lZk.jpg | `BULA_FINAL_5r7lZk.png` |
| **FINAL** | JocuriHorrorSky_t2L6AnKJDjE.jpg | `BULA_FINAL_nKJDjE.png` |
| **FUGI!** | JocuriHorrorSky_8BxmOBKt84I.jpg | `BULA_FUGI!_BKt84I.png` |
| **MORI** | JocuriHorrorSky_jWsJyQ9yKHQ.jpg | `BULA_MORI_Q9yKHQ.png` |
| **PROST** | JocuriHorrorSky_cP2H14-G_Wk.jpg | `BULA_PROST_4-G_Wk.png` |
| **SCOALA DIN** | JocuriHorrorSky_2CSW8Yx7Peo.jpg | `BULA_SCOALADIN_Yx7Peo.png` |
| **SI** | JocuriHorrorSky_tvANsruR1MU.jpg | `BULA_SI_ruR1MU.png` |
| **TATA?** | JocuriHorrorSky_auNYTQ4k-hI.jpg | `BULA_TATA?_Q4k-hI.png` |

## CE INSEAMNA ASTA PENTRU NOI (regula de aur a bossului)
Cand facem un thumbnail pentru iZentric, **bula vine de aici**, cu unul din cuvintele lui
(scurte, 1-2 cuvinte, gen FUGI! / AJUTOR / CE? / TATA? / MORI / FINAL), ajustata pe scena noastra.
Nu scriem texte lungi, nu inventam fonturi: copiem semnul lui, il punem pe personajele noastre.

## CUM IL LIPESTI
```bash
python3 tools/thumb_brand.py SCENA.jpg --out THUMB.jpg \
  --balon "elemente_brand/JH/BULA_FUGI!_BKt84I.png:300:150:430" \
  --ntag iZentric:700:110 --ntag Mocivanu:1000:110 \
  --cerc 664:500:130 --logo pokecity --test120
```
(`CALE:x:y:latime` — x,y = centrul bulii in cadrul 1280x720.)

## CERCUL SI SAGEATA („ala de arata")
| Fisier | Din | Marime |
|---|---|---|
| `CERC_Yx7Peo_177x406.png` | JocuriHorrorSky_2CSW8Yx7Peo.jpg | 239x219 |
| `CERC_BKt84I_801x29.png` | JocuriHorrorSky_8BxmOBKt84I.jpg | 256x235 |
| `CERC_BKt84I_324x224.png` | JocuriHorrorSky_8BxmOBKt84I.jpg | 216x182 |
| `CERC_Q9yKHQ_1143x224.png` | JocuriHorrorSky_jWsJyQ9yKHQ.jpg | 138x187 |
| `SAGEATA_-LVi6Q_114x70.png` | JocuriHorrorSky_74YDp-LVi6Q.jpg | 265x543 |
| `SAGEATA_BKt84I_570x542.png` | JocuriHorrorSky_8BxmOBKt84I.jpg | 711x179 |
| `SAGEATA_-wedWM_503x474.png` | JocuriHorrorSky_F2S4d-wedWM.jpg | 80x167 |
| `SAGEATA_etwZKM_1210x364.png` | JocuriHorrorSky_MerQRetwZKM.jpg | 71x357 |
| `SAGEATA_etwZKM_645x112.png` | JocuriHorrorSky_MerQRetwZKM.jpg | 73x185 |
| `SAGEATA_Q4k-hI_832x630.png` | JocuriHorrorSky_auNYTQ4k-hI.jpg | 166x91 |
| `SAGEATA_4-G_Wk_987x108.png` | JocuriHorrorSky_cP2H14-G_Wk.jpg | 67x173 |
| `SAGEATA_Q9yKHQ_232x364.png` | JocuriHorrorSky_jWsJyQ9yKHQ.jpg | 866x357 |
| `SAGEATA_qiMc0Q_810x120.png` | JocuriHorrorSky_rV5R3qiMc0Q.jpg | 230x121 |
| `SAGEATA_qiMc0Q_412x317.png` | JocuriHorrorSky_rV5R3qiMc0Q.jpg | 64x255 |
| `SAGEATA_ruR1MU_26x485.png` | JocuriHorrorSky_tvANsruR1MU.jpg | 324x136 |
| `SAGEATA_W4UtCE_412x407.png` | JocuriHorrorSky_uDh7jW4UtCE.jpg | 71x314 |
| `SAGEATA_nObc3o_6x499.png` | JocuriHorrorSky_y7lGqnObc3o.jpg | 556x222 |

## CUM REFACI / EXTINZI LIBRARIA
```bash
python3 tools/extrage_elemente_jh.py                     # toate JocuriHorrorSky
python3 tools/extrage_elemente_jh.py --canal dagar       # sau alt canal din biblioteca
python3 tools/extrage_elemente_jh.py --fisier NUME.jpg   # unul singur
```
Fiecare element e verificat prin OCR: daca OCR nu mai citeste cuvantul DUPA decupare,
elementul e aruncat (nu livra gunoaie).
