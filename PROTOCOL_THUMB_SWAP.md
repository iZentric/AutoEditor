
## METODA CÂȘTIGĂTOARE (validată vizual 06-10-2026, THUMB_SWAP_31M_FINAL.jpg)
DECOUPARE MANUALĂ = EȘUAT (flood-fill mănâncă hanoracul alb / lasă fundal pătrat — NU mai încerca).
METODA CORECTĂ = EDITAREA AI CU AMBELE IMAGINI:
  Image A = thumbnail-ul de referință (31M) | Image B = masterul cu personajele noastre
  Prompt: "replace ONLY the heads with the two characters from image 2, redrawn in image 1's
  exact 3D Minecraft style; keep EVERYTHING else EXACTLY identical (grass, dotted outlines,
  shadows, positions, sizes, tilts); NO text/nametags/logos".
  → apoi stratul UMAN în Pillow: nametag-uri Monocraft + orice bulă/cerc/săgeată cerută.
Verificare: capetele în ACELEAȘI poziții/mărimi ca originalele; conceptul intact.

## ⭐ DIRECTIVA 1:1 A BOSSULUI (06-10-2026) — cum se execută, pas cu pas
1. Baza = FIȘIERUL EXACT din `refs/brand_1la1/` (NU se regenerează compoziția).
2. Swap personaje: `generate_image` cu **Image A = baza 1:1** + **Image B = refs/BRAND_THUMB_MASTER.png**
   (promptul: „replace ONLY the characters… keep EVERYTHING else identical, NO text/bubbles/
   nametags/logos/circles/arrows").
3. Stratul UMAN: `python3 tools/thumb_brand.py … --ntag --bula --cerc --sageata --logo pokecity --test120`
   → 1280x720 + varianta de test 120px.
4. Finisaj automat în thumb_brand.py: culoare 1.08 / contrast 1.05 / claritate 1.22.

**Corecție verificată (nu ghicită): UC8EkcHOycB94lHDkbAPSnQA = @nacho-minecraft (Nacho, 5,8M ab),
NU „Sami".** Bossul l-a numit @SamiMinecraft în directivă → se folosește ID-ul, care e sigur.

**ADEVĂRUL DESPRE „FUNDAL ÎNGHEȚAT"** (măsurat 06-10 cu `tools/gaseste_swap.py`):
modelele de editare NU îngheață fundalul pixel-cu-pixel — re-randează toată imaginea
(la swapul EP1: ~85% din cadru s-a schimbat la nivel de pixel; compoziția, pozițiile și
scara rămân). Deci „1:1" înseamnă **aceeași compoziție/încadrare**, nu identic la pixel.
Dacă bossul vrea fundal IDENTIC la pixel, singura cale reală = decupare/inpainting clasic
(care a EȘUAT deja — vezi mai sus), nu generare.

**Unde punem elementele de brand**: agentul nu vede imaginile → `tools/gaseste_swap.py`
compară baza cu rezultatul și tipărește coordonatele zonelor schimbate (harta de diferențe
16×9). Când modelul re-randează tot, detectia devine zgomotoasă → se folosesc pozițiile
SAFE (bula stânga-sus, nametagurile în banda de sus, cercul pe centrul acțiunii) și
bossul corectează din ochi.

## ⭐ BIBLIOTECA 1:1 (legea de la boss, 06-10-2026) — `refs/brand_1la1/`
61 thumbnail-uri ORIGINALE (byte-cu-byte, descărcate de pe i.ytimg, FĂRĂ nicio regenerare):
top-15 câștigători de la Nocivanu (+ clipul EXACT cerut de boss: I0NiXn_YVCQ), JocuriHorrorSky,
dagar-minecraft, UC8EkcHOycB94lHDkbAPSnQA + INDEX.csv (canal, id, views, titlu, fișier).

### CUM SE FOLOSEȘTE (când bossul cere un thumbnail):
1. Alegi din INDEX.csv modelul cel mai potrivit temei (views + potrivire cuvinte).
2. Iei FIȘIERUL EXACT din bibliotecă — NU îl redesenezi, NU îl regenerezi.
3. Swap DOAR PE PERSONAJE (metoda validată: AI edit cu Image A=modelul 1:1 + Image B=masterul
   cu personajele noastre; "replace ONLY the characters, keep EVERYTHING else EXACTLY identical
   INCLUDING text bubbles, red circles, arrows, nametags — they are ALREADY in the template").
4. Elementele de brand din model (bulă/cerc/săgeată) rămân CE SUNT — nu le mai deseni manual.
5. Livrezi 1280x720 + test 120px.
LEGE: template-urile din brand_1la1 nu se modifică niciodată în sine; se copiază și se
schimbă doar personajele. Bossul prinde ACELAȘI look viral, de fiecare dată.
