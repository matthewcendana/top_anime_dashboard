import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from image_handler import AnimeImageHandler

# Load data
@st.cache_data
def load_data():
    df = pd.read_csv("popular_anime.csv")
    df['release_date'] = pd.to_datetime(df['release_date'], errors='coerce')
    # Remove timezone (if any)
    df['release_date'] = df['release_date'].dt.tz_localize(None)
    df = df.dropna(subset=['release_date'])
    return df

def get_sentiment_info(score):
    """Return sentiment label and color based on score"""
    if score >= 0.6:
        return "Positive", "#28a745"
    elif score >= 0.4:
        return "Neutral", "#ffc107"
    else:
        return "Negative", "#dc3545"

# Initialize image handler
image_handler = AnimeImageHandler()

# Load data
df = load_data()

# Dashboard Configuration
st.set_page_config(page_title="Upcoming Anime Sentiment Dashboard", layout="wide")

# Main dashboard header
st.title("Upcoming Anime Sentiment Dashboard")

# Description about sentiment analysis
st.markdown("""
**About this dashboard:** Sentiment analysis for upcoming anime 
            on MyAnimeList. Descriptions were generated using Google Gemini and data sourced from Reddit and YouTube.
""")

# Sidebar filters
with st.sidebar:
    st.title("")
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
        ("Highest members first", "Earliest release date first", "Highest sentiment score")
    )
    
    # Sentiment filter
    st.markdown("### Sentiment Filter")
    sentiment_filter = st.selectbox(
        "Filter by sentiment:",
        ("All", "Positive (≥0.6)", "Neutral (0.4-0.6)", "Negative (<0.4)")
    )

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

# Apply sorting
if sort_option == "Earliest release date first":
    filtered_df = filtered_df.sort_values(by='release_date', ascending=True)
elif sort_option == "Highest sentiment score":
    filtered_df = filtered_df.sort_values(by='sentiment_score', ascending=False)
else:
    filtered_df = filtered_df.sort_values(by='members', ascending=False)

filtered_df = filtered_df.head(top_n)

# Display filters summary
st.markdown(f"### Showing top {top_n} anime released between **{start_date}** and **{end_date}**")

# Key metrics
col1, col2, col3 = st.columns(3)
with col1:
    avg_sentiment = filtered_df['sentiment_score'].mean()
    sentiment_label, _ = get_sentiment_info(avg_sentiment)
    st.metric("Average Sentiment", f"{avg_sentiment:.2f}", f"{sentiment_label}")

with col2:
    avg_score = filtered_df['sentiment_score'].mean()
    st.metric("Avg Sentiment Score", f"{avg_score:.2f}")

with col3:
    total_anime = len(filtered_df)
    st.metric("Total Anime", total_anime)

# Anime list with three key elements
st.markdown("## Anime List")

# Create a container for the anime list
container = st.container()

with container:
    for idx, anime in filtered_df.iterrows():
        # Create a bordered container for each anime
        with st.container():
            # Add some styling
            st.markdown("""
                <style>
                .anime-card {
                    border: 1px solid #ddd;
                    border-radius: 10px;
                    padding: 20px;
                    margin: 15px 0;
                    background-color: #f9f9f9;
                }
                </style>
            """, unsafe_allow_html=True)
            
            # Create columns for layout
            col1, col2 = st.columns([1, 3])
            
            with col1:
                # ANIME IMAGE (First key element)
                image_handler.display_image(anime['url'], anime['title'], width=280)
            
            with col2:
                # ANIME TITLE (Second key element)
                st.markdown(f"## [{anime['title']}]({anime['url']})")
                
                # Basic info with better formatting
                st.markdown(f"""
                **Release Date:** {anime['release_date'].strftime('%B %d, %Y')} | 
                **Members:** {anime['members']:,} | 
                **Episodes:** {anime['episodes']} | 
                **Type:** {anime['type']}
                """)
                
                st.markdown(f"**Genres:** {anime['genres']}")
                
                # SENTIMENT DESCRIPTION (Third key element)
                sentiment_label, sentiment_color = get_sentiment_info(anime['sentiment_score'])
                
                # Create a prominent sentiment display
                st.markdown(f"""
                <div style="
                    background-color: {sentiment_color}20; 
                    border-left: 4px solid {sentiment_color}; 
                    padding: 15px; 
                    margin: 15px 0; 
                    border-radius: 5px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                ">
                    <h4 style="margin: 0; color: {sentiment_color};">
                        Sentiment: {sentiment_label} ({anime['sentiment_score']:.2f})
                    </h4>
                    <p style="margin: 10px 0 0 0; font-style: italic; line-height: 1.4;">
                        <strong>AI Analysis:</strong> {anime['reasoning_text']}
                    </p>
                </div>
                """, unsafe_allow_html=True)
                
               
        
        # Add separator with better styling
        st.markdown("<hr style='margin: 30px 0; border: 1px solid #eee;'>", unsafe_allow_html=True)

# Footer with additional info
st.markdown("---")