import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import hashlib
import json

logger = logging.getLogger(__name__)

@dataclass
class Security:
    """Standardized security representation"""
    symbol: str
    name: str
    quantity: float
    avg_price: float
    current_price: float
    market_value: float
    pnl: float
    pnl_percentage: float
    security_type: str  # 'STOCK', 'MUTUAL_FUND', 'BOND', 'GOLD', etc.
    isin: Optional[str] = None
    source: str = ""  # 'FYERS', 'CAS', 'MANUAL'
    last_updated: Optional[datetime] = None
    
    def __post_init__(self):
        if self.last_updated is None:
            self.last_updated = datetime.now()
    
    def to_dict(self):
        return {
            'symbol': self.symbol,
            'name': self.name,
            'quantity': self.quantity,
            'avg_price': self.avg_price,
            'current_price': self.current_price,
            'market_value': self.market_value,
            'pnl': self.pnl,
            'pnl_percentage': self.pnl_percentage,
            'security_type': self.security_type,
            'isin': self.isin,
            'source': self.source,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None
        }

class PortfolioService:
    """Handles portfolio data consolidation and deduplication"""
    
    def __init__(self):
        self.portfolio_data = {}
        self.deduplication_rules = {
            'primary_key': 'isin',  # Use ISIN as primary identifier
            'fallback_keys': ['symbol'],  # Fallback to symbol if ISIN not available
            'merge_strategy': 'latest'  # 'latest', 'sum', 'average'
        }
    
    def consolidate_portfolio(self, fyers_data: List[Dict], cas_data: List[Dict], 
                           manual_data: List[Dict]) -> Dict[str, Any]:
        """
        Consolidate portfolio data from multiple sources with smart deduplication
        """
        try:
            # Convert all data to standardized Security objects
            securities = []
            
            # Process FYERS data
            for item in fyers_data:
                security = self._convert_fyers_to_security(item)
                if security:
                    securities.append(security)
            
            # Process CAS data
            for item in cas_data:
                security = self._convert_cas_to_security(item)
                if security:
                    securities.append(security)
            
            # Process manual data
            for item in manual_data:
                security = self._convert_manual_to_security(item)
                if security:
                    securities.append(security)
            
            # Deduplicate and merge securities
            consolidated = self._deduplicate_securities(securities)
            
            # Calculate portfolio summary
            summary = self._calculate_portfolio_summary(consolidated)
            
            return {
                'securities': [s.to_dict() for s in consolidated],
                'summary': summary,
                'last_updated': datetime.now().isoformat(),
                'sources': {
                    'fyers': len([s for s in consolidated if s.source == 'FYERS']),
                    'cas': len([s for s in consolidated if s.source == 'CAS']),
                    'manual': len([s for s in consolidated if s.source == 'MANUAL'])
                }
            }
            
        except Exception as e:
            logger.error(f"Error consolidating portfolio: {str(e)}")
            raise
    
    def _convert_fyers_to_security(self, item: Dict) -> Optional[Security]:
        """Convert FYERS API data to Security object"""
        try:
            return Security(
                symbol=item.get('symbol', ''),
                name=item.get('name', ''),
                quantity=float(item.get('quantity', 0)),
                avg_price=float(item.get('avg_price', 0)),
                current_price=float(item.get('current_price', 0)),
                market_value=float(item.get('market_value', 0)),
                pnl=float(item.get('pnl', 0)),
                pnl_percentage=float(item.get('pnl_percentage', 0)),
                security_type=item.get('security_type', 'STOCK'),
                isin=item.get('isin'),
                source='FYERS'
            )
        except Exception as e:
            logger.error(f"Error converting FYERS data: {str(e)}")
            return None
    
    def _convert_cas_to_security(self, item: Dict) -> Optional[Security]:
        """Convert CAS data to Security object"""
        try:
            return Security(
                symbol=item.get('symbol', ''),
                name=item.get('name', ''),
                quantity=float(item.get('quantity', 0)),
                avg_price=float(item.get('avg_price', 0)),
                current_price=float(item.get('current_price', 0)),
                market_value=float(item.get('market_value', 0)),
                pnl=float(item.get('pnl', 0)),
                pnl_percentage=float(item.get('pnl_percentage', 0)),
                security_type=item.get('security_type', 'STOCK'),
                isin=item.get('isin'),
                source='CAS'
            )
        except Exception as e:
            logger.error(f"Error converting CAS data: {str(e)}")
            return None
    
    def _convert_manual_to_security(self, item: Dict) -> Optional[Security]:
        """Convert manual data to Security object"""
        try:
            return Security(
                symbol=item.get('symbol', ''),
                name=item.get('name', ''),
                quantity=float(item.get('quantity', 0)),
                avg_price=float(item.get('avg_price', 0)),
                current_price=float(item.get('current_price', 0)),
                market_value=float(item.get('market_value', 0)),
                pnl=float(item.get('pnl', 0)),
                pnl_percentage=float(item.get('pnl_percentage', 0)),
                security_type=item.get('security_type', 'STOCK'),
                isin=item.get('isin'),
                source='MANUAL'
            )
        except Exception as e:
            logger.error(f"Error converting manual data: {str(e)}")
            return None
    
    def _deduplicate_securities(self, securities: List[Security]) -> List[Security]:
        """
        Smart deduplication based on ISIN or symbol
        """
        grouped = {}
        
        for security in securities:
            # Create unique key based on ISIN or symbol
            key = security.isin if security.isin else security.symbol
            
            if key in grouped:
                # Merge with existing security
                existing = grouped[key]
                merged = self._merge_securities(existing, security)
                grouped[key] = merged
            else:
                grouped[key] = security
        
        return list(grouped.values())
    
    def _merge_securities(self, existing: Security, new: Security) -> Security:
        """
        Merge two securities with conflict resolution
        """
        # Priority: FYERS > CAS > MANUAL
        priority = {'FYERS': 3, 'CAS': 2, 'MANUAL': 1}
        
        # Choose the higher priority source
        if priority.get(new.source, 0) > priority.get(existing.source, 0):
            return new
        
        # If same priority, use the more recent one
        if (new.last_updated and existing.last_updated and 
            new.last_updated > existing.last_updated):
            return new
        
        return existing
    
    def _calculate_portfolio_summary(self, securities: List[Security]) -> Dict:
        """Calculate portfolio summary statistics"""
        total_value = sum(s.market_value for s in securities)
        total_pnl = sum(s.pnl for s in securities)
        total_investment = sum(s.quantity * s.avg_price for s in securities)
        
        # Group by security type
        by_type = {}
        for security in securities:
            sec_type = security.security_type
            if sec_type not in by_type:
                by_type[sec_type] = {
                    'count': 0,
                    'value': 0,
                    'pnl': 0
                }
            by_type[sec_type]['count'] += 1
            by_type[sec_type]['value'] += security.market_value
            by_type[sec_type]['pnl'] += security.pnl
        
        return {
            'total_value': total_value,
            'total_pnl': total_pnl,
            'total_investment': total_investment,
            'overall_pnl_percentage': (total_pnl / total_investment * 100) if total_investment > 0 else 0,
            'security_count': len(securities),
            'by_type': by_type
        }
    
    def get_portfolio_data(self) -> Dict:
        """Get current portfolio data"""
        return self.portfolio_data
    
    def update_portfolio_data(self, data: Dict):
        """Update portfolio data"""
        self.portfolio_data = data 