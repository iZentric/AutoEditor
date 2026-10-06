# ELEMENTELE LUI JOCURI HORROR SKY — TĂIATE 1:1 (iei, nu refaci)

**Nimic aici nu e generat, redesenat sau „inspirat".** Sunt decupaje pixel-cu-pixel din
thumbnail-urile lui ORIGINALE (`refs/brand_1la1/JocuriHorrorSky_*.jpg`, salvate byte-cu-byte
de pe i.ytimg). Fiecare dosar = UN thumbnail de-al lui, cu elementele lui:

```
elemente_brand/JH/<thumbnail>/
  _SURSA.jpg      <- thumbnailul lui, intreg (sa compari: elementul e IDENTIC cu ce e acolo)
  BULA_CUVANT.png <- balonul/bula cu cuvantul EXACT folosit de el
  CERC_x_y.png    <- cercul rosu de highlight, exact ala
  SAGEATA_x_y.png <- sageata/„linia" care arata, exact aia
  SEMN_*.png      <- semnatura lui repetata (OHIO, WELCOME TO, STRICT, TikTok)
```

78 de elemente din 15 thumbnail-uri. `OCR ✔` = cuvantul a fost recitit cu OCR DIN PNG-ul
decupat (deci decupajul e bun). `de verificat` = OCR n-a putut confirma (text stilizat) —
uite-te la el in galerie.

## CE CUVINTE ARE FIECARE THUMBNAIL (lista lui de cuvinte)
| Thumbnail-ul lui | Cuvinte (bulele lui) | Ce are in dosar |
|---|---|---|
| `JocuriHorrorSky_2CSW8Yx7Peo` | **24, OHIO, ORE, SCOALA DIN, WELCOME TO** | 3 bula, 3 semn/logo_jh, 1 cerc |
| `JocuriHorrorSky_74YDp-LVi6Q` | **240RE, OHIO, WELCOME TO** | 1 bula, 2 semn/logo_jh, 1 sageata |
| `JocuriHorrorSky_8BxmOBKt84I` | **FUGI!, OHIO** | 1 bula, 1 semn/logo_jh, 1 sageata, 2 cerc |
| `JocuriHorrorSky_F2S4d-wedWM` | **AJUTOR, OHIO, WELCOME TO** | 1 bula, 2 semn/logo_jh, 1 sageata |
| `JocuriHorrorSky_MerQRetwZKM` | **CE?** | 1 bula, 2 sageata |
| `JocuriHorrorSky_TX1MAv0zXrI` | **10RA, CE?, OHIO, WELCOME TO** | 2 bula, 4 semn/logo_jh |
| `JocuriHorrorSky_auNYTQ4k-hI` | **OHIO, STRICT, TATA?, WELCOME TO** | 1 bula, 4 semn/logo_jh, 1 sageata |
| `JocuriHorrorSky_cP2H14-G_Wk` | **COPIL, OHIO, PROST, WELCOME TO** | 2 bula, 2 semn/logo_jh, 1 sageata |
| `JocuriHorrorSky_hSfHO5r7lZk` | **FINAL, OHIO, STRICT, WELCOME TO** | 1 bula, 4 semn/logo_jh |
| `JocuriHorrorSky_jWsJyQ9yKHQ` | **FILM, MORI, STRICT** | 2 bula, 2 semn/logo_jh, 1 sageata, 1 cerc |
| `JocuriHorrorSky_rV5R3qiMc0Q` | **CE FACI ?, Q0, STRICT** | 2 bula, 1 semn/logo_jh, 2 sageata |
| `JocuriHorrorSky_t2L6AnKJDjE` | **FINAL, OHIO, STRICT, WELCOME TO** | 1 bula, 4 semn/logo_jh |
| `JocuriHorrorSky_tvANsruR1MU` | **DRACULASS, LUMEA LUI, OHIO, SI, SKY, WELCOME TO** | 4 bula, 2 semn/logo_jh, 1 sageata |
| `JocuriHorrorSky_uDh7jW4UtCE` | **CU CAPRA, OHIO, ORA, WELCOME TO** | 2 bula, 2 semn/logo_jh, 1 sageata |
| `JocuriHorrorSky_y7lGqnObc3o` | **10RA, OHIO, TikTok, WELCOMET** | 1 bula, 3 semn/logo_jh, 1 sageata |

## REGULA DE FOLOSIRE (cum le foloseste agentul mai tarziu)
Cand facem un thumbnail pentru iZentric: alegem tema → luam dosarul lui cu cuvantul care se
potriveste (FUGI! / AJUTOR / CE? / TATA? / MORI / FINAL / COPIL PROST / CE FACI?) → lipim
**bula lui, cercul lui, sageata lui** peste scena noastra. Ajustam doar marimea si pozitia.
Nu scriem text nou, nu desenam cercuri noi, nu regeneram semnele.

```bash
python3 tools/thumb_brand.py SCENA.jpg --out THUMB.jpg \
  --balon "elemente_brand/JH/JocuriHorrorSky_8BxmOBKt84I/BULA_FUGI!.png:300:150:430" \
  --pune   "elemente_brand/JH/JocuriHorrorSky_8BxmOBKt84I/SAGEATA_570x542.png:900:600:400" \
  --pune   "elemente_brand/JH/JocuriHorrorSky_8BxmOBKt84I/CERC_324x224.png:640:400:230" \
  --ntag iZentric:700:110 --logo pokecity --test120
```

## CUM MAI SCOTI ALTELE (cand punem thumbnail-uri noi in biblioteca)
```bash
python3 tools/extrage_elemente_jh.py                    # tot JocuriHorrorSky din biblioteca
python3 tools/extrage_elemente_jh.py --canal dagar      # sau alt canal
python3 tools/extrage_elemente_jh.py --fisier NUME.jpg  # unul singur
```
