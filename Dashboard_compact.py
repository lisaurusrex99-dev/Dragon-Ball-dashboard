
from pathlib import Path
from decimal import Decimal, InvalidOperation
import base64
import re

import pandas as pd
import requests
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
CSV_FILE = ROOT / "dragon_ball_69_complete_structure.csv"

GREEN = "#39b54a"


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
        </style>
        """,
        unsafe_allow_html=True
    )


# ==========================================
# HELPER FUNCTIONS
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


def show_image(url):
    if isinstance(url, str) and url.startswith(
        ("https://", "http://")
    ):
        st.image(url, width="stretch")
    else:
        st.caption("No image available")


# ==========================================
# LOAD CSV + API
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
        "win_rate_pct"
    ]

    missing = [
        column for column in required
        if column not in data.columns
    ]

    if missing:
        raise ValueError(
            "Missing CSV columns: " + ", ".join(missing)
        )

    # Optional Dragon Ball API information
    api_characters = {}

    try:
        response = requests.get(
            "https://dragonball-api.com/api/characters",
            params={"limit": 100},
            timeout=12
        )
        response.raise_for_status()

        payload = response.json()

        items = (
            payload.get("items", [])
            if isinstance(payload, dict)
            else payload
        )

        for character in items:
            key = name_key(character.get("name", ""))
            api_characters[key] = character

    except (requests.RequestException, ValueError, TypeError):
        pass

    aliases = {
        "chichi": "chichi",
        "krillin": "krilin",
        "masterroshi": "roshi",
        "frieza": "freezer",
        "futuretrunks": "trunks",
        "trunkskid": "trunks",
        "android17": "androide17",
        "android18": "androide18",
        "majinbuu": "majinbuu"
    }

    characters = []

    for _, row in data.iterrows():

        name = text_value(row["english_name"])
        key = name_key(name)
        api_key = aliases.get(key, key)

        info = api_characters.get(
            api_key,
            api_characters.get(key, {})
        )

        # Avoid assigning another character's API
        # information when names are ambiguous.
        if key in ["futuretrunks", "trunkskid"]:
            info = {}

        ki = text_value(info.get("ki"))
        max_ki = text_value(info.get("maxKi"))

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
            "race": text_value(info.get("race")),
            "gender": text_value(info.get("gender")),
            "affiliation": text_value(
                info.get("affiliation")
            ),
            "image": info.get("image", ""),
"biography": text_value(
    row.get("bio") or info.get("description")
            ),
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
        '<a href="?" target="_self">← Back to Dashboard</a>',
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
    col2.metric("Maximum Ki", character["max_ki"])

    st.divider()
    st.header("BATTLE STATISTICS")

    a, b, c, d = st.columns(4)

    a.metric(
        "Total Battles",
        display_number(character["total_battles"])
    )
    b.metric(
        "Wins",
        display_number(character["wins"])
    )
    c.metric(
        "Losses",
        display_number(character["losses"])
    )
    d.metric(
        "Draws",
        display_number(character["draws"])
    )

    rate = pd.to_numeric(
        character["win_rate"],
        errors="coerce"
    )

    if pd.notna(rate):
        st.metric("Win Rate", f"{rate:.1f}%")
    else:
        st.metric("Win Rate", "Not verified")

    if numeric_value(character["total_battles"]) is None:
        st.warning(
            "Battle statistics are not yet verified "
            "for this character."
        )

    if character["scope"] != "Unknown":
        st.caption(
            "Battle data scope: " + character["scope"]
        )

    if character["source"].startswith(
        ("https://", "http://")
    ):
        st.link_button(
            "View Battle Source",
            character["source"]
        )

    st.divider()
    st.header("BIOGRAPHY")

    st.write(character["biography"])


# ==========================================
# CHARACTER CARDS
# ==========================================

def character_card(character, key):
    with st.container(border=True):
        show_image(character["image"])

        st.subheader(character["name"])

        st.caption(
            character["race"] + " | "
            + character["affiliation"]
        )

        st.write(
            "**Battles:**",
            display_number(character["total_battles"])
        )

        from urllib.parse import quote

        url = "?character=" + quote(character["name"], safe="")

        st.markdown(
            f'<a href="{url}" target="_self">View Profile →</a>',
            unsafe_allow_html=True
        )

# ==========================================
# MAIN APPLICATION
# ==========================================

setup_design()

if not CSV_FILE.exists():
    st.error(
        "CSV not found: "
        "dragon_ball_69_complete_structure.csv"
    )
    st.stop()

try:
    df = load_data()

except Exception as error:
    st.error(f"Could not load data: {error}")
    st.stop()

if "selected_character" not in st.session_state:
    st.session_state.selected_character = None
# ==========================================
# HEADER
# ==========================================

st.title("EVERYTHING DRAGON BALL")

st.caption(
    "Character encyclopedia | Power Levels | "
    "Battle Statistics"
)


# ==========================================
# PROFILE VIEW
# ==========================================

selected = st.query_params.get("character")
if selected is not None:

    matches = df[df["name"] == selected]

    if not matches.empty:
        show_profile(matches.iloc[0])

    else:
        st.session_state.selected_character = None

    st.stop()


# ==========================================
# DASHBOARD OVERVIEW
# ==========================================

st.header("DASHBOARD OVERVIEW")

verified = df[df["total_battles"].notna()].copy()

a, b, c = st.columns(3)

a.metric("IT'S OVER 68?!", f"{len(df)} TOTAL CHARACTERS!")

b.metric(
    "Characters with Battle Data",
    len(verified)
)

c.metric(
    "Battles in Available Records",
    display_number(verified["total_battles"].sum())
    if not verified.empty
    else "Not verified"
)

st.caption(
    "The combined battle count is a sum of character "
    "records, not a count of unique fights. "
    "Some fights may appear for multiple characters."
)

st.divider()


# ==========================================
# RANKINGS
# ==========================================

st.header("CHARACTER RANKINGS")

strongest = df[df["power"].notna()].copy()

if not strongest.empty:
    strongest = strongest.sort_values(
        "power",
        ascending=False
    )

weakest = strongest.sort_values(
    "power",
    ascending=True
)

most_battles = verified.sort_values(
    "total_battles",
    ascending=False
)

col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("TOP 5 STRONGEST")

    if strongest.empty:
        st.info("No Ki data available.")
    else:
        for index, (_, character) in enumerate(
            strongest.head(5).iterrows()
        ):
            character_card(
                character,
                f"strong_{index}"
            )

with col2:
    st.subheader("TOP 5 WEAKEST")

    if weakest.empty:
        st.info("No Ki data available.")
    else:
        for index, (_, character) in enumerate(
            weakest.head(5).iterrows()
        ):
            character_card(
                character,
                f"weak_{index}"
            )

with col3:
    st.subheader("TOP 5 MOST BATTLES")

    if most_battles.empty:
        st.info("No verified battle data.")
    else:
        for index, (_, character) in enumerate(
            most_battles.head(5).iterrows()
        ):
            character_card(
                character,
                f"battle_{index}"
            )

st.divider()


# ==========================================
# EXPLORE CHARACTERS
# ==========================================

st.header("EXPLORE ALL CHARACTERS")

search = st.text_input(
    "Search Characters",
    placeholder="Goku, Vegeta, Frieza..."
)

filtered = df[
    df["name"].str.contains(
        search,
        case=False,
        na=False,
        regex=False
    )
].copy()

race_options = sorted(df["race"].unique())

selected_races = st.multiselect(
    "Filter by Race",
    race_options
)

if selected_races:
    filtered = filtered[
        filtered["race"].isin(selected_races)
    ]

battle_filter = st.checkbox(
    "Only characters with battle statistics"
)

if battle_filter:
    filtered = filtered[
        filtered["total_battles"].notna()
    ]

st.caption(
    f"Showing {len(filtered)} of {len(df)} characters"
)

for start in range(0, len(filtered), 4):

    columns = st.columns(4)
    batch = filtered.iloc[start:start + 4]

    for column, (_, character) in zip(
        columns,
        batch.iterrows()
    ):

        with column:
            character_card(
                character,
                f"all_{character['name']}"
            )


# ==========================================
# FOOTER
# ==========================================

st.divider()

st.caption(
    "Data: Dragon Ball API and Dragon Ball "
    "battle research CSV. Missing statistics "
    "are displayed as Not verified, not zero."
)
