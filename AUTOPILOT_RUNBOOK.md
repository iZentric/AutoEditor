# AUTOPILOT RUNBOOK — divizia muncii (ordin Overlord 2026-10-04)
**CONTRACT**: USERUL face DOAR live-uri și dă „DA". AGENTUL face TOT restul. Maxim în orice.

## DIVIZIA MUNCII
| ACTOR |.face |
|---|---|
| **OVERLORD (user)** | 1) INTRĂ PE LIVE (joacă MC/Roblox). 2) Zice „DA" la ce-i pregătesc. ATÂT. |
| **DEMIURG (agent)** | research net zilnic • trending RO+MD watch • titluri (doctrina MrBeast) • miniaturi (3/EP, Test&Compare, verificare vizuală) • edit EP-uri (EDIT_DNA: 7%/44%/end-spike) • shorturi 16s loop • descrieri/taguri kw • ore de postare • postări comunitate • răspunsuri comentarii (plan JSON) • comentariu fixat • tracker zilnic • QC 8/8 • Releases • raport % zilnic |

## CE RULEĂ SINGUR (fără nicio acțiune a userului)
1. **Detectare live AUTOMATĂ** — creier_shorturi mod AUTO (CANAL_STREAMS pe ID permanent, 54 live-uri testate): userul intră pe live FĂRĂ să anunțe → agentul îl vede, alege live-ul + momentele nefolosite (manifest ±90s, zero repetiții)
2. **Tracker zilnic** — ab/views/creștere (istoric.jsonl, măsurători multiple/zi)
3. **Senzori trending** — RO gaming 50 + MD 49 + global, cu sesiune logată
4. **Pregătire kit-uri** — coada min. 2 EP-uri complete (titlu+thumb+desc+taguri+fixat+postare)
5. **Planuri comentarii** — JSON gata de executat (max 2 propoziții + 1 emoji, ≤40/zi)

## CE AȘTEAPTĂ DOAR „DA"
- Upload public (EP/short) • postare comunitate • răspuns comentariu publicat • A/B thumb schimbat

## CALENDAR STANDARD ZILNIC (ora RO = ora MD)
| Ora | Acțiune |
|---|---|
| 10:00–11:00 (weekend) | EP sau short weekend |
| **16:00** | **EP/SHORT PRINCIPAL** (copiii ies din școală) |
| 16:30 | postare comunitate + perete-spoiler (la EP) |
| **17:30** | **al doilea short** (dacă există în rotație) |
| 18:00 | comentariu fixat „Ce prindem în EP următor?" + primul val răspunsuri comentarii |
| seară | tracker + raport % pentru Overlord |

## PROTOCOL LIVE → PRODUSE (automat la fiecare live al userului)
1. AUTO detectează live-ul (și momentele nefolosite din manifest)
2. Randare shorturi 16s (fallback VPS dacă cloud-ul e blocat) — 1–2 buc/live
3. Kit: titlu DNA + pops la timpii VTT + SFX + logo POKECITY + −14 LUFS + QC 8/8 + verificare vizuală
4. „DA?" → publicat la ora din calendar → tracker măsoară → raport

## STAREA MACHINEI (2026-10-04)
- ✅ creier AUTO (54 live-uri) • tracker (4 măsurători azi) • trending logat • EDIT_DNA + STRATEGIE_100 comise
- ⚠️ cookies server expirate pt comentarii → re-export user în SECRET (o singură dată); între timp agentul scanează local
- 🔒 GATE: „DA EPISOD 1" (kitul e COMPLET: titlu-MrBeast + miniatură + scenariu 7%/44%/end-spike + calendar)
