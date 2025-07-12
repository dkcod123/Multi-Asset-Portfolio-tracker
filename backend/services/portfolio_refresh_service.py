import logging
import schedule
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from database.mongodb import get_collection
from services.fyers_service import FyersService
from services.fundamental_scraper import FundamentalScraper
import os

logger = logging.getLogger(__name__)

class PortfolioRefreshService:
    def __init__(self):
        self.fyers_service = FyersService()
        self.fundamental_scraper = FundamentalScraper()
        self.refresh_interval = int(os.getenv('PORTFOLIO_REFRESH_INTERVAL', 300))  # 5 minutes default
        self.is_running = False
        self.scheduler_thread = None
    
    def start_auto_refresh(self):
        """Start automatic portfolio refresh scheduler"""
        try:
            if self.is_running:
                logger.info("Auto refresh is already running")
                return {'message': 'Auto refresh already running'}
            
            # Schedule refresh every 5 minutes (or configured interval)
            schedule.every(self.refresh_interval).seconds.do(self.refresh_all_portfolios)
            
            # Schedule market hours refresh (every 1 minute during market hours)
            schedule.every(1).minutes.do(self.refresh_market_hours_portfolios)
            
            # Schedule end of day summary
            schedule.every().day.at("15:30").do(self.generate_daily_summary)
            
            self.is_running = True
            
            # Start scheduler in separate thread
            self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
            self.scheduler_thread.start()
            
            logger.info("Auto refresh scheduler started")
            return {'message': 'Auto refresh scheduler started successfully'}
            
        except Exception as e:
            logger.error(f"Error starting auto refresh: {e}")
            return {'error': f'Failed to start auto refresh: {str(e)}'}
    
    def stop_auto_refresh(self):
        """Stop automatic portfolio refresh"""
        try:
            self.is_running = False
            schedule.clear()
            
            if self.scheduler_thread and self.scheduler_thread.is_alive():
                self.scheduler_thread.join(timeout=5)
            
            logger.info("Auto refresh scheduler stopped")
            return {'message': 'Auto refresh scheduler stopped successfully'}
            
        except Exception as e:
            logger.error(f"Error stopping auto refresh: {e}")
            return {'error': f'Failed to stop auto refresh: {str(e)}'}
    
    def manual_refresh_portfolio(self, user_id: str) -> Dict:
        """Manually refresh portfolio for a specific user"""
        try:
            logger.info(f"Manual refresh requested for user: {user_id}")
            
            # Get user's portfolio
            portfolio = self._get_user_portfolio(user_id)
            if not portfolio:
                return {'error': 'No portfolio found for user'}
            
            # Refresh portfolio prices
            refresh_result = self._refresh_portfolio_prices(user_id, portfolio, manual=True)
            
            # Update last refresh timestamp
            self._update_refresh_timestamp(user_id, 'manual')
            
            return refresh_result
            
        except Exception as e:
            logger.error(f"Error in manual refresh for user {user_id}: {e}")
            return {'error': f'Manual refresh failed: {str(e)}'}
    
    def refresh_all_portfolios(self):
        """Refresh all portfolios in the system"""
        try:
            logger.info("Starting refresh of all portfolios")
            
            # Get all users with portfolios
            users = self._get_all_users_with_portfolios()
            
            refresh_results = {
                'total_users': len(users),
                'successful': 0,
                'failed': 0,
                'errors': []
            }
            
            for user_id in users:
                try:
                    portfolio = self._get_user_portfolio(user_id)
                    if portfolio:
                        result = self._refresh_portfolio_prices(user_id, portfolio, manual=False)
                        if result.get('success'):
                            refresh_results['successful'] += 1
                        else:
                            refresh_results['failed'] += 1
                            refresh_results['errors'].append({
                                'user_id': user_id,
                                'error': result.get('error', 'Unknown error')
                            })
                except Exception as e:
                    logger.error(f"Error refreshing portfolio for user {user_id}: {e}")
                    refresh_results['failed'] += 1
                    refresh_results['errors'].append({
                        'user_id': user_id,
                        'error': str(e)
                    })
            
            # Update system refresh timestamp
            self._update_system_refresh_timestamp()
            
            logger.info(f"Portfolio refresh completed: {refresh_results['successful']} successful, {refresh_results['failed']} failed")
            return refresh_results
            
        except Exception as e:
            logger.error(f"Error in refresh all portfolios: {e}")
            return {'error': f'Refresh all portfolios failed: {str(e)}'}
    
    def refresh_market_hours_portfolios(self):
        """Refresh portfolios during market hours only"""
        try:
            current_time = datetime.now().time()
            market_start = datetime.strptime('09:15', '%H:%M').time()
            market_end = datetime.strptime('15:30', '%H:%M').time()
            
            # Only refresh during market hours
            if market_start <= current_time <= market_end:
                logger.info("Market hours refresh triggered")
                return self.refresh_all_portfolios()
            else:
                logger.info("Outside market hours, skipping refresh")
                return {'message': 'Outside market hours, refresh skipped'}
                
        except Exception as e:
            logger.error(f"Error in market hours refresh: {e}")
            return {'error': f'Market hours refresh failed: {str(e)}'}
    
    def generate_daily_summary(self):
        """Generate daily portfolio summary"""
        try:
            logger.info("Generating daily portfolio summary")
            
            users = self._get_all_users_with_portfolios()
            daily_summary = {
                'date': datetime.now().strftime('%Y-%m-%d'),
                'total_users': len(users),
                'portfolios': []
            }
            
            for user_id in users:
                try:
                    portfolio = self._get_user_portfolio(user_id)
                    if portfolio:
                        summary = self._generate_user_daily_summary(user_id, portfolio)
                        daily_summary['portfolios'].append(summary)
                except Exception as e:
                    logger.error(f"Error generating summary for user {user_id}: {e}")
            
            # Store daily summary
            self._store_daily_summary(daily_summary)
            
            logger.info(f"Daily summary generated for {len(daily_summary['portfolios'])} portfolios")
            return daily_summary
            
        except Exception as e:
            logger.error(f"Error generating daily summary: {e}")
            return {'error': f'Daily summary generation failed: {str(e)}'}
    
    def _refresh_portfolio_prices(self, user_id: str, portfolio: Dict, manual: bool = False) -> Dict:
        """Refresh prices for a specific portfolio"""
        try:
            updated_holdings = []
            total_value = 0
            total_pnl = 0
            
            for holding in portfolio.get('holdings', []):
                try:
                    # Get current price from multiple sources
                    current_price = self._get_current_price(holding['symbol'])
                    
                    if current_price:
                        # Update holding with current price
                        holding['current_price'] = current_price
                        holding['current_value'] = holding['quantity'] * current_price
                        holding['total_pnl'] = holding['current_value'] - (holding['quantity'] * holding['avg_price'])
                        holding['pnl_percentage'] = (holding['total_pnl'] / (holding['quantity'] * holding['avg_price']) * 100) if holding['avg_price'] > 0 else 0
                        holding['last_updated'] = datetime.now().isoformat()
                        
                        total_value += holding['current_value']
                        total_pnl += holding['total_pnl']
                        updated_holdings.append(holding)
                    else:
                        # Keep existing data if price fetch failed
                        updated_holdings.append(holding)
                        total_value += holding.get('current_value', 0)
                        total_pnl += holding.get('total_pnl', 0)
                        
                except Exception as e:
                    logger.error(f"Error updating holding {holding.get('symbol')}: {e}")
                    # Keep existing data if update failed
                    updated_holdings.append(holding)
                    total_value += holding.get('current_value', 0)
                    total_pnl += holding.get('total_pnl', 0)
            
            # Update portfolio in database
            updated_portfolio = {
                'user_id': user_id,
                'holdings': updated_holdings,
                'total_value': total_value,
                'total_pnl': total_pnl,
                'last_refreshed': datetime.now().isoformat(),
                'refresh_type': 'manual' if manual else 'automatic'
            }
            
            self._update_portfolio(user_id, updated_portfolio)
            
            return {
                'success': True,
                'holdings_updated': len(updated_holdings),
                'total_value': total_value,
                'total_pnl': total_pnl,
                'last_refreshed': updated_portfolio['last_refreshed']
            }
            
        except Exception as e:
            logger.error(f"Error refreshing portfolio prices: {e}")
            return {'error': f'Failed to refresh prices: {str(e)}'}
    
    def _get_current_price(self, symbol: str) -> Optional[float]:
        """Get current price from multiple sources"""
        try:
            # Try FYERS first
            if self.fyers_service.access_token:
                price = self.fyers_service._get_current_price(symbol)
                if price:
                    return price
            
            # Try fundamental scraper
            fundamental_data = self.fundamental_scraper.get_cached_fundamentals(symbol)
            if fundamental_data and fundamental_data.get('current_price'):
                return fundamental_data['current_price']
            
            # Try fresh scrape
            fresh_data = self.fundamental_scraper.get_stock_fundamentals(symbol)
            if fresh_data and fresh_data.get('current_price'):
                return fresh_data['current_price']
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting current price for {symbol}: {e}")
            return None
    
    def _generate_user_daily_summary(self, user_id: str, portfolio: Dict) -> Dict:
        """Generate daily summary for a user"""
        try:
            holdings = portfolio.get('holdings', [])
            
            summary = {
                'user_id': user_id,
                'total_holdings': len(holdings),
                'total_value': portfolio.get('total_value', 0),
                'total_pnl': portfolio.get('total_pnl', 0),
                'best_performer': None,
                'worst_performer': None,
                'asset_allocation': {}
            }
            
            if holdings:
                # Find best and worst performers
                sorted_holdings = sorted(holdings, key=lambda x: x.get('pnl_percentage', 0), reverse=True)
                summary['best_performer'] = {
                    'symbol': sorted_holdings[0]['symbol'],
                    'pnl_percentage': sorted_holdings[0].get('pnl_percentage', 0)
                }
                summary['worst_performer'] = {
                    'symbol': sorted_holdings[-1]['symbol'],
                    'pnl_percentage': sorted_holdings[-1].get('pnl_percentage', 0)
                }
                
                # Calculate asset allocation
                asset_types = {}
                for holding in holdings:
                    asset_type = holding.get('asset_type', 'unknown')
                    value = holding.get('current_value', 0)
                    if asset_type in asset_types:
                        asset_types[asset_type] += value
                    else:
                        asset_types[asset_type] = value
                
                summary['asset_allocation'] = asset_types
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating user summary: {e}")
            return {'user_id': user_id, 'error': str(e)}
    
    def _run_scheduler(self):
        """Run the scheduler in a separate thread"""
        try:
            while self.is_running:
                schedule.run_pending()
                time.sleep(1)
        except Exception as e:
            logger.error(f"Error in scheduler thread: {e}")
    
    def _get_user_portfolio(self, user_id: str) -> Optional[Dict]:
        """Get user portfolio from database"""
        try:
            collection = get_collection('portfolios')
            return collection.find_one({'user_id': user_id})
        except Exception as e:
            logger.error(f"Error getting user portfolio: {e}")
            return None
    
    def _get_all_users_with_portfolios(self) -> List[str]:
        """Get all users who have portfolios"""
        try:
            collection = get_collection('portfolios')
            portfolios = collection.find({}, {'user_id': 1})
            return [p['user_id'] for p in portfolios]
        except Exception as e:
            logger.error(f"Error getting users with portfolios: {e}")
            return []
    
    def _update_portfolio(self, user_id: str, portfolio: Dict):
        """Update portfolio in database"""
        try:
            collection = get_collection('portfolios')
            collection.update_one(
                {'user_id': user_id},
                {'$set': portfolio},
                upsert=True
            )
        except Exception as e:
            logger.error(f"Error updating portfolio: {e}")
    
    def _update_refresh_timestamp(self, user_id: str, refresh_type: str):
        """Update refresh timestamp for user"""
        try:
            collection = get_collection('refresh_logs')
            collection.insert_one({
                'user_id': user_id,
                'refresh_type': refresh_type,
                'timestamp': datetime.now(),
                'status': 'success'
            })
        except Exception as e:
            logger.error(f"Error updating refresh timestamp: {e}")
    
    def _update_system_refresh_timestamp(self):
        """Update system-wide refresh timestamp"""
        try:
            collection = get_collection('system_metrics')
            collection.update_one(
                {'metric': 'last_portfolio_refresh'},
                {'$set': {
                    'value': datetime.now(),
                    'updated_at': datetime.now()
                }},
                upsert=True
            )
        except Exception as e:
            logger.error(f"Error updating system refresh timestamp: {e}")
    
    def _store_daily_summary(self, summary: Dict):
        """Store daily summary in database"""
        try:
            collection = get_collection('daily_summaries')
            collection.insert_one(summary)
        except Exception as e:
            logger.error(f"Error storing daily summary: {e}")
    
    def get_refresh_status(self) -> Dict:
        """Get current refresh service status"""
        try:
            return {
                'is_running': self.is_running,
                'refresh_interval': self.refresh_interval,
                'last_system_refresh': self._get_last_system_refresh(),
                'total_users': len(self._get_all_users_with_portfolios())
            }
        except Exception as e:
            logger.error(f"Error getting refresh status: {e}")
            return {'error': str(e)}
    
    def _get_last_system_refresh(self) -> Optional[datetime]:
        """Get last system refresh timestamp"""
        try:
            collection = get_collection('system_metrics')
            metric = collection.find_one({'metric': 'last_portfolio_refresh'})
            return metric.get('value') if metric else None
        except Exception as e:
            logger.error(f"Error getting last system refresh: {e}")
            return None 