
import json
import os
from datetime import datetime
from typing import Dict, Any

class DataStorage:
    """Handles data storage and retrieval for user preferences and cache"""
    
    def __init__(self):
        self.preferences_file = "user_preferences.json"
        self.cache_file = "paper_cache.json"
    
    def load_preferences(self) -> Dict[str, Any]:
        """Load user preferences from JSON file"""
        
        try:
            if os.path.exists(self.preferences_file):
                with open(self.preferences_file, 'r', encoding='utf-8') as f:
                    preferences = json.load(f)
                return preferences
            else:
                # Return default preferences
                return self._get_default_preferences()
                
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading preferences: {e}")
            return self._get_default_preferences()
    
    def save_preferences(self, preferences: Dict[str, Any]) -> bool:
        """Save user preferences to JSON file"""
        
        try:
            # Add timestamp
            preferences['last_updated'] = datetime.now().isoformat()
            
            with open(self.preferences_file, 'w', encoding='utf-8') as f:
                json.dump(preferences, f, indent=2, ensure_ascii=False)
            return True
            
        except IOError as e:
            print(f"Error saving preferences: {e}")
            return False
    
    def _get_default_preferences(self) -> Dict[str, Any]:
        """Get default user preferences"""
        
        return {
            'keywords': [
                "Alzheimer's disease",
                "PET",
                "MRI", 
                "dementia",
                "amyloid",
                "tau",
                "brain",
                "plasma"
            ],
            'days_back': 7,
            'max_results': 100,
            'last_updated': datetime.now().isoformat()
        }
    
    def cache_papers(self, papers: list, keywords: list, date_range: dict) -> bool:
        """Cache fetched papers data"""
        
        try:
            cache_data = {
                'papers': papers,
                'keywords': keywords,
                'date_range': date_range,
                'cached_at': datetime.now().isoformat()
            }
            
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)
            return True
            
        except IOError as e:
            print(f"Error caching papers: {e}")
            return False
    
    def load_cached_papers(self, keywords: list, date_range: dict, max_age_hours: int = 24) -> list:
        """Load cached papers if they match criteria and are recent enough"""
        
        try:
            if not os.path.exists(self.cache_file):
                return []
            
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            # Check if cache is recent enough
            cached_at = datetime.fromisoformat(cache_data['cached_at'])
            age_hours = (datetime.now() - cached_at).total_seconds() / 3600
            
            if age_hours > max_age_hours:
                return []
            
            # Check if keywords and date range match
            cached_keywords = set(cache_data.get('keywords', []))
            current_keywords = set(keywords)
            cached_date_range = cache_data.get('date_range', {})
            
            if (cached_keywords == current_keywords and 
                cached_date_range == date_range):
                return cache_data.get('papers', [])
            
            return []
            
        except (json.JSONDecodeError, IOError, KeyError) as e:
            print(f"Error loading cached papers: {e}")
            return []
    
    def clear_cache(self) -> bool:
        """Clear cached papers data"""
        
        try:
            if os.path.exists(self.cache_file):
                os.remove(self.cache_file)
            return True
            
        except OSError as e:
            print(f"Error clearing cache: {e}")
            return False
    
    def export_papers_csv(self, papers: list, filename: str = None) -> str:
        """Export papers data to CSV format"""
        
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"arxiv_papers_{timestamp}.csv"
        
        try:
            import pandas as pd
            
            # Prepare data for CSV export
            export_data = []
            for paper in papers:
                row = {
                    'Title': paper.get('title', ''),
                    'Authors': ', '.join(paper.get('authors', [])),
                    'Abstract': paper.get('abstract', ''),
                    'Published': paper.get('published', ''),
                    'ArXiv URL': paper.get('arxiv_url', ''),
                    'Relevance Score': paper.get('relevance_score', 0),
                    'Matched Keywords': ', '.join(paper.get('matched_keywords', []))
                }
                export_data.append(row)
            
            df = pd.DataFrame(export_data)
            csv_content = df.to_csv(index=False)
            
            return csv_content
            
        except Exception as e:
            print(f"Error exporting to CSV: {e}")
            return ""
    
    def get_storage_info(self) -> Dict[str, Any]:
        """Get information about stored data"""
        
        info = {
            'preferences_exists': os.path.exists(self.preferences_file),
            'cache_exists': os.path.exists(self.cache_file),
            'preferences_size': 0,
            'cache_size': 0,
            'cache_age_hours': None
        }
        
        try:
            if info['preferences_exists']:
                info['preferences_size'] = os.path.getsize(self.preferences_file)
            
            if info['cache_exists']:
                info['cache_size'] = os.path.getsize(self.cache_file)
                
                # Get cache age
                with open(self.cache_file, 'r') as f:
                    cache_data = json.load(f)
                    cached_at = datetime.fromisoformat(cache_data['cached_at'])
                    age_hours = (datetime.now() - cached_at).total_seconds() / 3600
                    info['cache_age_hours'] = round(age_hours, 2)
                    
        except Exception as e:
            print(f"Error getting storage info: {e}")
        
        return info
