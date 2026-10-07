# Minecraft pe telefon — reparații (iZentric filmează pe Samsung A20e)

## Echipamentul (din logul real, mclo.gs/loTtPic, 07.10.2026)

| | |
|---|---|
| Dispozitiv | Samsung **SM-A202F** (Galaxy A20e), **Exynos 7884B**, arm64 |
| Android | 11 (API 30) |
| Launcher | **Zalith Launcher 2.6.1** (com.movtery.zalithlauncher.v2) |
| Instanță | `A20e ULTIMATE 1.21.4 FPS MAX` |
| Minecraft | 1.21.4, Fabric loader 0.16.13 |
| Java | **Internal-21** (Java 21) |
| RAM alocat | **-Xmx936M** (strâmt! telefonul are ~2-3 GB) |
| Renderer | opengles3 / libng_gl4es (Krypton Wrapper), 1560x720 |

## Eroarea: „Incompatible mods found!” (jocul nu pornește deloc)

```
- Mod 'More Culling' (moreculling) 1.2.10 requires version 16.0.0 or later of cloth-config, which is missing!
- Mod 'Concurrent Chunk Management Engine (Optimizations/Natives Math)' (c2me-opts-natives-math)
  requires version 22 or later of 'OpenJDK 64-Bit Server VM' (java), but only 21 is present!
```

### Rețeta (în ordine)

1. **Instalează Cloth Config pentru 1.21.4 Fabric** — exact varianta bună:
   `cloth-config-17.0.144-fabric.jar` (1,15 MB, 13 dec 2024)
   https://cdn.modrinth.com/data/9s6osm5g/versions/TJ6o2sr4/cloth-config-17.0.144-fabric.jar
   (pagina: https://modrinth.com/mod/cloth-config/version/17.0.144+fabric )
   → Zalith Launcher → instanță → **Mods** → importă jarul.
2. **Șterge/dezactivează `c2me-opts-natives-math-*.jar`**. Cere Java 22, telefonul are 21.
   Varianta sigură pe 936 MB RAM: **șterge toate jar-urile `c2me-*`** — C2ME e făcut pentru
   servere mari, mănâncă RAM și pe arm64 poate crăpa nativ.
   Dacă vrei neapărat C2ME: lasă doar `c2me-base` + modulele care nu cer Java 22 și testează.
3. **Restart** jocul.

Dacă tot apare ceva: mai simplu e să ștergi `moreculling` cu totul (e opțional) — dar pe
A20e merită păstrat, ajută la FPS; de-aia se instalează cloth-config, nu se scoate More Culling.

## De reținut

- Zalith Launcher pornește cu **Java 21**; orice mod care cere Java 22+ nu merge, orice ai face.
- RAM: 936 MB e la limită. Dacă jocul se închide singur la generarea lumii → scade
  render distance / simulation distance, nu crește Xmx (telefonul n-are de unde).
- Logurile se pun pe https://mclo.gs și se trimit agentului — citește singur, în 30 de secunde.

## Istoric

- 07.10.2026 — log #loTtPic: More Culling fără cloth-config + c2me-opts-natives-math cu Java 21.
  Fix: cloth-config 17.0.144 + scos modulele C2ME.
