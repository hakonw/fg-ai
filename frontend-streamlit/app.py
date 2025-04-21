import time
import os
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

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
    logging.info(title)
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

Denne tjenesten lagrer **ikke** bildet du laster opp. Siden har blitt kjørt på et subset av FG sine bilder. Både nye og veldig gamle bilder kan være uprosessert.
         
Logg på [foto.samfundet.no](https://foto.samfundet.no/arkiv/DIGGC/18/19/) før du begynner for å se internbilder.
Takk til FG for bildene! 
Alle bilder skal krediteres med: `Foto: foto.samfundet.no`
         
Den viser mange *ikke riktige* bilder. 😐

[Kildekode på github](https://github.com/hakonw/fg-ai)
""")

st.divider()

image_input = st.empty()

input_col1, input_col2 , input_col3= st.columns(3)
dist_algo = input_col1.segmented_control("Vektoravstand", ["L2", "Cosine"], default="Cosine")
max_images = input_col2.slider("Maks antall bilder", 20, 500, 100)
cutoff = input_col3.slider("Likhetsgrense", 0.5, 0.95, 0.7, help="Grensen på hvor lik bildet må være for å bli vist.")

query_embeddings = st.query_params.get("embedding")
if query_embeddings:
    try:
        assert len(query_embeddings) > 100
        query_embeddings = [float(x) for x in query_embeddings[1:-1].split(",")]
        if len(query_embeddings) != 512:
            raise ValueError("Embedding must be a list of 512 floats")
    except:
        st.error(f"Ugyldig embedding format")
        st.stop()
    image_embeddings = [{
        "embedding": query_embeddings
    }]
    st.write("Bruker egendefinert embedding")
    st.button("Fjern embedding", on_click=lambda: st.query_params.clear())
else:
    image_input = image_input.file_uploader("Last opp bilde", type=["jpg", "jpeg", "png"], accept_multiple_files=False)


    with st.spinner("Laster ai-modell"):
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
    e.embedding,
    e.embedding {distance_op} '{embedding}' AS distance
  FROM embeddingfacenet e
  WHERE e.embedding {distance_op} '{embedding}' < 0.5
),
ranked_embeddings AS (
  SELECT DISTINCT ON (image_id)
    e.image_id,
    e.embedding,
    e.distance
  FROM embeddings e
  ORDER BY e.image_id, e.distance ASC
)
SELECT
  i.*,
  r.distance,
  r.embedding
FROM ranked_embeddings r
JOIN image i ON i.id = r.image_id
ORDER BY r.distance
LIMIT {max_images};
'''

results = conn.query(query, show_spinner="Sammenligner bilder")

if len(results) == 0:
    st.warning("Ingen bilder funnet. Prøv å last opp et annet bilde.")
    st.stop()

log("Data hentet", f"Rader: {len(results)}")

html_images = ""

for image in results.itertuples():
    url = f"https://fg.samfundet.no{image.arkiv}"
    thumbnail_url = f"https://fg.samfundet.no{image.thumbnail}"
    download_url = f"https://fg.samfundet.no{image.download_link}"
    
    if (1-image.distance) < cutoff:
        continue

    html_images += f"""
        <div class="image-card">
            <a href="{url}" target="_blank">
            <img src="{thumbnail_url}" alt="{image.motive}">
            </a>
            <p>{image.motive}</p>
            <p>Likhet: {(1-image.distance):.2f} <a href="?embedding={image.embedding}">Se lignende</a> <a href="{download_url}">Last ned</a></p>
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