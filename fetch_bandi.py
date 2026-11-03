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
