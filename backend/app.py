from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import logging

# Import our modules
from database.mongodb import init_db
from services.stock_service import StockService
from services.portfolio_service import PortfolioService
from services.analytics_service import AnalyticsService
from services.screening_service import ScreeningService
from services.fyers_service import FyersService
from services.fundamental_scraper import FundamentalScraper
from services.portfolio_refresh_service import PortfolioRefreshService
from services.cas_upload_service import CASUploadService
from services.mutual_fund_service import MutualFundService
from services.cas_scraper_service import CASScraperService
from services.zerodha_service import ZerodhaService

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'your-secret-key')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)

# Initialize extensions
CORS(app)
jwt = JWTManager(app)

# Initialize services
stock_service = StockService()
portfolio_service = PortfolioService()
analytics_service = AnalyticsService()
screening_service = ScreeningService()
fyers_service = FyersService()
fundamental_scraper = FundamentalScraper()
portfolio_refresh_service = PortfolioRefreshService()
cas_upload_service = CASUploadService()
mutual_fund_service = MutualFundService()
cas_scraper_service = CASScraperService()
zerodha_service = ZerodhaService()

@app.before_first_request
def initialize_app():
    """Initialize database and services"""
    try:
        init_db()
        logger.info("Application initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize application: {e}")

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })

