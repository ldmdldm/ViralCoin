"""
Configuration file for the ViralCoin project.
"""
import os
import logging
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Base directory of the project
BASE_DIR = Path(__file__).resolve().parent


class Config:
    """Base configuration class with settings common to all environments."""
    
    # Application settings
    APP_NAME = "ViralCoin"
    SECRET_KEY = os.getenv("SECRET_KEY", "development-key-change-in-production")
    DEBUG = False
    TESTING = False
    
    # API Settings
    API_PREFIX = "/api/v1"
    API_RATE_LIMIT = "100 per minute"
    
    # OpenAI API Configuration
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4")
    
    # Trend Analysis Settings
    TREND_SOURCES = ["twitter", "reddit", "news", "google_trends"]
    TREND_REFRESH_INTERVAL = 3600  # seconds
    TREND_MINIMUM_SCORE = float(os.getenv("MIN_TREND_SCORE", "0.75"))
    
    # Data sources weights for trend analysis
    TREND_WEIGHTS = {
        "twitter": float(os.getenv("WEIGHT_TWITTER", "0.4")),
        "reddit": float(os.getenv("WEIGHT_REDDIT", "0.3")),
        "google_trends": float(os.getenv("WEIGHT_GOOGLE_TRENDS", "0.2")),
        "news": float(os.getenv("WEIGHT_NEWS", "0.1")),
    }
    
    # Blockchain Configuration
    BLOCKCHAIN_NETWORK = os.getenv("BLOCKCHAIN_NETWORK", "polygon-mumbai")
    RPC_URL = os.getenv("RPC_URL", "https://polygon-mumbai.infura.io/v3/your-api-key")
    CHAIN_ID = int(os.getenv("CHAIN_ID", "80001"))  # Default to Polygon Mumbai
    PRIVATE_KEY = os.getenv("PRIVATE_KEY")
    WALLET_ADDRESS = os.getenv("WALLET_ADDRESS")
    
    # Smart Contract Settings
    FACTORY_ADDRESS = os.getenv("FACTORY_ADDRESS")
    GAS_LIMIT = int(os.getenv("GAS_LIMIT", "5000000"))
    GAS_PRICE = os.getenv("GAS_PRICE", "auto")  # "auto" or specific value in gwei
    
    # Token Defaults
    DEFAULT_TOKEN_SUPPLY = int(os.getenv("DEFAULT_INITIAL_SUPPLY", "1000000000"))
    DEFAULT_DECIMALS = int(os.getenv("DEFAULT_DECIMALS", "18"))
    
    # Token types and their characteristics
    TOKEN_TYPES = {
        "memecoin": {
            "supply_multiplier": 1000000000,
            "tax_rate": 0.05,
            "liquidity_allocation": 0.4,
        },
        "utility": {
            "supply_multiplier": 1000000,
            "tax_rate": 0.02,
            "liquidity_allocation": 0.6,
        },
        "governance": {
            "supply_multiplier": 100000,
            "tax_rate": 0.01,
            "liquidity_allocation": 0.7,
        },
    }
    
    # Liquidity Settings
    LIQUIDITY_PERCENTAGE = float(os.getenv("LIQUIDITY_PERCENTAGE", "0.3"))
    INITIAL_LIQUIDITY = float(os.getenv("INITIAL_LIQUIDITY", "0.1"))  # In ETH/MATIC
    
    # External API Keys
    TWITTER_API_KEY = os.getenv("TWITTER_API_KEY")
    TWITTER_API_SECRET = os.getenv("TWITTER_API_SECRET")
    TWITTER_ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
    TWITTER_ACCESS_SECRET = os.getenv("TWITTER_ACCESS_SECRET")
    
    REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
    REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
    REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT", "ViralCoin/1.0")
    
    # Logging Configuration
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_FILE = BASE_DIR / "logs" / "viralcoin.log"
    
    # File Paths
    CONTRACTS_DIR = BASE_DIR / "contracts"
    TOKEN_TEMPLATE = CONTRACTS_DIR / "token_template.vy"
    FACTORY_TEMPLATE = CONTRACTS_DIR / "TokenFactory.vy"
    
    @staticmethod
    def configure_logging():
        """Configure logging for the application."""
        log_dir = BASE_DIR / "logs"
        log_dir.mkdir(exist_ok=True)
        
        logging.basicConfig(
            level=getattr(logging, Config.LOG_LEVEL),
            format=Config.LOG_FORMAT,
            handlers=[
                logging.FileHandler(Config.LOG_FILE),
                logging.StreamHandler()
            ]
        )


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    LOG_LEVEL = "DEBUG"
    

class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    DEBUG = True
    LOG_LEVEL = "DEBUG"
    # Use test blockchain network
    BLOCKCHAIN_NETWORK = "hardhat"
    RPC_URL = "http://localhost:8545"


class ProductionConfig(Config):
    """Production configuration."""
    # Production should use environment variables for all sensitive data
    # Ensure SECRET_KEY is properly set in environment
    
    @classmethod
    def validate_config(cls):
        """Validate that all required configuration is set."""
        required_vars = [
            "SECRET_KEY", "OPENAI_API_KEY", "RPC_URL", 
            "PRIVATE_KEY", "WALLET_ADDRESS"
        ]
        
        missing_vars = [var for var in required_vars if not getattr(cls, var)]
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
            
            
# Configuration dictionary for easy access to different configurations
config_by_name = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig
}

# Active configuration based on environment variable or default to development
active_config = config_by_name[os.getenv("FLASK_ENV", "development")]

# If in production mode, validate required configuration
if os.getenv("FLASK_ENV") == "production":
    ProductionConfig.validate_config()

# Configure logging
active_config.configure_logging()
