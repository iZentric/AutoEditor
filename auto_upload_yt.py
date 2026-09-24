# UPLOAD AUTOMAT pe YouTube (Data API v3) — porneste DOAR daca exista Secretele:
#   YT_UPLOAD_ENABLED=true and OAuth values configured securely in Actions Secrets.
#   Never use credentials copied from chat.
# Episodes and shorts are PRIVATE by default, with metadata from *_upload.txt.
# Reguli canal respectate: FARA madeForKids (comentarii deschise), categoria Gaming.
import glob, os, sys

def citeste_upload_txt(cale):
    """Keep the full multi-paragraph description; blank lines are not section ends."""
    title, description, section = None, [], None
    with open(cale, encoding='utf-8') as stream:
        for line in stream:
            line = line.rstrip('\n')
            if line.startswith('TITLU:'):
                title = line.split(':', 1)[1].strip()
                section = 'title' if not title else None
            elif line.startswith('DESCRIERE:'):
                section = 'description'
                remainder = line.split(':', 1)[1].strip()
                if remainder:
                    description.append(remainder)
            elif line.startswith(('TAG-URI:', 'TAGURI:', 'TAGS:')):
                section = None
            elif section == 'title' and line.strip():
                title, section = line.strip(), None
            elif section == 'description':
                description.append(line)
    return title, '\n'.join(description).strip() or title


def principal():
    if os.environ.get('YT_UPLOAD_ENABLED', 'false').lower() != 'true':
        print('UPLOAD YT: dezactivat. Activeaza numai dupa configurarea sigura a autorizarii.', flush=True)
        return
    need = ["YT_CLIENT_ID", "YT_CLIENT_SECRET", "YT_REFRESH_TOKEN"]
    if not all(os.environ.get(k) for k in need):
        print("UPLOAD YT: skip (lipsesc Secretele OAuth — episodul asteapta in Releases)", flush=True)
        return
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload

    creds = Credentials(token=None, refresh_token=os.environ["YT_REFRESH_TOKEN"],
                        client_id=os.environ["YT_CLIENT_ID"],
                        client_secret=os.environ["YT_CLIENT_SECRET"],
                        token_uri="https://oauth2.googleapis.com/token")
    creds.refresh(Request())
    yt = build("youtube", "v3", credentials=creds)
    ch = yt.channels().list(part="snippet,contentDetails,statistics", mine=True).execute()
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
                "status": {"privacyStatus": "private",
                           "selfDeclaredMadeForKids": False}}
        media = MediaFileUpload(f, chunksize=8 * 1024 * 1024, resumable=True)
        req = yt.videos().insert(part="snippet,status", body=body, media_body=media, notifySubscribers=False)
        rasp = None
        while rasp is None:
            stare, rasp = req.next_chunk()
            if stare:
                print(f"  {os.path.basename(f)}: {int(stare.progress()*100)}%", flush=True)
        vid = rasp["id"]
        if os.path.exists(mini):
            try:
                yt.thumbnails().set(videoId=vid, media_body=MediaFileUpload(
                    mini, mimetype='image/jpeg')).execute()
            except Exception as ex:
                print(f"  Miniatura neaplicata ({type(ex).__name__}); video-ul ramane incarcat privat.")
        publicate.append((f, titlu, vid))
        print(f"  URCAT (privacy={'private'}): {titlu} -> https://youtu.be/{vid}", flush=True)
    if publicate:
        # PLAYLISTUL SPECIAL "FĂCUTE DE AI": toate piesele facute de AI intra aici automat
        try:
            pid = ""
            if os.path.exists("cunoastere/ai_playlist_id.txt"):
                pid = open("cunoastere/ai_playlist_id.txt", encoding="utf-8").read().strip()
            if not pid:
                gasit = yt.playlists().list(part="snippet", mine=True, maxResults=50).execute()
                for p in gasit.get("items", []):
                    if p["snippet"]["title"].strip().upper() == "FĂCUTE DE AI":
                        pid = p["id"]
                        break
                if not pid:
                    nou = yt.playlists().insert(part="snippet,status", body={
                        "snippet": {"title": "FĂCUTE DE AI",
                                    "description": "Episoade + shorts generate automat din live-uri (AutoEditor)."},
                        "status": {"privacyStatus": "public"}}).execute()
                    pid = nou["id"]
                os.makedirs("cunoastere", exist_ok=True)
                open("cunoastere/ai_playlist_id.txt", "w").write(pid)
            for _, _, vid in publicate:
                yt.playlistItems().insert(part="snippet", body={
                    "snippet": {"playlistId": pid, "resourceId": {"kind": "youtube#video", "videoId": vid}}}).execute()
            print(f"  ADAUGATE IN PLAYLIST 'FĂCUTE DE AI': https://www.youtube.com/playlist?list={pid}", flush=True)
        except Exception as ex:
            print(f"  (playlist skip: {str(ex)[:80]})", flush=True)
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
