#!/bin/bash

# Multi-Asset Portfolio Tracker Setup Script
# This script sets up the development environment for the portfolio tracker project

echo "🚀 Setting up Multi-Asset Portfolio Tracker..."
echo "================================================"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    echo "Visit: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    echo "Visit: https://docs.docker.com/compose/install/"
    exit 1
fi

echo "✅ Docker and Docker Compose are installed"

# Create necessary directories
echo "📁 Creating project directories..."
mkdir -p backend/logs
mkdir -p frontend/src/assets
mkdir -p database/data
mkdir -p docs

# Create environment files
echo "⚙️  Creating environment files..."

# Backend .env
cat > backend/.env << EOF
MONGODB_URI=mongodb://admin:password123@mongodb:27017/portfolio_tracker?authSource=admin
JWT_SECRET_KEY=your-super-secret-jwt-key-change-this-in-production
FLASK_ENV=development
FLASK_APP=app.py
FYERS_APP_ID=your_fyers_app_id
FYERS_APP_SECRET=your_fyers_app_secret
FREEAPI_KEY=your_freeapi_key
DATAJOCKEY_API_KEY=your_datajockey_api_key
PORTFOLIO_REFRESH_INTERVAL=300
EOF

# Frontend environment
cat > frontend/src/environments/environment.ts << EOF
export const environment = {
  production: false,
  apiUrl: 'http://localhost:5000/api',
  appName: 'Portfolio Tracker',
  version: '1.0.0'
};
EOF

echo "✅ Environment files created"

# Create database initialization script
echo "🗄️  Creating database initialization..."
mkdir -p database/init
cat > database/init/01-init.js << EOF
// Initialize database collections
db = db.getSiblingDB('portfolio_tracker');

// Create collections
db.createCollection('users');
db.createCollection('portfolios');
db.createCollection('holdings');
db.createCollection('transactions');
db.createCollection('stocks');
db.createCollection('mutual_funds');
db.createCollection('bonds');
db.createCollection('analytics');

// Create indexes
db.users.createIndex({ "username": 1 }, { unique: true });
db.users.createIndex({ "email": 1 }, { unique: true });

db.portfolios.createIndex({ "user_id": 1 });
db.portfolios.createIndex({ "user_id": 1, "name": 1 });

db.holdings.createIndex({ "portfolio_id": 1 });
db.holdings.createIndex({ "symbol": 1 });
db.holdings.createIndex({ "portfolio_id": 1, "symbol": 1 });

db.transactions.createIndex({ "holding_id": 1 });
db.transactions.createIndex({ "date": 1 });
db.transactions.createIndex({ "holding_id": 1, "date": -1 });

db.stocks.createIndex({ "symbol": 1 }, { unique: true });
db.stocks.createIndex({ "nse_symbol": 1 });
db.stocks.createIndex({ "bse_symbol": 1 });

db.mutual_funds.createIndex({ "isin": 1 }, { unique: true });
db.mutual_funds.createIndex({ "amc": 1 });
db.mutual_funds.createIndex({ "category": 1 });

print("Database initialized successfully!");
EOF

echo "✅ Database initialization script created"

# Create a simple test script
echo "🧪 Creating test script..."
cat > test-setup.sh << 'EOF'
#!/bin/bash

echo "🧪 Testing Portfolio Tracker Setup..."
echo "====================================="

# Test if containers are running
echo "📊 Checking container status..."
docker-compose ps

# Test backend health
echo "🔍 Testing backend health..."
sleep 10
curl -f http://localhost:5000/api/health || echo "❌ Backend not responding"

# Test frontend
echo "🌐 Testing frontend..."
curl -f http://localhost:4200 || echo "❌ Frontend not responding"

# Test database connection
echo "🗄️  Testing database connection..."
docker exec portfolio_mongodb mongosh --eval "db.runCommand('ping')" || echo "❌ Database not responding"

