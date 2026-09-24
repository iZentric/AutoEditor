# INVATARE AUTOMATA: la fiecare rulare citeste CE A PUBLICAT concurenta recent
# (RSS oficial YouTube = fara chei, fara cookies, nu moare) + distileaza formulele
import subprocess, sys, time
import xml.etree.ElementTree as ET

CANALE = [("JocuriHorrorSky", "UC7Tmdxj18fdu4tTtxVUhoCA"),
          ("iSilent", "UC4tcRE6ezR1ChjNUHM0kbmA")]   # top kids-gaming RO (verificate: 1.33M / 1.67M subs)
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/141.0.0.0 Safari/537.36"

def rss_canale(handle, cid=""):
    """RSS oficial: ultimele ~15 video-uri cu VIEWS (media:statistics)."""
    import urllib.request
    url = (f"https://www.youtube.com/feeds/videos.xml?channel_id={cid}" if cid
           else f"https://www.youtube.com/feeds/videos.xml?user={handle}")
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    root = ET.fromstring(urllib.request.urlopen(req, timeout=30).read())
    ns = {"a": "http://www.w3.org/2005/Atom", "m": "http://search.yahoo.com/mrss/"}
    iesiri = []
    for e in root.findall("a:entry", ns):
        titlu = (e.findtext("a:title", default="", namespaces=ns) or "").strip()
        pub = e.findtext("a:published", default="", namespaces=ns)[:10]
        st = e.find("m:community/m:statistics", ns)
        views = int(st.get("views", "0")) if st is not None else 0
        if titlu:
            iesiri.append((views, titlu, pub))
    return iesiri

def tab_canal(handle, n=25):
    """Rezerva: yt-dlp flat pe /videos (uneori merge si pe servere)."""
    try:
        r = subprocess.run([sys.executable, "-m", "yt_dlp", "--flat-playlist",
                            "--playlist-items", str(n), "-J", "--no-warnings",
                            f"https://www.youtube.com/@{handle}/videos"],
                           capture_output=True, text=True, timeout=60)
        d = __import__("json").loads(r.stdout or "{}")
        return [(int(e.get("view_count") or 0), e.get("title") or "", "")
                for e in (d.get("entries") or []) if e.get("title")]
    except Exception:
        return []

def distileaza():
    import os
    linii, tot_bun = [], []
    # canale extra pot fi adaugate de creator in cunoastere/canale_extra.txt (un ID per linie)
    extra = []
    p_ex = "cunoastere/canale_extra.txt"
    if os.path.exists(p_ex):
        extra = [(f"extra-{i+1}", l.strip()) for i, l in enumerate(open(p_ex, encoding="utf-8"))
                 if l.strip().startswith("UC") and len(l.strip()) > 20]
    for nume, cid in CANALE + extra:
        tab = tab_canal(nume)                      # views (uneori partial)
        try:
            rss = rss_canale(nume, cid)            # titluri + date (sigur)
        except Exception:
            rss = []
        combined = {t.lower().strip(): [v, t, p] for v, t, p in tab}
        for v, t, p in rss:                        # RSS completeaza (date) si adauga ce lipseste
            k = t.lower().strip()
            if k in combined:
                if not combined[k][0]:
                    combined[k][0] = v
                if not combined[k][2]:
                    combined[k][2] = p
            else:
                combined[k] = [v, t, p]
        videouri = sorted(combined.values(), key=lambda x: x[2] or "", reverse=True)
        if len(videouri) < 3 and not videouri:
            videouri = tab or rss
        if not videouri:
            linii.append(f"## {nume}: n-am putut citi acum (continuam fara)")
            continue
        cu_views = sorted(v for v, _, _ in videouri if v > 0)
        med = cu_views[len(cu_views) // 2] if cu_views else 0
        top = sorted(videouri, key=lambda x: -x[0])[:6]
        linii.append(f"## {nume} — CE A PUBLICAT RECENT (citit ACUM: tab={len(tab)}, rss={len(rss)}):")
        for v, t, p in videouri[:10]:
            rap = (v / med) if med else 0
            stea = " ⭐HIT(2x mediana)" if med and rap >= 2 else ""
            linii.append(f"- [{p or 'recent'}] {v:,} views · {t}{stea}")
        if not med:
            linii.append("  (views inca 0 la clipurile foarte proaspete — foc pe TITLURI si frecventa)")
        else:
            b = top[0]
            linii.append(f"  -> MEDIE ~{med:,} · CEL MAI TARE ACUM: \"{b[1]}\" ({b[0]:,} views)")
        linii.append("")
        tot_bun += [(v, t) for v, t, _ in videouri]
    if tot_bun:
        cuv = {}
        for _, t in tot_bun:
            for w in t.upper().replace("!", "").replace("?", "").replace("…", "").replace('"', "").split():
                if len(w) >= 4 and not w.islower():
                    cuv[w] = cuv.get(w, 0) + 1
        frecvente = sorted(cuv.items(), key=lambda x: -x[1])[:12]
        if frecvente:
            linii.append("## CUVINTE-CHEIE CARE CUCERESC ACUM (frecventa in titluri recente):")
            linii.append(", ".join(f"{w}({c})" for w, c in frecvente))
    md = ("# TRENDING RO KIDS-GAMING (invatat automat la aceasta rulare din RSS oficial)\n\n"
          + "\n".join(linii) + "\n")
    open("cunoastere/trending_ro.md", "w", encoding="utf-8").write(md)
    print(f"LEARNING OK: {len(tot_bun)} video-uri analizate -> cunoastere/trending_ro.md", flush=True)

if __name__ == "__main__":
    for i in range(2):           # o reincercare blanda daca netul sale
        try:
            distileaza()
            break
        except Exception as ex:
            print(f"  incercare {i+1} a picat: {str(ex)[:60]}", flush=True)
            time.sleep(5)
    else:
        print("trending n/a -> rulam fara (fallback in pipeline nu opreste nimic)", flush=True)
