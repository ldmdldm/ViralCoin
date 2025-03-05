from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime, Text, Enum, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import enum

Base = declarative_base()

class TokenType(enum.Enum):
    MEME = "meme"
    UTILITY = "utility"
    SOCIAL = "social"
    GOVERNANCE = "governance"
    DEFI = "defi"
    NFT = "nft"
    GAMING = "gaming"

class TrendSource(enum.Enum):
    TWITTER = "twitter"
    REDDIT = "reddit"
    GOOGLE = "google_trends"
    TIKTOK = "tiktok"
    NEWS = "news"
    CUSTOM = "custom"

class TransactionType(enum.Enum):
    TRANSFER = "transfer"
    MINT = "mint"
    BURN = "burn"
    SWAP = "swap"
    LIQUIDITY_ADD = "liquidity_add"
    LIQUIDITY_REMOVE = "liquidity_remove"

class User(Base):
    """Model representing a registered user in the ViralCoin platform."""
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String(64), unique=True, nullable=False, index=True)
    email = Column(String(120), unique=True, nullable=False, index=True)
    password_hash = Column(String(128), nullable=False)
    wallet_address = Column(String(42))
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    api_key = Column(String(64), unique=True)
    settings = Column(JSON)

    # Relationships
    tokens = relationship("Token", back_populates="owner")
    deployments = relationship("TokenDeployment", back_populates="deployer")
    transactions = relationship("TokenTransaction", back_populates="user")
    trend_submissions = relationship("TrendSubmission", back_populates="submitter")

    def __repr__(self):
        return f"<User {self.username}>"

class Token(Base):
    """Model representing a token created on the ViralCoin platform."""
    __tablename__ = 'tokens'

    id = Column(Integer, primary_key=True)
    name = Column(String(64), nullable=False)
    symbol = Column(String(10), nullable=False)
    owner_id = Column(Integer, ForeignKey('users.id'))
    token_type = Column(Enum(TokenType), nullable=False)
    initial_supply = Column(Float, nullable=False)
    max_supply = Column(Float)
    decimals = Column(Integer, default=18)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_mintable = Column(Boolean, default=True)
    burn_rate = Column(Float, default=0)  # Percentage as decimal (0.01 = 1%)
    tax_rate = Column(Float, default=0)   # Percentage as decimal (0.01 = 1%)
    description = Column(Text)
    website = Column(String(255))
    logo_url = Column(String(255))
    social_links = Column(JSON)  # Store as JSON: {twitter: "url", discord: "url", etc.}
    current_price = Column(Float)
    market_cap = Column(Float)
    
    # Trend-related fields
    trend_id = Column(Integer, ForeignKey('trends.id'))
    trend_score = Column(Float)
    
    # Blockchain fields
    contract_address = Column(String(42))
    contract_bytecode = Column(Text)
    abi = Column(JSON)
    chain_id = Column(Integer)
    network_name = Column(String(50))
    creator_address = Column(String(42))
    
    # Relationships
    owner = relationship("User", back_populates="tokens")
    trend = relationship("Trend", back_populates="tokens")
    deployments = relationship("TokenDeployment", back_populates="token")
    transactions = relationship("TokenTransaction", back_populates="token")
    liquidity_pools = relationship("LiquidityPool", back_populates="token")
    price_history = relationship("TokenPrice", back_populates="token")
    analytics = relationship("TokenAnalytics", back_populates="token", uselist=False)

    def __repr__(self):
        return f"<Token {self.symbol}>"

