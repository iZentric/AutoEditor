# UPLOAD AUTOMAT pe YouTube (Data API v3) — porneste DOAR daca exista Secretele:
#   YT_CLIENT_ID + YT_CLIENT_SECRET + YT_REFRESH_TOKEN  (OAuth, setate de creator)
# Episoadele + shorturile intra PUBLIC, cu titlu/descriere din *_upload.txt.
# Reguli canal respectate: FARA madeForKids (comentarii deschise), categoria Gaming.
import glob, os, sys

def citeste_upload_txt(cale):
    titlu, desc = None, []
    sec = None
    for l in open(cale, encoding="utf-8"):
        l = l.rstrip("\n")
        if l.startswith("TITLU:"):
            titlu = l.split(":", 1)[1].strip(); sec = None
        elif l.startswith("DESCRIERE:"):
            sec = "d"
        elif l.strip() == "" and sec == "d":
            sec = None
        elif sec == "d" and l.strip():
            desc.append(l)
    return titlu, "\n".join(desc).strip() or titlu

def principal():
    need = ["YT_CLIENT_ID", "YT_CLIENT_SECRET", "YT_REFRESH_TOKEN"]
    if not all(os.environ.get(k) for k in need):
        print("UPLOAD YT: skip (lipsesc Secretele OAuth — episodul asteapta in Releases)", flush=True)
        return
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    import requests

    creds = Credentials(token=None, refresh_token=os.environ["YT_REFRESH_TOKEN"],
                        client_id=os.environ["YT_CLIENT_ID"],
                        client_secret=os.environ["YT_CLIENT_SECRET"],
                        token_uri="https://oauth2.googleapis.com/token")
    creds.refresh(Request())
    yt = build("youtube", "v3", credentials=creds)
    ch = yt.channels().list(part="contentDetails,statistics", mine=True).execute()
    it = ch["items"][0]
    print(f"canal: {it['snippet']['title']} ({it['statistics'].get('subscriberCount','?')} subs)", flush=True)

    fisiere = sorted(glob.glob("episodes/EP*.mp4")) + sorted(glob.glob("episodes/SHORT*.mp4"))
    fisiere = [f for f in fisiere if "_miniatura" not in f]
    publicate = []
    for f in fisiere:
        txt = f[:-4] + "_upload.txt"
        if not os.path.exists(txt):
            print(f"  skip {f} (fara upload.txt)"); continue
        titlu, desc = citeste_upload_txt(txt)
        if not titlu:
            print(f"  skip {f} (upload.txt fara titlu)"); continue
        mini = f[:-4] + "_miniatura.jpg"
        body = {"snippet": {"title": titlu[:100], "description": desc[:4900],
                            "categoryId": "20", "defaultLanguage": "ro",
                            "defaultAudioLanguage": "ro"},
                "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False}}
        media = MediaFileUpload(f, chunksize=8 * 1024 * 1024, resumable=True)
        req = yt.videos().insert(part="snippet,status", body=body, media_body=media)
        rasp = None
        while rasp is None:
            stare, rasp = req.next_chunk()
            if stare:
                print(f"  {os.path.basename(f)}: {int(stare.progress()*100)}%", flush=True)
        vid = rasp["id"]
        if os.path.exists(mini):
            requests.put(f"https://www.googleapis.com/upload/youtube/v3/thumbnails/set"
                         f"?videoId={vid}", headers={"Authorization": f"Bearer {creds.token}"},
                         data=open(mini, "rb").read(), timeout=120)
        publicate.append((f, titlu, vid))
        print(f"  PUBLICAT: {titlu} -> https://youtu.be/{vid}", flush=True)
    if publicate:
        linii = "\n".join(f"- [{t}](https://youtu.be/{v})" for _, t, v in publicate)
        open("episodes/PUBLICATE_ON_YT.md", "w", encoding="utf-8").write(
            "# Publicate automat pe YouTube\n\n" + linii + "\n")
        print(f"UPLOAD YT GATA: {len(publicate)} video-uri live pe canal", flush=True)

if __name__ == "__main__":
    try:
        principal()
    except Exception as ex:
        print(f"UPLOAD YT a esuat ({str(ex)[:120]}) — fisierele raman in Releases", flush=True)
        sys.exit(0)   # NU stricam pipeline-ul pentru upload