@app.route('/api/auth/login', methods=['POST'])
def login():
    """User login endpoint"""
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        # TODO: Implement proper authentication
        # For now, accept any username/password
        if username and password:
            access_token = create_access_token(identity=username)
            return jsonify({
                'access_token': access_token,
                'user': {'username': username}
            }), 200
        else:
            return jsonify({'error': 'Invalid credentials'}), 401
    except Exception as e:
        logger.error(f"Login error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/portfolio', methods=['GET'])
@jwt_required()
def get_portfolio():
    """Get user portfolio"""
    try:
        user_id = get_jwt_identity()
        portfolio = portfolio_service.get_portfolio(user_id)
        return jsonify(portfolio), 200
    except Exception as e:
        logger.error(f"Error getting portfolio: {e}")
        return jsonify({'error': 'Failed to get portfolio'}), 500

@app.route('/api/portfolio/consolidated', methods=['GET'])
@jwt_required()
def get_consolidated_portfolio():
    """Get consolidated portfolio from all sources (FYERS, CAS, Manual)"""
    try:
        user_id = get_jwt_identity()
        
        # Get data from different sources
        fyers_data = fyers_service.get_portfolio(user_id).get('holdings', [])
        cas_data = cas_upload_service.get_cas_data(user_id).get('holdings', [])
        manual_data = []  # TODO: Implement manual holdings storage
        
        # Consolidate portfolio data
        consolidated = portfolio_service.consolidate_portfolio(
            fyers_data=fyers_data,
            cas_data=cas_data,
            manual_data=manual_data
        )
        
        return jsonify(consolidated), 200
    except Exception as e:
        logger.error(f"Error getting consolidated portfolio: {e}")
        return jsonify({'error': 'Failed to get consolidated portfolio'}), 500

@app.route('/api/portfolio/holdings', methods=['POST'])
@jwt_required()
def add_holding():
    """Add new holding to portfolio"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        holding = portfolio_service.add_holding(user_id, data)
        return jsonify(holding), 201
    except Exception as e:
        logger.error(f"Error adding holding: {e}")
        return jsonify({'error': 'Failed to add holding'}), 500

@app.route('/api/stocks/<symbol>', methods=['GET'])
def get_stock_data(symbol):
    """Get stock data by symbol"""
    try:
        stock_data = stock_service.get_stock_data(symbol)
        return jsonify(stock_data), 200
    except Exception as e:
        logger.error(f"Error getting stock data for {symbol}: {e}")
        return jsonify({'error': 'Failed to get stock data'}), 500

@app.route('/api/mutual-funds/<isin>', methods=['GET'])
def get_mutual_fund_data(isin):
    """Get mutual fund data by ISIN"""
    try:
        mf_data = stock_service.get_mutual_fund_data(isin)
        return jsonify(mf_data), 200
    except Exception as e:
        logger.error(f"Error getting mutual fund data for {isin}: {e}")
        return jsonify({'error': 'Failed to get mutual fund data'}), 500

@app.route('/api/screen', methods=['POST'])
def screen_stocks():
    """Stock screening endpoint"""
    try:
        filters = request.get_json()
        results = screening_service.screen_stocks(filters)
        return jsonify(results), 200
    except Exception as e:
        logger.error(f"Error screening stocks: {e}")
        return jsonify({'error': 'Failed to screen stocks'}), 500

@app.route('/api/analytics/xirr', methods=['POST'])
@jwt_required()
def calculate_xirr():
    """Calculate XIRR for portfolio"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        xirr = analytics_service.calculate_xirr(user_id, data)
        return jsonify({'xirr': xirr}), 200
    except Exception as e:
        logger.error(f"Error calculating XIRR: {e}")
        return jsonify({'error': 'Failed to calculate XIRR'}), 500

@app.route('/api/analytics/cagr', methods=['GET'])
@jwt_required()
def calculate_cagr():
    """Calculate CAGR for portfolio"""
    try:
        user_id = get_jwt_identity()
        cagr = analytics_service.calculate_cagr(user_id)
        return jsonify({'cagr': cagr}), 200
    except Exception as e:
        logger.error(f"Error calculating CAGR: {e}")
        return jsonify({'error': 'Failed to calculate CAGR'}), 500

# FYERS API Integration
@app.route('/api/fyers/auth', methods=['POST'])
def fyers_auth():
    """Authenticate with FYERS API"""
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        pin = data.get('pin')
        
        if not all([username, password, pin]):
            return jsonify({'error': 'Username, password, and PIN are required'}), 400
        
        result = fyers_service.authenticate(username, password, pin)
        return jsonify(result), 200 if result.get('success') else 400
    except Exception as e:
        logger.error(f"FYERS authentication error: {e}")
        return jsonify({'error': 'Authentication failed'}), 500

@app.route('/api/fyers/portfolio', methods=['GET'])
@jwt_required()
def get_fyers_portfolio():
    """Get portfolio from FYERS"""
    try:
        user_id = get_jwt_identity()
        portfolio = fyers_service.get_portfolio(user_id)
        return jsonify(portfolio), 200
    except Exception as e:
        logger.error(f"Error getting FYERS portfolio: {e}")
        return jsonify({'error': 'Failed to get portfolio'}), 500

@app.route('/api/fyers/history/<symbol>', methods=['GET'])
@jwt_required()
def get_historical_data(symbol):
    """Get historical data for backtesting"""
    try:
        start_date = request.args.get('start_date', '2023-01-01')
        end_date = request.args.get('end_date', datetime.now().strftime('%Y-%m-%d'))
        interval = request.args.get('interval', '1D')
        
        data = fyers_service.get_historical_data(symbol, start_date, end_date, interval)
        return jsonify(data), 200
    except Exception as e:
        logger.error(f"Error getting historical data: {e}")
        return jsonify({'error': 'Failed to get historical data'}), 500

@app.route('/api/fyers/order', methods=['POST'])
@jwt_required()
def place_order():
    """Place order on FYERS"""
    try:
        order_data = request.get_json()
        result = fyers_service.place_order(order_data)
        return jsonify(result), 200 if result.get('success') else 400
    except Exception as e:
        logger.error(f"Error placing order: {e}")
        return jsonify({'error': 'Failed to place order'}), 500

@app.route('/api/fyers/cas/<pan_number>', methods=['GET'])
@jwt_required()
def get_cas_portfolio(pan_number):
    """Get portfolio from CAS statements"""
    try:
        cas_data = fyers_service.get_cas_portfolio(pan_number)
        return jsonify(cas_data), 200
    except Exception as e:
        logger.error(f"Error getting CAS portfolio: {e}")
        return jsonify({'error': 'Failed to get CAS portfolio'}), 500

# Fundamental Data Scraping
@app.route('/api/fundamentals/<symbol>', methods=['GET'])
def get_fundamentals(symbol):
    """Get fundamental data for a stock"""
    try:
        # Check cache first
        cached_data = fundamental_scraper.get_cached_fundamentals(symbol)
        if cached_data:
            return jsonify(cached_data), 200
        
        # Scrape fresh data
        fundamental_data = fundamental_scraper.get_stock_fundamentals(symbol)
        return jsonify(fundamental_data), 200
    except Exception as e:
        logger.error(f"Error getting fundamentals for {symbol}: {e}")
        return jsonify({'error': 'Failed to get fundamental data'}), 500

@app.route('/api/fundamentals/bulk', methods=['POST'])
def bulk_scrape_fundamentals():
    """Bulk scrape fundamental data for multiple symbols"""
    try:
        data = request.get_json()
        symbols = data.get('symbols', [])
        
        if not symbols:
            return jsonify({'error': 'Symbols list is required'}), 400
        
        results = fundamental_scraper.bulk_scrape_fundamentals(symbols)
        return jsonify(results), 200
    except Exception as e:
        logger.error(f"Error in bulk fundamental scraping: {e}")
        return jsonify({'error': 'Failed to scrape fundamentals'}), 500

# Portfolio Refresh
@app.route('/api/refresh/start', methods=['POST'])
@jwt_required()
def start_auto_refresh():
    """Start automatic portfolio refresh"""
    try:
        result = portfolio_refresh_service.start_auto_refresh()
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Error starting auto refresh: {e}")
        return jsonify({'error': 'Failed to start auto refresh'}), 500

@app.route('/api/refresh/stop', methods=['POST'])
@jwt_required()
def stop_auto_refresh():
    """Stop automatic portfolio refresh"""
    try:
        result = portfolio_refresh_service.stop_auto_refresh()
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Error stopping auto refresh: {e}")
        return jsonify({'error': 'Failed to stop auto refresh'}), 500

@app.route('/api/refresh/manual', methods=['POST'])
@jwt_required()
def manual_refresh():
    """Manually refresh portfolio"""
    try:
        user_id = get_jwt_identity()
        result = portfolio_refresh_service.manual_refresh_portfolio(user_id)
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Error in manual refresh: {e}")
        return jsonify({'error': 'Failed to refresh portfolio'}), 500

@app.route('/api/refresh/status', methods=['GET'])
@jwt_required()
def get_refresh_status():
    """Get refresh service status"""
    try:
        status = portfolio_refresh_service.get_refresh_status()
        return jsonify(status), 200
    except Exception as e:
        logger.error(f"Error getting refresh status: {e}")
        return jsonify({'error': 'Failed to get refresh status'}), 500

# CAS Upload Service
@app.route('/api/cas/upload', methods=['POST'])
@jwt_required()
def upload_cas_statement():
    """Upload and parse CAS statement"""
    try:
        user_id = get_jwt_identity()
        
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Save file temporarily
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp_file:
            file.save(tmp_file.name)
            tmp_file_path = tmp_file.name
        
        try:
            # Parse CAS statement
            result = cas_upload_service.parse_cas_statement(tmp_file_path, user_id)
            
            if 'error' not in result:
                # Store parsed data
                cas_upload_service.store_cas_data(user_id, result)
            
            return jsonify(result), 200
            
        finally:
            # Clean up temporary file
            if os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)
                
    except Exception as e:
        logger.error(f"Error uploading CAS statement: {e}")
        return jsonify({'error': 'Failed to upload CAS statement'}), 500

