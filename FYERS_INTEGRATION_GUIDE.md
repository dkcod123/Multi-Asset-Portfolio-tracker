# FYERS API Integration & Portfolio Management Guide

## 🎯 Overview

This guide covers the implementation of FYERS API integration, fundamental data scraping, and automated portfolio refresh functionality for the Multi-Asset Portfolio Tracker.

## 🔧 FYERS API Integration

### Features Implemented

1. **Authentication System**
   - Secure login with username, password, and PIN
   - Token management and storage
   - Automatic token refresh

2. **Portfolio Management**
   - Real-time portfolio fetching from FYERS
   - Holdings and positions tracking
   - P&L calculations

3. **Historical Data for Backtesting**
   - Historical price data retrieval
   - Multiple timeframe support (1D, 1W, 1M)
   - Data formatting for analysis

4. **Order Placement**
   - Buy/Sell order execution
   - Order validation
   - Order tracking and storage

5. **CAS Statement Integration**
   - CDSL holdings extraction
   - NSDL holdings extraction
   - Mutual fund holdings
   - Bond and gold holdings

### API Endpoints

#### Authentication
```http
POST /api/fyers/auth
Content-Type: application/json

{
  "username": "your_username",
  "password": "your_password",
  "pin": "your_pin"
}
```

#### Portfolio Management
```http
GET /api/fyers/portfolio
Authorization: Bearer <jwt_token>
```

#### Historical Data
```http
GET /api/fyers/history/RELIANCE?start_date=2023-01-01&end_date=2023-12-31&interval=1D
Authorization: Bearer <jwt_token>
```

#### Order Placement
```http
POST /api/fyers/order
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "symbol": "NSE:RELIANCE-EQ",
  "qty": 100,
  "side": "BUY",
  "productType": "CNC",
  "orderType": "MARKET"
}
```

#### CAS Portfolio
```http
GET /api/fyers/cas/ABCDE1234F
Authorization: Bearer <jwt_token>
```

## 📊 Fundamental Data Scraping

### Features Implemented

1. **Multi-Source Scraping**
   - Tickertape.in scraping
   - Screener.in scraping
   - NSE website fallback

2. **Data Extraction**
   - Market cap, P/E ratio, P/B ratio
   - ROE, ROCE, Debt to Equity
   - Current price and 52-week high/low
   - Volume and other technical indicators

3. **Caching System**
   - 24-hour data caching
   - Automatic cache invalidation
   - Bulk scraping capabilities

4. **Error Handling**
   - Fallback mechanisms
   - Rate limiting protection
   - Comprehensive error logging

### API Endpoints

#### Single Stock Fundamentals
```http
GET /api/fundamentals/RELIANCE
```

#### Bulk Scraping
```http
POST /api/fundamentals/bulk
Content-Type: application/json

{
  "symbols": ["RELIANCE", "TCS", "HDFCBANK", "INFY"]
}
```

### Scraping Sources

1. **Tickertape.in**
   - Primary source for fundamental data
   - Real-time price updates
   - Comprehensive financial ratios

2. **Screener.in**
   - Fallback source
   - Detailed financial analysis
   - Historical data

3. **NSE Website**
   - Last resort option
   - Basic price information
   - Official exchange data

## 🔄 Portfolio Refresh System

### Features Implemented

1. **Automatic Refresh**
   - Configurable refresh intervals (default: 5 minutes)
   - Market hours optimization
   - Background processing

2. **Manual Refresh**
   - User-triggered refresh
   - Real-time price updates
   - Immediate feedback

3. **Smart Scheduling**
   - Market hours detection (9:15 AM - 3:30 PM)
   - Reduced frequency outside market hours
   - Daily summary generation

4. **Multi-Source Price Fetching**
   - FYERS API (primary)
   - Fundamental scraper (fallback)
   - Cached data (last resort)

### API Endpoints

#### Start Auto Refresh
```http
POST /api/refresh/start
Authorization: Bearer <jwt_token>
```

#### Stop Auto Refresh
```http
POST /api/refresh/stop
Authorization: Bearer <jwt_token>
```

#### Manual Refresh
```http
POST /api/refresh/manual
Authorization: Bearer <jwt_token>
```

#### Refresh Status
```http
GET /api/refresh/status
Authorization: Bearer <jwt_token>
```

## 🗄️ Database Collections

### New Collections Added

1. **fyers_tokens**
   ```json
   {
     "username": "user123",
     "access_token": "token_string",
     "refresh_token": "refresh_string",
     "user_id": "fyers_user_id",
     "created_at": "2024-01-01T10:00:00Z",
     "expires_at": "2024-01-02T10:00:00Z"
   }
   ```

2. **stock_fundamentals**
   ```json
   {
     "symbol": "RELIANCE",
     "market_cap": 1500000000000,
     "pe_ratio": 18.5,
     "pb_ratio": 2.1,
     "roe": 12.5,
     "roce": 15.2,
     "current_price": 2500.50,
     "source": "tickertape",
     "scraped_at": "2024-01-01T10:00:00Z"
   }
   ```

3. **refresh_logs**
   ```json
   {
     "user_id": "user123",
     "refresh_type": "manual",
     "timestamp": "2024-01-01T10:00:00Z",
     "status": "success"
   }
   ```

4. **system_metrics**
   ```json
   {
     "metric": "last_portfolio_refresh",
     "value": "2024-01-01T10:00:00Z",
     "updated_at": "2024-01-01T10:00:00Z"
   }
   ```

5. **daily_summaries**
   ```json
   {
     "date": "2024-01-01",
     "total_users": 50,
     "portfolios": [
       {
         "user_id": "user123",
         "total_holdings": 10,
         "total_value": 500000,
         "total_pnl": 25000,
         "best_performer": {"symbol": "RELIANCE", "pnl_percentage": 15.5},
         "worst_performer": {"symbol": "INFY", "pnl_percentage": -5.2},
         "asset_allocation": {"equity": 80, "mutual_fund": 20}
       }
     ]
   }
   ```