class Trend(Base):
    """Model representing a trending topic that can be tokenized."""
    __tablename__ = 'trends'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, index=True)
    description = Column(Text)
    category = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    expiry_at = Column(DateTime)  # When this trend might no longer be relevant
    score = Column(Float, default=0.0)  # Overall trend score
    sources = Column(JSON)  # Sources where trend was found
    keywords = Column(JSON)  # Related keywords
    sentiment = Column(Float)  # -1.0 to 1.0
    volume = Column(Integer)  # Number of mentions
    growth_rate = Column(Float)  # Growth rate over time
    tokenized = Column(Boolean, default=False)  # Whether a token was created
    recommended_token_type = Column(Enum(TokenType))
    ai_analysis = Column(Text)  # AI-generated analysis
    
    # Relationships
    tokens = relationship("Token", back_populates="trend")
    submissions = relationship("TrendSubmission", back_populates="trend")
    history = relationship("TrendHistory", back_populates="trend")
    analytics = relationship("TrendAnalytics", back_populates="trend", uselist=False)

    def __repr__(self):
        return f"<Trend {self.name}>"

class TokenDeployment(Base):
    """Model tracking token deployments to blockchain networks."""
    __tablename__ = 'token_deployments'

    id = Column(Integer, primary_key=True)
    token_id = Column(Integer, ForeignKey('tokens.id'))
    deployer_id = Column(Integer, ForeignKey('users.id'))
    deployment_hash = Column(String(66), unique=True)  # Transaction hash
    deployed_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String(20))  # 'pending', 'success', 'failed'
    network_name = Column(String(50))
    chain_id = Column(Integer)
    gas_used = Column(Integer)
    gas_price = Column(Float)
    contract_address = Column(String(42))
    block_number = Column(Integer)
    constructor_args = Column(JSON)
    error_message = Column(Text)

    # Relationships
    token = relationship("Token", back_populates="deployments")
    deployer = relationship("User", back_populates="deployments")

    def __repr__(self):
        return f"<TokenDeployment {self.token.symbol} on {self.network_name}>"

class TokenTransaction(Base):
    """Model representing token transactions."""
    __tablename__ = 'token_transactions'

    id = Column(Integer, primary_key=True)
    token_id = Column(Integer, ForeignKey('tokens.id'))
    user_id = Column(Integer, ForeignKey('users.id'))
    transaction_hash = Column(String(66), unique=True)
    transaction_type = Column(Enum(TransactionType))
    amount = Column(Float)
    from_address = Column(String(42))
    to_address = Column(String(42))
    timestamp = Column(DateTime, default=datetime.utcnow)
    block_number = Column(Integer)
    gas_used = Column(Integer)
    gas_price = Column(Float)
    status = Column(String(20))  # 'pending', 'success', 'failed'
    network_name = Column(String(50))
    chain_id = Column(Integer)
    note = Column(Text)
    metadata = Column(JSON)  # Additional transaction data

    # Relationships
    token = relationship("Token", back_populates="transactions")
    user = relationship("User", back_populates="transactions")

    def __repr__(self):
        return f"<TokenTransaction {self.transaction_type.value} {self.amount} {self.token.symbol}>"

class TrendSubmission(Base):
    """Model representing user-submitted trends."""
    __tablename__ = 'trend_submissions'

    id = Column(Integer, primary_key=True)
    submitter_id = Column(Integer, ForeignKey('users.id'))
    trend_id = Column(Integer, ForeignKey('trends.id'))
    source = Column(Enum(TrendSource))
    source_url = Column(String(255))
    submitted_at = Column(DateTime, default=datetime.utcnow)
    notes = Column(Text)
    approved = Column(Boolean, default=False)
    approved_at = Column(DateTime)
    approved_by_id = Column(Integer, ForeignKey('users.id'))

    # Relationships
    submitter = relationship("User", back_populates="trend_submissions", foreign_keys=[submitter_id])
    approved_by = relationship("User", foreign_keys=[approved_by_id])
    trend = relationship("Trend", back_populates="submissions")

    def __repr__(self):
        return f"<TrendSubmission {self.trend.name} by {self.submitter.username}>"

class TrendHistory(Base):
    """Model tracking historical trend data."""
    __tablename__ = 'trend_history'

    id = Column(Integer, primary_key=True)
    trend_id = Column(Integer, ForeignKey('trends.id'))
    timestamp = Column(DateTime, default=datetime.utcnow)
    score = Column(Float)
    volume = Column(Integer)
    sentiment = Column(Float)
    sources_data = Column(JSON)  # Detailed data from each source

    # Relationships
    trend = relationship("Trend", back_populates="history")

    def __repr__(self):
        return f"<TrendHistory {self.trend.name} at {self.timestamp}>"

