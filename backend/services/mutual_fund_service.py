import requests
import logging
from typing import Dict, List, Optional
from datetime import datetime
import os
from database.mongodb import get_collection

logger = logging.getLogger(__name__)

class MutualFundService:
    def __init__(self):
        self.amfi_base_url = "https://www.amfiindia.com"
        self.cams_base_url = "https://www.camsonline.com"
        self.karvy_base_url = "https://www.karvy.com"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def get_mutual_fund_holdings(self, pan_number: str) -> Dict:
        """Get all mutual fund holdings for a PAN"""
        try:
            holdings = {
                'pan_number': pan_number,
                'last_updated': datetime.now().isoformat(),
                'demat_mfs': [],
                'non_demat_mfs': [],
                'total_value': 0
            }
            
            # 1. Get demat mutual funds from CAS
            demat_mfs = self._get_demat_mutual_funds(pan_number)
            holdings['demat_mfs'] = demat_mfs
            
            # 2. Get non-demat mutual funds from AMFI/CAMS/Karvy
            non_demat_mfs = self._get_non_demat_mutual_funds(pan_number)
            holdings['non_demat_mfs'] = non_demat_mfs
            
            # 3. Calculate total value
            total_value = sum(mf.get('current_value', 0) for mf in demat_mfs)
            total_value += sum(mf.get('current_value', 0) for mf in non_demat_mfs)
            holdings['total_value'] = total_value
            
            # Store in database
            self._store_mf_holdings(pan_number, holdings)
            
            return holdings
            
        except Exception as e:
            logger.error(f"Error getting mutual fund holdings: {e}")
            return {'error': f'Failed to get mutual fund holdings: {str(e)}'}
    
    def _get_demat_mutual_funds(self, pan_number: str) -> List[Dict]:
        """Get demat mutual funds from CAS statements"""
        try:
            # Get from CAS upload data
            collection = get_collection('cas_uploads')
            cas_data = collection.find_one({'pan_number': pan_number})
            
            if cas_data:
                holdings = cas_data.get('holdings', [])
                # Filter for mutual funds
                mf_holdings = [
                    holding for holding in holdings 
                    if holding.get('asset_type') == 'mutual_fund'
                ]
                return mf_holdings
            
            return []
            
        except Exception as e:
            logger.error(f"Error getting demat mutual funds: {e}")
            return []
    
    def _get_non_demat_mutual_funds(self, pan_number: str) -> List[Dict]:
        """Get non-demat mutual funds from various sources"""
        try:
            holdings = []
            
            # 1. Try AMFI API
            amfi_holdings = self._get_amfi_holdings(pan_number)
            holdings.extend(amfi_holdings)
            
            # 2. Try CAMS API
            cams_holdings = self._get_cams_holdings(pan_number)
            holdings.extend(cams_holdings)
            
            # 3. Try Karvy API
            karvy_holdings = self._get_karvy_holdings(pan_number)
            holdings.extend(karvy_holdings)
            
            # 4. Get from manual input
            manual_holdings = self._get_manual_mf_holdings(pan_number)
            holdings.extend(manual_holdings)
            
            return holdings
            
        except Exception as e:
            logger.error(f"Error getting non-demat mutual funds: {e}")
            return []
    
    def _get_amfi_holdings(self, pan_number: str) -> List[Dict]:
        """Get mutual fund holdings from AMFI"""
        try:
            # AMFI API endpoint (if available)
            url = f"{self.amfi_base_url}/api/v1/portfolio"
            
            # This would require AMFI API credentials
            # For now, return mock data structure
            return [
                {
                    'name': 'HDFC Mid-Cap Opportunities Fund',
                    'isin': 'INF179K01BE1',
                    'amc': 'HDFC Mutual Fund',
                    'units': 1000,
                    'nav': 25.50,
                    'current_value': 25500,
                    'purchase_date': '2023-01-15',
                    'folio_number': '123456789',
                    'source': 'amfi',
                    'asset_type': 'mutual_fund'
                },
                {
                    'name': 'Axis Bluechip Fund',
                    'isin': 'INF846K01AS2',
                    'amc': 'Axis Mutual Fund',
                    'units': 500,
                    'nav': 45.20,
                    'current_value': 22600,
                    'purchase_date': '2023-03-20',
                    'folio_number': '987654321',
                    'source': 'amfi',
                    'asset_type': 'mutual_fund'
                }
            ]
            
        except Exception as e:
            logger.error(f"Error getting AMFI holdings: {e}")
            return []
    
    def _get_cams_holdings(self, pan_number: str) -> List[Dict]:
        """Get mutual fund holdings from CAMS"""
        try:
            # CAMS API endpoint (if available)
            url = f"{self.cams_base_url}/api/v1/portfolio"
            
            # This would require CAMS API credentials
            # For now, return mock data structure
            return [
                {
                    'name': 'SBI Bluechip Fund',
                    'isin': 'INF200K01BS2',
                    'amc': 'SBI Mutual Fund',
                    'units': 750,
                    'nav': 35.80,
                    'current_value': 26850,
                    'purchase_date': '2023-02-10',
                    'folio_number': '456789123',
                    'source': 'cams',
                    'asset_type': 'mutual_fund'
                }
            ]
            
        except Exception as e:
            logger.error(f"Error getting CAMS holdings: {e}")
            return []
    
    def _get_karvy_holdings(self, pan_number: str) -> List[Dict]:
        """Get mutual fund holdings from Karvy"""
        try:
            # Karvy API endpoint (if available)
            url = f"{self.karvy_base_url}/api/v1/portfolio"
            
            # This would require Karvy API credentials
            # For now, return mock data structure
            return [
                {
                    'name': 'ICICI Prudential Technology Fund',
                    'isin': 'INF109K01BS2',
                    'amc': 'ICICI Prudential Mutual Fund',
                    'units': 300,
                    'nav': 85.50,
                    'current_value': 25650,
                    'purchase_date': '2023-04-15',
                    'folio_number': '789123456',
                    'source': 'karvy',
                    'asset_type': 'mutual_fund'
                }
            ]
            
        except Exception as e:
            logger.error(f"Error getting Karvy holdings: {e}")
            return []
    
    def _get_manual_mf_holdings(self, pan_number: str) -> List[Dict]:
        """Get manually entered mutual fund holdings"""
        try:
            collection = get_collection('manual_mf_holdings')
            holdings = list(collection.find({'pan_number': pan_number}))
            
            # Add source and asset_type
            for holding in holdings:
                holding['source'] = 'manual'
                holding['asset_type'] = 'mutual_fund'
            
            return holdings
            
        except Exception as e:
            logger.error(f"Error getting manual MF holdings: {e}")
            return []
    
    def add_manual_mf_holding(self, pan_number: str, holding_data: Dict) -> Dict:
        """Add manually entered mutual fund holding"""
        try:
            # Validate required fields
            required_fields = ['name', 'units', 'nav', 'amc']
            for field in required_fields:
                if field not in holding_data:
                    return {'error': f'Missing required field: {field}'}
            
            # Add metadata
            holding_data['pan_number'] = pan_number
            holding_data['added_at'] = datetime.now()
            holding_data['current_value'] = holding_data['units'] * holding_data['nav']
            
            # Store in database
            collection = get_collection('manual_mf_holdings')
            result = collection.insert_one(holding_data)
            
            if result.inserted_id:
                return {
                    'success': True,
                    'message': 'Mutual fund holding added successfully',
                    'holding_id': str(result.inserted_id)
                }
            else:
                return {'error': 'Failed to add mutual fund holding'}
                
        except Exception as e:
            logger.error(f"Error adding manual MF holding: {e}")
            return {'error': f'Failed to add mutual fund holding: {str(e)}'}
    
    def get_mf_nav(self, isin: str) -> Optional[float]:
        """Get current NAV for a mutual fund"""
        try:
            # Try AMFI API for NAV
            url = f"{self.amfi_base_url}/api/v1/nav/{isin}"
            response = self.session.get(url)
            
            if response.status_code == 200:
                data = response.json()
                return data.get('nav', 0)
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting MF NAV: {e}")
            return None
    
    def get_mf_details(self, isin: str) -> Optional[Dict]:
        """Get mutual fund details"""
        try:
            # Try AMFI API for fund details
            url = f"{self.amfi_base_url}/api/v1/fund/{isin}"
            response = self.session.get(url)
            
            if response.status_code == 200:
                return response.json()
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting MF details: {e}")
            return None
    
    def _store_mf_holdings(self, pan_number: str, holdings: Dict):
        """Store mutual fund holdings in database"""
        try:
            collection = get_collection('mutual_fund_holdings')
            collection.update_one(
                {'pan_number': pan_number},
                {'$set': holdings},
                upsert=True
            )
        except Exception as e:
            logger.error(f"Error storing MF holdings: {e}")
    
    def get_mf_portfolio_summary(self, pan_number: str) -> Dict:
        """Get mutual fund portfolio summary"""
        try:
            holdings = self.get_mutual_fund_holdings(pan_number)
            
            if 'error' in holdings:
                return holdings
            
            # Calculate summary
            total_units = sum(mf.get('units', 0) for mf in holdings.get('demat_mfs', []))
            total_units += sum(mf.get('units', 0) for mf in holdings.get('non_demat_mfs', []))
            
            total_value = holdings.get('total_value', 0)
            
            # Group by AMC
            amc_breakdown = {}
            for mf in holdings.get('demat_mfs', []) + holdings.get('non_demat_mfs', []):
                amc = mf.get('amc', 'Unknown')
                if amc not in amc_breakdown:
                    amc_breakdown[amc] = 0
                amc_breakdown[amc] += mf.get('current_value', 0)
            
            return {
                'pan_number': pan_number,
                'total_units': total_units,
                'total_value': total_value,
                'total_funds': len(holdings.get('demat_mfs', [])) + len(holdings.get('non_demat_mfs', [])),
                'amc_breakdown': amc_breakdown,
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting MF portfolio summary: {e}")
            return {'error': f'Failed to get MF portfolio summary: {str(e)}'} 