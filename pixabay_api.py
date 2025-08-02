"""
Pixabay API handler for searching images, videos, music, and GIFs
"""
import logging
import requests
import os
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class PixabayAPI:
    def __init__(self):
        self.api_key = os.environ.get("PIXABAY_API_KEY", "51444506-bffefcaf12816bd85a20222d1")
        self.base_url = "https://pixabay.com/api/"
        self.video_url = "https://pixabay.com/api/videos/"
        self.music_url = "https://pixabay.com/api/music/"

    def search_images(self, query: str, per_page: int = 20) -> List[Dict]:
        """Search for images"""
        try:
            params = {
                'key': self.api_key,
                'q': query,
                'image_type': 'all',
                'orientation': 'all',
                'category': 'all',
                'min_width': 0,
                'min_height': 0,
                'safesearch': 'true',
                'per_page': per_page,
                'pretty': 'true'
            }

            response = requests.get(self.base_url, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                return data.get('hits', [])
            else:
                logger.error(f"Pixabay images API error: {response.status_code}")
                return []

        except Exception as e:
            logger.error(f"Error searching images: {e}")
            return []

    def search_videos(self, query: str, per_page: int = 20) -> List[Dict]:
        """Search for videos"""
        try:
            params = {
                'key': self.api_key,
                'q': query,
                'video_type': 'all',
                'category': 'all',
                'min_width': 0,
                'min_height': 0,
                'safesearch': 'true',
                'per_page': per_page,
                'pretty': 'true'
            }

            response = requests.get(self.video_url, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                return data.get('hits', [])
            else:
                logger.error(f"Pixabay videos API error: {response.status_code}")
                return []

        except Exception as e:
            logger.error(f"Error searching videos: {e}")
            return []

    def search_music(self, query: str, per_page: int = 20) -> List[Dict]:
        """Search for music (using video API with music category)"""
        try:
            params = {
                'key': self.api_key,
                'q': query + ' music audio',
                'video_type': 'all',
                'category': 'music',
                'min_width': 0,
                'min_height': 0,
                'safesearch': 'true',
                'per_page': per_page,
                'pretty': 'true'
            }

            response = requests.get(self.video_url, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                hits = data.get('hits', [])
                
                # Filter for audio/music content
                music_results = []
                for hit in hits:
                    if 'music' in hit.get('tags', '').lower() or 'audio' in hit.get('tags', '').lower():
                        music_results.append(hit)
                
                return music_results[:per_page//2] if music_results else hits[:per_page//2]
            else:
                logger.error(f"Pixabay music API error: {response.status_code}")
                return []

        except Exception as e:
            logger.error(f"Error searching music: {e}")
            return []

    def search_gifs(self, query: str, per_page: int = 20) -> List[Dict]:
        """Search for GIF-like content (using video API)"""
        try:
            params = {
                'key': self.api_key,
                'q': query + ' animation gif',
                'video_type': 'all',
                'category': 'all',
                'min_width': 0,
                'min_height': 0,
                'safesearch': 'true',
                'per_page': per_page,
                'pretty': 'true'
            }

            response = requests.get(self.video_url, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                hits = data.get('hits', [])
                
                # Prefer shorter videos for GIF-like content
                gif_results = []
                for hit in hits:
                    duration = hit.get('duration', 0)
                    if duration <= 10:  # Videos 10 seconds or less
                        gif_results.append(hit)
                
                return gif_results if gif_results else hits[:per_page//2]
            else:
                logger.error(f"Pixabay GIF API error: {response.status_code}")
                return []

        except Exception as e:
            logger.error(f"Error searching GIFs: {e}")
            return []

    def search(self, query: str, search_type: str, per_page: int = 20) -> List[Dict]:
        """Main search method that routes to appropriate search function"""
        try:
            if search_type == 'images':
                return self.search_images(query, per_page)
            elif search_type == 'videos':
                return self.search_videos(query, per_page)
            elif search_type == 'music':
                return self.search_music(query, per_page)
            elif search_type == 'gifs':
                return self.search_gifs(query, per_page)
            else:
                logger.error(f"Unknown search type: {search_type}")
                return []

        except Exception as e:
            logger.error(f"Error in main search method: {e}")
            return []

    def get_image_info(self, image_id: int) -> Optional[Dict]:
        """Get detailed information about a specific image"""
        try:
            params = {
                'key': self.api_key,
                'id': image_id,
                'pretty': 'true'
            }

            response = requests.get(self.base_url, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                hits = data.get('hits', [])
                return hits[0] if hits else None
            else:
                logger.error(f"Pixabay image info API error: {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"Error getting image info: {e}")
            return None

    def test_api_connection(self) -> bool:
        """Test API connection and key validity"""
        try:
            params = {
                'key': self.api_key,
                'q': 'test',
                'per_page': 3,
                'pretty': 'true'
            }

            response = requests.get(self.base_url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'hits' in data:
                    logger.info("Pixabay API connection successful")
                    return True
                else:
                    logger.error("Invalid API response structure")
                    return False
            else:
                logger.error(f"Pixabay API test failed: {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"Error testing API connection: {e}")
            return False