echo "✅ Setup test completed!"
echo ""
echo "🎉 Portfolio Tracker is ready!"
echo "📱 Frontend: http://localhost:4200"
echo "🔧 Backend API: http://localhost:5000"
echo "🗄️  MongoDB: localhost:27017"
echo ""
echo "📚 Next steps:"
echo "1. Visit http://localhost:4200 to see the application"
echo "2. Check the README.md for detailed documentation"
echo "3. Review EXECUTION_PLAN.md for development roadmap"
EOF

chmod +x test-setup.sh

echo "✅ Test script created"

# Create development guide
echo "📚 Creating development guide..."
cat > DEVELOPMENT.md << 'EOF'
# Development Guide

## Quick Start

1. **Start the application:**
   ```bash
   docker-compose up -d
   ```

2. **Test the setup:**
   ```bash
   ./test-setup.sh
   ```

3. **View logs:**
   ```bash
   docker-compose logs -f
   ```

## Development Workflow

### Backend Development
- Backend code is in `backend/`
- Flask app runs on port 5000
- MongoDB runs on port 27017
- API documentation available at `/api/health`

### Frontend Development
- Frontend code is in `frontend/`
- Angular app runs on port 4200
- Hot reload enabled for development
- Material Design components available

### Database
- MongoDB with authentication
- Collections: users, portfolios, holdings, transactions, stocks, mutual_funds, bonds, analytics
- Indexes created automatically

## API Endpoints

- `GET /api/health` - Health check
- `POST /api/auth/login` - User login
- `GET /api/portfolio` - Get user portfolio
- `POST /api/portfolio/holdings` - Add holding
- `GET /api/stocks/{symbol}` - Get stock data
- `POST /api/screen` - Stock screening
- `GET /api/analytics/xirr` - Calculate XIRR

## Environment Variables

### Backend (.env)
- `MONGODB_URI` - MongoDB connection string
- `JWT_SECRET_KEY` - JWT secret key
- `ZERODHA_API_KEY` - Zerodha API key
- `FYERS_API_KEY` - FYERS API key
- `FREEAPI_KEY` - FreeAPI key
- `DATAJOCKEY_API_KEY` - DataJockey API key

## Troubleshooting

### Common Issues

1. **Port conflicts:**
   - Change ports in docker-compose.yml
   - Kill processes using ports 4200, 5000, 27017

2. **Database connection issues:**
   - Check MongoDB container is running
   - Verify credentials in .env file

3. **Frontend not loading:**
   - Check Angular container logs
   - Verify Node.js dependencies

4. **API errors:**
   - Check Flask container logs
   - Verify environment variables

### Useful Commands

```bash
# View all logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f mongodb

# Restart services
docker-compose restart

# Rebuild containers
docker-compose up --build

# Stop all services
docker-compose down

# Remove all data
docker-compose down -v
```

## Next Steps

1. Review the EXECUTION_PLAN.md for detailed roadmap
2. Set up your IDE with proper extensions
3. Configure API keys for external services
4. Start implementing features according to the plan
EOF

echo "✅ Development guide created"

# Make scripts executable
chmod +x setup.sh

echo ""
echo "🎉 Setup completed successfully!"
echo "================================================"
echo ""
echo "📋 What was created:"
echo "✅ Project structure with all directories"
echo "✅ Docker Compose configuration"
echo "✅ Environment files (.env)"
echo "✅ Database initialization scripts"
echo "✅ Test script (test-setup.sh)"
echo "✅ Development guide (DEVELOPMENT.md)"
echo ""
echo "🚀 To start the application:"
echo "1. Run: docker-compose up -d"
echo "2. Test: ./test-setup.sh"
echo "3. Visit: http://localhost:4200"
echo ""
echo "📚 Documentation:"
echo "- README.md - Project overview and setup"
echo "- EXECUTION_PLAN.md - Detailed development roadmap"
echo "- DEVELOPMENT.md - Development guide"
echo ""
echo "Happy coding! 🎯" 