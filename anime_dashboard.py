import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from collections import Counter
import altair as alt

# Load data
@st.cache_data
def load_data():
    df = pd.read_csv("popular_anime.csv")
    df['release_date'] = pd.to_datetime(df['release_date'], errors='coerce')

    # Remove timezone (if any)
    df['release_date'] = df['release_date'].dt.tz_localize(None)

    df = df.dropna(subset=['release_date'])
    return df

df = load_data()

# Creating Dashboard
st.set_page_config(page_title="Top Anime Dashboard", layout="wide")

# Sidebar filters
with st.sidebar:
    st.title("Upcoming Anime Explorer")
    st.markdown("Filter by release date range:")

    min_date = df['release_date'].min().date()
    max_date = df['release_date'].max().date()
    default_start = max(min_date, max_date - timedelta(days=365))
    default_end = max_date

    start_date = st.date_input("Start date", default_start, min_value=min_date, max_value=max_date)
    end_date = st.date_input("End date", default_end, min_value=min_date, max_value=max_date)
    top_n = st.slider("Number of top anime to show", 5, 50, 10)

# Filter by date range
mask = (df['release_date'] >= pd.to_datetime(start_date)) & (df['release_date'] <= pd.to_datetime(end_date))
filtered_df = df.loc[mask].sort_values(by='members', ascending=False).head(top_n)

# Title and caption
st.title("Most Popular Anime by Members")
st.caption(f"Showing top {top_n} anime released between **{start_date}** and **{end_date}**")

# Display DataFrame with clickable titles
def make_clickable(title, url):
    return f'<a href="{url}" target="_blank">{title}</a>'

display_df = filtered_df.copy()
display_df['Title'] = display_df.apply(lambda x: make_clickable(x['title'], x['url']), axis=1)
display_df['Release Date'] = display_df['release_date'].dt.date
display_df['Members'] = display_df['members']
display_df['Genres'] = display_df['genres']

st.write("## Anime List")
st.write(f"Top {top_n} anime by member count with clickable titles:")
st.write(display_df[['Title', 'Release Date', 'Members', 'Genres']].to_html(escape=False, index=False), unsafe_allow_html=True)

# Popularity bar chart
st.subheader("Top Anime Popularity Chart")
# Bar chart for Top Anime by Members (highest on the left)
anime_chart = alt.Chart(filtered_df).mark_bar().encode(
    x=alt.X('members:Q', title='Members'),
    y=alt.Y('title:N', sort='-x', title='Anime Title'),
    tooltip=['title', 'members']
).properties(
    width=700,
    height=400,
    title='Top Anime by Members'
)
st.altair_chart(anime_chart, use_container_width=True)

# Bar chart for Genre Frequency (highest on the left)
def get_genre_counts(df, genre_col='genres'):
    all_genres = []
    for genres in df[genre_col].dropna():
        split_genres = [g.strip() for g in genres.split(',')]
        all_genres.extend(split_genres)
    return pd.DataFrame(Counter(all_genres).items(), columns=['Genre', 'Count']).sort_values(by='Count', ascending=False)

genre_counts_df = get_genre_counts(filtered_df)

genre_chart = alt.Chart(genre_counts_df).mark_bar().encode(
    x=alt.X('Count:Q', title='Count'),
    y=alt.Y('Genre:N', sort='-x'),
    tooltip=['Genre', 'Count']
).properties(
    width=700,
    height=400,
    title='Genre Frequency Among Top Anime'
)
st.altair_chart(genre_chart, use_container_width=True)
