# Multi-Asset Portfolio Tracker & Stock Analysis Platform

A comprehensive full-stack web platform to track real-time holdings across stocks, mutual funds, bonds, and other Indian asset classes.

## 🚀 Features

- **Real-time Portfolio Tracking**: Track holdings across multiple asset classes
- **FYERS API Integration**: Complete trading and portfolio management through FYERS
- **CAS Statement Integration**: Import holdings from CDSL/NSDL CAS statements
- **Fundamental Data Scraping**: Automated scraping from Tickertape, Screener, and NSE
- **Portfolio Refresh System**: Automatic and manual portfolio price updates
- **Live Market Data**: Real-time stock prices and fundamental data
- **Advanced Analytics**: XIRR, CAGR, P&L calculations
- **Stock Screening**: Custom filters (Low PE + High ROE, etc.)
- **Backtesting Engine**: Test trading strategies with historical data
- **Interactive Dashboard**: Asset allocation, sector breakdowns, performance charts
- **Mobile Responsive**: Optimized for all devices

## 🛠 Tech Stack

- **Frontend**: Angular 17, TypeScript, Angular Material
- **Backend**: Python Flask, SQLAlchemy
- **Database**: MongoDB
- **APIs**: FreeAPI.app, DataJockey API, Zerodha Kite API, FYERS API
- **Deployment**: Docker, Docker Compose

## 📁 Project Structure

```
portfolio-tracker/
├── frontend/                 # Angular application
├── backend/                  # Flask API
├── database/                 # MongoDB setup
├── docker/                   # Docker configuration
├── docs/                     # Documentation
└── scripts/                  # Utility scripts
```

## 🚀 Quick Start

### Prerequisites
- Node.js 18+
- Python 3.9+
- Docker & Docker Compose
- MongoDB

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd portfolio-tracker
   ```

2. **Set up environment variables**
   ```bash
   # Copy the example environment file
   cp backend/env.example backend/.env
   
   # Edit the .env file with your actual API keys
   # DO NOT commit the .env file to GitHub!
   ```

3. **Start with Docker (Recommended)**
   ```bash
   docker-compose up -d
   ```

4. **Manual Setup**
   ```bash
   # Backend setup
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   python app.py

   # Frontend setup
   cd frontend
   npm install
   ng serve
   ```

## 📊 API Documentation

### Core Endpoints

- `GET /api/portfolio` - Get user portfolio
- `POST /api/portfolio/holdings` - Add new holding
- `GET /api/stocks/{symbol}` - Get stock data
- `GET /api/mutual-funds/{isin}` - Get mutual fund data
- `POST /api/screen` - Stock screening
- `GET /api/analytics/xirr` - Calculate XIRR

### FYERS Integration

- `POST /api/fyers/auth` - Authenticate with FYERS
- `GET /api/fyers/portfolio` - Get FYERS portfolio
- `GET /api/fyers/history/{symbol}` - Get historical data
- `POST /api/fyers/order` - Place orders
- `GET /api/fyers/cas/{pan}` - Get CAS portfolio

### Fundamental Data

- `GET /api/fundamentals/{symbol}` - Get stock fundamentals
- `POST /api/fundamentals/bulk` - Bulk scrape fundamentals

### Portfolio Refresh

- `POST /api/refresh/start` - Start auto refresh
- `POST /api/refresh/stop` - Stop auto refresh
- `POST /api/refresh/manual` - Manual refresh
- `GET /api/refresh/status` - Get refresh status

## 🔧 Configuration

Create `.env` files in respective directories:

### Backend (.env)
```
MONGODB_URI=mongodb://localhost:27017/portfolio_tracker
FYERS_APP_ID=your_fyers_app_id
FYERS_APP_SECRET=your_fyers_app_secret
FREEAPI_KEY=your_api_key
PORTFOLIO_REFRESH_INTERVAL=300
```

### Frontend (environment.ts)
```typescript
export const environment = {
  production: false,
  apiUrl: 'http://localhost:5000/api'
};
```

## 📈 Features Roadmap

- [x] Basic portfolio tracking
- [x] Stock data integration
- [x] Dashboard visualization
- [ ] Goal tracking
- [ ] SIP optimization
- [ ] Advanced analytics
- [ ] Mobile app

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

For support, email support@portfoliotracker.com or create an issue in the repository. 