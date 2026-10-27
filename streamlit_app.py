"""Streamlit wrapper for the static site, for hosting on Streamlit Community Cloud from a private repo.

Each page of site/ is inlined (CSS, JS, data) and rendered in a component iframe; URL parameters are passed
through window.__PARAMS so the test links work: https://<app>.streamlit.app/?page=tuteur&prof=histoire&auto=1
Set APP_URL in the app's secrets (Settings > Secrets: APP_URL = "https://<app>.streamlit.app/") so the
"lien de classe" built on the tutor page points back to the app.
"""
import json
import pathlib
import re

import streamlit as st
import streamlit.components.v1 as components

SITE = pathlib.Path(__file__).parent / "site"
PAGES = {"accueil": "index.html", "tuteur": "tuteur/index.html", "orientation": "orientation/index.html", "tests": "tests.html"}

st.set_page_config(page_title="Tuteur IA public", page_icon="🎓", layout="wide", initial_sidebar_state="collapsed")
st.markdown("<style>#MainMenu, header, footer {visibility: hidden;} .block-container {padding: 0 !important; max-width: 100% !important;}</style>",
            unsafe_allow_html=True)


@st.cache_data
def page_html(name):
    path = SITE / PAGES[name]
    html = path.read_text(encoding="utf-8")
    here = path.parent

    def inline_css(m):
        return "<style>" + (here / m.group(1)).resolve().read_text(encoding="utf-8") + "</style>"

    def inline_js(m):
        return "<script>" + (here / m.group(1)).resolve().read_text(encoding="utf-8") + "</script>"

    html = re.sub(r'<link rel="stylesheet" href="((?:\.\./)?assets/[^"]+)">', inline_css, html)
    html = re.sub(r'<script src="([^":]+\.js)"></script>', inline_js, html)

    # Internal links -> app pages, opened in the top window.
    def link(m):
        target, query = m.group(1), (m.group(2) or "").lstrip("?")
        page = {"tuteur/": "tuteur", "orientation/": "orientation", "tests.html": "tests"}.get(target, "accueil")
        q = "page=" + page + ("&" + query if query else "")
        return f'href="?{q}" target="_top"'

    html = re.sub(r'href="(?:\.\./|\./)?((?:tuteur|orientation)/|tests\.html|)(\?[^"]*)?"', link, html)
    return html


params = {k: st.query_params[k] for k in st.query_params}
page = params.pop("page", "accueil")
if page not in PAGES:
    page = "accueil"
try:
    app_url = st.secrets.get("APP_URL", "")
except FileNotFoundError:  # no secrets.toml: shareable links fall back to relative ones
    app_url = ""
boot = f"<script>window.__PARAMS = {json.dumps(params, ensure_ascii=False)}; window.__APP_URL = {json.dumps(app_url)};</script>"
html = page_html(page).replace("<head>", "<head>" + boot, 1)
components.html(html, height=900, scrolling=True)
