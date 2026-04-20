import streamlit as st
import pandas as pd
import requests
import re
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import CountVectorizer

st.set_page_config(page_title="📚 Book Recommender", layout="wide")

# ---------------- CSS ---------------- #
st.markdown("""
<style>
.book-card {
    background-color: #1c1f26;
    padding: 10px;
    border-radius: 12px;
    text-align: center;
}
.title {
    font-size: 14px;
    font-weight: 600;
}
</style>
""", unsafe_allow_html=True)

# ---------------- LOAD DATA ---------------- #
@st.cache_data
def load_data():
    books = pd.read_csv("books.csv")

    books = books.dropna(subset=["title"])
    books["authors"] = books["authors"].fillna("")

    # 🔥 LIMIT DATA (IMPORTANT FOR STREAMLIT)
    books = books.head(5000)

    books["tags"] = books["title"] + " " + books["authors"]

    cv = CountVectorizer(max_features=3000, stop_words="english")
    vectors = cv.fit_transform(books["tags"]).toarray()

    similarity = cosine_similarity(vectors)

    return books, similarity

books, similarity = load_data()

# ---------------- IMAGE ---------------- #
@st.cache_data
def fetch_image(book_name):
    try:
        clean = re.sub(r"\(.*?\)", "", book_name)

        url = f"https://openlibrary.org/search.json?title={clean}&limit=1"
        res = requests.get(url, timeout=3)

        if res.status_code == 200:
            data = res.json()
            if data.get("docs"):
                cover_id = data["docs"][0].get("cover_i")
                if cover_id:
                    return f"https://covers.openlibrary.org/b/id/{cover_id}-L.jpg"
    except:
        pass

    return "https://via.placeholder.com/150"

# ---------------- RECOMMEND ---------------- #
def recommend(book, n=5):
    index = books[books['title'] == book].index[0]
    distances = similarity[index]

    books_list = sorted(
        list(enumerate(distances)),
        key=lambda x: x[1],
        reverse=True
    )[1:n+1]

    return [books.iloc[i[0]] for i in books_list]

# ---------------- SIDEBAR ---------------- #
st.sidebar.title("📚 Book Recommender")

selected_book = st.sidebar.selectbox(
    "🔍 Select a book",
    books['title'].values
)

top_n = st.sidebar.slider("📊 Number of recommendations", 3, 10, 5)

# ---------------- MAIN ---------------- #
st.markdown("<h1 style='text-align:center;'>📚 Book Recommendation System</h1>", unsafe_allow_html=True)
st.markdown("<hr>", unsafe_allow_html=True)

if st.button("🚀 Recommend"):

    with st.spinner("Finding best books..."):

        results = recommend(selected_book, top_n)

        cols = st.columns(top_n)

        for i, book in enumerate(results):
            with cols[i]:

                img = fetch_image(book.title)

                rating = book["average_rating"] if "average_rating" in books.columns else "N/A"

                st.markdown(f"""
                <div class="book-card">
                    <img src="{img}" width="100%">
                    <div class="title">{book.title}</div>
                    <div>⭐ {rating}</div>
                </div>
                """, unsafe_allow_html=True)

        st.success("✅ Done!")
