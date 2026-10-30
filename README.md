# AutoEditor — iZentric

> **Automatizarea este inclusa:** nu mai este necesara incarcarea manuala a
> fisierelor Actions. `docs/WORKFLOWS_PENDING.patch` este doar o copie istorica;
> nu o reaplica. Testele de cod nu inlocuiesc verificarea unui episod real.

Dintr-un live: episoade de aproximativ 3 minute, shorts de 16 secunde,
miniaturi din cadre reale si fisiere cu titlu/descriere. Randarea se face
pe GitHub Actions; livrarea este in Releases.

## Ce pastreaza editorul

- O poveste clara, un singur joc, titlu sustinut de imagini.
- Sunetele tale, alese dupa evenimente — nu efecte aleatorii.
- Subtitrari galbene doar la replicile importante; subtitrarea completa separat.
- Export 2K, audio verificat; fara watermark, confetti sau zoom-uri aleatorii.
- Fara episoade neverificate doar ca sa existe o livrare.

## Analizeaza sunetele unui video de referinta

Ruleaza `python sunete_referinta.py "https://www.youtube.com/watch?v=..."` pentru un raport cu sunete/meme-uri, posibile melodii, potriviri cu biblioteca locala si cautari pe YouTube/Freesound/Pixabay. Pentru numele exact al pieselor e necesar un token AudD optional; detalii, configurare si limite: [docs/SUNETE_REFERINTA.md](docs/SUNETE_REFERINTA.md). Nu descarca automat efecte si nu verifica licentele rezultatelor.

AI-ul poate gresi. Prima livrare trebuie vizionata si ascultata pentru calibrare;
nu promitem editare perfecta sau timpi de procesare nemasurati.

## Ce faci tu

1. Setare unica: urmeaza [GH_SETUP.md](GH_SETUP.md). Cheile se pun **numai in Secrets**.
2. Pentru un live nou: release `vod-N`, cu inregistrarea originala atasata.
3. Primesti titlul si linkul de descarcare. Tu decizi cand publici pe YouTube.

Live-ul `vod-1` si cele 10 sunete existente nu trebuie retrimise.
Incarcarea privata pe YouTube este separata de editare si necesita activare explicita.

## Unde este fiecare lucru

| Folder / fisier | Rol |
|---|---|
| `sunete_mele/` | Originalele tale + regulile din `catalog.json`; nu se sterg sau modifica automat |
| `sunete_referinta.py` | Analizeaza audio dintr-un link/fisier si cauta piese/SFX similare fara sa descarce efecte |
| `assets/` | Elemente optionale; nimic nou nu se descarca automat ca efect |
| `cunoastere/` | Stilul canalului, transcripte, reguli si istoric editorial |
| `episodes/` | Rezultate generate — nu se comit in Git |
| `.cache/` | Analize reutilizabile — nu se comit in Git |
| `tests/` | Teste fara chei, API real sau randari de VOD |

## Verificare pentru dezvoltare

```sh
python -m unittest discover -s tests -v
python -m compileall -q .
```

- [Operare si optimizari](docs/OPERARE.md)
- [Autorizare YouTube pe PC, fara tokenuri in chat](docs/AUTORIZARE_YOUTUBE.md)
- [Securitate si chei expuse](SECURITY.md)
- [Instructiuni pentru agent](AGENTS.md)
- [Memoria sesiunilor](MEMORY.md) · [Istoric complet](ISTORIC_COMPLET.md)
- [Documentatia versiunilor vechi](docs/ISTORIC_README.md)

Scripturile locale vechi raman pentru compatibilitate; fluxul principal este
`.github/workflows/episod.yml` → `pipeline_github.py`. Nu se proceseaza VOD-uri
in sandbox. Un commit local sau teste verzi nu inseamna ca versiunea este
publicata pe GitHub: verifica rezultatul push-ului si ramura folosita de Actions.
