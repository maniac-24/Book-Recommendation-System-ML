import streamlit as st
import pickle
import pandas as pd

books_dict = pickle.load(open('book_dict.pkl', 'rb'))
similarity = pickle.load(open('book_similarity.pkl', 'rb'))

books = pd.DataFrame(books_dict)

st.title("📚 Book Recommendation System")

selected_book = st.selectbox(
    "Choose a book",
    books['title'].values
)

def recommend(book):
    index = books[books['title'] == book].index[0]
    distances = similarity[index]

    books_list = sorted(list(enumerate(distances)), reverse=True, key=lambda x: x[1])[1:6]

    names = []
    images = []

    for i in books_list:
        names.append(books.iloc[i[0]].title)
        images.append(books.iloc[i[0]].image_url)

    return names, images

if st.button("Recommend"):
    names, images = recommend(selected_book)

    cols = st.columns(5)
    for i in range(len(names)):
        with cols[i]:
            st.text(names[i])
            st.image(images[i])