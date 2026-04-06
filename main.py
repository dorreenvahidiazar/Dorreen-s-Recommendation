import requests
import streamlit as st
import csv
import os
from datetime import datetime

#CSV 
CONSENT_CSV     = "consent_data.csv"
DEMOGRAPHIC_CSV = "demographic_data.csv"

def save_consent(first_name, last_name):
    file_exists = os.path.isfile(CONSENT_CSV)
    with open(CONSENT_CSV, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["first_name", "last_name", "timestamp"])
        if not file_exists:
            writer.writeheader()
        writer.writerow({
            "first_name": first_name,
            "last_name":  last_name,
            "timestamp":  datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        })

def save_demographic(first_name, last_name, age, occupation):
    file_exists = os.path.isfile(DEMOGRAPHIC_CSV)
    with open(DEMOGRAPHIC_CSV, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["first_name", "last_name", "age", "occupation", "timestamp"])
        if not file_exists:
            writer.writeheader()
        writer.writerow({
            "first_name": first_name,
            "last_name":  last_name,
            "age":        age,
            "occupation": occupation,
            "timestamp":  datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        })

EXIT_SURVEY_FIELDS = [
    "first_name","last_name","time_spent",
    "satisfaction_rating","navigation_ease","recommend_likelihood",
    "features_used","feedback","timestamp"
]

