import json, re, datetime, html, os
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup

# ---------- IMPOSTAZIONI (modificabili) ----------
KEYWORDS = [
    "riabilit", "fisioterap", "logoped", "neuropsichiatria", "psicomotric",
    "terapia occupazionale", "terapista", "disabilit", "neuroscienz",
    "pediatri", "assegno di ricerca", "borsa di ricerca", "contratto di ricerca",
    "dottorato", "ricercatore",
]
# accept_all=True: la pagina e' gia' filtrata dal sito, si tengono tutti i link
SOURCES = [
    {"name": "Gazzetta Ufficiale - Concorsi",
     "url": "https://www.gazzettaufficiale.it/30giorni/concorsi", "accept_all": False},
    {"name": "inPA - Bandi e avvisi",
     "url": "https://www.inpa.gov.it/bandi-e-avvisi/", "accept_all": False},
    {"name": "EURAXESS - rehabilitation",
     "url": "https://euraxess.ec.europa.eu/jobs/search?keywords=rehabilitation", "accept_all": True},
    {"name": "EURAXESS - physiotherapy",
     "url": "https://euraxess.ec.europa.eu/jobs/search?keywords=physiotherapy", "accept_all": True},
]
NEW_DAYS = 3  # per quanti giorni un bando resta "nuovo"
# --------------------------------------------------

HEADERS = {"User-Agent": "Mozilla/5.0 (monitor bandi personale)"}
today = datetime.date.today().isoformat()
os.makedirs("docs", exist_ok=True)
try:
    db = json.load(open("docs/data.json", encoding="utf-8"))
except Exception:
    db = {}

status = []
for s in SOURCES:
    try:
        r = requests.get(s["url"], headers=HEADERS, timeout=30)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        n = 0
        for a in soup.find_all("a", href=True):
            title = " ".join(a.get_text(" ", strip=True).split())
            if len(title) < 15:
                continue
            if not s["accept_all"] and not any(k in title.lower() for k in KEYWORDS):
                continue
            link = urljoin(s["url"], a["href"])
            if link not in db:
                db[link] = {"title": title, "source": s["name"], "first_seen": today}
            n += 1
        status.append((s["name"], f"ok ({n} link)"))
    except Exception as e:
        status.append((s["name"], f"ERRORE: {str(e)[:80]}"))

json.dump(db, open("docs/data.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)

def is_new(d):
    return (datetime.date.today() - datetime.date.fromisoformat(d)).days < NEW_DAYS

items = sorted(db.items(), key=lambda kv: kv[1]["first_seen"], reverse=True)
rows = ""
for link, v in items:
    badge = '<span class="new">NUOVO</span>' if is_new(v["first_seen"]) else ""
    rows += (f'<li data-t="{html.escape(v["title"].lower())}">{badge}'
             f'<a href="{html.escape(link)}" target="_blank" rel="noopener">{html.escape(v["title"])}</a>'
             f'<small>{html.escape(v["source"])} &middot; visto il {v["first_seen"]}</small></li>\n')
st = "".join(f"<li>{html.escape(n)}: {html.escape(m)}</li>" for n, m in status)

page = f"""<!doctype html><html lang="it"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Bandi ricerca e riabilitazione</title>
<style>
body{{font-family:system-ui,sans-serif;max-width:720px;margin:0 auto;padding:16px;line-height:1.4;color:#1a1a1a;background:#fff}}
h1{{font-size:1.3rem}} input{{width:100%;padding:10px;font-size:1rem;margin:8px 0 16px;box-sizing:border-box}}
ul{{list-style:none;padding:0}} li{{padding:10px 0;border-bottom:1px solid #ddd}}
li a{{display:block;font-weight:600;color:#0b57d0;text-decoration:none}} small{{color:#666}}
.new{{background:#d93025;color:#fff;font-size:.7rem;padding:2px 6px;border-radius:4px;margin-right:6px}}
details{{margin-top:24px;color:#555;font-size:.85rem}}
@media(prefers-color-scheme:dark){{body{{background:#121212;color:#eee}}li{{border-color:#333}}li a{{color:#8ab4f8}}small{{color:#aaa}}details{{color:#bbb}}}}
</style></head><body>
<h1>Bandi ricerca e riabilitazione</h1>
<p><small>Aggiornato il {today} &middot; {len(items)} risultati</small></p>
<input id="q" placeholder="Filtra (es. assegno, pediatri, Milano)" oninput="f()">
<ul id="l">{rows}</ul>
<details><summary>Stato delle fonti</summary><ul>{st}</ul></details>
<script>function f(){{var q=document.getElementById('q').value.toLowerCase();
document.querySelectorAll('#l li').forEach(function(li){{li.style.display=li.dataset.t.indexOf(q)>-1?'':'none'}})}}</script>
</body></html>"""
open("docs/index.html", "w", encoding="utf-8").write(page)
