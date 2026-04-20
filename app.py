import streamlit as st
import pandas as pd
import requests
import re
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import CountVectorizer

# ---------------- CONFIG ---------------- #
st.set_page_config(page_title="📚 Book Recommender", layout="wide")

# ---------------- CUSTOM CSS (NETFLIX UI) ---------------- #
st.markdown("""
<style>
body {
    background-color: #0e1117;
    color: white;
}
.book-card {
    background-color: #1c1f26;
    padding: 10px;
    border-radius: 12px;
    text-align: center;
    transition: transform 0.2s;
}
.book-card:hover {
    transform: scale(1.05);
}
.title {
    font-size: 14px;
    font-weight: 600;
}
</style>
""", unsafe_allow_html=True)

# ---------------- LOAD DATA (NO PKL ✅) ---------------- #
@st.cache_data
def load_data():
    books = pd.read_csv("books.csv")

    # Clean data
    books = books.dropna(subset=["title"])
    books["authors"] = books["authors"].fillna("")

    # Create tags
    books["tags"] = books["title"] + " " + books["authors"]

    cv = CountVectorizer(max_features=5000, stop_words="english")
    vectors = cv.fit_transform(books["tags"]).toarray()

    similarity = cosine_similarity(vectors)

    return books, similarity

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
st.sidebar.title("📚 Book Recommender")

selected_book = st.sidebar.selectbox(
    "🔍 Select a book",
    books['title'].values
)

top_n = st.sidebar.slider("📊 Number of recommendations", 3, 10, 5)

st.sidebar.markdown("---")

st.sidebar.info("""
🎯 Features:
- ML-based recommendations
- Netflix-style UI
- Book ratings display
- API-based images
""")

# ---------------- MAIN TITLE ---------------- #
st.markdown(
    "<h1 style='text-align:center;'>📚 Book Recommendation System</h1>",
    unsafe_allow_html=True
)

st.markdown("<hr>", unsafe_allow_html=True)

# ---------------- BUTTON ---------------- #
if st.button("🚀 Recommend"):

    with st.spinner("Finding best books for you..."):

        results = recommend(selected_book, top_n)

        st.markdown("## 🎬 Recommended For You")

        cols = st.columns(top_n)

        for i, book in enumerate(results):
            with cols[i]:

                img = fetch_image(book.title)

                # ⭐ rating (if exists)
                rating = book["average_rating"] if "average_rating" in books.columns else "N/A"

                # Netflix-style card
                st.markdown(f"""
                <div class="book-card">
                    <img src="{img}" style="width:100%; border-radius:10px;" />
                    <div class="title">{book.title}</div>
                    <div>⭐ {rating}</div>
                </div>
                """, unsafe_allow_html=True)

        st.success("✅ Recommendations ready!")
