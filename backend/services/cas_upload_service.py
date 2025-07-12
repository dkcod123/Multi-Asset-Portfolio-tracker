import PyPDF2
import pandas as pd
import re
import logging
from typing import Dict, List, Optional
from datetime import datetime
import os
from database.mongodb import get_collection

logger = logging.getLogger(__name__)

class CASUploadService:
    def __init__(self):
        self.upload_dir = "uploads/cas_statements"
        os.makedirs(self.upload_dir, exist_ok=True)
    
    def parse_cas_statement(self, file_path: str, user_id: str) -> Dict:
        """Parse uploaded CAS statement file"""
        try:
            file_extension = file_path.lower().split('.')[-1]
            
            if file_extension == 'pdf':
                return self._parse_cas_pdf(file_path, user_id)
            elif file_extension in ['xlsx', 'xls']:
                return self._parse_cas_excel(file_path, user_id)
            else:
                return {'error': 'Unsupported file format. Please upload PDF or Excel file.'}
                
        except Exception as e:
            logger.error(f"Error parsing CAS statement: {e}")
            return {'error': f'Failed to parse CAS statement: {str(e)}'}
    
    def _parse_cas_pdf(self, pdf_path: str, user_id: str) -> Dict:
        """Parse CAS statement PDF file"""
        try:
            holdings = []
            transactions = []
            
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                for page_num, page in enumerate(pdf_reader.pages):
                    text = page.extract_text()
                    
                    # Extract holdings from text
                    page_holdings = self._extract_holdings_from_text(text, page_num)
                    holdings.extend(page_holdings)
                    
                    # Extract transactions from text
                    page_transactions = self._extract_transactions_from_text(text, page_num)
                    transactions.extend(page_transactions)
            
            # Remove duplicates and validate
            unique_holdings = self._remove_duplicate_holdings(holdings)
            
            return {
                'user_id': user_id,
                'statement_date': datetime.now().strftime('%Y-%m-%d'),
                'source': 'uploaded_pdf',
                'holdings': unique_holdings,
                'transactions': transactions,
                'summary': {
                    'total_holdings': len(unique_holdings),
                    'total_value': sum(h.get('current_value', 0) for h in unique_holdings)
                }
            }
            
        except Exception as e:
            logger.error(f"Error parsing PDF: {e}")
            return {'error': f'PDF parsing failed: {str(e)}'}
    
    def _parse_cas_excel(self, excel_path: str, user_id: str) -> Dict:
        """Parse CAS statement Excel file"""
        try:
            holdings = []
            
            # Read Excel file
            df = pd.read_excel(excel_path)
            
            # Process each row
            for index, row in df.iterrows():
                holding = self._extract_holding_from_excel_row(row)
                if holding:
                    holdings.append(holding)
            
            return {
                'user_id': user_id,
                'statement_date': datetime.now().strftime('%Y-%m-%d'),
                'source': 'uploaded_excel',
                'holdings': holdings,
                'transactions': [],
                'summary': {
                    'total_holdings': len(holdings),
                    'total_value': sum(h.get('current_value', 0) for h in holdings)
                }
            }
            
        except Exception as e:
            logger.error(f"Error parsing Excel: {e}")
            return {'error': f'Excel parsing failed: {str(e)}'}
    
    def _extract_holdings_from_text(self, text: str, page_num: int) -> List[Dict]:
        """Extract holdings from CAS statement text"""
        holdings = []
        
        try:
            # Common patterns in CAS statements
            patterns = [
                # Pattern for equity holdings
                r'(\w+)\s+(\d+)\s+([\d,]+\.?\d*)\s+([\d,]+\.?\d*)\s+([\d,]+\.?\d*)',
                # Pattern for mutual fund holdings
                r'([A-Z\s]+Fund[^0-9]*)\s+(\d+)\s+([\d,]+\.?\d*)\s+([\d,]+\.?\d*)',
                # Pattern for bonds
                r'([A-Z\s]+Bond[^0-9]*)\s+(\d+)\s+([\d,]+\.?\d*)\s+([\d,]+\.?\d*)'
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                
                for match in matches:
                    holding = self._create_holding_from_match(match, pattern)
                    if holding:
                        holding['page_number'] = page_num
                        holdings.append(holding)
            
            return holdings
            
        except Exception as e:
            logger.error(f"Error extracting holdings from text: {e}")
            return []
    
    def _extract_transactions_from_text(self, text: str, page_num: int) -> List[Dict]:
        """Extract transactions from CAS statement text"""
        transactions = []
        
        try:
            # Pattern for transactions
            transaction_pattern = r'(\d{2}/\d{2}/\d{4})\s+(\w+)\s+(\d+)\s+([\d,]+\.?\d*)'
            matches = re.findall(transaction_pattern, text)
            
            for match in matches:
                transaction = {
                    'date': match[0],
                    'type': match[1],
                    'quantity': int(match[2]),
                    'amount': float(match[3].replace(',', '')),
                    'page_number': page_num
                }
                transactions.append(transaction)
            
            return transactions
            
        except Exception as e:
            logger.error(f"Error extracting transactions from text: {e}")
            return []
    
    def _extract_holding_from_excel_row(self, row) -> Optional[Dict]:
        """Extract holding from Excel row"""
        try:
            # Common column names in CAS Excel files
            symbol_col = None
            quantity_col = None
            avg_price_col = None
            current_value_col = None
            
            for col in row.index:
                col_lower = str(col).lower()
                if 'symbol' in col_lower or 'scrip' in col_lower:
                    symbol_col = col
                elif 'quantity' in col_lower or 'qty' in col_lower:
                    quantity_col = col
                elif 'avg' in col_lower and 'price' in col_lower:
                    avg_price_col = col
                elif 'value' in col_lower or 'amount' in col_lower:
                    current_value_col = col
            
            if symbol_col and quantity_col:
                symbol = str(row[symbol_col]).strip()
                quantity = float(row[quantity_col]) if pd.notna(row[quantity_col]) else 0
                avg_price = float(row[avg_price_col]) if avg_price_col and pd.notna(row[avg_price_col]) else 0
                current_value = float(row[current_value_col]) if current_value_col and pd.notna(row[current_value_col]) else 0
                
                if symbol and quantity > 0:
                    return {
                        'symbol': symbol,
                        'quantity': quantity,
                        'avg_price': avg_price,
                        'current_value': current_value,
                        'current_price': current_value / quantity if quantity > 0 else 0,
                        'asset_type': self._determine_asset_type(symbol),
                        'source': 'excel_upload'
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Error extracting holding from Excel row: {e}")
            return None
    
    def _create_holding_from_match(self, match: tuple, pattern: str) -> Optional[Dict]:
        """Create holding from regex match"""
        try:
            if len(match) >= 3:
                symbol = match[0].strip()
                quantity = float(match[1].replace(',', ''))
                avg_price = float(match[2].replace(',', '')) if len(match) > 2 else 0
                current_value = float(match[3].replace(',', '')) if len(match) > 3 else 0
                
                if symbol and quantity > 0:
                    return {
                        'symbol': symbol,
                        'quantity': quantity,
                        'avg_price': avg_price,
                        'current_value': current_value,
                        'current_price': current_value / quantity if quantity > 0 else avg_price,
                        'asset_type': self._determine_asset_type(symbol),
                        'source': 'pdf_upload'
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Error creating holding from match: {e}")
            return None
    
    def _determine_asset_type(self, symbol: str) -> str:
        """Determine asset type based on symbol"""
        symbol_upper = symbol.upper()
        
        if 'FUND' in symbol_upper or 'MF' in symbol_upper:
            return 'MUTUAL_FUND'
        elif 'BOND' in symbol_upper or 'GOVT' in symbol_upper:
            return 'BOND'
        elif 'GOLD' in symbol_upper or 'ETF' in symbol_upper:
            return 'GOLD'
        else:
            return 'STOCK'
    
    def _remove_duplicate_holdings(self, holdings: List[Dict]) -> List[Dict]:
        """Remove duplicate holdings based on symbol"""
        seen_symbols = set()
        unique_holdings = []
        
        for holding in holdings:
            symbol = holding.get('symbol', '').upper()
            if symbol and symbol not in seen_symbols:
                seen_symbols.add(symbol)
                unique_holdings.append(holding)
        
        return unique_holdings
    
    def store_cas_data(self, user_id: str, cas_data: Dict):
        """Store CAS data in database"""
        try:
            collection = get_collection('cas_data')
            cas_data['user_id'] = user_id
            cas_data['uploaded_at'] = datetime.now()
            
            collection.update_one(
                {'user_id': user_id, 'source': cas_data.get('source')},
                {'$set': cas_data},
                upsert=True
            )
            
            logger.info(f"CAS data stored for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error storing CAS data: {e}")
    
    def get_cas_data(self, user_id: str) -> Optional[Dict]:
        """Get stored CAS data for user"""
        try:
            collection = get_collection('cas_data')
            cas_data = collection.find_one({'user_id': user_id})
            
            if cas_data:
                # Remove MongoDB ObjectId
                cas_data.pop('_id', None)
                return cas_data
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting CAS data: {e}")
            return None 