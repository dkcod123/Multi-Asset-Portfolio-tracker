import logging
import re
import requests
from typing import Dict, List, Optional, Any
from datetime import datetime
import pandas as pd
from io import BytesIO
import json
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class CASSecurity:
    """Standardized CAS security representation"""
    isin: str
    symbol: str
    name: str
    quantity: float
    avg_price: float
    current_price: float
    market_value: float
    security_type: str  # 'STOCK', 'MUTUAL_FUND', 'BOND', 'GOLD', etc.
    dp_id: Optional[str] = None
    client_id: Optional[str] = None
    source: str = "CAS"
    last_updated: Optional[datetime] = None
    
    def __post_init__(self):
        if self.last_updated is None:
            self.last_updated = datetime.now()

class CASScraperService:
    """
    Service to handle CAS statement processing
    
    ⚠️ IMPORTANT: CDSL and NSDL websites require authentication and don't allow direct scraping.
    This service focuses on parsing uploaded CAS files and provides guidance for manual processes.
    """
    
    def __init__(self):
        self.supported_formats = ['pdf', 'csv', 'excel', 'html']
        self.cas_parsers = {
            'csv': self._parse_csv_cas,
            'excel': self._parse_excel_cas,
            'pdf': self._parse_pdf_cas
        }
        
    def scrape_cas_from_url(self, url: str, pan_number: str) -> Dict[str, Any]:
        """
        Process CAS statement from URL or file
        
        ⚠️ Note: CDSL/NSDL direct scraping is not possible due to authentication requirements.
        This function focuses on processing uploaded files.
        """
        try:
            logger.info(f"Processing CAS from URL: {url}")
            
            # Check if URL points to a file
            if any(ext in url.lower() for ext in ['.pdf', '.csv', '.xlsx', '.xls']):
                response = requests.get(url, timeout=30)
                if response.status_code == 200:
                    return self._parse_uploaded_cas(response.content, url, pan_number)
            
            return {
                'success': False,
                'error': 'Direct CAS scraping not available. CDSL and NSDL require authentication.',
                'suggestion': 'Please upload your CAS statement file manually.',
                'available_methods': [
                    'Manual file upload (CSV/Excel/PDF)',
                    'CDSL website login (manual process)',
                    'NSDL website login (manual process)',
                    'Third-party CAS aggregators'
                ]
            }
            
        except Exception as e:
            logger.error(f"Error processing CAS from URL: {e}")
            return {
                'success': False,
                'error': f'Failed to process CAS: {str(e)}'
            }
    
    def _parse_uploaded_cas(self, content: bytes, url: str, pan_number: str) -> Dict[str, Any]:
        """
        Parse uploaded CAS file (PDF, CSV, Excel)
        """
        try:
            file_extension = url.split('.')[-1].lower()
            
            if file_extension == 'csv':
                return self._parse_csv_cas(content, pan_number)
            elif file_extension in ['xlsx', 'xls']:
                return self._parse_excel_cas(content, pan_number)
            elif file_extension == 'pdf':
                return self._parse_pdf_cas(content, pan_number)
            else:
                return {'success': False, 'error': f'Unsupported file format: {file_extension}'}
                
        except Exception as e:
            logger.error(f"Error parsing uploaded CAS: {e}")
            return {'success': False, 'error': f'Upload parsing failed: {str(e)}'}
    
    def _parse_csv_cas(self, content: bytes, pan_number: str) -> Dict[str, Any]:
        """Parse CSV format CAS"""
        try:
            df = pd.read_csv(BytesIO(content))
            securities = []
            
            # Common CSV column mappings
            column_mappings = {
                'ISIN': ['ISIN', 'isin', 'Isin'],
                'Symbol': ['Symbol', 'symbol', 'Scrip', 'SCRIP'],
                'Name': ['Name', 'name', 'Company', 'COMPANY', 'Scheme Name'],
                'Quantity': ['Quantity', 'quantity', 'Balance', 'Units'],
                'AvgPrice': ['Average Price', 'avg_price', 'Average Cost', 'NAV'],
                'MarketValue': ['Market Value', 'market_value', 'Current Value']
            }
            
            # Map columns
            mapped_columns = {}
            for target, possible_names in column_mappings.items():
                for col in df.columns:
                    if col in possible_names:
                        mapped_columns[target] = col
                        break
            
            # Process each row
            for _, row in df.iterrows():
                security_data = {}
                for target, source_col in mapped_columns.items():
                    if source_col in row:
                        security_data[target.lower()] = row[source_col]
                
                if security_data:
                    securities.append(self._create_cas_security(security_data))
            
            return {
                'success': True,
                'source': 'CSV Upload',
                'pan_number': pan_number,
                'securities': [s.__dict__ for s in securities],
                'total_securities': len(securities),
                'parsed_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error parsing CSV CAS: {e}")
            return {'success': False, 'error': f'CSV parsing failed: {str(e)}'}
    
    def _parse_excel_cas(self, content: bytes, pan_number: str) -> Dict[str, Any]:
        """Parse Excel format CAS"""
        try:
            df = pd.read_excel(BytesIO(content))
            # Similar logic to CSV parsing
            return self._parse_csv_cas(content, pan_number)
            
        except Exception as e:
            logger.error(f"Error parsing Excel CAS: {e}")
            return {'success': False, 'error': f'Excel parsing failed: {str(e)}'}
    
    def _parse_pdf_cas(self, content: bytes, pan_number: str) -> Dict[str, Any]:
        """Parse PDF format CAS"""
        try:
            # This would require PDF parsing library like PyPDF2 or pdfplumber
            # For now, return error suggesting manual upload
            return {
                'success': False,
                'error': 'PDF parsing not implemented. Please convert to CSV/Excel format.',
                'suggestion': 'Use online PDF to CSV converters or manual data entry'
            }
            
        except Exception as e:
            logger.error(f"Error parsing PDF CAS: {e}")
            return {'success': False, 'error': f'PDF parsing failed: {str(e)}'}
    
    def _create_cas_security(self, data: Dict) -> Optional[CASSecurity]:
        """Create CASSecurity object from parsed data"""
        try:
            return CASSecurity(
                isin=data.get('isin', ''),
                symbol=data.get('symbol', ''),
                name=data.get('name', ''),
                quantity=float(data.get('quantity', 0).replace(',', '')),
                avg_price=float(data.get('avgprice', 0).replace(',', '')),
                current_price=0.0,  # Will be updated later
                market_value=float(data.get('marketvalue', 0).replace(',', '')),
                security_type='STOCK'  # Default, will be updated based on ISIN
            )
        except Exception as e:
            logger.error(f"Error creating CAS security: {e}")
            return None
    
    def _create_mf_security(self, data: Dict) -> Optional[CASSecurity]:
        """Create CASSecurity object for mutual funds"""
        try:
            return CASSecurity(
                isin=data.get('isin', ''),
                symbol=data.get('symbol', ''),
                name=data.get('name', ''),
                quantity=float(data.get('quantity', 0).replace(',', '')),
                avg_price=float(data.get('nav', 0).replace(',', '')),
                current_price=0.0,  # Will be updated later
                market_value=float(data.get('marketvalue', 0).replace(',', '')),
                security_type='MUTUAL_FUND'
            )
        except Exception as e:
            logger.error(f"Error creating MF security: {e}")
            return None
    
    def get_cas_sources(self) -> List[Dict]:
        """Get list of available CAS sources with realistic limitations"""
        return [
            {
                'name': 'Manual Upload',
                'url': 'Upload CSV/Excel file',
                'description': 'Upload CAS statement file',
                'supported': True,
                'limitations': 'Requires user to download and upload file'
            },
            {
                'name': 'CDSL Website',
                'url': 'https://www.cdslindia.com/InvestorServices/CAS.aspx',
                'description': 'Central Depository Services Limited',
                'supported': False,
                'limitations': 'Requires login credentials and manual download',
                'note': 'Direct scraping not possible due to authentication'
            },
            {
                'name': 'NSDL Website',
                'url': 'https://www.nsdl.co.in/investor-services/cas',
                'description': 'National Securities Depository Limited',
                'supported': False,
                'limitations': 'Requires login credentials and manual download',
                'note': 'Direct scraping not possible due to authentication'
            },
            {
                'name': 'Third-party Services',
                'url': 'CAMS, Karvy, etc.',
                'description': 'Mutual fund registrars and aggregators',
                'supported': False,
                'limitations': 'Requires business partnership and API access',
                'note': 'May require commercial agreements'
            }
        ]
    
    def get_cas_manual_process_guide(self) -> Dict[str, Any]:
        """Get guide for manual CAS processing"""
        return {
            'title': 'Manual CAS Processing Guide',
            'steps': [
                {
                    'step': 1,
                    'title': 'Download CAS Statement',
                    'description': 'Log into CDSL/NSDL website and download your CAS statement',
                    'urls': {
                        'CDSL': 'https://www.cdslindia.com/InvestorServices/CAS.aspx',
                        'NSDL': 'https://www.nsdl.co.in/investor-services/cas'
                    }
                },
                {
                    'step': 2,
                    'title': 'Convert to CSV/Excel',
                    'description': 'If downloaded as PDF, convert to CSV or Excel format',
                    'tools': [
                        'Online PDF to CSV converters',
                        'Adobe Acrobat',
                        'Manual data entry for small portfolios'
                    ]
                },
                {
                    'step': 3,
                    'title': 'Upload to System',
                    'description': 'Upload the CSV/Excel file through the web interface',
                    'endpoint': '/api/cas/upload'
                },
                {
                    'step': 4,
                    'title': 'Verify Data',
                    'description': 'Review parsed data and make corrections if needed'
                }
            ],
            'limitations': [
                'CDSL and NSDL require user authentication',
                'Direct API access not available to public',
                'Third-party services require business partnerships',
                'PDF parsing is limited and may require manual intervention'
            ],
            'alternatives': [
                'Use FYERS API for real-time portfolio data',
                'Manual entry for small portfolios',
                'Third-party portfolio aggregators',
                'Broker-provided portfolio tools'
            ]
        } 