## ⚙️ Configuration

### Environment Variables

```bash
# FYERS API Configuration
FYERS_APP_ID=your_fyers_app_id
FYERS_APP_SECRET=your_fyers_app_secret

# Portfolio Refresh Configuration
PORTFOLIO_REFRESH_INTERVAL=300  # 5 minutes

# Database Configuration
MONGODB_URI=mongodb://admin:password123@mongodb:27017/portfolio_tracker?authSource=admin

# JWT Configuration
JWT_SECRET_KEY=your-super-secret-jwt-key-change-this-in-production
```

### FYERS API Setup

1. **Create FYERS App**
   - Visit https://api.fyers.in/
   - Create a new app
   - Get App ID and App Secret

2. **Configure Redirect URI**
   - Set redirect URI to: `https://api.fyers.in/api/v2/redirect-uri`

3. **Update Environment**
   - Add FYERS_APP_ID and FYERS_APP_SECRET to .env file

## 🔄 Usage Examples

### 1. Authenticate with FYERS
```python
import requests

# Authenticate
auth_response = requests.post('http://localhost:5000/api/fyers/auth', json={
    'username': 'your_username',
    'password': 'your_password',
    'pin': 'your_pin'
})

if auth_response.status_code == 200:
    print("Authentication successful")
else:
    print("Authentication failed")
```

### 2. Get Portfolio
```python
# Get portfolio (requires JWT token)
headers = {'Authorization': 'Bearer your_jwt_token'}
portfolio_response = requests.get('http://localhost:5000/api/fyers/portfolio', headers=headers)

if portfolio_response.status_code == 200:
    portfolio = portfolio_response.json()
    print(f"Total portfolio value: ₹{portfolio['total_value']:,.2f}")
```

### 3. Get Historical Data
```python
# Get historical data for backtesting
history_response = requests.get(
    'http://localhost:5000/api/fyers/history/RELIANCE',
    params={
        'start_date': '2023-01-01',
        'end_date': '2023-12-31',
        'interval': '1D'
    },
    headers=headers
)

if history_response.status_code == 200:
    data = history_response.json()
    print(f"Retrieved {len(data['data'])} data points")
```

### 4. Get Fundamental Data
```python
# Get fundamental data
fundamental_response = requests.get('http://localhost:5000/api/fundamentals/RELIANCE')

if fundamental_response.status_code == 200:
    fundamentals = fundamental_response.json()
    print(f"P/E Ratio: {fundamentals.get('pe_ratio')}")
    print(f"Market Cap: ₹{fundamentals.get('market_cap'):,.0f}")
```

### 5. Refresh Portfolio
```python
# Manual refresh
refresh_response = requests.post('http://localhost:5000/api/refresh/manual', headers=headers)

if refresh_response.status_code == 200:
    result = refresh_response.json()
    print(f"Refreshed {result['holdings_updated']} holdings")
    print(f"Total value: ₹{result['total_value']:,.2f}")
```

## 🚀 Advanced Features

### 1. Backtesting Support
- Historical data retrieval for any timeframe
- Data formatting for technical analysis
- Support for multiple intervals (1D, 1W, 1M)

### 2. CAS Statement Integration
- Automatic extraction of holdings from CAS statements
- Support for CDSL and NSDL
- Mutual fund, bond, and gold holdings

### 3. Smart Refresh Logic
- Market hours detection
- Configurable refresh intervals
- Fallback mechanisms for price fetching

### 4. Comprehensive Logging
- Detailed error logging
- Performance monitoring
- Audit trails for all operations

## 🔒 Security Considerations

1. **Token Management**
   - Secure storage of FYERS tokens
   - Automatic token refresh
   - Token expiration handling

2. **Rate Limiting**
   - Built-in delays between API calls
   - Respect for API rate limits
   - Fallback mechanisms

3. **Error Handling**
   - Comprehensive error catching
   - Graceful degradation
   - User-friendly error messages

## 📈 Performance Optimization

1. **Caching Strategy**
   - 24-hour fundamental data cache
   - Portfolio data caching
   - Smart cache invalidation

2. **Background Processing**
   - Asynchronous refresh operations
   - Non-blocking API calls
   - Thread-safe operations

3. **Database Optimization**
   - Proper indexing on collections
   - Efficient queries
   - Connection pooling

## 🛠️ Troubleshooting

### Common Issues

1. **Authentication Failures**
   - Verify FYERS credentials
   - Check App ID and Secret
   - Ensure correct redirect URI

2. **Data Fetching Issues**
   - Check network connectivity
   - Verify API rate limits
   - Review error logs

3. **Refresh Problems**
   - Check scheduler status
   - Verify market hours
   - Review refresh logs

### Debug Commands

```bash
# Check service status
curl http://localhost:5000/api/refresh/status

# View logs
docker-compose logs -f backend

# Test fundamental scraping
curl http://localhost:5000/api/fundamentals/RELIANCE
```

## 📚 Next Steps

1. **Production Deployment**
   - Set up proper SSL certificates
   - Configure production environment variables
   - Set up monitoring and alerting

2. **Advanced Features**
   - Implement real-time websocket connections
   - Add advanced charting capabilities
   - Integrate with more data sources

3. **Mobile App**
   - Develop React Native mobile app
   - Push notifications for price alerts
   - Offline data synchronization

---

This implementation provides a robust foundation for portfolio tracking with FYERS integration, comprehensive fundamental data scraping, and intelligent portfolio refresh capabilities. The system is designed to be scalable, secure, and user-friendly. 