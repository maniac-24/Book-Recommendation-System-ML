import streamlit as st
import pandas as pd
import requests
import re
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import CountVectorizer

st.set_page_config(page_title="📚 Book Recommender", layout="wide")

# ---------------- CSS (PREMIUM UI) ---------------- #
st.markdown("""
<style>
body {
    background-color: #0e1117;
}

.main-title {
    text-align: center;
    font-size: 40px;
    font-weight: bold;
    margin-bottom: 10px;
}

.search-box {
    display: flex;
    justify-content: center;
    margin-bottom: 20px;
}

.book-card {
    background: linear-gradient(145deg, #1c1f26, #111318);
    padding: 12px;
    border-radius: 15px;
    text-align: center;
    transition: 0.3s;
}

.book-card:hover {
    transform: scale(1.07);
    box-shadow: 0 10px 25px rgba(255,255,255,0.15);
}

.title {
    font-size: 14px;
    font-weight: 600;
    margin-top: 8px;
}

.rating {
    color: gold;
    font-weight: bold;
}
</style>
""", unsafe_allow_html=True)

# ---------------- LOAD DATA ---------------- #
@st.cache_data
def load_data():
    books = pd.read_csv("books.csv")

    books = books.dropna(subset=["title"])
    books["authors"] = books["authors"].fillna("")

    books = books.head(5000)  # performance

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

    return "https://via.placeholder.com/150?text=No+Image"

# ---------------- RECOMMEND ---------------- #
def recommend(book, n=5):
    try:
        index = books[books['title'] == book].index[0]
    except:
        return []

    distances = similarity[index]

    books_list = sorted(
        list(enumerate(distances)),
        key=lambda x: x[1],
        reverse=True
    )[1:n+1]

    return [books.iloc[i[0]] for i in books_list]

# ---------------- HEADER ---------------- #
st.markdown("<div class='main-title'>📚 Book Recommender</div>", unsafe_allow_html=True)

# ---------------- GOOGLE-STYLE SEARCH ---------------- #
search = st.text_input("🔍 Search for a book (like Google)...")

# Filter books based on search
filtered_books = books
if search:
    filtered_books = books[books['title'].str.contains(search, case=False)]

# ---------------- SIDEBAR ---------------- #
st.sidebar.title("⚙️ Settings")

selected_book = st.sidebar.selectbox(
    "📖 Choose a book",
    filtered_books['title'].values
)

top_n = st.sidebar.slider("📊 Recommendations", 3, 10, 5)

# ---------------- TRENDING SECTION ---------------- #
st.markdown("## 🔥 Trending Books")

top_books = books.sort_values(by="average_rating", ascending=False).head(5)
cols = st.columns(5)

for i, book in enumerate(top_books.itertuples()):
    with cols[i]:
        img = fetch_image(book.title)
        st.image(img)
        st.caption(book.title)

st.markdown("---")

# ---------------- BUTTON ---------------- #
if st.button("🚀 Recommend"):

    with st.spinner("Finding best books for you..."):

        results = recommend(selected_book, top_n)

        if not results:
            st.error("❌ Book not found")
        else:
            st.markdown("## 🎯 Recommended For You")

            cols = st.columns(top_n)

            for i, book in enumerate(results):
                with cols[i]:

                    img = fetch_image(book.title)
                    rating = book["average_rating"] if "average_rating" in books.columns else "N/A"

                    st.markdown(f"""
                    <div class="book-card">
                        <img src="{img}" width="100%" style="border-radius:10px;">
                        <div class="title">{book.title}</div>
                        <div class="rating">⭐ {rating}</div>
                    </div>
                    """, unsafe_allow_html=True)

            st.success("✅ Recommendations ready!")
