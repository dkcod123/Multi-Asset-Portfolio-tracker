import os
import logging
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from pymongo.database import Database
from typing import Optional

logger = logging.getLogger(__name__)

class MongoDB:
    def __init__(self):
        self.client: Optional[MongoClient] = None
        self.db: Optional[Database] = None
        self.uri = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/portfolio_tracker')
    
    def connect(self):
        """Connect to MongoDB"""
        try:
            self.client = MongoClient(self.uri)
            # Test the connection
            self.client.admin.command('ping')
            self.db = self.client.get_database()
            logger.info("Successfully connected to MongoDB")
            return True
        except ConnectionFailure as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            return False
    
    def get_collection(self, collection_name):
        """Get a collection from the database"""
        if self.db is None:
            self.connect()
        if self.db is None:
            raise ConnectionError("Failed to connect to MongoDB")
        return self.db[collection_name]
    
    def close(self):
        """Close the MongoDB connection"""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")

# Global MongoDB instance
mongodb = MongoDB()

def init_db():
    """Initialize database and create indexes"""
    try:
        if mongodb.connect():
            # Create collections and indexes
            create_collections()
            create_indexes()
            logger.info("Database initialized successfully")
        else:
            logger.error("Failed to initialize database")
    except Exception as e:
        logger.error(f"Database initialization error: {e}")

def create_collections():
    """Create necessary collections"""
    collections = [
        'users',
        'portfolios',
        'holdings',
        'transactions',
        'stocks',
        'mutual_funds',
        'bonds',
        'analytics'
    ]
    
    for collection_name in collections:
        mongodb.get_collection(collection_name)

def create_indexes():
    """Create database indexes for better performance"""
    try:
        # Users collection indexes
        users_collection = mongodb.get_collection('users')
        users_collection.create_index('username', unique=True)
        users_collection.create_index('email', unique=True)
        
        # Portfolios collection indexes
        portfolios_collection = mongodb.get_collection('portfolios')
        portfolios_collection.create_index('user_id')
        portfolios_collection.create_index([('user_id', 1), ('name', 1)])
        
        # Holdings collection indexes
        holdings_collection = mongodb.get_collection('holdings')
        holdings_collection.create_index('portfolio_id')
        holdings_collection.create_index('symbol')
        holdings_collection.create_index([('portfolio_id', 1), ('symbol', 1)])
        
        # Transactions collection indexes
        transactions_collection = mongodb.get_collection('transactions')
        transactions_collection.create_index('holding_id')
        transactions_collection.create_index('date')
        transactions_collection.create_index([('holding_id', 1), ('date', -1)])
        
        # Stocks collection indexes
        stocks_collection = mongodb.get_collection('stocks')
        stocks_collection.create_index('symbol', unique=True)
        stocks_collection.create_index('nse_symbol')
        stocks_collection.create_index('bse_symbol')
        
        # Mutual funds collection indexes
        mf_collection = mongodb.get_collection('mutual_funds')
        mf_collection.create_index('isin', unique=True)
        mf_collection.create_index('amc')
        mf_collection.create_index('category')
        
        logger.info("Database indexes created successfully")
    except Exception as e:
        logger.error(f"Error creating indexes: {e}")

def get_db():
    """Get the database instance"""
    return mongodb.db

def get_collection(collection_name):
    """Get a collection from the database"""
    return mongodb.get_collection(collection_name) 