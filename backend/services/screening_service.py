import logging
from typing import Dict, List, Optional
from database.mongodb import get_collection
from datetime import datetime

logger = logging.getLogger(__name__)

class ScreeningService:
    def __init__(self):
        self.stocks_collection = get_collection('stocks')
        self.mutual_funds_collection = get_collection('mutual_funds')
    
    def screen_stocks(self, filters: Dict) -> Dict:
        """Screen stocks based on provided filters"""
        try:
            # Build query based on filters
            query = self._build_screening_query(filters)
            
            # Execute screening
            results = self._execute_screening(query, filters)
            
            # Apply sorting and pagination
            sorted_results = self._sort_results(results, filters.get('sort_by', 'market_cap'))
            paginated_results = self._paginate_results(sorted_results, filters)
            
            return {
                'results': paginated_results,
                'total_count': len(results),
                'filtered_count': len(paginated_results),
                'filters_applied': filters,
                'screening_date': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error screening stocks: {e}")
            return {'error': 'Failed to screen stocks'}
    
    def get_screening_templates(self) -> Dict:
        """Get predefined screening templates"""
        try:
            templates = {
                'value_stocks': {
                    'name': 'Value Stocks',
                    'description': 'Stocks with low P/E and high ROE',
                    'filters': {
                        'pe_ratio_max': 15,
                        'roe_min': 12,
                        'market_cap_min': 1000000000
                    }
                },
                'growth_stocks': {
                    'name': 'Growth Stocks',
                    'description': 'Stocks with high revenue growth',
                    'filters': {
                        'revenue_growth_min': 15,
                        'market_cap_min': 500000000
                    }
                },
                'dividend_stocks': {
                    'name': 'Dividend Stocks',
                    'description': 'Stocks with high dividend yield',
                    'filters': {
                        'dividend_yield_min': 3,
                        'pe_ratio_max': 25
                    }
                },
                'momentum_stocks': {
                    'name': 'Momentum Stocks',
                    'description': 'Stocks with strong price momentum',
                    'filters': {
                        'price_change_1m_min': 5,
                        'volume_ratio_min': 1.5
                    }
                },
                'quality_stocks': {
                    'name': 'Quality Stocks',
                    'description': 'Stocks with high quality metrics',
                    'filters': {
                        'roe_min': 15,
                        'debt_to_equity_max': 0.5,
                        'current_ratio_min': 1.5
                    }
                }
            }
            
            return {
                'templates': templates,
                'total_templates': len(templates)
            }
        except Exception as e:
            logger.error(f"Error getting screening templates: {e}")
            return {'error': 'Failed to get screening templates'}
    
    def screen_mutual_funds(self, filters: Dict) -> Dict:
        """Screen mutual funds based on provided filters"""
        try:
            # Build query for mutual funds
            query = self._build_mf_screening_query(filters)
            
            # Execute screening
            results = self._execute_mf_screening(query, filters)
            
            # Apply sorting and pagination
            sorted_results = self._sort_mf_results(results, filters.get('sort_by', 'aum'))
            paginated_results = self._paginate_results(sorted_results, filters)
            
            return {
                'results': paginated_results,
                'total_count': len(results),
                'filtered_count': len(paginated_results),
                'filters_applied': filters,
                'screening_date': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error screening mutual funds: {e}")
            return {'error': 'Failed to screen mutual funds'}
    
    def _build_screening_query(self, filters: Dict) -> Dict:
        """Build MongoDB query based on screening filters"""
        query = {}
        
        # Fundamental filters
        if 'pe_ratio_min' in filters:
            query['fundamental_data.pe_ratio'] = {'$gte': filters['pe_ratio_min']}
        if 'pe_ratio_max' in filters:
            if 'fundamental_data.pe_ratio' in query:
                query['fundamental_data.pe_ratio']['$lte'] = filters['pe_ratio_max']
            else:
                query['fundamental_data.pe_ratio'] = {'$lte': filters['pe_ratio_max']}
        
        if 'pb_ratio_min' in filters:
            query['fundamental_data.pb_ratio'] = {'$gte': filters['pb_ratio_min']}
        if 'pb_ratio_max' in filters:
            if 'fundamental_data.pb_ratio' in query:
                query['fundamental_data.pb_ratio']['$lte'] = filters['pb_ratio_max']
            else:
                query['fundamental_data.pb_ratio'] = {'$lte': filters['pb_ratio_max']}
        
        if 'roe_min' in filters:
            query['fundamental_data.roe'] = {'$gte': filters['roe_min']}
        if 'roe_max' in filters:
            if 'fundamental_data.roe' in query:
                query['fundamental_data.roe']['$lte'] = filters['roe_max']
            else:
                query['fundamental_data.roe'] = {'$lte': filters['roe_max']}
        
        if 'roce_min' in filters:
            query['fundamental_data.roce'] = {'$gte': filters['roce_min']}
        
        # Market cap filters
        if 'market_cap_min' in filters:
            query['basic_info.market_cap'] = {'$gte': filters['market_cap_min']}
        if 'market_cap_max' in filters:
            if 'basic_info.market_cap' in query:
                query['basic_info.market_cap']['$lte'] = filters['market_cap_max']
            else:
                query['basic_info.market_cap'] = {'$lte': filters['market_cap_max']}
        
        # Price filters
        if 'price_min' in filters:
            query['price_data.current_price'] = {'$gte': filters['price_min']}
        if 'price_max' in filters:
            if 'price_data.current_price' in query:
                query['price_data.current_price']['$lte'] = filters['price_max']
            else:
                query['price_data.current_price'] = {'$lte': filters['price_max']}
        
        # Sector filters
        if 'sectors' in filters and filters['sectors']:
            query['basic_info.sector'] = {'$in': filters['sectors']}
        
        # Exclude sectors
        if 'exclude_sectors' in filters and filters['exclude_sectors']:
            query['basic_info.sector'] = {'$nin': filters['exclude_sectors']}
        
        return query
    
    def _build_mf_screening_query(self, filters: Dict) -> Dict:
        """Build MongoDB query for mutual fund screening"""
        query = {}
        
        # Category filters
        if 'categories' in filters and filters['categories']:
            query['basic_info.category'] = {'$in': filters['categories']}
        
        if 'sub_categories' in filters and filters['sub_categories']:
            query['basic_info.sub_category'] = {'$in': filters['sub_categories']}
        
        # AMC filters
        if 'amcs' in filters and filters['amcs']:
            query['basic_info.amc'] = {'$in': filters['amcs']}
        
        # AUM filters
        if 'aum_min' in filters:
            query['basic_info.aum'] = {'$gte': filters['aum_min']}
        if 'aum_max' in filters:
            if 'basic_info.aum' in query:
                query['basic_info.aum']['$lte'] = filters['aum_max']
            else:
                query['basic_info.aum'] = {'$lte': filters['aum_max']}
        
        # Expense ratio filters
        if 'expense_ratio_max' in filters:
            query['basic_info.expense_ratio'] = {'$lte': filters['expense_ratio_max']}
        
        # Performance filters
        if 'returns_1y_min' in filters:
            query['performance_data.returns_1y'] = {'$gte': filters['returns_1y_min']}
        if 'returns_3y_min' in filters:
            query['performance_data.returns_3y'] = {'$gte': filters['returns_3y_min']}
        
        return query
    
    def _execute_screening(self, query: Dict, filters: Dict) -> List[Dict]:
        """Execute stock screening query"""
        try:
            # Get stocks from database (in production, this would be real data)
            # For now, return mock data
            mock_stocks = self._get_mock_stocks()
            
            # Apply filters to mock data
            filtered_stocks = []
            for stock in mock_stocks:
                if self._apply_stock_filters(stock, query):
                    filtered_stocks.append(stock)
            
            return filtered_stocks
        except Exception as e:
            logger.error(f"Error executing screening: {e}")
            return []
    
    def _execute_mf_screening(self, query: Dict, filters: Dict) -> List[Dict]:
        """Execute mutual fund screening query"""
        try:
            # Get mutual funds from database (in production, this would be real data)
            # For now, return mock data
            mock_mfs = self._get_mock_mutual_funds()
            
            # Apply filters to mock data
            filtered_mfs = []
            for mf in mock_mfs:
                if self._apply_mf_filters(mf, query):
                    filtered_mfs.append(mf)
            
            return filtered_mfs
        except Exception as e:
            logger.error(f"Error executing MF screening: {e}")
            return []
    
    def _apply_stock_filters(self, stock: Dict, query: Dict) -> bool:
        """Apply filters to a stock"""
        try:
            for field, condition in query.items():
                if not self._check_field_condition(stock, field, condition):
                    return False
            return True
        except Exception:
            return False
    
    def _apply_mf_filters(self, mf: Dict, query: Dict) -> bool:
        """Apply filters to a mutual fund"""
        try:
            for field, condition in query.items():
                if not self._check_field_condition(mf, field, condition):
                    return False
            return True
        except Exception:
            return False
    
    def _check_field_condition(self, item: Dict, field: str, condition: Dict) -> bool:
        """Check if an item meets a field condition"""
        try:
            # Navigate nested fields (e.g., 'fundamental_data.pe_ratio')
            value = item
            for key in field.split('.'):
                if key in value:
                    value = value[key]
                else:
                    return False
            
            # Check conditions
            for operator, threshold in condition.items():
                if operator == '$gte' and value < threshold:
                    return False
                elif operator == '$lte' and value > threshold:
                    return False
                elif operator == '$in' and value not in threshold:
                    return False
                elif operator == '$nin' and value in threshold:
                    return False
            
            return True
        except Exception:
            return False
    
    def _sort_results(self, results: List[Dict], sort_by: str) -> List[Dict]:
        """Sort results by specified field"""
        try:
            reverse = sort_by.startswith('-')
            field = sort_by[1:] if reverse else sort_by
            
            def get_sort_value(item):
                try:
                    # Navigate nested fields
                    value = item
                    for key in field.split('.'):
                        value = value.get(key, 0)
                    return value if value is not None else 0
                except Exception:
                    return 0
            
            return sorted(results, key=get_sort_value, reverse=reverse)
        except Exception as e:
            logger.error(f"Error sorting results: {e}")
            return results
    
    def _sort_mf_results(self, results: List[Dict], sort_by: str) -> List[Dict]:
        """Sort mutual fund results by specified field"""
        try:
            reverse = sort_by.startswith('-')
            field = sort_by[1:] if reverse else sort_by
            
            def get_sort_value(item):
                try:
                    # Navigate nested fields
                    value = item
                    for key in field.split('.'):
                        value = value.get(key, 0)
                    return value if value is not None else 0
                except Exception:
                    return 0
            
            return sorted(results, key=get_sort_value, reverse=reverse)
        except Exception as e:
            logger.error(f"Error sorting MF results: {e}")
            return results
    
    def _paginate_results(self, results: List[Dict], filters: Dict) -> List[Dict]:
        """Apply pagination to results"""
        try:
            page = filters.get('page', 1)
            limit = filters.get('limit', 20)
            
            start_index = (page - 1) * limit
            end_index = start_index + limit
            
            return results[start_index:end_index]
        except Exception as e:
            logger.error(f"Error paginating results: {e}")
            return results
    
    def _get_mock_stocks(self) -> List[Dict]:
        """Get mock stock data for screening"""
        return [
            {
                'symbol': 'RELIANCE',
                'basic_info': {
                    'name': 'Reliance Industries',
                    'sector': 'Oil & Gas',
                    'market_cap': 1500000000000
                },
                'price_data': {
                    'current_price': 2500.50
                },
                'fundamental_data': {
                    'pe_ratio': 18.5,
                    'pb_ratio': 2.1,
                    'roe': 12.5,
                    'roce': 15.2
                }
            },
            {
                'symbol': 'TCS',
                'basic_info': {
                    'name': 'Tata Consultancy Services',
                    'sector': 'Technology',
                    'market_cap': 1200000000000
                },
                'price_data': {
                    'current_price': 3800.75
                },
                'fundamental_data': {
                    'pe_ratio': 25.2,
                    'pb_ratio': 8.5,
                    'roe': 35.8,
                    'roce': 42.1
                }
            },
            {
                'symbol': 'HDFCBANK',
                'basic_info': {
                    'name': 'HDFC Bank',
                    'sector': 'Banking',
                    'market_cap': 800000000000
                },
                'price_data': {
                    'current_price': 1650.25
                },
                'fundamental_data': {
                    'pe_ratio': 22.1,
                    'pb_ratio': 3.2,
                    'roe': 16.8,
                    'roce': 18.5
                }
            }
        ]
    
    def _get_mock_mutual_funds(self) -> List[Dict]:
        """Get mock mutual fund data for screening"""
        return [
            {
                'isin': 'INF179K01BE1',
                'basic_info': {
                    'name': 'HDFC Mid-Cap Opportunities Fund',
                    'amc': 'HDFC Mutual Fund',
                    'category': 'Equity',
                    'sub_category': 'Mid Cap',
                    'expense_ratio': 1.8,
                    'aum': 25000000000
                },
                'performance_data': {
                    'returns_1y': 18.5,
                    'returns_3y': 22.3,
                    'returns_5y': 25.7
                }
            },
            {
                'isin': 'INF179K01BE2',
                'basic_info': {
                    'name': 'Axis Bluechip Fund',
                    'amc': 'Axis Mutual Fund',
                    'category': 'Equity',
                    'sub_category': 'Large Cap',
                    'expense_ratio': 1.5,
                    'aum': 15000000000
                },
                'performance_data': {
                    'returns_1y': 15.2,
                    'returns_3y': 18.7,
                    'returns_5y': 20.1
                }
            }
        ] 