class TrendAnalytics(Base):
    """Model for trend analytics data."""
    __tablename__ = 'trend_analytics'

    id = Column(Integer, primary_key=True)
    trend_id = Column(Integer, ForeignKey('trends.id'), unique=True)
    total_mentions = Column(Integer, default=0)
    peak_volume = Column(Integer)
    peak_time = Column(DateTime)
    average_sentiment = Column(Float)
    longevity_score = Column(Float)  # Predicted trend longevity
    virality_score = Column(Float)  # Measure of rapid spread
    monetization_potential = Column(Float)  # Potential for token value
    audience_demographics = Column(JSON)  # Demographics data
    related_trends = Column(JSON)  # IDs of related trends
    prediction_accuracy = Column(Float)  # How accurate previous predictions were

    # Relationships
    trend = relationship("Trend", back_populates="analytics")

    def __repr__(self):
        return f"<TrendAnalytics for {self.trend.name}>"

class TokenAnalytics(Base):
    """Model for token analytics data."""
    __tablename__ = 'token_analytics'

    id = Column(Integer, primary_key=True)
    token_id = Column(Integer, ForeignKey('tokens.id'), unique=True)
    holders_count = Column(Integer, default=0)
    total_transactions = Column(Integer, default=0)
    average_transaction_value = Column(Float)
    liquidity_ratio = Column(Float)  # Liquidity as proportion of market cap
    price_volatility = Column(Float)  # Measure of price movement
    burn_rate_actual = Column(Float)  # Actual burn rate observed
    transaction_velocity = Column(Float)  # Transactions per time unit
    holder_distribution = Column(JSON)  # Distribution across wallet sizes
    trading_volume_24h = Column(Float)
    price_change_24h = Column(Float)  # As percentage
    trend_correlation = Column(Float)  # Correlation with trend popularity

    # Relationships
    token = relationship("Token", back_populates="analytics")

    def __repr__(self):
        return f"<TokenAnalytics for {self.token.symbol}>"

class TokenPrice(Base):
    """Model for historical token price data."""
    __tablename__ = 'token_prices'

    id = Column(Integer, primary_key=True)
    token_id = Column(Integer, ForeignKey('tokens.id'))
    timestamp = Column(DateTime, default=datetime.utcnow)
    price = Column(Float)
    volume = Column(Float)
    liquidity = Column(Float)
    market_cap = Column(Float)
    source = Column(String(50))  # Where price data came from

    # Relationships
    token = relationship("Token", back_populates="price_history")

    def __repr__(self):
        return f"<TokenPrice {self.token.symbol} ${self.price} at {self.timestamp}>"

class LiquidityPool(Base):
    """Model representing liquidity pools for tokens."""
    __tablename__ = 'liquidity_pools'

    id = Column(Integer, primary_key=True)
    token_id = Column(Integer, ForeignKey('tokens.id'))
    platform = Column(String(50))  # E.g., "Uniswap", "QuickSwap"
    pool_address = Column(String(42))
    pair_token = Column(String(42))  # Address of paired token (often WETH/WMATIC)
    created_at = Column(DateTime, default=datetime.utcnow)
    liquidity_token_address = Column(String(42))  # LP token address
    token_reserves = Column(Float)
    pair_token_reserves = Column(Float)
    total_liquidity_value = Column(Float)  # In USD
    apr = Column(Float)  # Annual percentage rate
    total_fees_generated = Column(Float)
    network_name = Column(String(50))
    chain_id = Column(Integer)

    # Relationships
    token = relationship("Token", back_populates="liquidity_pools")

    def __repr__(self):
        return f"<LiquidityPool {self.token.symbol}-{self.pair_token} on {self.platform}>"

