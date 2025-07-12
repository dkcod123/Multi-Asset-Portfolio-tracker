import requests
import logging
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import pandas as pd
from database.mongodb import get_collection
import os

logger = logging.getLogger(__name__)

class FyersService:
    def __init__(self):
        self.base_url = "https://api.fyers.in"
        self.app_id = os.getenv('FYERS_APP_ID')
        self.app_secret = os.getenv('FYERS_APP_SECRET')
        self.access_token = None
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def authenticate(self, username: str, password: str, pin: str) -> Dict:
        """Authenticate with FYERS API"""
        try:
            # Step 1: Generate auth code
            auth_url = f"{self.base_url}/api/v2/generate-authcode"
            auth_data = {
                "appId": self.app_id,
                "appSecret": self.app_secret,
                "redirectUri": "https://api.fyers.in/api/v2/redirect-uri",
                "state": "sample_state"
            }
            
            response = self.session.post(auth_url, json=auth_data)
            if response.status_code != 200:
                return {'error': 'Failed to generate auth code'}
            
            auth_code = response.json().get('auth_code')
            
            # Step 2: Login with credentials
            login_url = f"{self.base_url}/api/v2/validate-authcode"
            login_data = {
                "auth_code": auth_code,
                "appId": self.app_id,
                "appSecret": self.app_secret
            }
            
            response = self.session.post(login_url, json=login_data)
            if response.status_code != 200:
                return {'error': 'Authentication failed'}
            
            token_data = response.json()
            self.access_token = token_data.get('access_token')
            
            # Store token in database
            self._store_token(username, token_data)
            
            return {
                'success': True,
                'access_token': self.access_token,
                'user_id': token_data.get('user_id')
            }
            
        except Exception as e:
            logger.error(f"FYERS authentication error: {e}")
            return {'error': f'Authentication failed: {str(e)}'}
    
    def get_portfolio(self, user_id: str) -> Dict:
        """Get user's portfolio from FYERS"""
        try:
            if not self.access_token:
                return {'error': 'Not authenticated'}
            
            # Get holdings
            holdings_url = f"{self.base_url}/api/v2/holdings"
            headers = {'Authorization': f'Bearer {self.access_token}'}
            
            response = self.session.get(holdings_url, headers=headers)
            if response.status_code != 200:
                return {'error': 'Failed to fetch holdings'}
            
            holdings_data = response.json()
            
            # Get positions
            positions_url = f"{self.base_url}/api/v2/positions"
            response = self.session.get(positions_url, headers=headers)
            positions_data = response.json() if response.status_code == 200 else {}
            
            # Process and format portfolio data
            portfolio = self._process_portfolio_data(holdings_data, positions_data)
            
            # Store in database
            self._store_portfolio(user_id, portfolio)
            
            return portfolio
            
        except Exception as e:
            logger.error(f"Error fetching portfolio: {e}")
            return {'error': f'Failed to fetch portfolio: {str(e)}'}
    
    def get_historical_data(self, symbol: str, start_date: str, end_date: str, interval: str = "1D") -> Dict:
        """Get historical data for backtesting"""
        try:
            if not self.access_token:
                return {'error': 'Not authenticated'}
            
            # Convert dates to timestamps
            start_ts = int(datetime.strptime(start_date, "%Y-%m-%d").timestamp())
            end_ts = int(datetime.strptime(end_date, "%Y-%m-%d").timestamp())
            
            # FYERS symbol format: NSE:RELIANCE-EQ
            fyers_symbol = self._convert_to_fyers_symbol(symbol)
            
            history_url = f"{self.base_url}/api/v2/history"
            params = {
                'symbol': fyers_symbol,
                'resolution': interval,
                'date_format': '1',
                'range_from': start_ts,
                'range_to': end_ts,
                'cont_flag': '1'
            }
            
            headers = {'Authorization': f'Bearer {self.access_token}'}
            response = self.session.get(history_url, params=params, headers=headers)
            
            if response.status_code != 200:
                return {'error': 'Failed to fetch historical data'}
            
            data = response.json()
            
            # Convert to pandas DataFrame for easier manipulation
            candles = data.get('candles', [])
            if candles:
                df = pd.DataFrame(candles)
                if len(df.columns) >= 6:
                    df.columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
                    df['date'] = pd.to_datetime(df['timestamp'], unit='s')
                else:
                    df = pd.DataFrame()
            else:
                df = pd.DataFrame()
            
            return {
                'symbol': symbol,
                'data': df.to_dict('records'),
                'summary': {
                    'total_days': len(df),
                    'start_date': df['date'].min().strftime('%Y-%m-%d'),
                    'end_date': df['date'].max().strftime('%Y-%m-%d'),
                    'avg_volume': df['volume'].mean(),
                    'price_change': df['close'].iloc[-1] - df['close'].iloc[0]
                }
            }
            
        except Exception as e:
            logger.error(f"Error fetching historical data: {e}")
            return {'error': f'Failed to fetch historical data: {str(e)}'}
    
    def place_order(self, order_data: Dict) -> Dict:
        """Place order on FYERS"""
        try:
            if not self.access_token:
                return {'error': 'Not authenticated'}
            
            order_url = f"{self.base_url}/api/v2/orders"
            headers = {'Authorization': f'Bearer {self.access_token}'}
            
            # Validate order data
            if not self._validate_order(order_data):
                return {'error': 'Invalid order data'}
            
            response = self.session.post(order_url, json=order_data, headers=headers)
            
            if response.status_code != 200:
                return {'error': 'Order placement failed'}
            
            order_result = response.json()
            
            # Store order in database
            self._store_order(order_result)
            
            return order_result
            
        except Exception as e:
            logger.error(f"Error placing order: {e}")
            return {'error': f'Order placement failed: {str(e)}'}
    
    def get_cas_portfolio(self, pan_number: str) -> Dict:
        """Extract portfolio from CDSL/NSDL CAS statements"""
        try:
            # This would integrate with CAS APIs or parse CAS statements
            # For now, return mock data structure
            cas_data = {
                'pan_number': pan_number,
                'cdsl_holdings': self._get_cdsl_holdings(pan_number),
                'nsdl_holdings': self._get_nsdl_holdings(pan_number),
                'mutual_funds': self._get_mf_holdings(pan_number),
                'bonds': self._get_bond_holdings(pan_number),
                'gold': self._get_gold_holdings(pan_number),
                'last_updated': datetime.now().isoformat()
            }
            
            # Store CAS data in database
            self._store_cas_data(pan_number, cas_data)
            
            return cas_data
            
        except Exception as e:
            logger.error(f"Error fetching CAS portfolio: {e}")
            return {'error': f'Failed to fetch CAS portfolio: {str(e)}'}
    
    def refresh_portfolio_prices(self, user_id: str, manual_refresh: bool = False) -> Dict:
        """Refresh portfolio prices - can be called manually or automatically"""
        try:
            # Get user's portfolio
            portfolio = self._get_user_portfolio(user_id)
            if not portfolio:
                return {'error': 'No portfolio found'}
            
            updated_holdings = []
            total_value = 0
            
            for holding in portfolio.get('holdings', []):
                # Get current price
                current_price = self._get_current_price(holding['symbol'])
                
                if current_price:
                    # Update holding with current price
                    holding['current_price'] = current_price
                    holding['current_value'] = holding['quantity'] * current_price
                    holding['total_pnl'] = holding['current_value'] - (holding['quantity'] * holding['avg_price'])
                    holding['pnl_percentage'] = (holding['total_pnl'] / (holding['quantity'] * holding['avg_price']) * 100) if holding['avg_price'] > 0 else 0
                    holding['last_updated'] = datetime.now().isoformat()
                    
                    total_value += holding['current_value']
                    updated_holdings.append(holding)
            
            # Update portfolio in database
            updated_portfolio = {
                'user_id': user_id,
                'holdings': updated_holdings,
                'total_value': total_value,
                'last_refreshed': datetime.now().isoformat(),
                'refresh_type': 'manual' if manual_refresh else 'automatic'
            }
            
            self._update_portfolio(user_id, updated_portfolio)
            
            return {
                'success': True,
                'holdings_updated': len(updated_holdings),
                'total_value': total_value,
                'last_refreshed': updated_portfolio['last_refreshed']
            }
            
        except Exception as e:
            logger.error(f"Error refreshing portfolio prices: {e}")
            return {'error': f'Failed to refresh prices: {str(e)}'}
    
    def _process_portfolio_data(self, holdings_data: Dict, positions_data: Dict) -> Dict:
        """Process raw portfolio data from FYERS"""
        try:
            holdings = []
            
            # Process equity holdings
            for holding in holdings_data.get('holdings', []):
                holdings.append({
                    'symbol': holding.get('symbol'),
                    'quantity': holding.get('quantity', 0),
                    'avg_price': holding.get('avgPrice', 0),
                    'current_price': holding.get('ltp', 0),
                    'current_value': holding.get('quantity', 0) * holding.get('ltp', 0),
                    'total_pnl': holding.get('pl', 0),
                    'asset_type': 'equity',
                    'exchange': holding.get('exchange', 'NSE')
                })
            
            # Process mutual fund holdings
            for mf in holdings_data.get('mutualFunds', []):
                holdings.append({
                    'symbol': mf.get('symbol'),
                    'quantity': mf.get('units', 0),
                    'avg_price': mf.get('avgPrice', 0),
                    'current_price': mf.get('nav', 0),
                    'current_value': mf.get('units', 0) * mf.get('nav', 0),
                    'total_pnl': mf.get('pl', 0),
                    'asset_type': 'mutual_fund',
                    'amc': mf.get('amc', ''),
                    'isin': mf.get('isin', '')
                })
            
            return {
                'holdings': holdings,
                'total_value': sum(h['current_value'] for h in holdings),
                'total_pnl': sum(h['total_pnl'] for h in holdings),
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error processing portfolio data: {e}")
            return {'holdings': [], 'total_value': 0, 'total_pnl': 0}
    
    def _get_cdsl_holdings(self, pan_number: str) -> List[Dict]:
        """Get CDSL holdings for PAN"""
        # This would integrate with CDSL API or parse CAS statements
        # For now, return mock data
        return [
            {
                'symbol': 'RELIANCE',
                'quantity': 100,
                'avg_price': 2500,
                'current_price': 2550,
                'exchange': 'NSE',
                'isin': 'INE002A01018'
            }
        ]
    
    def _get_nsdl_holdings(self, pan_number: str) -> List[Dict]:
        """Get NSDL holdings for PAN"""
        # This would integrate with NSDL API or parse CAS statements
        return [
            {
                'symbol': 'TCS',
                'quantity': 50,
                'avg_price': 3800,
                'current_price': 3850,
                'exchange': 'NSE',
                'isin': 'INE467B01029'
            }
        ]
    
    def _get_mf_holdings(self, pan_number: str) -> List[Dict]:
        """Get mutual fund holdings for PAN"""
        # This would integrate with AMFI or CAS statements
        return [
            {
                'name': 'HDFC Mid-Cap Opportunities Fund',
                'isin': 'INF179K01BE1',
                'units': 1000,
                'nav': 25.50,
                'current_value': 25500,
                'amc': 'HDFC Mutual Fund'
            }
        ]
    
    def _get_bond_holdings(self, pan_number: str) -> List[Dict]:
        """Get bond holdings for PAN"""
        return [
            {
                'name': 'Government of India Bond',
                'isin': 'IN0020190001',
                'quantity': 10,
                'face_value': 1000,
                'current_price': 1050,
                'maturity_date': '2025-03-31'
            }
        ]
    
    def _get_gold_holdings(self, pan_number: str) -> List[Dict]:
        """Get gold holdings for PAN"""
        return [
            {
                'type': 'Gold ETF',
                'symbol': 'GOLDBEES',
                'quantity': 100,
                'current_price': 55.20,
                'current_value': 5520
            }
        ]
    
    def _get_current_price(self, symbol: str) -> Optional[float]:
        """Get current price for a symbol"""
        try:
            # This would call FYERS quote API
            # For now, return mock price
            return 150.50  # Mock price
        except Exception as e:
            logger.error(f"Error getting current price for {symbol}: {e}")
            return None
    
    def _convert_to_fyers_symbol(self, symbol: str) -> str:
        """Convert symbol to FYERS format"""
        # Example: RELIANCE -> NSE:RELIANCE-EQ
        return f"NSE:{symbol}-EQ"
    
    def _validate_order(self, order_data: Dict) -> bool:
        """Validate order data"""
        required_fields = ['symbol', 'qty', 'side', 'productType', 'orderType']
        return all(field in order_data for field in required_fields)
    
    def _store_token(self, username: str, token_data: Dict):
        """Store authentication token in database"""
        try:
            collection = get_collection('fyers_tokens')
            collection.update_one(
                {'username': username},
                {'$set': {
                    'access_token': token_data.get('access_token'),
                    'refresh_token': token_data.get('refresh_token'),
                    'user_id': token_data.get('user_id'),
                    'created_at': datetime.now(),
                    'expires_at': datetime.now() + timedelta(hours=24)
                }},
                upsert=True
            )
        except Exception as e:
            logger.error(f"Error storing token: {e}")
    
    def _store_portfolio(self, user_id: str, portfolio: Dict):
        """Store portfolio data in database"""
        try:
            collection = get_collection('portfolios')
            collection.update_one(
                {'user_id': user_id, 'source': 'fyers'},
                {'$set': {
                    'portfolio_data': portfolio,
                    'last_updated': datetime.now()
                }},
                upsert=True
            )
        except Exception as e:
            logger.error(f"Error storing portfolio: {e}")
    
    def _store_order(self, order_result: Dict):
        """Store order in database"""
        try:
            collection = get_collection('orders')
            order_result['created_at'] = datetime.now()
            collection.insert_one(order_result)
        except Exception as e:
            logger.error(f"Error storing order: {e}")
    
    def _store_cas_data(self, pan_number: str, cas_data: Dict):
        """Store CAS data in database"""
        try:
            collection = get_collection('cas_data')
            cas_data['pan_number'] = pan_number
            cas_data['stored_at'] = datetime.now()
            
            collection.update_one(
                {'pan_number': pan_number},
                {'$set': cas_data},
                upsert=True
            )
        except Exception as e:
            logger.error(f"Error storing CAS data: {e}")
    
    def _get_user_portfolio(self, user_id: str) -> Optional[Dict]:
        """Get user's portfolio from database"""
        try:
            collection = get_collection('portfolios')
            portfolio = collection.find_one({'user_id': user_id, 'source': 'fyers'})
            
            if portfolio:
                return portfolio.get('portfolio_data', {})
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting user portfolio: {e}")
            return None
    
    def _update_portfolio(self, user_id: str, portfolio: Dict):
        """Update portfolio in database"""
        try:
            collection = get_collection('portfolios')
            collection.update_one(
                {'user_id': user_id, 'source': 'fyers'},
                {'$set': {
                    'portfolio_data': portfolio,
                    'last_updated': datetime.now()
                }},
                upsert=True
            )
        except Exception as e:
            logger.error(f"Error updating portfolio: {e}") 