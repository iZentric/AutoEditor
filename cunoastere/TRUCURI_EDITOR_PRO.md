# TRUCURI EDITOR PRO — implementate 25.09.2026 (surse: documentul MrBeast scurs via markstudios.com, filmora/voice123/packapop guides 2026)

## Ce am adaugat in motor (autoeditor.py):
1. **DUCKING (sidechaincompress)**: muzica de fundal coboara AUTOMAT cand creatorul vorbeste (threshold 0.02, ratio 6, attack 25ms, release 350ms). Vocea e mereu clară — regula de mixaj pro (-6..-12 LUFS dialog).
2. **SILENTIUL DE PAYOFF (MrBeast)**: 0.75s de liniste totala (muzica la 0.1%) imediat INAINTE de momentul maxim (START_P3). Revele-ul loveste de 2x mai tare.
3. **ACCENTE PLANIFICATE din biblioteca creatorului** (nu doar random): "whoosh trecere" la trecerea dintre acte (START_P2-1.2s), "riser tensiune" 10s inainte de explozie (cand slotul hype e gol) — pattern-interrupt SFX care anunta ca CEVA vine.
4. **FADE IN/OUT video**: 0.25s la intrare, 0.6s la final — standard editorial (fara asta clipul "taie" brutal).

## Ce exista deja si e dovedit (nu se renunta):
- Cold open cu explozia langa inceput (primele 60s = cele mai importante — MrBeast doc).
- Pops galbene doar la momente-cheie (max 6) — text nu acopera replici.
- 3-4 muzici pe scena? -> avem 1 muzica consistenta pe tot episodul (consistent music bed = nu anunta "boring section").
- Cut doar cu intentie; final elastic 90s+.
- Loudnorm -14 LUFS master, -16 pre-mix; shorturi -16/-14.

## INTERZISE (regulile creatorului — nu le incalca niciun truc):
- zoom default OFF (AE_ZOOM=0), confetti OFF, watermark OFF, doar gameplay real.

## De facut cand avem date (faza 2):
- Citit retention graph din YT Studio dupa fiecare upload -> ajustare puncte de re-engagement.
- Beat-sync exact (detctie BPM) — complex, doar daca retentia cere.
- Re-engagement beat la 1/3 si 2/3 (avem whoosh la act-2; explozia e la ~2/3) — deja aproximat de structura 4 acte.
