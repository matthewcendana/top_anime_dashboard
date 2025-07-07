import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from collections import Counter
import altair as alt
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

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

# Helper functions
def get_sentiment_color(score):
    """Return color based on sentiment score"""
    if score >= 0.6:
        return "#2E8B57"  # Green for positive
    elif score >= 0.4:
        return "#FFD700"  # Gold for neutral
    else:
        return "#DC143C"  # Red for negative

def get_sentiment_label(score):
    """Return sentiment label based on score"""
    if score >= 0.6:
        return "Positive"
    elif score >= 0.4:
        return "Neutral"
    else:
        return "Negative"

def make_clickable(title, url):
    return f'<a href="{url}" target="_blank">{title}</a>'

def get_genre_counts(df, genre_col='genres'):
    all_genres = []
    for genres in df[genre_col].dropna():
        split_genres = [g.strip() for g in genres.split(',')]
        all_genres.extend(split_genres)
    return pd.DataFrame(Counter(all_genres).items(), columns=['Genre', 'Count']).sort_values(by='Count', ascending=False)

# Dashboard Configuration
st.set_page_config(page_title="Top Anime Dashboard", layout="wide", page_icon="🎌")

# Custom CSS for better styling
st.markdown("""
<style>
    .metric-container {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
    }
    .sentiment-positive { color: #2E8B57; font-weight: bold; }
    .sentiment-neutral { color: #FFD700; font-weight: bold; }
    .sentiment-negative { color: #DC143C; font-weight: bold; }
    .anime-card {
        border: 1px solid #ddd;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 10px;
        background-color: #fafafa;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar filters
with st.sidebar:
    st.title("🎌 Anime Explorer")
    st.markdown("### Filter Options")
    
    # Date range filter
    min_date = df['release_date'].min().date()
    max_date = df['release_date'].max().date()
    default_start = max(min_date, max_date - timedelta(days=365))
    default_end = max_date
    
    start_date = st.date_input("Start date", default_start, min_value=min_date, max_value=max_date)
    end_date = st.date_input("End date", default_end, min_value=min_date, max_value=max_date)
    
    # Top N filter
    top_n = st.slider("Number of top anime to show", 5, 50, 10)
    
    # Sort options
    sort_option = st.selectbox(
        "Sort anime by:",
        ("Highest members first", "Earliest release date first", "Highest sentiment score", "Most social engagement")
    )
    
    # Sentiment filter
    st.markdown("### Sentiment Filter")
    sentiment_filter = st.selectbox(
        "Filter by sentiment:",
        ("All", "Positive (≥0.6)", "Neutral (0.4-0.6)", "Negative (<0.4)")
    )
    
    # Genre filter
    all_genres = set()
    for genres in df['genres'].dropna():
        all_genres.update([g.strip() for g in genres.split(',')])
    selected_genres = st.multiselect("Filter by genres:", sorted(all_genres))

# Apply filters
mask = (df['release_date'] >= pd.to_datetime(start_date)) & (df['release_date'] <= pd.to_datetime(end_date))
filtered_df = df.loc[mask].copy()

# Apply sentiment filter
if sentiment_filter != "All":
    if sentiment_filter == "Positive (≥0.6)":
        filtered_df = filtered_df[filtered_df['sentiment_score'] >= 0.6]
    elif sentiment_filter == "Neutral (0.4-0.6)":
        filtered_df = filtered_df[(filtered_df['sentiment_score'] >= 0.4) & (filtered_df['sentiment_score'] < 0.6)]
    elif sentiment_filter == "Negative (<0.4)":
        filtered_df = filtered_df[filtered_df['sentiment_score'] < 0.4]

# Apply genre filter
if selected_genres:
    genre_mask = filtered_df['genres'].str.contains('|'.join(selected_genres), case=False, na=False)
    filtered_df = filtered_df[genre_mask]

# Apply sorting
if sort_option == "Earliest release date first":
    filtered_df = filtered_df.sort_values(by='release_date', ascending=True)
elif sort_option == "Highest sentiment score":
    filtered_df = filtered_df.sort_values(by='sentiment_score', ascending=False)
elif sort_option == "Most social engagement":
    filtered_df = filtered_df.sort_values(by='total_social_items', ascending=False)
else:
    filtered_df = filtered_df.sort_values(by='members', ascending=False)

filtered_df = filtered_df.head(top_n)

# Main dashboard
st.title("🎌 Most Popular Anime Dashboard")
st.markdown(f"### Showing top {top_n} anime released between **{start_date}** and **{end_date}**")

# Key metrics
col1, col2, col3, col4 = st.columns(4)
with col1:
    avg_sentiment = filtered_df['sentiment_score'].mean()
    sentiment_label = get_sentiment_label(avg_sentiment)
    st.metric("Average Sentiment", f"{avg_sentiment:.2f}", f"{sentiment_label}")

with col2:
    total_members = filtered_df['members'].sum()
    st.metric("Total Members", f"{total_members:,}")

with col3:
    avg_social = filtered_df['total_social_items'].mean()
    st.metric("Avg Social Engagement", f"{avg_social:.0f}")

with col4:
    total_anime = len(filtered_df)
    st.metric("Total Anime", total_anime)

# Enhanced anime cards with images and sentiment
st.markdown("## 📺 Anime Showcase")

# Create columns for anime cards
for i in range(0, len(filtered_df), 2):
    col1, col2 = st.columns(2)
    
    for j, col in enumerate([col1, col2]):
        if i + j < len(filtered_df):
            anime = filtered_df.iloc[i + j]
            with col:
                # Anime card with image
                st.markdown(f"""
                <div class="anime-card">
                    <h4><a href="{anime['url']}" target="_blank">{anime['title']}</a></h4>
                    <p><strong>Release:</strong> {anime['release_date'].strftime('%Y-%m-%d')}</p>
                    <p><strong>Members:</strong> {anime['members']:,}</p>
                    <p><strong>Genres:</strong> {anime['genres']}</p>
                    <p><strong>Sentiment:</strong> 
                        <span class="sentiment-{get_sentiment_label(anime['sentiment_score']).lower()}">
                            {get_sentiment_label(anime['sentiment_score'])} ({anime['sentiment_score']:.2f})
                        </span>
                    </p>
                    <p><strong>Social Engagement:</strong> {anime['total_social_items']} items</p>
                    <details>
                        <summary>AI Sentiment Analysis</summary>
                        <p><em>{anime['reasoning_text']}</em></p>
                    </details>
                </div>
                """, unsafe_allow_html=True)
                
                # Add image if URL exists
                if pd.notna(anime.get('image_url')):
                    st.image(anime['image_url'], width=200)

# Visualizations
st.markdown("## 📊 Analytics Dashboard")

# Create tabs for different visualizations
tab1, tab2, tab3, tab4 = st.tabs(["📈 Popularity vs Sentiment", "🎭 Sentiment Distribution", "🎪 Genre Analysis", "📱 Social Engagement"])

with tab1:
    st.subheader("Popularity vs Sentiment Analysis")
    
    # Scatter plot of members vs sentiment
    fig = px.scatter(
        filtered_df,
        x='members',
        y='sentiment_score',
        color='sentiment_score',
        size='total_social_items',
        hover_data=['title', 'genres'],
        title="Anime Popularity vs Sentiment Score",
        labels={'members': 'Member Count', 'sentiment_score': 'Sentiment Score'},
        color_continuous_scale=['red', 'gold', 'green']
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Correlation insights
    correlation = filtered_df['members'].corr(filtered_df['sentiment_score'])
    st.info(f"📊 **Correlation between popularity and sentiment:** {correlation:.3f}")

with tab2:
    st.subheader("Sentiment Distribution")
    
    # Add sentiment labels
    filtered_df['sentiment_label'] = filtered_df['sentiment_score'].apply(get_sentiment_label)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Sentiment distribution pie chart
        sentiment_counts = filtered_df['sentiment_label'].value_counts()
        fig = px.pie(
            values=sentiment_counts.values,
            names=sentiment_counts.index,
            title="Sentiment Distribution",
            color_discrete_map={'Positive': '#2E8B57', 'Neutral': '#FFD700', 'Negative': '#DC143C'}
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Sentiment histogram
        fig = px.histogram(
            filtered_df,
            x='sentiment_score',
            nbins=20,
            title="Sentiment Score Distribution",
            labels={'sentiment_score': 'Sentiment Score', 'count': 'Count'}
        )
        st.plotly_chart(fig, use_container_width=True)

with tab3:
    st.subheader("Genre Analysis")
    
    # Genre popularity and sentiment
    genre_counts_df = get_genre_counts(filtered_df)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Genre frequency bar chart
        fig = px.bar(
            genre_counts_df.head(15),
            x='Count',
            y='Genre',
            orientation='h',
            title="Top 15 Genres by Frequency"
        )
        fig.update_layout(yaxis={'categoryorder': 'total ascending'})
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Average sentiment by genre
        genre_sentiment = []
        for genre in genre_counts_df['Genre'].head(10):
            genre_anime = filtered_df[filtered_df['genres'].str.contains(genre, case=False, na=False)]
            if len(genre_anime) > 0:
                avg_sentiment = genre_anime['sentiment_score'].mean()
                genre_sentiment.append({'Genre': genre, 'Avg_Sentiment': avg_sentiment})
        
        if genre_sentiment:
            genre_sentiment_df = pd.DataFrame(genre_sentiment)
            fig = px.bar(
                genre_sentiment_df,
                x='Avg_Sentiment',
                y='Genre',
                orientation='h',
                title="Average Sentiment by Genre",
                color='Avg_Sentiment',
                color_continuous_scale=['red', 'gold', 'green']
            )
            st.plotly_chart(fig, use_container_width=True)

with tab4:
    st.subheader("Social Engagement Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Social engagement vs members
        fig = px.scatter(
            filtered_df,
            x='members',
            y='total_social_items',
            color='sentiment_score',
            hover_data=['title'],
            title="Social Engagement vs Popularity",
            labels={'members': 'Member Count', 'total_social_items': 'Total Social Items'},
            color_continuous_scale=['red', 'gold', 'green']
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Social engagement breakdown
        social_cols = ['n_reddit_items', 'n_youtube_items']
        if all(col in filtered_df.columns for col in social_cols):
            social_data = filtered_df[social_cols].sum()
            fig = px.pie(
                values=social_data.values,
                names=['Reddit', 'YouTube'],
                title="Social Engagement Sources"
            )
            st.plotly_chart(fig, use_container_width=True)

# Summary insights
st.markdown("## 💡 Key Insights")
col1, col2 = st.columns(2)

with col1:
    st.markdown("### 📈 Top Performers")
    top_sentiment = filtered_df.nlargest(3, 'sentiment_score')[['title', 'sentiment_score']]
    for _, anime in top_sentiment.iterrows():
        st.markdown(f"**{anime['title']}**: {anime['sentiment_score']:.2f}")

with col2:
    st.markdown("### 🔥 Most Engaged")
    top_social = filtered_df.nlargest(3, 'total_social_items')[['title', 'total_social_items']]
    for _, anime in top_social.iterrows():
        st.markdown(f"**{anime['title']}**: {anime['total_social_items']} items")

# Footer
st.markdown("---")
st.markdown("🎌 **Anime Dashboard** | Data refreshed daily | Built with Streamlit")
