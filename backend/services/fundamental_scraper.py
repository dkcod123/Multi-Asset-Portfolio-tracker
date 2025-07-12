import requests
import logging
import time
import re
from typing import Dict, Optional, List
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from database.mongodb import get_collection
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)

class FundamentalScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.driver = None
        self.setup_selenium()
    
    def setup_selenium(self):
        """Setup Selenium WebDriver for dynamic content scraping"""
        try:
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
            
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.implicitly_wait(10)
        except Exception as e:
            logger.error(f"Failed to setup Selenium: {e}")
            self.driver = None
    
    def get_stock_fundamentals(self, symbol: str) -> Dict:
        """Get fundamental data for a stock from multiple sources"""
        try:
            # Try Tickertape first
            tickertape_data = self._scrape_tickertape(symbol)
            if tickertape_data and not tickertape_data.get('error'):
                return tickertape_data
            
            # Try Screener as fallback
            screener_data = self._scrape_screener(symbol)
            if screener_data and not screener_data.get('error'):
                return screener_data
            
            # Try NSE website as last resort
            nse_data = self._scrape_nse(symbol)
            if nse_data and not nse_data.get('error'):
                return nse_data
            
            return {'error': f'Could not fetch fundamental data for {symbol}'}
            
        except Exception as e:
            logger.error(f"Error getting fundamentals for {symbol}: {e}")
            return {'error': f'Failed to fetch fundamentals: {str(e)}'}
    
    def _scrape_tickertape(self, symbol: str) -> Dict:
        """Scrape fundamental data from Tickertape"""
        try:
            url = f"https://www.tickertape.in/stocks/{symbol}"
            
            if self.driver:
                self.driver.get(url)
                time.sleep(3)
                
                # Wait for page to load
                try:
                    WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.CLASS_NAME, "stock-info"))
                    )
                except TimeoutException:
                    return {'error': 'Page load timeout'}
                
                page_source = self.driver.page_source
                soup = BeautifulSoup(page_source, 'html.parser')
            else:
                response = self.session.get(url)
                if response.status_code != 200:
                    return {'error': 'Failed to fetch page'}
                soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract fundamental data
            fundamentals = {}
            
            # Market Cap
            try:
                market_cap_elem = soup.find('div', {'data-testid': 'market-cap'})
                if market_cap_elem:
                    market_cap_text = market_cap_elem.get_text()
                    fundamentals['market_cap'] = self._parse_market_cap(market_cap_text)
            except Exception as e:
                logger.error(f"Error extracting market cap: {e}")
            
            # P/E Ratio
            try:
                pe_elem = soup.find('div', {'data-testid': 'pe-ratio'})
                if pe_elem:
                    pe_text = pe_elem.get_text()
                    fundamentals['pe_ratio'] = self._parse_number(pe_text)
            except Exception as e:
                logger.error(f"Error extracting P/E ratio: {e}")
            
            # P/B Ratio
            try:
                pb_elem = soup.find('div', {'data-testid': 'pb-ratio'})
                if pb_elem:
                    pb_text = pb_elem.get_text()
                    fundamentals['pb_ratio'] = self._parse_number(pb_text)
            except Exception as e:
                logger.error(f"Error extracting P/B ratio: {e}")
            
            # ROE
            try:
                roe_elem = soup.find('div', {'data-testid': 'roe'})
                if roe_elem:
                    roe_text = roe_elem.get_text()
                    fundamentals['roe'] = self._parse_number(roe_text)
            except Exception as e:
                logger.error(f"Error extracting ROE: {e}")
            
            # ROCE
            try:
                roce_elem = soup.find('div', {'data-testid': 'roce'})
                if roce_elem:
                    roce_text = roce_elem.get_text()
                    fundamentals['roce'] = self._parse_number(roce_text)
            except Exception as e:
                logger.error(f"Error extracting ROCE: {e}")
            
            # Debt to Equity
            try:
                debt_equity_elem = soup.find('div', {'data-testid': 'debt-equity'})
                if debt_equity_elem:
                    debt_equity_text = debt_equity_elem.get_text()
                    fundamentals['debt_to_equity'] = self._parse_number(debt_equity_text)
            except Exception as e:
                logger.error(f"Error extracting Debt/Equity: {e}")
            
            # Current Price
            try:
                price_elem = soup.find('span', {'data-testid': 'current-price'})
                if price_elem:
                    price_text = price_elem.get_text()
                    fundamentals['current_price'] = self._parse_number(price_text)
            except Exception as e:
                logger.error(f"Error extracting current price: {e}")
            
            # 52 Week High/Low
            try:
                high_elem = soup.find('div', {'data-testid': '52-week-high'})
                low_elem = soup.find('div', {'data-testid': '52-week-low'})
                
                if high_elem:
                    fundamentals['52_week_high'] = self._parse_number(high_elem.get_text())
                if low_elem:
                    fundamentals['52_week_low'] = self._parse_number(low_elem.get_text())
            except Exception as e:
                logger.error(f"Error extracting 52-week data: {e}")
            
            if fundamentals:
                fundamentals['source'] = 'tickertape'
                fundamentals['symbol'] = symbol
                fundamentals['scraped_at'] = datetime.now().isoformat()
                
                # Store in database
                self._store_fundamentals(symbol, fundamentals)
                
                return fundamentals
            
            return {'error': 'No fundamental data found on Tickertape'}
            
        except Exception as e:
            logger.error(f"Error scraping Tickertape for {symbol}: {e}")
            return {'error': f'Tickertape scraping failed: {str(e)}'}
    
    def _scrape_screener(self, symbol: str) -> Dict:
        """Scrape fundamental data from Screener.in"""
        try:
            url = f"https://www.screener.in/company/{symbol}/"
            
            if self.driver:
                self.driver.get(url)
                time.sleep(3)
                
                # Wait for page to load
                try:
                    WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.CLASS_NAME, "company-info"))
                    )
                except TimeoutException:
                    return {'error': 'Page load timeout'}
                
                page_source = self.driver.page_source
                soup = BeautifulSoup(page_source, 'html.parser')
            else:
                response = self.session.get(url)
                if response.status_code != 200:
                    return {'error': 'Failed to fetch page'}
                soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract fundamental data
            fundamentals = {}
            
            # Market Cap
            try:
                market_cap_elem = soup.find('td', text=re.compile(r'Market Cap', re.IGNORECASE))
                if market_cap_elem and market_cap_elem.find_next_sibling():
                    market_cap_text = market_cap_elem.find_next_sibling().get_text()
                    fundamentals['market_cap'] = self._parse_market_cap(market_cap_text)
            except Exception as e:
                logger.error(f"Error extracting market cap: {e}")
            
            # P/E Ratio
            try:
                pe_elem = soup.find('td', text=re.compile(r'P/E', re.IGNORECASE))
                if pe_elem and pe_elem.find_next_sibling():
                    pe_text = pe_elem.find_next_sibling().get_text()
                    fundamentals['pe_ratio'] = self._parse_number(pe_text)
            except Exception as e:
                logger.error(f"Error extracting P/E ratio: {e}")
            
            # P/B Ratio
            try:
                pb_elem = soup.find('td', text=re.compile(r'P/B', re.IGNORECASE))
                if pb_elem and pb_elem.find_next_sibling():
                    pb_text = pb_elem.find_next_sibling().get_text()
                    fundamentals['pb_ratio'] = self._parse_number(pb_text)
            except Exception as e:
                logger.error(f"Error extracting P/B ratio: {e}")
            
            # ROE
            try:
                roe_elem = soup.find('td', text=re.compile(r'ROE', re.IGNORECASE))
                if roe_elem and roe_elem.find_next_sibling():
                    roe_text = roe_elem.find_next_sibling().get_text()
                    fundamentals['roe'] = self._parse_number(roe_text)
            except Exception as e:
                logger.error(f"Error extracting ROE: {e}")
            
            # ROCE
            try:
                roce_elem = soup.find('td', text=re.compile(r'ROCE', re.IGNORECASE))
                if roce_elem and roce_elem.find_next_sibling():
                    roce_text = roce_elem.find_next_sibling().get_text()
                    fundamentals['roce'] = self._parse_number(roce_text)
            except Exception as e:
                logger.error(f"Error extracting ROCE: {e}")
            
            if fundamentals:
                fundamentals['source'] = 'screener'
                fundamentals['symbol'] = symbol
                fundamentals['scraped_at'] = datetime.now().isoformat()
                
                # Store in database
                self._store_fundamentals(symbol, fundamentals)
                
                return fundamentals
            
            return {'error': 'No fundamental data found on Screener'}
            
        except Exception as e:
            logger.error(f"Error scraping Screener for {symbol}: {e}")
            return {'error': f'Screener scraping failed: {str(e)}'}
    
    def _scrape_nse(self, symbol: str) -> Dict:
        """Scrape fundamental data from NSE website"""
        try:
            url = f"https://www.nseindia.com/get-quotes/equity?symbol={symbol}"
            
            response = self.session.get(url)
            if response.status_code != 200:
                return {'error': 'Failed to fetch NSE page'}
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract basic data
            fundamentals = {}
            
            # Current Price
            try:
                price_elem = soup.find('div', {'id': 'quoteLtp'})
                if price_elem:
                    price_text = price_elem.get_text()
                    fundamentals['current_price'] = self._parse_number(price_text)
            except Exception as e:
                logger.error(f"Error extracting current price: {e}")
            
            # Market Cap
            try:
                market_cap_elem = soup.find('td', text=re.compile(r'Market Cap', re.IGNORECASE))
                if market_cap_elem and market_cap_elem.find_next_sibling():
                    market_cap_text = market_cap_elem.find_next_sibling().get_text()
                    fundamentals['market_cap'] = self._parse_market_cap(market_cap_text)
            except Exception as e:
                logger.error(f"Error extracting market cap: {e}")
            
            if fundamentals:
                fundamentals['source'] = 'nse'
                fundamentals['symbol'] = symbol
                fundamentals['scraped_at'] = datetime.now().isoformat()
                
                # Store in database
                self._store_fundamentals(symbol, fundamentals)
                
                return fundamentals
            
            return {'error': 'No fundamental data found on NSE'}
            
        except Exception as e:
            logger.error(f"Error scraping NSE for {symbol}: {e}")
            return {'error': f'NSE scraping failed: {str(e)}'}
    
    def _parse_market_cap(self, text: str) -> Optional[float]:
        """Parse market cap text to number"""
        try:
            if not text:
                return None
            
            # Remove common text and convert to number
            text = text.strip().upper()
            text = re.sub(r'[^\d.]', '', text)
            
            if text:
                return float(text)
            
            return None
            
        except Exception as e:
            logger.error(f"Error parsing market cap: {e}")
            return None
    
    def _parse_number(self, text: str) -> Optional[float]:
        """Parse number from text"""
        try:
            if not text:
                return None
            
            # Remove common text and convert to number
            text = text.strip()
            text = re.sub(r'[^\d.-]', '', text)
            
            if text:
                return float(text)
            
            return None
            
        except Exception as e:
            logger.error(f"Error parsing number: {e}")
            return None
    
    def _store_fundamentals(self, symbol: str, fundamentals: Dict):
        """Store fundamental data in database"""
        try:
            collection = get_collection('fundamentals')
            fundamentals['symbol'] = symbol.upper()
            fundamentals['stored_at'] = datetime.now()
            
            collection.update_one(
                {'symbol': symbol.upper()},
                {'$set': fundamentals},
                upsert=True
            )
            
        except Exception as e:
            logger.error(f"Error storing fundamentals: {e}")
    
    def get_cached_fundamentals(self, symbol: str) -> Optional[Dict]:
        """Get cached fundamental data"""
        try:
            collection = get_collection('fundamentals')
            data = collection.find_one({'symbol': symbol.upper()})
            
            if data:
                # Check if cache is still valid (24 hours)
                stored_at = data.get('stored_at')
                if stored_at and (datetime.now() - stored_at).total_seconds() < 86400:
                    # Remove MongoDB ObjectId
                    data.pop('_id', None)
                    return data
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting cached fundamentals: {e}")
            return None
    
    def bulk_scrape_fundamentals(self, symbols: List[str]) -> Dict:
        """Scrape fundamental data for multiple symbols"""
        results = {
            'successful': [],
            'failed': [],
            'total': len(symbols)
        }
        
        for symbol in symbols:
            try:
                # Check cache first
                cached_data = self.get_cached_fundamentals(symbol)
                if cached_data:
                    results['successful'].append({
                        'symbol': symbol,
                        'source': 'cache',
                        'data': cached_data
                    })
                    continue
                
                # Scrape fresh data
                fundamental_data = self.get_stock_fundamentals(symbol)
                
                if fundamental_data and not fundamental_data.get('error'):
                    results['successful'].append({
                        'symbol': symbol,
                        'source': fundamental_data.get('source', 'unknown'),
                        'data': fundamental_data
                    })
                else:
                    results['failed'].append({
                        'symbol': symbol,
                        'error': fundamental_data.get('error', 'Unknown error')
                    })
                
                # Add delay to avoid rate limiting
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"Error processing {symbol}: {e}")
                results['failed'].append({
                    'symbol': symbol,
                    'error': str(e)
                })
        
        return results
    
    def cleanup(self):
        """Cleanup resources"""
        if self.driver:
            self.driver.quit()
    
    def __del__(self):
        """Destructor to cleanup resources"""
        self.cleanup() 