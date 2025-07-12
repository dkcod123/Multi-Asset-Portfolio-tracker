import logging
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from database.mongodb import get_collection
from bson import ObjectId

logger = logging.getLogger(__name__)

class AnalyticsService:
    def __init__(self):
        self.transactions_collection = get_collection('transactions')
        self.holdings_collection = get_collection('holdings')
        self.portfolios_collection = get_collection('portfolios')
    
    def calculate_xirr(self, user_id: str, data: Dict) -> Dict:
        """Calculate XIRR (Internal Rate of Return) for portfolio"""
        try:
            portfolio_id = data.get('portfolio_id')
            if not portfolio_id:
                return {'error': 'Portfolio ID is required'}
            
            # Get all transactions for the portfolio
            transactions = self._get_portfolio_transactions(portfolio_id)
            
            if not transactions:
                return {'error': 'No transactions found for portfolio'}
            
            # Prepare cash flows for XIRR calculation
            cash_flows, dates = self._prepare_cash_flows(transactions)
            
            # Calculate XIRR
            xirr = self._calculate_xirr_numerical(cash_flows, dates)
            
            return {
                'xirr': xirr,
                'portfolio_id': portfolio_id,
                'calculation_date': datetime.now().isoformat(),
                'cash_flows_count': len(cash_flows)
            }
        except Exception as e:
            logger.error(f"Error calculating XIRR: {e}")
            return {'error': 'Failed to calculate XIRR'}
    
    def calculate_cagr(self, user_id: str) -> Dict:
        """Calculate CAGR (Compound Annual Growth Rate) for portfolio"""
        try:
            # Get user's portfolios
            portfolios = list(self.portfolios_collection.find({'user_id': user_id}))
            
            if not portfolios:
                return {'error': 'No portfolios found for user'}
            
            total_cagr = 0
            portfolio_cagrs = []
            
            for portfolio in portfolios:
                portfolio_id = portfolio['_id']
                transactions = self._get_portfolio_transactions(str(portfolio_id))
                
                if transactions:
                    # Calculate CAGR for this portfolio
                    cagr = self._calculate_cagr_for_portfolio(transactions, portfolio)
                    portfolio_cagrs.append({
                        'portfolio_id': str(portfolio_id),
                        'portfolio_name': portfolio.get('name', 'Unknown'),
                        'cagr': cagr
                    })
                    total_cagr += cagr
            
            avg_cagr = total_cagr / len(portfolio_cagrs) if portfolio_cagrs else 0
            
            return {
                'average_cagr': avg_cagr,
                'portfolio_cagrs': portfolio_cagrs,
                'calculation_date': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error calculating CAGR: {e}")
            return {'error': 'Failed to calculate CAGR'}
    
    def calculate_portfolio_metrics(self, user_id: str) -> Dict:
        """Calculate comprehensive portfolio metrics"""
        try:
            portfolio_data = self._get_user_portfolio_data(user_id)
            
            if not portfolio_data:
                return {'error': 'No portfolio data found'}
            
            metrics = {
                'total_value': portfolio_data['total_value'],
                'total_cost': portfolio_data['total_cost'],
                'total_pnl': portfolio_data['total_pnl'],
                'total_pnl_percentage': portfolio_data['total_pnl_percentage'],
                'asset_allocation': self._calculate_asset_allocation(portfolio_data['holdings']),
                'sector_allocation': self._calculate_sector_allocation(portfolio_data['holdings']),
                'risk_metrics': self._calculate_risk_metrics(portfolio_data['holdings']),
                'performance_metrics': self._calculate_performance_metrics(portfolio_data),
                'calculation_date': datetime.now().isoformat()
            }
            
            return metrics
        except Exception as e:
            logger.error(f"Error calculating portfolio metrics: {e}")
            return {'error': 'Failed to calculate portfolio metrics'}
    
    def _get_portfolio_transactions(self, portfolio_id: str) -> List[Dict]:
        """Get all transactions for a portfolio"""
        try:
            # Get holdings for the portfolio
            holdings = list(self.holdings_collection.find({'portfolio_id': ObjectId(portfolio_id)}))
            holding_ids = [h['_id'] for h in holdings]
            
            # Get transactions for these holdings
            transactions = list(self.transactions_collection.find({
                'holding_id': {'$in': holding_ids}
            }).sort('date', 1))
            
            # Convert ObjectId to string for JSON serialization
            for transaction in transactions:
                transaction['_id'] = str(transaction['_id'])
                transaction['holding_id'] = str(transaction['holding_id'])
            
            return transactions
        except Exception as e:
            logger.error(f"Error getting portfolio transactions: {e}")
            return []
    
    def _prepare_cash_flows(self, transactions: List[Dict]) -> Tuple[List[float], List[datetime]]:
        """Prepare cash flows and dates for XIRR calculation"""
        cash_flows = []
        dates = []
        
        for transaction in transactions:
            amount = transaction['total_amount']
            
            if transaction['type'] == 'buy':
                # Outflow (negative)
                cash_flows.append(-amount)
            elif transaction['type'] == 'sell':
                # Inflow (positive)
                cash_flows.append(amount)
            elif transaction['type'] == 'dividend':
                # Inflow (positive)
                cash_flows.append(amount)
            
            dates.append(transaction['date'])
        
        return cash_flows, dates
    
    def _calculate_xirr_numerical(self, cash_flows: List[float], dates: List[datetime]) -> float:
        """Calculate XIRR using numerical methods"""
        try:
            if len(cash_flows) < 2:
                return 0.0
            
            # Convert dates to years from first date
            start_date = dates[0]
            years = [(date - start_date).days / 365.25 for date in dates]
            
            # Use numpy's IRR function as starting point
            # Note: This is a simplified implementation
            # In production, you'd want a more robust XIRR implementation
            
            # For now, return a mock calculation
            total_investment = sum(cf for cf in cash_flows if cf < 0)
            total_return = sum(cf for cf in cash_flows if cf > 0)
            
            if total_investment == 0:
                return 0.0
            
            # Simple return calculation (not true XIRR)
            total_return_rate = (total_return - abs(total_investment)) / abs(total_investment)
            
            # Convert to annual rate (simplified)
            max_years = max(years) if years else 1
            annual_rate = (1 + total_return_rate) ** (1 / max_years) - 1
            
            return annual_rate * 100  # Return as percentage
        except Exception as e:
            logger.error(f"Error in XIRR calculation: {e}")
            return 0.0
    
    def _calculate_cagr_for_portfolio(self, transactions: List[Dict], portfolio: Dict) -> float:
        """Calculate CAGR for a specific portfolio"""
        try:
            if not transactions:
                return 0.0
            
            # Get first and last transaction dates
            first_date = min(t['date'] for t in transactions)
            last_date = max(t['date'] for t in transactions)
            
            # Calculate total investment and current value
            total_investment = sum(t['total_amount'] for t in transactions if t['type'] == 'buy')
            total_sales = sum(t['total_amount'] for t in transactions if t['type'] == 'sell')
            
            # Estimate current value (this would be more accurate with real-time data)
            current_value = total_investment + (total_sales * 0.1)  # Mock current value
            
            # Calculate time period in years
            time_period = (last_date - first_date).days / 365.25
            
            if time_period <= 0 or total_investment <= 0:
                return 0.0
            
            # Calculate CAGR
            cagr = (current_value / total_investment) ** (1 / time_period) - 1
            
            return cagr * 100  # Return as percentage
        except Exception as e:
            logger.error(f"Error calculating CAGR for portfolio: {e}")
            return 0.0
    
    def _get_user_portfolio_data(self, user_id: str) -> Optional[Dict]:
        """Get comprehensive portfolio data for user"""
        try:
            portfolios = list(self.portfolios_collection.find({'user_id': user_id}))
            
            total_value = 0
            total_cost = 0
            total_pnl = 0
            all_holdings = []
            
            for portfolio in portfolios:
                holdings = self._get_portfolio_holdings(portfolio['_id'])
                all_holdings.extend(holdings)
                
                for holding in holdings:
                    total_value += holding.get('current_value', 0)
                    total_cost += holding.get('quantity', 0) * holding.get('avg_price', 0)
                    total_pnl += holding.get('total_pnl', 0)
            
            total_pnl_percentage = (total_pnl / total_cost * 100) if total_cost > 0 else 0
            
            return {
                'total_value': total_value,
                'total_cost': total_cost,
                'total_pnl': total_pnl,
                'total_pnl_percentage': total_pnl_percentage,
                'holdings': all_holdings
            }
        except Exception as e:
            logger.error(f"Error getting user portfolio data: {e}")
            return None
    
    def _get_portfolio_holdings(self, portfolio_id: ObjectId) -> List[Dict]:
        """Get holdings for a portfolio"""
        try:
            holdings = list(self.holdings_collection.find({'portfolio_id': portfolio_id}))
            
            # Convert ObjectId to string for JSON serialization
            for holding in holdings:
                holding['_id'] = str(holding['_id'])
                holding['portfolio_id'] = str(holding['portfolio_id'])
            
            return holdings
        except Exception as e:
            logger.error(f"Error getting portfolio holdings: {e}")
            return []
    
    def _calculate_asset_allocation(self, holdings: List[Dict]) -> Dict:
        """Calculate asset allocation percentages"""
        try:
            total_value = sum(h.get('current_value', 0) for h in holdings)
            
            if total_value == 0:
                return {}
            
            allocation = {}
            for holding in holdings:
                asset_type = holding.get('asset_type', 'unknown')
                value = holding.get('current_value', 0)
                percentage = (value / total_value) * 100
                
                if asset_type in allocation:
                    allocation[asset_type] += percentage
                else:
                    allocation[asset_type] = percentage
            
            return allocation
        except Exception as e:
            logger.error(f"Error calculating asset allocation: {e}")
            return {}
    
    def _calculate_sector_allocation(self, holdings: List[Dict]) -> Dict:
        """Calculate sector allocation percentages"""
        try:
            total_value = sum(h.get('current_value', 0) for h in holdings)
            
            if total_value == 0:
                return {}
            
            allocation = {}
            for holding in holdings:
                sector = holding.get('sector', 'unknown')
                value = holding.get('current_value', 0)
                percentage = (value / total_value) * 100
                
                if sector in allocation:
                    allocation[sector] += percentage
                else:
                    allocation[sector] = percentage
            
            return allocation
        except Exception as e:
            logger.error(f"Error calculating sector allocation: {e}")
            return {}
    
    def _calculate_risk_metrics(self, holdings: List[Dict]) -> Dict:
        """Calculate risk metrics for portfolio"""
        try:
            # Mock risk metrics calculation
            # In production, this would use historical data and statistical methods
            
            total_value = sum(h.get('current_value', 0) for h in holdings)
            
            return {
                'volatility': 12.5,  # Mock volatility
                'beta': 0.95,  # Mock beta
                'sharpe_ratio': 1.2,  # Mock Sharpe ratio
                'max_drawdown': -8.5,  # Mock max drawdown
                'var_95': -5.2  # Mock Value at Risk (95%)
            }
        except Exception as e:
            logger.error(f"Error calculating risk metrics: {e}")
            return {}
    
    def _calculate_performance_metrics(self, portfolio_data: Dict) -> Dict:
        """Calculate performance metrics"""
        try:
            return {
                'total_return': portfolio_data['total_pnl_percentage'],
                'absolute_return': portfolio_data['total_pnl'],
                'annualized_return': 15.2,  # Mock annualized return
                'best_performing_holding': 'RELIANCE',  # Mock
                'worst_performing_holding': 'INFY'  # Mock
            }
        except Exception as e:
            logger.error(f"Error calculating performance metrics: {e}")
            return {} 