
## METODA CÂȘTIGĂTOARE (validată vizual 06-10-2026, THUMB_SWAP_31M_FINAL.jpg)
DECOUPARE MANUALĂ = EȘUAT (flood-fill mănâncă hanoracul alb / lasă fundal pătrat — NU mai încerca).
METODA CORECTĂ = EDITAREA AI CU AMBELE IMAGINI:
  Image A = thumbnail-ul de referință (31M) | Image B = masterul cu personajele noastre
  Prompt: "replace ONLY the heads with the two characters from image 2, redrawn in image 1's
  exact 3D Minecraft style; keep EVERYTHING else EXACTLY identical (grass, dotted outlines,
  shadows, positions, sizes, tilts); NO text/nametags/logos".
  → apoi stratul UMAN în Pillow: nametag-uri Monocraft + orice bulă/cerc/săgeată cerută.
Verificare: capetele în ACELEAȘI poziții/mărimi ca originalele; conceptul intact.
