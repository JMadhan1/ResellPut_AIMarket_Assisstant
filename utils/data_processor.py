import os
import pandas as pd
import logging
from typing import Optional, Dict, Any
from io import StringIO

class DataProcessor:
    """Data processor for marketplace analysis"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.df: Optional[pd.DataFrame] = None
        self.data_path = "data/marketplace_data.csv"
    
    def load_data(self) -> pd.DataFrame:
        """Load marketplace data from CSV"""
        if self.df is not None:
            return self.df
        
        try:
            if os.path.exists(self.data_path):
                self.df = pd.read_csv(self.data_path)
            else:
                self.logger.warning(f"Data file not found at {self.data_path}, using fallback data")
                self.df = self._create_fallback_data()
            
            # Clean and validate data
            self.df = self._clean_data(self.df)
            self.logger.info(f"Loaded {len(self.df)} records from marketplace data")
            
            return self.df
            
        except Exception as e:
            self.logger.error(f"Error loading data: {str(e)}")
            self.df = self._create_fallback_data()
            return self.df
    
    def _clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and validate the data"""
        # Remove any rows with missing critical fields
        critical_fields = ['title', 'category', 'brand', 'condition', 'age_months', 'asking_price']
        df = df.dropna(subset=critical_fields)
        
        # Ensure data types
        df['age_months'] = pd.to_numeric(df['age_months'], errors='coerce')
        df['asking_price'] = pd.to_numeric(df['asking_price'], errors='coerce')
        
        # Remove rows with invalid data
        df = df[(df['age_months'] >= 0) & (df['asking_price'] > 0)]
        
        # Standardize condition values
        df['condition'] = df['condition'].str.strip()
        
        return df
    
    def find_similar_products(self, category: str, brand: str, age_months: float, age_tolerance: int = 12) -> pd.DataFrame:
        """Find similar products based on category, brand, and age"""
        if self.df is None:
            self.load_data()
        
        # Primary filter: same category and brand
        similar = self.df[
            (self.df['category'] == category) & 
            (self.df['brand'] == brand)
        ]
        
        # Secondary filter: age within tolerance
        if not similar.empty and age_tolerance > 0:
            age_filtered = similar[
                abs(similar['age_months'] - age_months) <= age_tolerance
            ]
            if not age_filtered.empty:
                similar = age_filtered
        
        # If still no matches, try category only
        if similar.empty:
            similar = self.df[self.df['category'] == category]
        
        return similar.copy()
    
    def get_category_stats(self, category: str) -> Dict[str, Any]:
        """Get statistics for a specific category"""
        if self.df is None:
            self.load_data()
        
        category_data = self.df[self.df['category'] == category]
        
        if category_data.empty:
            return {
                'count': 0,
                'avg_price': 0,
                'median_price': 0,
                'min_price': 0,
                'max_price': 0,
                'avg_age': 0
            }
        
        return {
            'count': len(category_data),
            'avg_price': category_data['asking_price'].mean(),
            'median_price': category_data['asking_price'].median(),
            'min_price': category_data['asking_price'].min(),
            'max_price': category_data['asking_price'].max(),
            'avg_age': category_data['age_months'].mean()
        }
    
    def get_price_trends(self, category: str, brand: str) -> Dict[str, Any]:
        """Analyze price trends for category and brand combination"""
        if self.df is None:
            self.load_data()
        
        data = self.df[
            (self.df['category'] == category) & 
            (self.df['brand'] == brand)
        ]
        
        if data.empty:
            return {'trend': 'insufficient_data', 'correlation': 0}
        
        # Calculate correlation between age and price
        correlation = data['age_months'].corr(data['asking_price'])
        
        # Determine trend
        if correlation < -0.3:
            trend = 'declining'  # Higher age, lower price
        elif correlation > 0.3:
            trend = 'stable'     # Age doesn't affect price much
        else:
            trend = 'variable'   # Mixed trend
        
        return {
            'trend': trend,
            'correlation': correlation,
            'sample_size': len(data)
        }
    
    def _create_fallback_data(self) -> pd.DataFrame:
        """Create fallback data if CSV is not available"""
        self.logger.info("Creating fallback marketplace data")
        
        # Sample data for demonstration
        fallback_data = [
            {'id': 1, 'title': 'iPhone 12', 'category': 'Mobile', 'brand': 'Apple', 'condition': 'Good', 'age_months': 24, 'asking_price': 35000, 'location': 'Mumbai'},
            {'id': 2, 'title': 'Samsung Galaxy S21', 'category': 'Mobile', 'brand': 'Samsung', 'condition': 'Like New', 'age_months': 12, 'asking_price': 40000, 'location': 'Delhi'},
            {'id': 3, 'title': 'MacBook Air', 'category': 'Laptop', 'brand': 'Apple', 'condition': 'Good', 'age_months': 18, 'asking_price': 65000, 'location': 'Bangalore'},
            {'id': 4, 'title': 'Dell Inspiron', 'category': 'Laptop', 'brand': 'Dell', 'condition': 'Fair', 'age_months': 36, 'asking_price': 25000, 'location': 'Chennai'},
            {'id': 5, 'title': 'Sony Camera', 'category': 'Camera', 'brand': 'Sony', 'condition': 'Like New', 'age_months': 6, 'asking_price': 45000, 'location': 'Pune'}
        ]
        
        return pd.DataFrame(fallback_data)
