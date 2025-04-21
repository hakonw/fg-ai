import time
import os

try:
    from dotenv import load_dotenv
    load_dotenv()
    print("dotenv loaded")
except ImportError:
    pass

if os.getenv("POSTGRES_HOST") is None:
    raise ValueError("POSTGRES_HOST is not set")
if os.getenv("POSTGRES_PASSWORD") is None:
    raise ValueError("POSTGRES_PASSWORD is not set")

import streamlit as st

st.set_page_config(
    page_title="Ai av Fotogjengens arkiv 📷",
    initial_sidebar_state="collapsed",
    layout="wide"
)

st.sidebar.header("Logg")
last_log = time.time()
def log(title, obj, json=False):
    global last_log
    now = time.time()
    log_container = st.sidebar.expander(expanded=False, label=f"+{now-last_log:.0f}s: {title}")
    if json:
        log_container.json(obj)
    else:
        log_container.write(obj if obj else title)
    last_log = now

st.write("""
# Ai av Fotogjengens arkiv 📷
*Laget av Wardeberg*

Denne tjenesten lagrer **ikke** bildet du laster opp. Siden har et subset av FG sine bilder. Både nye og veldig gamle bilder kan være uprosessert.
         
Logg på [foto.samfundet.no](https://foto.samfundet.no/arkiv/DIGGC/18/19/) før du begynner for å se internbilder.
         
Den viser mange *ikke riktige* bilder.

[Kildekode på github](https://github.com/hakonw/fg-ai)
""")

st.divider()

image_input = st.file_uploader("Last opp bilde", type=["jpg", "jpeg", "png"], accept_multiple_files=False)

input_col1, intput_col2 = st.columns(2)
dist_algo = input_col1.segmented_control("Vektoravstand", ["L2", "Cosine"], default="Cosine")
max_images = intput_col2.slider("Maks antall bilder", 20, 500, 100)

with st.spinner("Laster ai-modell minnet"):
    import face_recognition

if not image_input:
    st.stop()

log("Image uploaded", {"name": image_input.name, "type": image_input.type})

with st.expander("Opplastet bilde", expanded=False):
    st.image(image_input, caption="Opplastet bilde", use_container_width=True)

image_embeddings = face_recognition.embed(image_input)

if image_embeddings is None or len(image_embeddings) == 0:
    st.warning("Ingen ansikt funnet i bildet")
    st.stop()

log("Embedding generert", image_embeddings, json=True)

conn = st.connection("postgresql",
                     type="sql",
                     host=os.getenv("POSTGRES_HOST"),
                     username="postgres",
                     password=os.getenv("POSTGRES_PASSWORD"),
                     dialect="postgresql",
                     )
log("Tilkoblet database", None)


if dist_algo == "L2":
    distance_op = "<->"
elif dist_algo == "Cosine":
    distance_op = "<=>"
else:
    distance_op = "<=>"

assert isinstance(max_images, int), "max_images must be an integer"

embedding = image_embeddings[0]["embedding"]
query = f'''
WITH embeddings AS (
  SELECT
    e.image_id,
    MIN(e.embedding {distance_op} '{embedding}') AS distance
  FROM embeddingfacenet e
  GROUP BY e.image_id
)
SELECT
  i.*,
  e1.distance
FROM embeddings e1
JOIN image i ON i.id = e1.image_id
ORDER BY e1.distance
LIMIT {max_images};
'''

results = conn.query(query, show_spinner="Sammenligner bilder")

log("Data hentet", f"Rader: {len(results)}")


html_images = ""

for image in results.itertuples():
    url = f"https://fg.samfundet.no{image.arkiv}"
    thumbnail_url = f"https://fg.samfundet.no{image.thumbnail}"
    
    html_images += f"""
        <div class="image-card">
            <a href="{url}" target="_blank">
            <img src="{thumbnail_url}" alt="{image.motive}">
            </a>
            <p>{image.motive}</p>
        </div>
    """

st.html(f"""
    <style>
    .image-container {{
        display: grid;
        grid-gap: 10px;
        grid-template-columns: repeat(auto-fill, minmax(300px,1fr));
        align-items: center;
    }}
    .image-card {{
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        padding: 10px;
        border-radius: 10px;
        background: #fff;
    }}
    .image-card img {{
        width: 100%;
        border-radius: 8px;
    }}
    .image-card p {{
        text-align: center;
        margin: 0;
    }}
    </style>

    <div class="image-container">
        {html_images}
    </div>
""")


# with st.empty():
#     cols = st.columns(3)
#     for i, image in enumerate(results.itertuples(), 0):
#         with cols[i % 3]:
#             download_url = f"https://fg.samfundet.no/{image.download_link}"
#             thumbnail_url = f"https://fg.samfundet.no/{image.thumbnail}"
#             st.image(thumbnail_url,
#                     caption=f"{image.motive} [Lenke]({download_url})",
#                     use_container_width=True)