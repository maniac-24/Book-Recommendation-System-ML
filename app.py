import streamlit as st
import pickle
import pandas as pd
import requests
import re

# ---------------- CONFIG ---------------- #
st.set_page_config(page_title="Book Recommender", layout="wide")

# ---------------- LOAD DATA ---------------- #
@st.cache_data
def load_data():
    books_dict = pickle.load(open('book_dict.pkl', 'rb'))
    similarity = pickle.load(open('book_similarity.pkl', 'rb'))
    return pd.DataFrame(books_dict), similarity

books, similarity = load_data()

# ---------------- FETCH IMAGE ---------------- #
@st.cache_data
def fetch_image(book_name):
    try:
        clean_name = re.sub(r"\(.*?\)", "", book_name).strip()

        # OpenLibrary
        url = f"https://openlibrary.org/search.json?title={clean_name}&limit=1"
        res = requests.get(url, timeout=5).json()

        if res.get("docs"):
            cover_id = res["docs"][0].get("cover_i")
            if cover_id:
                return f"https://covers.openlibrary.org/b/id/{cover_id}-L.jpg"

        # Google Books fallback
        url2 = f"https://www.googleapis.com/books/v1/volumes?q=intitle:{clean_name}"
        res2 = requests.get(url2, timeout=5).json()

        if "items" in res2:
            for item in res2["items"]:
                img = item.get("volumeInfo", {}).get("imageLinks", {}).get("thumbnail")
                if img:
                    return img

    except:
        pass

    return "https://via.placeholder.com/150?text=No+Image"

# ---------------- RECOMMEND FUNCTION ---------------- #
def recommend(book, n=5):
    index = books[books['title'] == book].index[0]
    distances = similarity[index]

    books_list = sorted(
        list(enumerate(distances)),
        reverse=True,
        key=lambda x: x[1]
    )[1:n+1]

    return [books.iloc[i[0]] for i in books_list]

# ---------------- SIDEBAR ---------------- #
st.sidebar.title("📚 About")

st.sidebar.info("""
### Book Recommendation System

- 🤖 ML: Cosine Similarity  
- 🖼️ Images: OpenLibrary + Google API  
- ⚡ UI: Streamlit  
""")

st.sidebar.markdown("---")

selected_book = st.sidebar.selectbox(
    "🔍 Select a book",
    books['title'].values
)

top_n = st.sidebar.slider("📊 Number of recommendations", 3, 10, 5)

# ---------------- MAIN UI ---------------- #
st.markdown(
    "<h1 style='text-align: center;'>📚 Book Recommendation System</h1>",
    unsafe_allow_html=True
)

st.markdown("<hr>", unsafe_allow_html=True)

# ---------------- RECOMMEND BUTTON ---------------- #
if st.button("🚀 Recommend"):

    with st.spinner("Finding best books for you..."):

        results = recommend(selected_book, top_n)

        st.markdown("## 📖 Recommended Books")

        cols = st.columns(top_n)

        for i, book in enumerate(results):
            with cols[i]:

                img = fetch_image(book.title)

                st.image(img, use_container_width=True)

                # Title
                st.markdown(
                    f"<div style='font-weight:600; font-size:14px;'>{book.title}</div>",
                    unsafe_allow_html=True
                )

                # Optional fields (safe check)
                if 'authors' in books.columns:
                    st.caption(f"✍️ {book.authors}")

                if 'average_rating' in books.columns:
                    st.caption(f"⭐ {book.average_rating}")

        st.success("✅ Recommendations ready!")