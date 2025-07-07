import requests
import os
import streamlit as st
import time
import re
from urllib.parse import urlparse

class AnimeImageHandler:
    def __init__(self, images_dir='anime_images'):
        self.images_dir = images_dir
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
        }
        
        # Create images directory if it doesn't exist
        if not os.path.exists(self.images_dir):
            os.makedirs(self.images_dir)
    
    def _extract_mal_id(self, mal_url):
        """Extract MyAnimeList ID from URL"""
        try:
            # Extract ID from URLs like https://myanimelist.net/anime/16498/Shingeki_no_Kyojin
            match = re.search(r'/anime/(\d+)', mal_url)
            if match:
                return int(match.group(1))
        except Exception as e:
            print(f"Error extracting MAL ID from {mal_url}: {e}")
        return None
    
    def _sanitize_filename(self, anime_title, mal_id):
        """Generate a safe filename from anime title and MAL ID"""
        safe_title = "".join(c for c in anime_title if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_title = safe_title.replace(' ', '_')[:40]  # Limit filename length
        return f"{self.images_dir}/{safe_title}_{mal_id}.jpg"
    
    def _download_image(self, url, filename):
        """Download image from URL and save to local file"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Add delay between attempts
                if attempt > 0:
                    time.sleep(1)
                
                response = requests.get(url, headers=self.headers, timeout=15, stream=True)
                if response.status_code == 200:
                    # Check if it's actually an image
                    content_type = response.headers.get('content-type', '')
                    if 'image' in content_type.lower():
                        with open(filename, 'wb') as f:
                            for chunk in response.iter_content(chunk_size=8192):
                                f.write(chunk)
                        
                        # Verify file was created and has content
                        if os.path.exists(filename) and os.path.getsize(filename) > 0:
                            return True
                        else:
                            if os.path.exists(filename):
                                os.remove(filename)
                            
            except Exception as e:
                print(f"Attempt {attempt + 1} failed for {url}: {e}")
                if os.path.exists(filename):
                    os.remove(filename)
                continue
        
        return False
    
    def _get_image_from_jikan(self, mal_id):
        """Get anime image URL using Jikan API"""
        try:
            # Rate limiting - be respectful to the API
            time.sleep(0.5)  # 500ms delay between requests
            
            api_url = f"https://api.jikan.moe/v4/anime/{mal_id}"
            response = requests.get(api_url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Extract image URLs from the response
                if 'data' in data and 'images' in data['data']:
                    images = data['data']['images']
                    
                    # Prefer webp large image, then jpg large, then jpg regular
                    if 'webp' in images and 'large_image_url' in images['webp']:
                        return images['webp']['large_image_url']
                    elif 'jpg' in images and 'large_image_url' in images['jpg']:
                        return images['jpg']['large_image_url']
                    elif 'jpg' in images and 'image_url' in images['jpg']:
                        return images['jpg']['image_url']
                        
            elif response.status_code == 429:  # Rate limited
                print(f"Rate limited, waiting longer for MAL ID {mal_id}")
                time.sleep(2)  # Wait 2 seconds and try once more
                return self._get_image_from_jikan(mal_id)
                
        except Exception as e:
            print(f"Error getting image from Jikan API for MAL ID {mal_id}: {e}")
        
        return None
    
    def get_anime_image_path(self, mal_url, anime_title):
        """Get local path to anime image, downloading if necessary"""
        # Extract MAL ID from URL
        mal_id = self._extract_mal_id(mal_url)
        if not mal_id:
            print(f"Could not extract MAL ID from {mal_url}")
            return None
        
        filename = self._sanitize_filename(anime_title, mal_id)
        
        # Check if image already exists locally and is valid
        if os.path.exists(filename) and os.path.getsize(filename) > 0:
            return filename
        
        # If file exists but is empty, remove it
        if os.path.exists(filename):
            os.remove(filename)
        
        # Get image URL from Jikan API
        image_url = self._get_image_from_jikan(mal_id)
        if image_url:
            # Download and save image
            if self._download_image(image_url, filename):
                return filename
        
        return None
    
    def display_image(self, mal_url, anime_title, width=250):
        """Display anime image in Streamlit, downloading if necessary"""
        image_path = self.get_anime_image_path(mal_url, anime_title)
        
        if image_path and os.path.exists(image_path):
            try:
                # Display with better quality settings
                st.image(image_path, width=width, use_container_width=False)
                return True
            except Exception as e:
                print(f"Error displaying image {image_path}: {e}")
                # If image is corrupted, remove it
                if os.path.exists(image_path):
                    os.remove(image_path)
        
        # Show placeholder if no image available
        st.info("Image not available")
        return False