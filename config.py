"""
Configuration file for the ViralCoin project.
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file if present
load_dotenv()

# Blockchain configuration
RPC_URL = os.getenv("RPC_URL", "https://polygon-mumbai.infura.io/v3/your-api-key")
PRIVATE_KEY = os.getenv("PRIVATE_KEY", "")
FACTORY_ADDRESS = os.getenv("FACTORY_ADDRESS", "")

# Gas settings
GAS_LIMIT = int(os.getenv("GAS_LIMIT", "5000000"))
GAS_PRICE = int(os.getenv("GAS_PRICE", "50000000000"))  # 50 gwei

# Token deployment settings
MIN_TREND_SCORE = float(os.getenv("MIN_TREND_SCORE", "0.75"))
DEFAULT_INITIAL_SUPPLY = int(os.getenv("DEFAULT_INITIAL_SUPPLY", "1000000"))

# API keys for trend analysis
TWITTER_API_KEY = os.getenv("TWITTER_API_KEY", "")
TWITTER_API_SECRET = os.getenv("TWITTER_API_SECRET", "")
TWITTER_ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN", "")
TWITTER_ACCESS_SECRET = os.getenv("TWITTER_ACCESS_SECRET", "")

REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID", "")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET", "")
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT", "ViralCoin/1.0")

# Data sources weights for trend analysis
TREND_WEIGHTS = {
    "twitter": float(os.getenv("WEIGHT_TWITTER", "0.4")),
    "reddit": float(os.getenv("WEIGHT_REDDIT", "0.3")),
    "google_trends": float(os.getenv("WEIGHT_GOOGLE_TRENDS", "0.2")),
    "news": float(os.getenv("WEIGHT_NEWS", "0.1")),
}

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