@app.route('/api/cas/data/<pan_number>', methods=['GET'])
@jwt_required()
def get_cas_data(pan_number):
    """Get uploaded CAS data for PAN"""
    try:
        cas_data = cas_upload_service.get_uploaded_cas_data(pan_number)
        if cas_data:
            return jsonify(cas_data), 200
        else:
            return jsonify({'error': 'No CAS data found for this PAN'}), 404
    except Exception as e:
        logger.error(f"Error getting CAS data: {e}")
        return jsonify({'error': 'Failed to get CAS data'}), 500

# CAS Scraper Endpoints
@app.route('/api/cas/scrape', methods=['POST'])
@jwt_required()
def scrape_cas():
    """Scrape CAS statement from URL or file"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        url = data.get('url')
        pan_number = data.get('pan_number')
        
        if not url or not pan_number:
            return jsonify({'error': 'URL and PAN number are required'}), 400
        
        result = cas_scraper_service.scrape_cas_from_url(url, pan_number)
        return jsonify(result), 200 if result.get('success') else 400
        
    except Exception as e:
        logger.error(f"Error scraping CAS: {e}")
        return jsonify({'error': 'Failed to scrape CAS'}), 500

@app.route('/api/cas/sources', methods=['GET'])
def get_cas_sources():
    """Get available CAS sources"""
    try:
        sources = cas_scraper_service.get_cas_sources()
        return jsonify({'sources': sources}), 200
    except Exception as e:
        logger.error(f"Error getting CAS sources: {e}")
        return jsonify({'error': 'Failed to get CAS sources'}), 500

@app.route('/api/cas/auto-scrape/<pan_number>', methods=['POST'])
@jwt_required()
def auto_scrape_cas(pan_number):
    """Automatically scrape CAS from all available sources"""
    try:
        user_id = get_jwt_identity()
        
        # Try all available sources
        sources = cas_scraper_service.get_cas_sources()
        results = []
        
        for source in sources:
            if source['supported']:
                try:
                    result = cas_scraper_service.scrape_cas_from_url(
                        source['url'], pan_number
                    )
                    if result.get('success'):
                        results.append({
                            'source': source['name'],
                            'data': result
                        })
                except Exception as e:
                    logger.warning(f"Source {source['name']} failed: {e}")
                    continue
        
        return jsonify({
            'success': len(results) > 0,
            'results': results,
            'total_sources_tried': len(sources),
            'successful_sources': len(results)
        }), 200
        
    except Exception as e:
        logger.error(f"Error auto-scraping CAS: {e}")
        return jsonify({'error': 'Failed to auto-scrape CAS'}), 500

# Zerodha API Integration
@app.route('/api/zerodha/auth', methods=['POST'])
def zerodha_auth():
    """Authenticate with Zerodha API"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        password = data.get('password')
        pin = data.get('pin')
        
        if not all([user_id, password, pin]):
            return jsonify({'error': 'User ID, password, and PIN are required'}), 400
        
        result = zerodha_service.authenticate(user_id, password, pin)
        return jsonify(result), 200 if result.get('success') else 400
    except Exception as e:
        logger.error(f"Zerodha authentication error: {e}")
        return jsonify({'error': 'Authentication failed'}), 500

