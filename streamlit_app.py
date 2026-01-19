import streamlit as st
import tempfile
import os
import glob
from PIL import Image
import io
from contextlib import redirect_stdout

import uuid

import create_map_poster as cmp

# ─────────────────────────────
# Page config
# ─────────────────────────────
st.set_page_config(page_title="MapToPoster", page_icon="🗺️", layout="centered")

st.title("🖼️ MapToPoster")
st.caption("Cities, turned into quiet geometry.")

# ─────────────────────────────
# Paths
# ─────────────────────────────
THEMES_DIR = "themes"
POSTERS_DIR = "posters"

# ─────────────────────────────
# Inputs
# ─────────────────────────────
city = st.text_input("City", placeholder="Berlin")
country = st.text_input("Country", placeholder="Germany")

themes = cmp.get_available_themes()

default_theme = "blueprint"

default_index = themes.index(default_theme) if default_theme in themes else 0

selected_theme = st.selectbox("Theme", themes, index=default_index)


distance = st.slider(
    "Map Radius (meters)", min_value=1000, max_value=20000, value=1000, step=1000
)

st.markdown("### 👀 Theme Preview")

preview_images = glob.glob(os.path.join(POSTERS_DIR, f"*{selected_theme}*.png"))

if preview_images:
    img_path = preview_images[0]  # pick the first one only
    st.image(Image.open(img_path), width=300)
else:
    st.caption("No preview posters found for this theme.")

# ─────────────────────────────
# Generate poster
# ─────────────────────────────
st.markdown("---")
generate = st.button("✨ Generate Poster")


def generate_poster_live(city, country, theme, distance):
    cmp.THEME = cmp.load_theme(theme)
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        output_file = tmp.name

    # placeholder for live output
    output_placeholder = st.empty()

    # custom file-like object that writes to Streamlit
    class StreamlitWriter(io.TextIOBase):
        def __init__(self):
            self.buffer = ""

        def write(self, s):
            self.buffer += s
            output_placeholder.text(self.buffer)
            return len(s)

        def flush(self):
            pass

    writer = StreamlitWriter()

    # redirect prints to Streamlit in real time
    with redirect_stdout(writer):
        coords = cmp.get_coordinates(city, country)
        cmp.create_poster(city, country, coords, distance, output_file)

    # load poster from temp file
    img = Image.open(output_file)
    return img, output_file


if generate:
    with st.spinner("Rendering the map…"):
        try:
            img, output_file = generate_poster_live(
                city, country, selected_theme, distance
            )
            st.success("Poster generated!")

            # show in Streamlit
            st.image(img, width=400)

            # download button
            with open(output_file, "rb") as f:
                st.download_button(
                    label="⬇️ Download Poster",
                    data=f,
                    file_name=f"{city.replace(' ','_')}_{distance}_{selected_theme}.png",
                    mime="image/png",
                )

            # optionally delete temp file
            os.remove(output_file)

        except Exception as e:
            st.error(f"Error generating poster: {e}")