class Notification(Base):
    """Model for user notifications."""
    __tablename__ = 'notifications'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    title = Column(String(100))
    message = Column(Text)
    notification_type = Column(String(50))  # 'token_deployed', 'trend_alert', etc.
    created_at = Column(DateTime, default=datetime.utcnow)
    read = Column(Boolean, default=False)
    read_at = Column(DateTime)
    link = Column(String(255))  # Link to related resource
    related_id = Column(Integer)  

"""
Database models for the ViralCoin application.
Defines SQLAlchemy models for storing tokens, trends, and related data.
"""
import datetime
from typing import List, Optional
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, Enum, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class User(Base):
    """User model for storing user account information."""
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String(64), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    password_hash = Column(String(128))
    wallet_address = Column(String(42), unique=True, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    api_key = Column(String(64), unique=True, nullable=True)

    # Relationships
    tokens = relationship("Token", back_populates="creator")
    trend_watchlists = relationship("TrendWatchlist", back_populates="user")
    
    def __repr__(self):
        return f"<User {self.username}>"


class Trend(Base):
    """Trend model for storing trend analysis data."""
    __tablename__ = 'trends'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(32), nullable=False)
    source = Column(String(32), nullable=False)  # twitter, reddit, news, etc.
    score = Column(Float, nullable=False)  # Trend score from 0 to 1
    momentum = Column(Float, nullable=True)  # Rate of change in trend popularity
    sentiment = Column(Float, nullable=True)  # Sentiment analysis score
    keywords = Column(JSON, nullable=True)  # List of related keywords
    detected_at = Column(DateTime, default=datetime.datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    tokens = relationship("Token", back_populates="trend")
    watchlists = relationship("TrendWatchlist", back_populates="trend")
    analytics = relationship("TrendAnalytics", back_populates="trend")
    
    def __repr__(self):
        return f"<Trend {self.name} ({self.score})>"


class TrendAnalytics(Base):
    """Model for storing detailed trend analytics data."""
    __tablename__ = 'trend_analytics'

    id = Column(Integer, primary_key=True)
    trend_id = Column(Integer, ForeignKey('trends.id'), nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    data_point_type = Column(String(32), nullable=False)  # mentions, engagement, etc.
    value = Column(Float, nullable=False)
    source = Column(String(32), nullable=False)  # twitter, reddit, etc.
    
    # Relationships
    trend = relationship("Trend", back_populates="analytics")
    
    def __repr__(self):
        return f"<TrendAnalytics {self.trend_id} {self.data_point_type}>"


class TrendWatchlist(Base):
    """Model for users' trend watchlists."""
    __tablename__ = 'trend_watchlists'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    trend_id = Column(Integer, ForeignKey('trends.id'), nullable=False)
    added_at = Column(DateTime, default=datetime.datetime.utcnow)
    notify = Column(Boolean, default=False)
    notes = Column(Text, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="trend_watchlists")
    trend = relationship("Trend", back_populates="watchlists")
    
    def __repr__(self):
        return f"<TrendWatchlist User:{self.user_id} Trend:{self.trend_id}>"


class Token(Base):
    """Token model for storing token information."""
    __tablename__ = 'tokens'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    symbol = Column(String(20), nullable=False)
    description = Column(Text, nullable=True)
    creator_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    trend_id = Column(Integer, ForeignKey('trends.id'), nullable=True)
    initial_supply = Column(Float, nullable=False)
    max_supply = Column(Float, nullable=True)
    decimals = Column(Integer, default=18)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Token parameters
    burn_rate = Column(Float, default=0)  # Percentage burn on transactions
    tax_rate = Column(Float, default=0)   # Percentage tax on transactions
    is_mintable = Column(Boolean, default=False)
    
    # Tokenomics configuration
    liquidity_allocation = Column(Float, default=0.5)  # Portion allocated to liquidity pool
    marketing_allocation = Column(Float, default=0.1)  # Portion allocated to marketing
    team_allocation = Column(Float, default=0.1)       # Portion allocated to team
    
    # Token status
    is_generated = Column(Boolean, default=False)
    is_deployed = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    creator = relationship("User", back_populates="tokens")
    trend = relationship("Trend", back_populates="tokens")
    deployments = relationship("TokenDeployment", back_populates="token")
    transactions = relationship("TokenTransaction", back_populates="token")
    
    def __repr__(self):
        return f"<Token {self.symbol} ({self.name})>"


class TokenDeployment(Base):
    """Model for tracking token deployments to blockchains."""
    __tablename__ = 'token_deployments'

    id = Column(Integer, primary_key=True)
    token_id = Column(Integer, ForeignKey('tokens.id'), nullable=False)
    blockchain = Column(String(32), nullable=False)  # ethereum, polygon, etc.
    network = Column(String(32), nullable=False)     # mainnet, testnet, mumbai, etc.
    contract_address = Column(String(42), nullable=False)
    deployer_address = Column(String(42), nullable=False)
    deployed_at = Column(DateTime, default=datetime.datetime.utcnow)
    transaction_hash = Column(String(66), nullable=False)
    gas_used = Column(Integer, nullable=True)
    gas_price = Column(Float, nullable=True)
    status = Column(String(20), default="pending")  # pending, confirmed, failed
    
    # Contract verification
    is_verified = Column(Boolean, default=False)
    verification_url = Column(String(255), nullable=True)
    
    # Relationships
    token = relationship("Token", back_populates="deployments")
    
    def __repr__(self):
        return f"<TokenDeployment {self.token_id} on {self.blockchain}:{self.network}>"


class TokenTransaction(Base):
    """Model for tracking token transactions."""
    __tablename__ = 'token_transactions'

    id = Column(Integer, primary_key=True)
    token_id = Column(Integer, ForeignKey('tokens.id'), nullable=False)
    transaction_type = Column(String(32), nullable=False)  # transfer, mint, burn, etc.
    from_address = Column(String(42), nullable=False)
    to_address = Column(String(42), nullable=False)
    amount = Column(Float, nullable=False)
    transaction_hash = Column(String(66), nullable=False)
    blockchain = Column(String(32), nullable=False)
    network = Column(String(32), nullable=False)
    block_number = Column(Integer, nullable=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    gas_used = Column(Integer, nullable=True)
    gas_price = Column(Float, nullable=True)
    
    # Relationships
    token = relationship("Token", back_populates="transactions")
    
    def __repr__(self):
        return f"<TokenTransaction {self.transaction_type} {self.amount} {self.token_id}>"


class LiquidityPool(Base):
    """Model for tracking liquidity pools for tokens."""
    __tablename__ = 'liquidity_pools'

    id = Column(Integer, primary_key=True)
    token_id = Column(Integer, ForeignKey('tokens.id'), nullable=False)
    dex = Column(String(32), nullable=False)  # quickswap, uniswap, etc.
    blockchain = Column(String(32), nullable=False)
    network = Column(String(32), nullable=False)
    pool_address = Column(String(42), nullable=False)
    pair_token = Column(String(42), nullable=False)  # address of pair token (USDC, ETH, etc.)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    initial_liquidity = Column(Float, nullable=False)
    current_liquidity = Column(Float, nullable=True)
    last_updated = Column(DateTime, nullable=True)
    
    token = relationship("Token")
    
    def __repr__(self):
        return f"<LiquidityPool {self.token_id} on {self.dex}>"


class MarketingCampaign(Base):
    """Model for tracking marketing campaigns for tokens."""
    __tablename__ = 'marketing_campaigns'

    id = Column(Integer, primary_key=True)
    token_id = Column(Integer, ForeignKey('tokens.id'), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    budget = Column(Float, nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=True)
    status = Column(String(20), default="planned")  # planned, active, completed
    platform = Column(String(32), nullable=False)  # twitter, reddit, etc.
    target_audience = Column(JSON, nullable=True)
    performance_metrics = Column(JSON, nullable=True)
    
    token = relationship("Token")
    
    def __repr__(self):
        return f"<MarketingCampaign {self.name} for {self.token_id}>"