def save_exit_survey(first_name, last_name, time_spent_seconds, rating, nav_ease, recommend, features_used, feedback):
    file_exists = os.path.isfile("exitSurvey_data.csv")
    with open("exitSurvey_data.csv", "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=EXIT_SURVEY_FIELDS, quoting=csv.QUOTE_ALL)
        if not file_exists:
            writer.writeheader()
        mins, secs = divmod(int(time_spent_seconds), 60)
        writer.writerow({
            "first_name":            first_name,
            "last_name":             last_name,
            "time_spent":            f"{mins:02d}:{secs:02d}",
            "satisfaction_rating":   rating,
            "navigation_ease":       nav_ease,
            "recommend_likelihood":  recommend,
            "features_used":         " | ".join(features_used) if features_used else "None",
            "feedback":              feedback,
            "timestamp":             datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        })

# Config
API_KEY  = "d4eae62fbb0afd2439b58b8c1b153af2"
BASE_URL = "https://api.themoviedb.org/3"
POSTER_URL = "https://image.tmdb.org/t/p/w500"

GENRES = {
    "All": None, "Action": 28, "Comedy": 35, "Drama": 18,
    "Horror": 27, "Sci-Fi": 878, "Romance": 10749, "Thriller": 53,
}

# API helpers
def search_movie(query):
    url = f"{BASE_URL}/search/movie?api_key={API_KEY}&query={query}"
    data = requests.get(url).json()
    return data["results"][0] if data.get("results") else None

def get_similar_movies(movie_id):
    url = f"{BASE_URL}/movie/{movie_id}/similar?api_key={API_KEY}"
    data = requests.get(url).json()
    return data.get("results", [])

def get_popular_movies(genre_id=None, min_year=1970, max_year=2026, page=1):
    url = f"{BASE_URL}/discover/movie?api_key={API_KEY}&sort_by=popularity.desc"
    url += f"&primary_release_date.gte={min_year}-01-01"
    url += f"&primary_release_date.lte={max_year}-12-31"
    url += f"&page={page}"
    if genre_id:
        url += f"&with_genres={genre_id}"
    data = requests.get(url).json()
    return data.get("results", []), min(data.get("total_pages", 1), 20)

def filter_similar(similar, genre_id, min_year, max_year):
    out = []
    for m in similar:
        year = int(m.get("release_date", "0000")[:4] or 0)
        if not (min_year <= year <= max_year):
            continue
        if genre_id and genre_id not in m.get("genre_ids", []):
            continue
        out.append(m)
    return out


def init_favs():
    if "favorites" not in st.session_state:
        st.session_state.favorites = {}
    if "fav_toast" not in st.session_state:
        st.session_state.fav_toast = None

def is_fav(movie_id):
    return str(movie_id) in st.session_state.favorites

def toggle_fav(movie):
    mid = str(movie["id"])
    if mid in st.session_state.favorites:
        del st.session_state.favorites[mid]
        st.session_state.fav_toast = ("removed", movie["title"])
    else:
        st.session_state.favorites[mid] = movie
        st.session_state.fav_toast = ("added", movie["title"])

def render_movie_card(m, key_prefix):
    mid      = m["id"]
    m_year   = (m.get("release_date") or "")[:4]
    m_rating = m.get("vote_average", 0)
    m_poster = f"{POSTER_URL}{m['poster_path']}" if m.get("poster_path") else None
    fav      = is_fav(mid)

    if m_poster:
        st.image(m_poster, use_container_width=True)

    heart = "♥" if fav else "♡"
    fav_label = f"{heart} Saved" if fav else f"{heart} Save"

    st.markdown(f"""
    <div class="sm-card-body">
      <p class="sm-card-title" title="{m['title']}">{m['title']}</p>
      <div class="sm-card-foot">
        <span class="sm-card-rating">★ {m_rating:.1f}</span>
        <span class="sm-card-year">{m_year}</span>
      </div>
    </div>
    """, unsafe_allow_html=True)

    btn_key = f"{key_prefix}_fav_{mid}"
    active_cls = "fav-active" if fav else "fav-inactive"
    st.markdown(f'<div class="fav-btn-wrap {active_cls}">', unsafe_allow_html=True)
    if st.button(fav_label, key=btn_key, use_container_width=True):
        toggle_fav(m)
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# Page setup 
st.set_page_config(
    page_title="Dorreen's Recommendation",
    page_icon="🎞️",
    layout="wide",
    initial_sidebar_state="collapsed",
)
init_favs()

# Session state init 
if "onboarded" not in st.session_state:
    st.session_state.onboarded = False
if "user_info" not in st.session_state:
    st.session_state.user_info = {}
if "page" not in st.session_state:
    st.session_state.page = "main"          
if "start_time" not in st.session_state:
    st.session_state.start_time = None      
if "survey_done" not in st.session_state:
    st.session_state.survey_done = False

# CSS for all
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,700;1,400&family=DM+Sans:wght@300;400;500&display=swap');

html, body, [data-testid="stAppViewContainer"] {
    background-color: #0a0a0f !important;
    color: #e8e0d5 !important;
}
[data-testid="stHeader"], footer { display: none !important; }
[data-testid="stAppViewContainer"] { padding-top: 0 !important; }
[data-testid="block-container"] { padding: 2rem 3rem 4rem !important; max-width: 1280px; }
* { font-family: 'DM Sans', sans-serif; }

/* ── Onboarding screen ── */
.onboard-wrap {
    padding: 1.5rem 0 2rem;
}
.onboard-card {
    background: #11111a;
    border: 1px solid #3d1f2a;
    border-radius: 6px;
    padding: 2rem 2.5rem 1.5rem;
    max-width: 100%;
    width: 100%;
    position: relative;
    box-shadow: 0 10px 40px rgba(0,0,0,0.4);
}
.onboard-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    background: linear-gradient(90deg, #e8658a, #c94070, transparent);
    border-radius: 6px 6px 0 0;
}
.onboard-eyebrow {
    font-size: 0.7rem;
    letter-spacing: 0.22em;
    text-transform: uppercase;
    color: #7d4f5e;
    margin-bottom: 0.6rem;
}
.onboard-title {
    font-family: 'Playfair Display', serif;
    font-size: 2rem;
    font-weight: 700;
    color: #f9c8d8;
    line-height: 1.1;
    margin-bottom: 0.6rem;
}
.onboard-desc {
    font-size: 0.93rem;
    line-height: 1.75;
    color: #b899a4;
    margin-bottom: 2rem;
}
.onboard-desc strong { color: #e8658a; font-weight: 500; }
.onboard-divider {
    border: none;
    border-top: 1px solid #2a1520;
    margin: 1.6rem 0;
}

/* ── Onboarding form inputs ── */
[data-testid="stTextInput"] input {
    background: #13131e !important;
    border: 1px solid #2a2a38 !important;
    border-radius: 2px !important;
    color: #f0e4ea !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 1rem !important;
    padding: 0.7rem 1rem !important;
    caret-color: #e8658a;
    transition: border-color 0.2s;
}
[data-testid="stTextInput"] input:focus {
    border-color: #e8658a !important;
    box-shadow: 0 0 0 3px rgba(232,101,138,0.15) !important;
}
[data-testid="stTextInput"] label {
    font-size: 0.72rem !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
    color: #7d4f5e !important;
}

[data-testid="stNumberInput"] input {
    background: #13131e !important;
    border: 1px solid #2a2a38 !important;
    border-radius: 2px !important;
    color: #f0e4ea !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 1rem !important;
    caret-color: #e8658a;
    transition: border-color 0.2s;
}
[data-testid="stNumberInput"] input:focus {
    border-color: #e8658a !important;
    box-shadow: 0 0 0 3px rgba(232,101,138,0.15) !important;
}
[data-testid="stNumberInput"] label {
    font-size: 0.72rem !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
    color: #7d4f5e !important;
}

[data-testid="stSelectbox"] label {
    font-size: 0.72rem !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
    color: #7d4f5e !important;
}
[data-testid="stSelectbox"] > div > div {
    background: #1a0d12 !important;
    border: 1px solid #3d1f2a !important;
    border-radius: 2px !important;
    color: #f0e4ea !important;
}

/* Checkbox styling */
[data-testid="stCheckbox"] label {
    font-size: 0.88rem !important;
    color: #b899a4 !important;
    line-height: 1.5 !important;
}
[data-testid="stCheckbox"] span { color: #e8658a !important; }

/* ── Buttons ── */
[data-testid="stButton"] button {
    background: #e8658a !important;
    color: #1a0d12 !important;
    border: none !important;
    border-radius: 2px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.78rem !important;
    font-weight: 500 !important;
    letter-spacing: 0.12em !important;
    text-transform: uppercase !important;
    padding: 0.6rem 1.4rem !important;
    transition: background 0.2s, color 0.2s, opacity 0.2s !important;
    width: 100% !important;
}
[data-testid="stButton"] button:hover { opacity: 0.85 !important; }

/* ── Main app styles ── */
.masthead {
    display: flex;
    flex-direction: column;
    gap: 0.4rem;
    border-bottom: 1px solid #2a2a38;
    padding-bottom: 1.4rem;
    margin-bottom: 2.5rem;
}
.masthead-title {
    font-family: 'Playfair Display', serif;
    font-size: 6.5rem;
    font-weight: 700;
    color: #f9c8d8;
    letter-spacing: -0.02em;
    line-height: 1;
    margin: 0;
}
.masthead-sub {
    font-size: 1.1rem;
    color: #7d4f5e;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    font-weight: 300;
}
.welcome-pill {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    background: rgba(232,101,138,0.1);
    border: 1px solid rgba(232,101,138,0.25);
    border-radius: 999px;
    padding: 0.3rem 0.9rem;
    font-size: 0.8rem;
    color: #e8658a;
    margin-bottom: 0.6rem;
}

.hero-title {
    font-family: 'Playfair Display', serif;
    font-size: 2.1rem;
    font-weight: 700;
    color: #f9c8d8;
    margin: 0 0 0.5rem;
    line-height: 1.15;
}
.hero-meta { display: flex; gap: 1rem; align-items: center; margin-bottom: 1.2rem; }
.badge {
    font-size: 0.72rem;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    padding: 0.25rem 0.6rem;
    border-radius: 2px;
    font-weight: 500;
}
.badge-year { background: #2e1520; color: #b07080; }
.badge-rating {
    background: rgba(232,101,138,0.15);
    color: #e8658a;
    border: 1px solid rgba(232,101,138,0.35);
}
.hero-overview {
    font-size: 0.95rem;
    line-height: 1.75;
    color: #b899a4;
    max-width: 660px;
    margin: 0;
}

.section-label {
    font-size: 0.72rem;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: #7d4f5e;
    margin-bottom: 1.2rem;
    display: flex;
    align-items: center;
    gap: 0.8rem;
}
.section-label::after { content: ''; flex: 1; height: 1px; background: #3d1f2a; }

.sm-card-body { padding: 0.75rem 0 0.2rem; }
.sm-card-title {
    font-size: 0.88rem;
    font-weight: 500;
    color: #f0d8e0;
    margin: 0 0 0.3rem;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.sm-card-rating { font-size: 0.78rem; color: #e8658a; }
.sm-card-year { font-size: 0.75rem; color: #6b3a48; margin-left: auto; }
.sm-card-foot { display: flex; justify-content: space-between; align-items: center; }

[data-testid="stHorizontalBlock"] > div,
[data-testid="stColumn"],
[data-testid="stColumn"] > div,
[data-testid="stColumn"] > div > div {
    overflow: visible !important;
}
[data-testid="stColumn"] [data-testid="stImage"] img {
    display: block;
    width: 100%;
    border-radius: 3px;
    transform-origin: center bottom;
    transition: transform 0.38s cubic-bezier(0.25, 0.46, 0.45, 0.94),
                box-shadow 0.38s cubic-bezier(0.25, 0.46, 0.45, 0.94);
    will-change: transform;
    position: relative;
    z-index: 1;
    cursor: pointer;
}
[data-testid="stColumn"] [data-testid="stImage"]:hover img {
    transform: scale(1.09);
    box-shadow: 0 20px 45px rgba(0,0,0,0.75), 0 0 0 1px rgba(232,101,138,0.3);
    z-index: 10;
}

[data-testid="stSlider"] label {
    font-size: 0.72rem !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
    color: #7d4f5e !important;
}
[data-testid="stSlider"] [data-baseweb="slider"] div[role="slider"] {
    background: #e8658a !important;
    border-color: #e8658a !important;
}

[data-testid="stButton"]:has(button[data-testid^="pg_"]) button {
    background: #200d16 !important;
    color: #b899a4 !important;
    border: 1px solid #3d1f2a !important;
    border-radius: 3px !important;
    font-size: 0.82rem !important;
    font-weight: 500 !important;
    letter-spacing: 0 !important;
    text-transform: none !important;
    padding: 0 0.4rem !important;
    height: 2.1rem !important;
    min-height: unset !important;
    min-width: 2.1rem !important;
    line-height: 1 !important;
    white-space: nowrap !important;
    opacity: 1 !important;
}
[data-testid="stButton"]:has(button[data-testid^="pg_"]) button:hover {
    background: #3d1f2a !important;
    color: #f9c8d8 !important;
    border-color: #7d3050 !important;
    opacity: 1 !important;
}

.fav-btn-wrap [data-testid="stButton"] button {
    background: transparent !important;
    color: #b899a4 !important;
    border: 1px solid #3d1f2a !important;
    border-radius: 2px !important;
    font-size: 0.72rem !important;
    letter-spacing: 0.06em !important;
    padding: 0.3rem 0.5rem !important;
    text-transform: none !important;
    transition: background 0.2s, color 0.2s, border-color 0.2s !important;
    margin-top: 0.3rem !important;
}
.fav-btn-wrap [data-testid="stButton"] button:hover {
    background: rgba(232,101,138,0.1) !important;
    color: #e8658a !important;
    border-color: #e8658a !important;
    opacity: 1 !important;
}
.fav-active [data-testid="stButton"] button {
    background: rgba(232,101,138,0.15) !important;
    color: #e8658a !important;
    border-color: #e8658a !important;
}
.fav-active [data-testid="stButton"] button:hover {
    background: rgba(232,101,138,0.08) !important;
    color: #b07080 !important;
    border-color: #7d3050 !important;
}

.favs-panel {
    background: #11111a;
    border: 1px solid #3d1f2a;
    border-radius: 4px;
    padding: 1.4rem 1.6rem;
    margin-bottom: 2rem;
    position: relative;
}
.favs-panel::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, #e8658a, #c94070, transparent);
    border-radius: 4px 4px 0 0;
}
.favs-empty {
    color: #5a2e3c;
    font-size: 0.88rem;
    text-align: center;
    padding: 1rem 0;
}

.not-found {
    background: #200d16;
    border: 1px dashed #3d1f2a;
    border-radius: 4px;
    padding: 3rem;
    text-align: center;
    color: #6b3a48;
    font-size: 0.95rem;
}
.pink-divider { border: none; border-top: 1px solid #3d1f2a; margin: 2rem 0; }

.pg-bar {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.35rem;
    flex-wrap: wrap;
    margin-top: 2rem;
}
.page-info {
    font-size: 0.75rem;
    color: #5a2e3c;
    text-align: center;
    margin-top: 0.5rem;
    letter-spacing: 0.06em;
}

.site-footer {
    margin-top: 4rem;
    padding-top: 1.5rem;
    border-top: 1px solid #1e1e2e;
    font-size: 0.78rem;
    color: #5a2e3c;
    text-align: center;
}
.site-footer a { color: #7d4f5e; text-decoration: none; }
.site-footer a:hover { color: #e8658a; }

/* ── Top action bar (stopwatch + assessment button) ── */
.topbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    background: #11111a;
    border: 1px solid #2a1520;
    border-radius: 4px;
    padding: 0.55rem 1.2rem;
    margin-bottom: 1.4rem;
}
.stopwatch {
    display: flex;
    align-items: center;
    gap: 0.55rem;
    font-family: 'DM Sans', monospace;
    font-size: 1rem;
    color: #f0d8e0;
    font-variant-numeric: tabular-nums;
    letter-spacing: 0.04em;
}
.stopwatch-dot {
    width: 8px; height: 8px;
    border-radius: 50%;
    background: #e8658a;
    box-shadow: 0 0 6px #e8658a;
    animation: pulse-dot 1.2s ease-in-out infinite;
}
@keyframes pulse-dot {
    0%,100% { opacity: 1; transform: scale(1); }
    50%      { opacity: 0.4; transform: scale(0.75); }
}
.topbar-label {
    font-size: 0.68rem;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: #7d4f5e;
}

/* ── Survey page ── */
.survey-wrap { padding: 1.5rem 0 3rem; }
.survey-card {
    background: #11111a;
    border: 1px solid #3d1f2a;
    border-radius: 6px;
    padding: 2rem 2.5rem 2rem;
    position: relative;
    box-shadow: 0 10px 40px rgba(0,0,0,0.4);
}
.survey-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    background: linear-gradient(90deg, #e8658a, #c94070, transparent);
    border-radius: 6px 6px 0 0;
}
.survey-title {
    font-family: 'Playfair Display', serif;
    font-size: 1.9rem;
    font-weight: 700;
    color: #f9c8d8;
    margin-bottom: 0.4rem;
}
.survey-sub {
    font-size: 0.88rem;
    color: #b899a4;
    margin-bottom: 1.6rem;
    line-height: 1.6;
}
.time-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    background: rgba(232,101,138,0.1);
    border: 1px solid rgba(232,101,138,0.25);
    border-radius: 999px;
    padding: 0.25rem 0.8rem;
    font-size: 0.8rem;
    color: #e8658a;
    margin-bottom: 1.4rem;
    font-variant-numeric: tabular-nums;
}
.survey-done {
    text-align: center;
    padding: 2rem 0 1rem;
    color: #b899a4;
}
.survey-done .done-icon { font-size: 2.5rem; margin-bottom: 0.5rem; }
.survey-done h2 { font-family: 'Playfair Display', serif; color: #f9c8d8; margin-bottom: 0.4rem; }
.survey-done p  { font-size: 0.9rem; color: #7d4f5e; }
</style>
""", unsafe_allow_html=True)



# ONBOARDING SCREEN

if not st.session_state.onboarded:

    st.markdown('<div class="onboard-wrap">', unsafe_allow_html=True)

  
    st.markdown("""
    <div class="onboard-card">
      <p class="onboard-eyebrow">🎞️ &nbsp; HCI Project</p>
      <h1 class="onboard-title">Dorreen's Movie Recommendation</h1>
      <p class="onboard-desc">
        Welcome! This movie discovery app was created by <strong>Dorreen</strong> as a school project.
        Please fill out the short form below before continuing.
      </p>
      <hr class="onboard-divider">
    </div>
    """, unsafe_allow_html=True)

    # Form fields — two columns for name + last name
    col1, col2 = st.columns(2)
    with col1:
        first_name = st.text_input("First Name", placeholder="first name")
    with col2:
        last_name = st.text_input("Last Name", placeholder="last name")

    col3, col4 = st.columns(2)
    with col3:
        age = st.number_input("Age", min_value=1, max_value=120, step=1, value=None, placeholder="age")
    with col4:
        occupation = st.text_input("Occupation", placeholder="e.g. Student, Teacher…")

    st.markdown("<br>", unsafe_allow_html=True)

    # Voluntary assessment checkbox
    agreed = st.checkbox(
        "✅  I understand this is a **voluntary assessment** — my participation is optional."
    )

    st.markdown("<br>", unsafe_allow_html=True)

    # Validation & submit
    all_filled = (
        first_name.strip() != "" and
        last_name.strip() != "" and
        age is not None and
        occupation.strip() != ""
    )

    if st.button("Enter the App →", key="onboard_submit"):
        if not all_filled:
            st.error("Please fill in all fields before continuing.")
        elif not agreed:
            st.warning("Please check the voluntary assessment box to continue.")
        else:
            fn = first_name.strip()
            ln = last_name.strip()
            save_consent(fn, ln)
            save_demographic(fn, ln, int(age), occupation.strip())
            st.session_state.user_info = {
                "first_name": fn,
                "last_name":  ln,
                "age":        int(age),
                "occupation": occupation.strip(),
            }
            st.session_state.onboarded = True
            st.session_state.start_time = datetime.now().timestamp()
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)  

    st.stop()   # ← don't render the main app until onboarded


# SURVEY PAGE

if st.session_state.page == "survey":
    user = st.session_state.user_info
    elapsed = int(datetime.now().timestamp() - (st.session_state.start_time or datetime.now().timestamp()))
    mins, secs = divmod(elapsed, 60)
    time_str = f"{mins:02d}:{secs:02d}"

    st.markdown('<div class="survey-wrap">', unsafe_allow_html=True)
    st.markdown(f"""
    <div class="survey-card">
      <p class="onboard-eyebrow">🎞️ &nbsp; Dorreen's Movie World</p>
      <h2 class="survey-title">App Assessment</h2>
      <p class="survey-sub">
        Thanks for using the app, <strong style="color:#e8658a">{user['first_name']}</strong>!
        Please take a moment to rate your experience.
      </p>
      <div class="time-badge">⏱ Time spent: {time_str}</div>
    </div>
    """, unsafe_allow_html=True)

    if st.session_state.survey_done:
        st.markdown("""
        <div class="survey-done">
          <div class="done-icon">🎬</div>
          <h2>Thank you!</h2>
          <p>Your feedback has been saved. Here's a summary of all responses so far.</p>
        </div>
        """, unsafe_allow_html=True)

        # Load data and show charts 
        if os.path.isfile("exitSurvey_data.csv"):
            import pandas as pd
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt

            df = pd.read_csv("exitSurvey_data.csv", on_bad_lines="skip")
            # strip accidental whitespace from column names
            df.columns = [c.strip() for c in df.columns]

            REQUIRED = {"satisfaction_rating", "navigation_ease", "recommend_likelihood", "features_used"}
            if not df.empty and REQUIRED.issubset(set(df.columns)):
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown('<div class="section-label">Response Summary</div>', unsafe_allow_html=True)

                PINK   = "#e8658a"
                ROSE   = "#c94070"
                MAUVE  = "#7d4f5e"
                TEAL   = "#4f7d7a"
                BG     = "#11111a"
                TEXT   = "#f0d8e0"
                GRID   = "#2a1520"

                def style_ax(ax, title):
                    ax.set_facecolor(BG)
                    ax.figure.patch.set_facecolor(BG)
                    ax.set_title(title, color=TEXT, fontsize=11, pad=10)
                    ax.tick_params(colors=TEXT, labelsize=8)
                    ax.spines[:].set_color(GRID)
                    ax.yaxis.set_major_locator(plt.MaxNLocator(integer=True))
                    ax.set_ylabel("Responses", color=TEXT, fontsize=8)
                    for spine in ax.spines.values():
                        spine.set_linewidth(0.5)
                    ax.grid(axis="y", color=GRID, linewidth=0.5, linestyle="--")
                    ax.set_axisbelow(True)

                # Chart 1: Overall satisfaction
                sat_labels = {1:"Very\nUnsatisfied", 2:"Unsatisfied", 3:"Neutral", 4:"Satisfied", 5:"Very\nSatisfied"}
                sat_counts = df["satisfaction_rating"].value_counts().reindex([1,2,3,4,5], fill_value=0)

                fig0, ax0 = plt.subplots(figsize=(7, 3.2))
                bars0 = ax0.bar([sat_labels[i] for i in sat_counts.index], sat_counts.values, color=TEAL, width=0.5, zorder=3)
                for bar, val in zip(bars0, sat_counts.values):
                    if val > 0:
                        ax0.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.05,
                                 str(val), ha="center", va="bottom", color=TEXT, fontsize=9)
                style_ax(ax0, "⭐ Overall Satisfaction")
                plt.tight_layout()
                st.pyplot(fig0)
                plt.close(fig0)

                st.markdown("<br>", unsafe_allow_html=True)

                # Chart 2: Navigation ease 
                nav_labels = {1:"Very\nDifficult", 2:"Difficult", 3:"Neutral", 4:"Easy", 5:"Very\nEasy"}
                nav_counts = df["navigation_ease"].value_counts().reindex([1,2,3,4,5], fill_value=0)

                fig1, ax1 = plt.subplots(figsize=(7, 3.2))
                bars = ax1.bar([nav_labels[i] for i in nav_counts.index], nav_counts.values, color=PINK, width=0.5, zorder=3)
                for bar, val in zip(bars, nav_counts.values):
                    if val > 0:
                        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.05,
                                 str(val), ha="center", va="bottom", color=TEXT, fontsize=9)
                style_ax(ax1, "🧭 Ease of Navigation")
                plt.tight_layout()
                st.pyplot(fig1)
                plt.close(fig1)

                st.markdown("<br>", unsafe_allow_html=True)

                # Chart 3: Likelihood to recommend
                rec_labels = {1:"Not at all\nLikely", 2:"Unlikely", 3:"Neutral", 4:"Likely", 5:"Very\nLikely"}
                rec_counts = df["recommend_likelihood"].value_counts().reindex([1,2,3,4,5], fill_value=0)

                fig2, ax2 = plt.subplots(figsize=(7, 3.2))
                bars2 = ax2.bar([rec_labels[i] for i in rec_counts.index], rec_counts.values, color=ROSE, width=0.5, zorder=3)
                for bar, val in zip(bars2, rec_counts.values):
                    if val > 0:
                        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.05,
                                 str(val), ha="center", va="bottom", color=TEXT, fontsize=9)
                style_ax(ax2, "📢 Likelihood to Recommend")
                plt.tight_layout()
                st.pyplot(fig2)
                plt.close(fig2)

                st.markdown("<br>", unsafe_allow_html=True)

                # Chart 4: Features used
                all_features = ["Adding to Favorites", "Genre filtering option", "Year range bars", "Search box"]
                feature_counts = {f: 0 for f in all_features}
                for entry in df["features_used"]:
                    if entry and str(entry).strip() != "None":
                        for f in str(entry).split(" | "):
                            f = f.strip()
                            if f in feature_counts:
                                feature_counts[f] += 1

                short_labels = ["Favorites", "Genre filter", "Year bars", "Search box"]
                fig3, ax3 = plt.subplots(figsize=(7, 3.2))
                bars3 = ax3.bar(short_labels, list(feature_counts.values()), color=MAUVE, width=0.5, zorder=3)
                for bar, val in zip(bars3, feature_counts.values()):
                    if val > 0:
                        ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.05,
                                 str(val), ha="center", va="bottom", color=TEXT, fontsize=9)
                style_ax(ax3, "🛠 Features Used")
                plt.tight_layout()
                st.pyplot(fig3)
                plt.close(fig3)

            elif not df.empty:
                st.warning("CSV columns don't match expected format. Please delete exitSurvey_data.csv and resubmit.")
    else:
        st.markdown("<br>", unsafe_allow_html=True)

        rating = st.select_slider(
            "⭐ How satisfied were you with the app overall?",
            options=[1, 2, 3, 4, 5],
            value=3,
            format_func=lambda x: {1:"1 — Very Unsatisfied", 2:"2 — Unsatisfied",
                                    3:"3 — Neutral", 4:"4 — Satisfied",
                                    5:"5 — Very Satisfied"}[x]
        )

        st.markdown("<br>", unsafe_allow_html=True)
        nav_ease = st.select_slider(
            "🧭 How easy was it to navigate the app?",
            options=[1, 2, 3, 4, 5],
            value=3,
            format_func=lambda x: {1:"1 — Very Difficult", 2:"2 — Difficult",
                                    3:"3 — Neutral", 4:"4 — Easy",
                                    5:"5 — Very Easy"}[x]
        )

        st.markdown("<br>", unsafe_allow_html=True)
        recommend = st.select_slider(
            "📢 How likely are you to recommend this app to someone else?",
            options=[1, 2, 3, 4, 5],
            value=3,
            format_func=lambda x: {1:"1 — Not at all likely", 2:"2 — Unlikely",
                                    3:"3 — Neutral", 4:"4 — Likely",
                                    5:"5 — Very Likely"}[x]
        )

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("**Which features did you use?** *(select all that apply)*")
        feat1 = st.checkbox("➕ Adding to Favorites")
        feat2 = st.checkbox("🎬 Using the Genre filtering option")
        feat3 = st.checkbox("📅 Using the year range bars to filter movies")
        feat4 = st.checkbox("🔍 Using the Search box")

        st.markdown("<br>", unsafe_allow_html=True)
        feedback = st.text_area(
            "Any comments or suggestions? (optional)",
            placeholder="What did you like or dislike? Any features you'd want added?",
            height=120
        )

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Submit Assessment →", key="survey_submit"):
            features_used = []
            if feat1: features_used.append("Adding to Favorites")
            if feat2: features_used.append("Genre filtering option")
            if feat3: features_used.append("Year range bars")
            if feat4: features_used.append("Search box")
            save_exit_survey(
                user["first_name"], user["last_name"],
                elapsed, rating, nav_ease, recommend, features_used, feedback.strip()
            )
            st.session_state.survey_done = True
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)
    st.stop()



# MAIN APP  

user = st.session_state.user_info
import streamlit.components.v1 as components

topbar_left, topbar_right = st.columns([3, 1])
with topbar_left:
    components.html(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500&display=swap');
    * {{ margin:0; padding:0; box-sizing:border-box; }}
    body {{ background: transparent; }}
    .topbar {{
        display: flex;
        align-items: center;
        gap: 0.8rem;
        background: #11111a;
        border: 1px solid #2a1520;
        border-radius: 4px;
        padding: 0.55rem 1.2rem;
        font-family: 'DM Sans', sans-serif;
    }}
    .topbar-label {{
        font-size: 0.68rem;
        letter-spacing: 0.14em;
        text-transform: uppercase;
        color: #7d4f5e;
    }}
    .stopwatch {{
        display: flex;
        align-items: center;
        gap: 0.5rem;
        font-size: 1rem;
        color: #f0d8e0;
        font-variant-numeric: tabular-nums;
        letter-spacing: 0.04em;
    }}
    .dot {{
        width: 8px; height: 8px;
        border-radius: 50%;
        background: #e8658a;
        box-shadow: 0 0 6px #e8658a;
        animation: pulse 1.2s ease-in-out infinite;
        flex-shrink: 0;
    }}
    @keyframes pulse {{
        0%,100% {{ opacity:1; transform:scale(1); }}
        50%      {{ opacity:0.4; transform:scale(0.75); }}
    }}
    </style>
    <div class="topbar">
      <span class="topbar-label">Session time</span>
      <div class="stopwatch">
        <div class="dot"></div>
        <span id="sw">00:00</span>
      </div>
    </div>
    <script>
      var start = {st.session_state.start_time or 0};
      function tick() {{
        var elapsed = Math.floor(Date.now() / 1000 - start);
        var m = Math.floor(elapsed / 60);
        var s = elapsed % 60;
        document.getElementById('sw').textContent =
          String(m).padStart(2,'0') + ':' + String(s).padStart(2,'0');
        setTimeout(tick, 1000);
      }}
      tick();
    </script>
    """, height=54)

with topbar_right:
    st.markdown('<div style="height:0.35rem"></div>', unsafe_allow_html=True)
    if st.button("📋 Assessment of the App", key="go_survey"):
        st.session_state.page = "survey"
        st.rerun()

fav_count = len(st.session_state.favorites)
fav_badge = f" ({fav_count})" if fav_count else ""

st.markdown(f"""
<div class="masthead">
  <div class="welcome-pill">👋 &nbsp; Welcome, {user['first_name']}!</div>
  <p class="masthead-title">Dorreen's Recommendation</p>
  <span class="masthead-sub">Movie Discovery Engine</span>
</div>
""", unsafe_allow_html=True)

if st.session_state.fav_toast:
    action, title = st.session_state.fav_toast
    if action == "added":
        st.success(f"♥ **{title}** added to your favorites!")
    else:
        st.info(f"♡ **{title}** removed from favorites.")
    st.session_state.fav_toast = None

# Favorites panel 
with st.expander(f"♥ My Favorites{fav_badge}", expanded=False):
    st.markdown('<div class="favs-panel">', unsafe_allow_html=True)
    favs = list(st.session_state.favorites.values())
    if not favs:
        st.markdown('<p class="favs-empty">No saved movies yet — hit ♡ on any movie to save it here.</p>', unsafe_allow_html=True)
    else:
        cols = st.columns(5)
        for i, m in enumerate(favs):
            with cols[i % 5]:
                render_movie_card(m, key_prefix="favs")
    st.markdown('</div>', unsafe_allow_html=True)

# Global filters 
f1, f2, f3 = st.columns([1.2, 1.5, 1.5])
with f1:
    genre_label = st.selectbox("Genre", list(GENRES.keys()))
with f2:
    min_year = st.slider("From year", 1970, 2026, 2000)
with f3:
    max_year = st.slider("To year", 1970, 2026, 2026)

genre_id = GENRES[genre_label]

filter_key = (genre_label, min_year, max_year)
if "browse_page" not in st.session_state:
    st.session_state.browse_page = 1
if st.session_state.get("last_filter_key") != filter_key:
    st.session_state.browse_page = 1
    st.session_state.last_filter_key = filter_key

st.markdown("<hr class='pink-divider'>", unsafe_allow_html=True)

# Search bar 
search_col, _ = st.columns([2, 1])
with search_col:
    movie_name = st.text_input(
        "", placeholder="Search a title to find similar movies…",
        label_visibility="collapsed"
    )

# Search result + similar movies 
if movie_name:
    movie = search_movie(movie_name)

    if movie:
        year       = (movie.get("release_date") or "")[:4]
        rating     = movie.get("vote_average", 0)
        poster_src = f"{POSTER_URL}{movie['poster_path']}" if movie.get("poster_path") else ""

        st.markdown("<br>", unsafe_allow_html=True)
        left, right = st.columns([1, 3])
        with left:
            if poster_src:
                st.image(poster_src, use_container_width=True)
            fav_cls = "fav-active" if is_fav(movie["id"]) else "fav-inactive"
            heart   = "♥ Saved" if is_fav(movie["id"]) else "♡ Save"
            st.markdown(f'<div class="fav-btn-wrap {fav_cls}">', unsafe_allow_html=True)
            if st.button(heart, key=f"hero_fav_{movie['id']}", use_container_width=True):
                toggle_fav(movie)
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        with right:
            st.markdown(f"""
            <div style="padding: 0.5rem 0">
              <h2 class="hero-title">{movie['title']}</h2>
              <div class="hero-meta">
                {'<span class="badge badge-year">' + year + '</span>' if year else ''}
                <span class="badge badge-rating">★ {rating:.1f}</span>
              </div>
              <p class="hero-overview">{movie.get('overview', 'No overview available.')}</p>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="section-label">Similar Titles</div>', unsafe_allow_html=True)

        similar_raw = get_similar_movies(movie["id"])
        similar     = filter_similar(similar_raw, genre_id, min_year, max_year)[:10]

        if similar:
            cols = st.columns(5)
            for i, sm in enumerate(similar):
                with cols[i % 5]:
                    render_movie_card(sm, key_prefix="sim")

            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown('<div class="section-label">Similar Titles — Data Table</div>', unsafe_allow_html=True)

            import pandas as pd
            table_data = []
            for sm in similar:
                table_data.append({
                    "Title":       sm.get("title", ""),
                    "Year":        (sm.get("release_date") or "")[:4],
                    "Rating":      round(sm.get("vote_average", 0), 1),
                    "Votes":       sm.get("vote_count", 0),
                    "Popularity":  round(sm.get("popularity", 0), 1),
                    "Overview":    sm.get("overview", ""),
                })
            df = pd.DataFrame(table_data)

            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True,
                height=420,
                column_config={
                    "Title":      st.column_config.TextColumn("Title", width="medium"),
                    "Year":       st.column_config.TextColumn("Year", width="small"),
                    "Rating":     st.column_config.NumberColumn("Rating", format="⭐ %.1f", width="small"),
                    "Votes":      st.column_config.NumberColumn("Votes", format="%d", width="small"),
                    "Popularity": st.column_config.ProgressColumn("Popularity", min_value=0, max_value=500, format="%.1f", width="medium"),
                    "Overview":   st.column_config.TextColumn("Overview", width="large"),
                },
                column_order=["Title", "Year", "Rating", "Votes", "Popularity", "Overview"],
            )
        else:
            st.markdown('<div class="not-found">No similar movies match your filters.</div>', unsafe_allow_html=True)

        st.markdown("<hr class='pink-divider'>", unsafe_allow_html=True)

    else:
        st.markdown(f'<div class="not-found" style="margin-top:1rem">No results found for <em>"{movie_name}"</em>.</div>', unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

# Featured 
browse_label = f"Popular in {genre_label}" if genre_label != "All" else "Popular Right Now"
st.markdown(f'<div class="section-label">{browse_label}</div>', unsafe_allow_html=True)

current_page = st.session_state.browse_page
popular, total_pages = get_popular_movies(genre_id, min_year, max_year, page=current_page)

if popular:
    cols = st.columns(5)
    for i, m in enumerate(popular):
        with cols[i % 5]:
            render_movie_card(m, key_prefix=f"pop_p{current_page}")

    st.markdown("<br>", unsafe_allow_html=True)

    def page_range(current, total):
        pages = set([1, total])
        for p in range(max(1, current - 3), min(total, current + 3) + 1):
            pages.add(p)
        sorted_pages = sorted(pages)
        result, prev_p = [], None
        for p in sorted_pages:
            if prev_p is not None and p - prev_p > 1:
                result.append(None)
            result.append(p)
            prev_p = p
        return result

    visible = page_range(current_page, total_pages)

    col_widths = []
    for item in visible:
        if item is None:       col_widths.append(0.6)
        elif item >= 10:       col_widths.append(1.5)
        else:                  col_widths.append(1)
    pad = max(1, (20 - sum(col_widths)) / 2)
    pg_cols = st.columns([pad] + col_widths + [pad])

    for idx, item in enumerate(visible):
        with pg_cols[idx + 1]:
            if item is None:
                st.markdown('<p style="text-align:center;color:#5a2e3c;margin:0;line-height:2.4rem">…</p>', unsafe_allow_html=True)
            else:
                if st.button(str(item), key=f"pg_{item}", use_container_width=True):
                    st.session_state.browse_page = item
                    st.rerun()

    pg_js = f"""<script>
(function(){{
    var t = "{current_page}";
    document.querySelectorAll('button[data-testid^="pg_"]').forEach(function(b){{
        if(b.innerText.trim()===t){{
            b.style.background="#e8658a";
            b.style.color="#1a0d12";
            b.style.borderColor="#e8658a";
            b.style.fontWeight="700";
        }}
    }});
}})();
</script>
<p class="page-info">Page {current_page} of {total_pages}</p>"""
    st.markdown(pg_js, unsafe_allow_html=True)

else:
    st.markdown('<div class="not-found">No movies found for the selected filters.</div>', unsafe_allow_html=True)

# Footer 
st.markdown("""
<div class="site-footer">
  Movie data provided by <a href="https://www.themoviedb.org/" target="_blank">TMDb</a> &mdash; This product uses the TMDb API but is not endorsed by TMDb.
</div>
""", unsafe_allow_html=True)