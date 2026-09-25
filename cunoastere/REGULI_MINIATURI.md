# REGULI MINIATURI — stil canale-top Minecraft (pt copii 8-15)

## DECONSTRUCTIE GANNICUS96 (canal RO MC, 6.9K-29K views in zile — studiat 25.09.2026)
| Element din miniaturile lui | De ce merge |
|---|---|
| Ilustratie 3D cartoon (NU cadru de joc) | arata "plastilina" — copilul recunoaste stilul instant |
| Personajele = skinurile REALE din video (Gani, Pepi, Randunel) | continuitate video->miniatura; stii cine joaca |
| Emotie EXTREMA pe fata (ochi uriasi, gura deschisa) | regulamentul CTR: fata+emotie = click |
| Contur ALB gros tip sticker pe personaje/obiecte | desparte subiectul de fundal = clar la 320px |
| Obiectul din video MARE (diamante, chest, scara curcubeu) | promite exact ce primesti |
| Sageata rosie / „?!" / inimi / „1000X" | tensiune + curiozitate |
| Etichete cu nume (PEPI, GANI, Bebe Gani) | relatie cu personajele = intoarcere |
| Fundal bright saturat (iarba vie, cer albastru, clasa) | culori care lupta cu feed-ul |
| FARA text de titlu pe miniatura (text doar in scena, ex tabla) | conceptul se CITESTE vizual |

## LIFEHACK-URI CTR (cercetare 1of10 / vidiq / thumbnailstudioo, 09.2026)
1. Regula 3 secunde: subiect CLAR + emotie + contrast.
2. UN singur punct focal dominant; restul suport.
3. Text: max 3-4 cuvinte SAU zero (concept vizual).
4. Culori: rosu, galben, albastru electric, verde neon — NU pastel.
5. Test telefon: la 320px subiectul+emotia trebuie sa se vada.
6. Privirea/gestul personajului spre obiectul de interes.
7. Brand constant: acelasi stil la fiecare video = recunoscut in feed.
8. Sageata/linii de miscare creeaza tensiune; split before/after pt transformari.
9. Min 1280x720, sub 2MB.

## REGULA DE AUR A USERULUI (obligatorie)
**Miniatura TREBUIE sa contina chestii DIN VIDEO-UL PRINCIPAL** (personaje/skinuri,
obiecte, evenimentul). Nimic inventat care nu exista in clip.

## SISTEMUL NOSTRU (miniaturi_ai.py, din 25.09.2026)
1. Alegerea #1: **AI Gemini image** (gemini-2.5-flash-image) — primeste 3 cadre REALE
   din momentul-varf (varf-8s, varf, varf+8s) si recreeaza scena EXACTA ca ilustratie
   3D cartoon: aceleasi skinuri+obiecte, emotie extrema, contur alb sticker, sageata
   rosie, fundal bright, ZERO text. Output 1280x720.
2. Fallback: fa_miniatura (cadrul real editat + titlu + sageata) — daca AI pică.
3. ENV: AE_MINIATURI_MODELE = lista modele separate prin virgula.
4. Avatar creator: assets/avatar.png (il urca userul) — pentru Consistenta brand.

## CE MA TREBUIE DE LA CREATOR
- assets/avatar.png = PNG cu fata/skinul din joc (fundal transparent ideal).

## REALITATE QUOTA (25.09.2026, dovedit in Actions)
- Modele image pe cheie (ListModels): gemini-3.1-flash-image, 3.1-flash-lite-image, 3-pro-image, 2.5-flash-image.
- Quota IMAGE = SEPARATA de text si s-a epuizat azi -> 429 pe toate; reset gratuit ~10:00 RO (miezul noptii Pacific).
- gemini-3.6-flash (TEXT) = 503 ocazional -> descrie_scena are retry x3.
- Pollinations.ai (plan B keyless) = cazut 500 la 02:20; ramane in cod, nu e critic.
- LANT FINAL: Gemini image -> descriere+Pollinations -> miniatura clasica (mereu functioneaza).
- Test rapid oricand: Actions -> "Test miniatura AI" -> Run workflow.
