import json, re, datetime, html, os, time
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup

# ---------- IMPOSTAZIONI (modificabili) ----------
# Parole che devono comparire (titolo o testo vicino) per tenere un bando
KEYWORDS = [
    "riabilit", "fisioterap", "logoped", "neuropsichiatria", "psicomotric",
    "terapia occupazionale", "terapista", "neuroscienz", "pediatri",
    "medicina fisica", "scienze motorie", "disabilit",
    "rehabilit", "physiotherap", "physical therapy", "occupational therapy",
    "speech and language", "cerebral palsy", "neurorehab", "paediatric",
]
# Per le pagine di offerte in inglese (EURAXESS) si usano parole piu' strette
KEYWORDS_DETAIL = [k for k in KEYWORDS if k != "disabilit"]
SOURCES = [
    {"name": "Gazzetta Ufficiale - Concorsi", "mode": "list",
     "url": "https://www.gazzettaufficiale.it/30giorni/concorsi"},
    {"name": "EURAXESS - offerte di ricerca", "mode": "euraxess",
     "url": "https://euraxess.ec.europa.eu/jobs/search", "pages": 5},
]
NEW_DAYS = 3       # per quanti giorni un bando resta "nuovo"
DETAIL_CAP = 120   # massimo di pagine offerta lette per ogni esecuzione
# --------------------------------------------------

HEADERS = {"User-Agent": "Mozilla/5.0 (monitor bandi personale)"}
today = datetime.date.today().isoformat()
os.makedirs("docs", exist_ok=True)
try:
    data = json.load(open("docs/data.json", encoding="utf-8"))
    items = data["items"]
    checked = set(data["checked"])
except Exception:
    items, checked = {}, set()

def get(url):
    r = requests.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    return BeautifulSoup(r.text, "html.parser")

status = []
for s in SOURCES:
    try:
        n = 0
        if s["mode"] == "list":
            soup = get(s["url"])
            for a in soup.find_all("a", href=True):
                href = a["href"]
                if href.startswith("#") or href.startswith("javascript"):
                    continue
                title = " ".join(a.get_text(" ", strip=True).split())
                parent = a.find_parent(["li", "tr", "article", "p", "div"])
                ctx = " ".join(parent.get_text(" ", strip=True).split())[:400] if parent else ""
                if not any(k in (title + " " + ctx).lower() for k in KEYWORDS):
                    continue
                if len(title) < 15:
                    title = ctx[:200]
                link = urljoin(s["url"], href)
                if link not in items:
                    items[link] = {"title": title, "source": s["name"], "first_seen": today}
                n += 1
            status.append((s["name"], f"ok ({n} bandi trovati)"))
        else:  # euraxess: leggo gli elenchi, poi apro le offerte nuove e controllo il testo
            cand = []
            for p in range(s["pages"]):
                soup = get(f'{s["url"]}?page={p}')
                for a in soup.find_all("a", href=True):
                    path = urlparse(urljoin(s["url"], a["href"])).path
                    if re.fullmatch(r"/jobs/\d+", path):
                        link = urljoin(s["url"], path)
                        if link not in cand:
                            cand.append(link)
                time.sleep(0.5)
            todo = [l for l in cand if l not in items and l not in checked][:DETAIL_CAP]
            for link in todo:
                try:
                    d = get(link)
                    text = d.get_text(" ", strip=True).lower()
                    if any(k in text for k in KEYWORDS_DETAIL):
                        h = d.find("h1")
                        title = " ".join((h.get_text(" ", strip=True) if h else d.title.get_text()).split())
                        items[link] = {"title": title, "source": s["name"], "first_seen": today}
                        n += 1
                    else:
                        checked.add(link)
                except Exception:
                    pass
                time.sleep(0.5)
            status.append((s["name"], f"ok ({len(cand)} offerte viste, {len(todo)} controllate, {n} pertinenti)"))
    except Exception as e:
        status.append((s["name"], f"ERRORE: {str(e)[:80]}"))

json.dump({"items": items, "checked": sorted(checked)},
          open("docs/data.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)

def is_new(d):
    return (datetime.date.today() - datetime.date.fromisoformat(d)).days < NEW_DAYS

rows = ""
for link, v in sorted(items.items(), key=lambda kv: kv[1]["first_seen"], reverse=True):
    badge = '<span class="new">NUOVO</span>' if is_new(v["first_seen"]) else ""
    rows += (f'<li data-t="{html.escape(v["title"].lower())}">{badge}'
             f'<a href="{html.escape(link)}" target="_blank" rel="noopener">{html.escape(v["title"])}</a>'
             f'<small>{html.escape(v["source"])} &middot; visto il {v["first_seen"]}</small></li>\n')
if not rows:
    rows = "<li>Nessun bando pertinente trovato per ora.</li>"
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
document.querySelectorAll('#l li').forEach(function(li){{li.style.display=(li.dataset.t||'').indexOf(q)>-1?'':'none'}})}}</script>
</body></html>"""
open("docs/index.html", "w", encoding="utf-8").write(page)