@app.route('/api/zerodha/portfolio', methods=['GET'])
@jwt_required()
def get_zerodha_portfolio():
    """Get portfolio from Zerodha"""
    try:
        user_id = get_jwt_identity()
        portfolio = zerodha_service.get_portfolio(user_id)
        return jsonify(portfolio), 200
    except Exception as e:
        logger.error(f"Error getting Zerodha portfolio: {e}")
        return jsonify({'error': 'Failed to get portfolio'}), 500

@app.route('/api/zerodha/history/<symbol>', methods=['GET'])
@jwt_required()
def get_zerodha_historical_data(symbol):
    """Get historical data from Zerodha"""
    try:
        start_date = request.args.get('start_date', '2024-01-01')
        end_date = request.args.get('end_date', datetime.now().strftime('%Y-%m-%d'))
        interval = request.args.get('interval', 'day')
        
        data = zerodha_service.get_historical_data(symbol, start_date, end_date, interval)
        return jsonify(data), 200
    except Exception as e:
        logger.error(f"Error getting Zerodha historical data: {e}")
        return jsonify({'error': 'Failed to get historical data'}), 500

@app.route('/api/zerodha/order', methods=['POST'])
@jwt_required()
def place_zerodha_order():
    """Place order on Zerodha"""
    try:
        data = request.get_json()
        symbol = data.get('symbol')
        quantity = data.get('quantity')
        side = data.get('side')  # BUY or SELL
        order_type = data.get('order_type', 'MARKET')
        price = data.get('price')
        
        if not all([symbol, quantity, side]):
            return jsonify({'error': 'Symbol, quantity, and side are required'}), 400
        
        result = zerodha_service.place_order(symbol, quantity, side, order_type, price)
        return jsonify(result), 200 if result.get('success') else 400
    except Exception as e:
        logger.error(f"Error placing Zerodha order: {e}")
        return jsonify({'error': 'Failed to place order'}), 500

@app.route('/api/zerodha/order/<order_id>', methods=['GET'])
@jwt_required()
def get_zerodha_order_status(order_id):
    """Get order status from Zerodha"""
    try:
        status = zerodha_service.get_order_status(order_id)
        return jsonify(status), 200
    except Exception as e:
        logger.error(f"Error getting Zerodha order status: {e}")
        return jsonify({'error': 'Failed to get order status'}), 500

