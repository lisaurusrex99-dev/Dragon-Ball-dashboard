from pathlib import Path
from decimal import Decimal, InvalidOperation
from urllib.parse import quote
import base64
import re

import pandas as pd
import streamlit as st


# ==========================================
# SETTINGS
# ==========================================

st.set_page_config(
    page_title="Everything Dragon Ball",
    page_icon="🐉",
    layout="wide"
)

ROOT = Path(__file__).resolve().parent
CSV_FILE = ROOT / "dragon_ball_69_OFFLINE_DATABASE.csv"
IMAGES_DIR = ROOT / "images"

GREEN = "#39b54a"


# ==========================================
# LOCAL IMAGE FILES
# ==========================================

# These names match the files in your screenshot.
# No renaming or format conversion is necessary.

LOCAL_IMAGES = {
    "goten": "Goten.jpeg",
    "futuretrunks": "Future Trunks.png",
    "trunkskid": "Trunks (kid).jpeg",
    "chaozu": "Chaozu.webp",
    "yajirobe": "Yajirobe.jpg",
    "videl": "Videl.png",
    "gokublack": "Goku Black.png",
    "zamasu": "Future_Zamasu.webp",
    "pan": "Pan.webp",
    "korin": "Korin.webp",
    "hit": "Hit.webp",
    "kefla": "Kefla.webp"
}


# ==========================================
# DESIGN
# ==========================================

def setup_design():

    font_css = ""

    for filename in [
        "angers-Regular.ttf",
        "Bangers-Regular.ttf",
        "LilitaOne-Regular.ttf"
    ]:
        font = ROOT / filename

        if font.exists():

            encoded = base64.b64encode(
                font.read_bytes()
            ).decode("utf-8")

            font_css = f"""
            @font-face {{
                font-family: DragonFont;
                src: url(data:font/ttf;base64,{encoded});
            }}
            """
            break

    st.markdown(
        f"""
        <style>
        {font_css}

        .stApp {{
            background-color: #090909;
            color: white;
        }}

        .block-container {{
            max-width: 1450px;
            padding-top: 2rem;
        }}

        h1, h2, h3 {{
            font-family: DragonFont, Impact, sans-serif;
            color: white !important;
        }}

        h1 {{
            border-bottom: 4px solid {GREEN};
            padding-bottom: 12px;
        }}

        [data-testid="stMetric"] {{
            background: #191919;
            border: 1px solid {GREEN};
            padding: 15px;
            border-radius: 12px;
        }}

        div.stButton > button {{
            background: #171717;
            color: white;
            border: 1px solid {GREEN};
            border-radius: 8px;
            width: 100%;
        }}

        div.stButton > button:hover {{
            background: {GREEN};
            color: black;
        }}

        [data-testid="stVerticalBlockBorderWrapper"] {{
            border-color: #333333;
        }}

        a {{
            color: {GREEN};
        }}
        </style>
        """,
        unsafe_allow_html=True
    )


# ==========================================
# HELPERS
# ==========================================

def text_value(value):

    if value is None:
        return "Unknown"

    try:
        if pd.isna(value):
            return "Unknown"
    except (TypeError, ValueError):
        pass

    value = str(value).strip()

    if value.lower() in ["", "nan", "none", "null"]:
        return "Unknown"

    return value


def numeric_value(value):

    result = pd.to_numeric(value, errors="coerce")

    if pd.isna(result):
        return None

    return int(result)


def display_number(value):

    number = numeric_value(value)

    if number is None:
        return "Not verified"

    return f"{number:,}"


def name_key(name):

    return re.sub(
        r"[^a-z0-9]",
        "",
        str(name).lower()
    )


def parse_ki(value):

    value = text_value(value).lower()

    if value == "unknown":
        return None

    value = value.replace(",", "").strip()

    match = re.fullmatch(
        r"(\d+(?:\.\d+)?)\s*([a-z]+)?",
        value
    )

    if not match:
        return None

    amount_text, unit = match.groups()

    magnitudes = {
        "thousand": 3,
        "million": 6,
        "billion": 9,
        "trillion": 12,
        "quadrillion": 15,
        "quintillion": 18,
        "sextillion": 21,
        "septillion": 24,
        "octillion": 27,
        "nonillion": 30
    }

    try:

        amount = Decimal(amount_text)

        if unit:
            if unit not in magnitudes:
                return None

            amount *= Decimal(10) ** magnitudes[unit]

        return amount

    except (InvalidOperation, ValueError, TypeError):
        return None


