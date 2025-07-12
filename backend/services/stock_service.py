import requests
import logging
from datetime import datetime
from typing import Dict, List, Optional
from database.mongodb import get_collection
import pandas as pd

logger = logging.getLogger(__name__)

class StockService:
    def __init__(self):
        self.base_urls = {
            'freeapi': 'https://api.freeapi.app',
            'datajockey': 'https://api.datajockey.com',
            'nse': 'https://www.nseindia.com',
            'bse': 'https://www.bseindia.com'
        }
        self.api_keys = {
            'freeapi': None,  # Will be loaded from env
            'datajockey': None  # Will be loaded from env
        }
    
    def get_stock_data(self, symbol: str) -> Dict:
        """Get comprehensive stock data by symbol"""
        try:
            # Check cache first
            cached_data = self._get_cached_stock_data(symbol)
            if cached_data and self._is_cache_valid(cached_data):
                return cached_data
            
            # Fetch fresh data from multiple sources
            stock_data = {
                'symbol': symbol.upper(),
                'timestamp': datetime.now().isoformat(),
                'basic_info': self._get_basic_info(symbol),
                'price_data': self._get_price_data(symbol),
                'fundamental_data': self._get_fundamental_data(symbol),
                'technical_data': self._get_technical_data(symbol)
            }
            
            # Cache the data
            self._cache_stock_data(symbol, stock_data)
            
            return stock_data
        except Exception as e:
            logger.error(f"Error getting stock data for {symbol}: {e}")
            return {'error': f'Failed to get stock data for {symbol}'}
    
    def get_mutual_fund_data(self, isin: str) -> Dict:
        """Get mutual fund data by ISIN"""
        try:
            # Check cache first
            cached_data = self._get_cached_mf_data(isin)
            if cached_data and self._is_cache_valid(cached_data):
                return cached_data
            
            # Fetch fresh data
            mf_data = {
                'isin': isin.upper(),
                'timestamp': datetime.now().isoformat(),
                'basic_info': self._get_mf_basic_info(isin),
                'nav_data': self._get_mf_nav_data(isin),
                'performance_data': self._get_mf_performance_data(isin)
            }
            
            # Cache the data
            self._cache_mf_data(isin, mf_data)
            
            return mf_data
        except Exception as e:
            logger.error(f"Error getting mutual fund data for {isin}: {e}")
            return {'error': f'Failed to get mutual fund data for {isin}'}
    
    def _get_basic_info(self, symbol: str) -> Dict:
        """Get basic stock information"""
        try:
            # This would integrate with NSE/BSE APIs
            # For now, return mock data
            return {
                'name': f'Company {symbol}',
                'sector': 'Technology',
                'market_cap': 1000000000,
                'listing_date': '2020-01-01',
                'face_value': 10
            }
        except Exception as e:
            logger.error(f"Error getting basic info for {symbol}: {e}")
            return {}
    
    def _get_price_data(self, symbol: str) -> Dict:
        """Get current price and historical data"""
        try:
            # This would integrate with real-time APIs
            # For now, return mock data
            return {
                'current_price': 150.50,
                'change': 2.50,
                'change_percent': 1.68,
                'high': 155.00,
                'low': 148.00,
                'volume': 1000000,
                'prev_close': 148.00
            }
        except Exception as e:
            logger.error(f"Error getting price data for {symbol}: {e}")
            return {}
    
    def _get_fundamental_data(self, symbol: str) -> Dict:
        """Get fundamental data (P/E, ROE, etc.)"""
        try:
            # This would scrape from screener.in or tickertape
            # For now, return mock data
            return {
                'pe_ratio': 15.5,
                'pb_ratio': 2.1,
                'roe': 12.5,
                'roce': 18.2,
                'eps': 9.7,
                'book_value': 72.3,
                'debt_to_equity': 0.3,
                'current_ratio': 1.8
            }
        except Exception as e:
            logger.error(f"Error getting fundamental data for {symbol}: {e}")
            return {}
    
    def _get_technical_data(self, symbol: str) -> Dict:
        """Get technical indicators"""
        try:
            # This would calculate technical indicators
            # For now, return mock data
            return {
                'rsi': 65.2,
                'macd': 2.1,
                'sma_20': 148.5,
                'sma_50': 145.2,
                'ema_12': 149.8,
                'ema_26': 146.3
            }
        except Exception as e:
            logger.error(f"Error getting technical data for {symbol}: {e}")
            return {}
    
    def _get_mf_basic_info(self, isin: str) -> Dict:
        """Get mutual fund basic information"""
        try:
            # This would integrate with AMFI or other MF data sources
            return {
                'name': f'Fund {isin}',
                'amc': 'Sample AMC',
                'category': 'Equity',
                'sub_category': 'Large Cap',
                'expense_ratio': 1.5,
                'aum': 5000000000
            }
        except Exception as e:
            logger.error(f"Error getting MF basic info for {isin}: {e}")
            return {}
    
    def _get_mf_nav_data(self, isin: str) -> Dict:
        """Get mutual fund NAV data"""
        try:
            # This would fetch from AMFI or other sources
            return {
                'nav': 25.50,
                'nav_date': datetime.now().strftime('%Y-%m-%d'),
                'nav_change': 0.25,
                'nav_change_percent': 0.99
            }
        except Exception as e:
            logger.error(f"Error getting MF NAV data for {isin}: {e}")
            return {}
    
    def _get_mf_performance_data(self, isin: str) -> Dict:
        """Get mutual fund performance data"""
        try:
            # This would calculate performance metrics
            return {
                'returns_1y': 12.5,
                'returns_3y': 15.2,
                'returns_5y': 18.7,
                'volatility': 12.3,
                'sharpe_ratio': 1.2,
                'alpha': 2.1,
                'beta': 0.95
            }
        except Exception as e:
            logger.error(f"Error getting MF performance data for {isin}: {e}")
            return {}
    
    def _get_cached_stock_data(self, symbol: str) -> Optional[Dict]:
        """Get cached stock data"""
        try:
            collection = get_collection('stocks')
            return collection.find_one({'symbol': symbol.upper()})
        except Exception as e:
            logger.error(f"Error getting cached stock data: {e}")
            return None
    
    def _get_cached_mf_data(self, isin: str) -> Optional[Dict]:
        """Get cached mutual fund data"""
        try:
            collection = get_collection('mutual_funds')
            return collection.find_one({'isin': isin.upper()})
        except Exception as e:
            logger.error(f"Error getting cached MF data: {e}")
            return None
    
    def _cache_stock_data(self, symbol: str, data: Dict):
        """Cache stock data"""
        try:
            collection = get_collection('stocks')
            collection.update_one(
                {'symbol': symbol.upper()},
                {'$set': data},
                upsert=True
            )
        except Exception as e:
            logger.error(f"Error caching stock data: {e}")
    
    def _cache_mf_data(self, isin: str, data: Dict):
        """Cache mutual fund data"""
        try:
            collection = get_collection('mutual_funds')
            collection.update_one(
                {'isin': isin.upper()},
                {'$set': data},
                upsert=True
            )
        except Exception as e:
            logger.error(f"Error caching MF data: {e}")
    
    def _is_cache_valid(self, data: Dict) -> bool:
        """Check if cached data is still valid (less than 15 minutes old)"""
        try:
            timestamp = datetime.fromisoformat(data.get('timestamp', ''))
            age = datetime.now() - timestamp
            return age.total_seconds() < 900  # 15 minutes
        except Exception:
            return False 