@app.route('/api/zerodha/order/<order_id>', methods=['DELETE'])
@jwt_required()
def cancel_zerodha_order(order_id):
    """Cancel order on Zerodha"""
    try:
        result = zerodha_service.cancel_order(order_id)
        return jsonify(result), 200 if result.get('success') else 400
    except Exception as e:
        logger.error(f"Error cancelling Zerodha order: {e}")
        return jsonify({'error': 'Failed to cancel order'}), 500

@app.route('/api/zerodha/market-data', methods=['POST'])
@jwt_required()
def get_zerodha_market_data():
    """Get real-time market data from Zerodha"""
    try:
        data = request.get_json()
        symbols = data.get('symbols', [])
        
        if not symbols:
            return jsonify({'error': 'Symbols list is required'}), 400
        
        market_data = zerodha_service.get_market_data(symbols)
        return jsonify(market_data), 200
    except Exception as e:
        logger.error(f"Error getting Zerodha market data: {e}")
        return jsonify({'error': 'Failed to get market data'}), 500

@app.route('/api/zerodha/instruments/<exchange>', methods=['GET'])
@jwt_required()
def get_zerodha_instruments(exchange):
    """Get instruments list from Zerodha"""
    try:
        instruments = zerodha_service.get_instruments(exchange)
        return jsonify(instruments), 200
    except Exception as e:
        logger.error(f"Error getting Zerodha instruments: {e}")
        return jsonify({'error': 'Failed to get instruments'}), 500

@app.route('/api/zerodha/margins', methods=['GET'])
@jwt_required()
def get_zerodha_margins():
    """Get account margins from Zerodha"""
    try:
        margins = zerodha_service.get_margins()
        return jsonify(margins), 200
    except Exception as e:
        logger.error(f"Error getting Zerodha margins: {e}")
        return jsonify({'error': 'Failed to get margins'}), 500

@app.route('/api/zerodha/positions', methods=['GET'])
@jwt_required()
def get_zerodha_positions():
    """Get current positions from Zerodha"""
    try:
        positions = zerodha_service.get_positions()
        return jsonify(positions), 200
    except Exception as e:
        logger.error(f"Error getting Zerodha positions: {e}")
        return jsonify({'error': 'Failed to get positions'}), 500

# Mutual Fund Management
@app.route('/api/mutual-funds/<pan_number>', methods=['GET'])
@jwt_required()
def get_mutual_fund_holdings(pan_number):
    """Get all mutual fund holdings for PAN"""
    try:
        holdings = mutual_fund_service.get_mutual_fund_holdings(pan_number)
        return jsonify(holdings), 200
    except Exception as e:
        logger.error(f"Error getting mutual fund holdings: {e}")
        return jsonify({'error': 'Failed to get mutual fund holdings'}), 500

@app.route('/api/mutual-funds/<pan_number>/summary', methods=['GET'])
@jwt_required()
def get_mf_portfolio_summary(pan_number):
    """Get mutual fund portfolio summary"""
    try:
        summary = mutual_fund_service.get_mf_portfolio_summary(pan_number)
        return jsonify(summary), 200
    except Exception as e:
        logger.error(f"Error getting MF portfolio summary: {e}")
        return jsonify({'error': 'Failed to get MF portfolio summary'}), 500

@app.route('/api/mutual-funds/<pan_number>/manual', methods=['POST'])
@jwt_required()
def add_manual_mf_holding(pan_number):
    """Add manually entered mutual fund holding"""
    try:
        holding_data = request.get_json()
        result = mutual_fund_service.add_manual_mf_holding(pan_number, holding_data)
        return jsonify(result), 200 if result.get('success') else 400
    except Exception as e:
        logger.error(f"Error adding manual MF holding: {e}")
        return jsonify({'error': 'Failed to add mutual fund holding'}), 500

@app.route('/api/mutual-funds/nav/<isin>', methods=['GET'])
def get_mf_nav(isin):
    """Get current NAV for mutual fund"""
    try:
        nav = mutual_fund_service.get_mf_nav(isin)
        if nav:
            return jsonify({'isin': isin, 'nav': nav}), 200
        else:
            return jsonify({'error': 'NAV not found'}), 404
    except Exception as e:
        logger.error(f"Error getting MF NAV: {e}")
        return jsonify({'error': 'Failed to get NAV'}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_ENV') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug) 