# ==========================================
# IMAGE HANDLING
# ==========================================

def get_character_image(name, image_url):

    key = name_key(name)

    # First check the 12 locally supplied images.
    if key in LOCAL_IMAGES:

        filename = LOCAL_IMAGES[key]
        path = IMAGES_DIR / filename

        if path.is_file():
            return str(path)

    # Then use an existing URL from the CSV.
    # This does not call the Dragon Ball API.
    url = text_value(image_url)

    if url.startswith(("https://", "http://")):
        return url

    return None


def show_image(image):

    if image:

        try:
            st.image(
                image,
                use_container_width=True
            )
        except Exception:
            st.caption("Image could not be loaded")

    else:
        st.caption("No image available")


# ==========================================
# LOAD OFFLINE DATABASE
# ==========================================

@st.cache_data(ttl=3600)
def load_data():

    data = pd.read_csv(CSV_FILE)

    required = [
        "english_name",
        "favorite_food",
        "name_origin",
        "total_battles",
        "wins",
        "losses",
        "draws",
        "win_rate_pct",
        "bio",
        "race",
        "gender",
        "affiliation",
        "image_url",
        "ki",
        "max_ki"
    ]

    missing = [
        column
        for column in required
        if column not in data.columns
    ]

    if missing:
        raise ValueError(
            "Missing database columns: "
            + ", ".join(missing)
        )

    characters = []

    for _, row in data.iterrows():

        name = text_value(row["english_name"])

        ki = text_value(row["ki"])
        max_ki = text_value(row["max_ki"])

        biography = text_value(row["bio"])

        if biography == "Unknown":
            biography = (
                "English biography not available "
                "for this character."
            )

        image = get_character_image(
            name,
            row["image_url"]
        )

        characters.append({

            "name": name,

            "favorite_food": text_value(
                row["favorite_food"]
            ),

            "name_origin": text_value(
                row["name_origin"]
            ),

            "total_battles": row["total_battles"],

            "wins": row["wins"],

            "losses": row["losses"],

            "draws": row["draws"],

            "win_rate": row["win_rate_pct"],

            "source": text_value(
                row.get("source_url")
            ),

            "scope": text_value(
                row.get("source_scope")
            ),

            "status": text_value(
                row.get("data_status")
            ),

            "race": text_value(
                row["race"]
            ),

            "gender": text_value(
                row["gender"]
            ),

            "affiliation": text_value(
                row["affiliation"]
            ),

            "image": image,

            "biography": biography,

            "ki": ki,

            "max_ki": max_ki,

            "power": parse_ki(max_ki)
        })

    return pd.DataFrame(characters)


# ==========================================
# CHARACTER PROFILE
# ==========================================

def show_profile(character):

    st.markdown(
        '<a href="?" target="_self">'
        '← Back to Dashboard</a>',
        unsafe_allow_html=True
    )

    st.divider()

    st.title(character["name"].upper())

    left, right = st.columns([1, 2])

    with left:
        show_image(character["image"])

    with right:

        st.subheader("CHARACTER INFORMATION")

        st.write("**Name:**", character["name"])

        st.write("**Race:**", character["race"])

        st.write("**Gender:**", character["gender"])

        st.write(
            "**Affiliation:**",
            character["affiliation"]
        )

        st.write(
            "**Favorite Food:**",
            character["favorite_food"]
        )

        st.write(
            "**Name Origin:**",
            character["name_origin"]
        )

    st.divider()

    st.header("POWER LEVELS")

    col1, col2 = st.columns(2)

    col1.metric("Base Ki", character["ki"])

    col2.metric(
        "Maximum Ki",
        character["max_ki"]
    )

    st.divider()

    st.header("BATTLE STATISTICS")

    a, b, c, d = st.columns(4)

    a.metric(
        "Total Battles",
        display_number(character["total_battles"])
    )

    b.metric(
