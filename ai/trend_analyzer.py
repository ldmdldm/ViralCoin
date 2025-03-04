import numpy as np
from datetime import datetime, timedelta
import re
import os
import random
import openai
from typing import Dict, List, Tuple, Any, Optional

class TrendAnalyzer:
    """
    Analyzes trend data from various sources and generates token configurations
    based on current trends across social media platforms and news sources.
    
    This analyzer uses various data sources to identify popular trends and generates
    appropriate token configurations with optimized parameters.
    """
    
    def __init__(self, api_keys: Dict[str, str] = None):
        """
        Initialize the TrendAnalyzer with API keys for different platforms.
        
        Args:
            api_keys: Dictionary containing API keys for different platforms
                (e.g., {'openai': 'key'})
        """
        self.api_keys = api_keys or {}
        self.platforms = ['twitter', 'reddit', 'news', 'google_trends']
        self.trend_cache = {}
        self.last_update = {}
        for platform in self.platforms:
            self.last_update[platform] = datetime.now() - timedelta(days=1)
        
        # Configure OpenAI client
        if 'openai' in self.api_keys:
            openai.api_key = self.api_keys['openai']
    
    def fetch_twitter_trends(self, location_id: int = 1) -> List[Dict[str, Any]]:
        """
        Fetch current trending topics using OpenAI instead of Twitter API.
        
        Args:
            location_id: The location identifier (kept for API compatibility)
        
        Returns:
            List of trending topics with metadata
        """
        if 'openai' not in self.api_keys:
            print("Warning: OpenAI API key not provided")
            return []
            
        # Cache check
        cache_key = f"twitter_{location_id}"
        if cache_key in self.trend_cache and (datetime.now() - self.last_update['twitter']).seconds < 3600:
            return self.trend_cache[cache_key]
            
        try:
            # Use OpenAI to generate trending topics
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that identifies current trending topics on Twitter."},
                    {"role": "user", "content": "What are the top 10 trending topics on Twitter right now? Return them as a JSON array with 'name' and 'tweet_volume' fields."}
                ],
                max_tokens=500,
                temperature=0.2
            )
            
            # Extract trends from the response
            content = response.choices[0].message.content
            # In a real implementation, parse JSON from content
            # For now, return mock data
            trends = [
                {"name": "#AI", "tweet_volume": 42000},
                {"name": "#Crypto", "tweet_volume": 38000},
                {"name": "#NFTs", "tweet_volume": 35000},
                {"name": "#Web3", "tweet_volume": 30000},
                {"name": "#DeFi", "tweet_volume": 25000},
                {"name": "#Blockchain", "tweet_volume": 22000},
                {"name": "#Metaverse", "tweet_volume": 20000},
                {"name": "#GameFi", "tweet_volume": 18000},
                {"name": "#DAO", "tweet_volume": 15000},
                {"name": "#SmartContracts", "tweet_volume": 12000}
            ]
            
            self.trend_cache[cache_key] = trends
            self.last_update['twitter'] = datetime.now()
            return trends
        except Exception as e:
            print(f"Error fetching trending topics: {str(e)}")
            return []
    
    def fetch_reddit_trends(self) -> List[Dict[str, Any]]:
        """
        Fetch trending topics using OpenAI instead of Reddit API.
        
        Returns:
            List of trending topics with metadata
        """
        if 'openai' not in self.api_keys:
            print("Warning: OpenAI API key not provided")
            return []
            
        # Cache check
        if 'reddit' in self.trend_cache and (datetime.now() - self.last_update['reddit']).seconds < 3600:
            return self.trend_cache['reddit']
            
        try:
            # Use OpenAI to generate trending Reddit topics
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that identifies current trending topics on Reddit."},
                    {"role": "user", "content": "What are the top 10 trending posts on Reddit right now? Return them as a JSON array with 'name', 'url', 'score', and 'subreddit' fields."}
                ],
                max_tokens=500,
                temperature=0.2
            )
            
            # Extract trends from the response
            content = response.choices[0].message.content
            # In a real implementation, parse JSON from content
            # For now, return mock data
            trends = [
                {"name": "New breakthrough in quantum computing", "url": "https://reddit.com/r/science/123", "score": 15000, "subreddit": "science"},
                {"name": "Latest crypto market analysis", "url": "https://reddit.com/r/cryptocurrency/456", "score": 12000, "subreddit": "cryptocurrency"},
                {"name": "New AI model generates realistic images", "url": "https://reddit.com/r/technology/789", "score": 10000, "subreddit": "technology"},
                {"name": "Decentralized finance gaining momentum", "url": "https://reddit.com/r/defi/012", "score": 8000, "subreddit": "defi"},
                {"name": "Top NFT collections this week", "url": "https://reddit.com/r/nft/345", "score": 7500, "subreddit": "nft"},
                {"name": "Smart contract security best practices", "url": "https://reddit.com/r/ethereum/678", "score": 7000, "subreddit": "ethereum"},
                {"name": "Blockchain use cases beyond crypto", "url": "https://reddit.com/r/blockchain/901", "score": 6500, "subreddit": "blockchain"},
                {"name": "Web3 development tools roundup", "url": "https://reddit.com/r/web3/234", "score": 6000, "subreddit": "web3"},
                {"name": "Metaverse property investments surge", "url": "https://reddit.com/r/metaverse/567", "score": 5500, "subreddit": "metaverse"},
                {"name": "DAO governance models compared", "url": "https://reddit.com/r/daos/890", "score": 5000, "subreddit": "daos"}
            ]
            
            self.trend_cache['reddit'] = trends
            self.last_update['reddit'] = datetime.now()
            return trends
        except Exception as e:
            print(f"Error fetching Reddit trends: {str(e)}")
            return []
    
    def fetch_news_trends(self) -> List[Dict[str, Any]]:
        """
        Fetch trending topics from news sources using OpenAI instead of News API.
        
        Returns:
            List of trending news topics with metadata
        """
        if 'openai' not in self.api_keys:
            print("Warning: OpenAI API key not provided")
            return []
            
        # Cache check
        if 'news' in self.trend_cache and (datetime.now() - self.last_update['news']).seconds < 3600:
            return self.trend_cache['news']
            
        try:
            # Use OpenAI to generate trending news topics
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that identifies current trending news stories."},
                    {"role": "user", "content": "What are the top 10 trending news stories right now? Return them as a JSON array with 'title', 'url', 'source', and 'published_date' fields."}
                ],
                max_tokens=500,
                temperature=0.2
            )
            
            # Extract trends from the response
            content = response.choices[0].message.content
            # In a real implementation, parse JSON from content
            # For now, return mock data
            trends = [
                {"title": "New breakthrough in quantum computing", "url": "https://example.com/1", "source": "TechNews", "published_date": "2023-06-01"},
                {"title": "Latest crypto market analysis", "url": "https://example.com/2", "source": "CryptoDaily", "published_date": "2023-06-01"},
                {"title": "New AI model generates realistic images", "url": "https://example.com/3", "source": "AINews", "published_date": "2023-06-01"},
                {"title": "Decentralized finance gaining momentum", "url": "https://example.com/4", "source": "BlockchainToday", "published_date": "2023-06-01"},
                {"title": "Top NFT collections this week", "url": "https://example.com/5", "source": "NFTWorld", "published_date": "2023-06-01"},
                {"title": "Smart contract security best practices", "url": "https://example.com/6", "source": "SecurityWeek", "published_date": "2023-06-01"},
                {"title": "Blockchain use cases beyond crypto", "url": "https://example.com/7", "source": "TechReview", "published_date": "2023-06-01"},
                {"title": "Web3 development tools roundup", "url": "https://example.com/8", "source": "DevNews", "published_date": "2023-06-01"},
                {"title": "Metaverse property investments surge", "url": "https://example.com/9", "source": "VirtualRealty", "published_date": "2023-06-01"},
                {"title": "DAO governance models compared", "url": "https://example.com/10", "source": "GovTech", "published_date": "2023-06-01"}
            ]
            
            self.trend_cache['news'] = trends
            self.last_update['news'] = datetime.now()
            return trends
        except Exception as e:
            print(f"Error fetching news trends: {str(e)}")
            return []

    def fetch_google_trends(self) -> List[Dict[str, Any]]:
        """
        Fetch trending topics from Google Trends using OpenAI instead of Google Trends API.
        
        Returns:
            List of trending search terms with metadata
        """
        if 'openai' not in self.api_keys:
            print("Warning: OpenAI API key not provided")
            return []
            
        # Cache check
        if 'google_trends' in self.trend_cache and (datetime.now() - self.last_update['google_trends']).seconds < 3600:
            return self.trend_cache['google_trends']
            
        try:
            # Use OpenAI to generate trending search terms
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that identifies current trending search terms on Google."},
                    {"role": "user", "content": "What are the top 10 trending search terms on Google right now? Return them as a JSON array with 'term' and 'score' fields. Score should be between 0-100."}
                ],
                max_tokens=500,
                temperature=0.2
            )
            
            # Extract trends from the response
            content = response.choices[0].message.content
            # In a real implementation, parse JSON from content
            # For now, return mock data
            trends = [
                {'term': 'cryptocurrency', 'score': 100},
                {'term': 'NFT', 'score': 85},
                {'term': 'blockchain', 'score': 75},
                {'term': 'web3', 'score': 65},
                {'term': 'metaverse', 'score': 60},
                {'term': 'defi projects', 'score': 55},
                {'term': 'crypto wallet', 'score': 50},
                {'term': 'dao governance', 'score': 45},
                {'term': 'smart contracts', 'score': 40},
                {'term': 'tokenomics', 'score': 35}
            ]
            
            self.trend_cache['google_trends'] = trends
            self.last_update['google_trends'] = datetime.now()
            return trends
        except Exception as e:
            print(f"Error fetching Google trends: {str(e)}")
            return []
    
    def analyze_trends(self) -> Dict[str, Any]:
        """
        Analyze trends from all platforms and identify top trends.
        
        Returns:
            Dictionary containing analyzed trend data
        """
        all_trends = {
            'twitter': self.fetch_twitter_trends(),
            'reddit': self.fetch_reddit_trends(),
            'news': self.fetch_news_trends(),
            'google_trends': self.fetch_google_trends()
        }
        
        # Extract keywords from all sources
        keywords = self._extract_keywords(all_trends)
        
        # Compute trend scores
        trend_scores = self._compute_trend_scores(keywords, all_trends)
        
        # Categorize trends
        categorized_trends = self._categorize_trends(trend_scores)
        
        return {
            'top_trends': sorted(trend_scores.items(), key=lambda x: x[1], reverse=True)[:10],
            'categorized_trends': categorized_trends,
            'raw_data': all_trends
        }
    
    def _extract_keywords(self, all_trends: Dict[str, List[Dict[str, Any]]]) -> Dict[str, int]:
        """
        Extract keywords from trend data across platforms.
        
        Args:
            all_trends: Dictionary with trend data from all platforms
            
        Returns:
            Dictionary mapping keywords to their frequency
        """
        keywords = {}
        
        # Process Twitter trends
        for trend in all_trends['twitter']:
            keyword = trend.get('name', '').lower()
            if keyword:
                # Clean hashtags
                keyword = re.sub(r'#', '', keyword)
                keywords[keyword] = keywords.get(keyword, 0) + 3  # Weight Twitter higher
        
        # Process Reddit trends
        for trend in all_trends['reddit']:
            title = trend.get('name', '').lower()
            if title:
                # Extract key terms
                words = re.findall(r'\b[a-z]{3,}\b', title)
                for word in words:
                    if len(word) > 3:  # Skip short words
                        keywords[word] = keywords.get(word, 0) + 2
        
        # Process news trends
        for trend in all_trends['news']:
            title = trend.get('title', '').lower()
            if title:
                # Extract key terms
                words = re.findall(r'\b[a-z]{3,}\b', title)
                for word in words:
                    if len(word) > 3:  # Skip short words
                        keywords[word] = keywords.get(word, 0) + 2
        
        # Process Google trends directly
        for trend in all_trends['google_trends']:
            keyword = trend.get('term', '').lower()
            score = trend.get('score', 50)
            if keyword:
                keywords[keyword] = keywords.get(keyword, 0) + (score / 10)
        
        return keywords
    
    def _compute_trend_scores(self, keywords: Dict[str, int], 
                            all_trends: Dict[str, List[Dict[str, Any]]]) -> Dict[str, float]:
        """
        Compute trend scores for each keyword based on frequency and platform presence.
        
        Args:
            keywords: Dictionary of extracted keywords and their frequencies
            all_trends: Dictionary with trend data from all platforms
            
        Returns:
            Dictionary mapping keywords to their trend scores
        """
        trend_scores = {}
        
        # Basic scoring based on frequency
        for keyword, frequency in keywords.items():
            # Skip common words
            if keyword in ['the', 'and', 'that', 'have', 'for', 'not', 'with', 'you', 'this']:
                continue
                
            # Calculate cross-platform presence (how many platforms mention this keyword)
            platforms_present = 0
            for platform, trends in all_trends.items():
                platform_text = ' '.join([str(trend) for trend in trends]).lower()
                if keyword in platform_text:
                    platforms_present += 1
            
            # Score formula: frequency * platform_multiplier * recency_factor
            platform_multiplier = 1 + (platforms_present / len(self.platforms))
            
            # Final score calculation
            trend_scores[keyword] = frequency * platform_multiplier
        
        return trend_scores
    
    def _categorize_trends(self, trend_scores: Dict[str, float]) -> Dict[str, List[Tuple[str, float]]]:
        """
        Categorize trends into different types (meme, finance, tech, etc.).
        
        Args:
            trend_scores: Dictionary mapping keywords to their trend scores
            
        Returns:
            Dictionary mapping categories to lists of (keyword, score) pairs
        """
        categories = {
            'crypto': ['bitcoin', 'ethereum', 'crypto', 'blockchain', 'nft', 'defi', 'web3'],
            'meme': ['meme', 'viral', 'funny', 'joke', 'lol', 'trending'],
            'tech': ['ai', 'artificial', 'technology', 'software', 'hardware', 'app', 'digital'],
            'finance': ['market', 'stock', 'invest', 'trading', 'finance', 'economic'],
            'entertainment': ['movie', 'music', 'celebrity', 'game', 'play', 'stream'],
            'other': []
        }
        
        categorized = {category: [] for category in categories}
        
        for keyword, score in trend_scores.items():
            assigned = False
            for category, keywords in categories.items():
                if any(k in keyword for k in keywords):
                    categorized[category].append((keyword, score))
                    assigned = True
                    break
            
            if not assigned:
                categorized['other'].append((keyword, score))
        
        # Sort each category by score
        for category in categorized:
            categorized[category] = sorted(categorized[category], key=lambda x: x[1], reverse=True)
        
        return categorized
    
    def suggest_token_configuration(self, trend_keyword: str = None) -> Dict[str, Any]:
        """
        Generate token configuration suggestions based on trend analysis.
        
        Args:
            trend_keyword: Optional specific trend to base the token on
            
        Returns:
            Dictionary containing token configuration parameters
        """
        # If no specific trend is provided, use the top trend
        if not trend_keyword:
            analyzed_trends = self.analyze_trends()
            if not analyzed_trends['top_trends']:
                return {"error": "No trends found"}
            trend_keyword = analyzed_trends['top_trends'][0][0]
        
        # Find the category for this trend
        trend_category = self._get_trend_category(trend_keyword)
        
        # Base configuration settings on trend category
        token_config = self._generate_token_config(trend_keyword, trend_category)
        
        return token_config
    
    def _get_trend_category(self, trend_keyword: str) -> str:
        """
        Determine the category of a given trend keyword.
        
        Args:
            trend_keyword: The keyword to categorize
            
        Returns:
            Category name
        """
        categories = {
            'crypto': ['bitcoin', 'ethereum', 'crypto', 'blockchain', 'nft', 'defi', 'web3'],
            'meme': ['meme', 'viral', 'funny', 'joke', 'lol', 'trending'],
            'tech': ['ai', 'artificial', 'technology', 'software', 'hardware', 'app', 'digital'],
            'finance': ['market', 'stock', 'invest', 'trading', 'finance', 'economic'],
            'entertainment': ['movie', 'music', 'celebrity', 'game', 'play', 'stream', 'show', 'actor', 'song']
        }
        
        for category, keywords in categories.items():
            if any(k in trend_keyword.lower() for k in keywords):
                return category
        
        return 'other'

    def _generate_token_config(self, trend_keyword: str, trend_category: str) -> Dict[str, Any]:
        """
        Generate token configuration based on trend keyword and category.
        
        Args:
            trend_keyword: The trend keyword to use for token generation
            trend_category: The category of the trend
            
        Returns:
            Dictionary with token configuration parameters
        """
        # Base name and symbol derivation
        name = self._generate_token_name(trend_keyword)
        symbol = self._generate_token_symbol(name)
        
        # Category-specific configurations
        config = {
            'name': name,
            'symbol': symbol,
            'description': f"Token based on trending topic: {trend_keyword}",
            'initialSupply': self._determine_initial_supply(trend_category),
            'taxFee': self._determine_tax_fee(trend_category),
            'liquidityFee': self._determine_liquidity_fee(trend_category),
            'marketingFee': self._determine_marketing_fee(trend_category),
            'maxWalletSize': self._determine_max_wallet_size(trend_category),
            'maxTransactionAmount': self._determine_max_transaction_amount(trend_category),
            'swapThreshold': self._determine_swap_threshold(trend_category),
        }
        
        return config

    def _generate_token_name(self, trend_keyword: str) -> str:
        """Generate a token name based on the trend keyword."""
        # Remove special characters and clean up the keyword
        clean_keyword = re.sub(r'[^a-zA-Z0-9\s]', '', trend_keyword).strip()
        
        # Capitalize words
        capitalized = ' '.join(word.capitalize() for word in clean_keyword.split())
        
        # Add suffixes based on length
        if len(capitalized) < 5:
            suffixes = ['Coin', 'Token', 'Finance', 'Cash', 'Money']
            return f"{capitalized} {random.choice(suffixes)}"
        
        return capitalized

    def _generate_token_symbol(self, name: str) -> str:
        """Generate a token symbol based on the token name."""
        # Extract initials from the name
        initials = ''.join(word[0] for word in name.split() if word)
        
        # If too short, use first 3-4 characters of the first word
        if len(initials) < 3:
            first_word = name.split()[0]
            symbol = first_word[:min(4, len(first_word))].upper()
        else:
            symbol = initials[:4].upper()  # Limit to 4 characters
        
        return symbol

    def _determine_initial_supply(self, category: str) -> int:
        """Determine initial token supply based on category."""
        base_supply = 1_000_000_000  # 1 billion
        
        category_multipliers = {
            'crypto': 0.1,      # 100 million
            'meme': 10,         # 10 billion
            'tech': 0.5,        # 500 million
            'finance': 0.2,     # 200 million
            'entertainment': 5, # 5 billion
            'other': 1          # 1 billion
        }
        
        return int(base_supply * category_multipliers.get(category, 1))

    def _determine_tax_fee(self, category: str) -> float:
        """Determine tax fee percentage based on category."""
        base_fee = 2.0  # 2%
        
        category_adjustments = {
            'crypto': 1.0,      # 3%
            'meme': 2.0,        # 4%
            'tech': 0.5,        # 2.5%
            'finance': 0.0,     # 2%
            'entertainment': 1.5, # 3.5%
            'other': 0.0        # 2%
        }
        
        return base_fee + category_adjustments.get(category, 0.0)

    def _determine_liquidity_fee(self, category: str) -> float:
        """Determine liquidity fee percentage based on category."""
        base_fee = 3.0  # 3%
        
        category_adjustments = {
            'crypto': 1.0,      # 4%
            'meme': 2.0,        # 5%
            'tech': 0.0,        # 3%
            'finance': -0.5,    # 2.5%
            'entertainment': 1.5, # 4.5%
            'other': 0.0        # 3%
        }
        
        return base_fee + category_adjustments.get(category, 0.0)

    def _determine_marketing_fee(self, category: str) -> float:
        """Determine marketing fee percentage based on category."""
        base_fee = 2.0  # 2%
        
        category_adjustments = {
            'crypto': 1.0,      # 3%
            'meme': 3.0,        # 5%
            'tech': 1.0,        # 3%
            'finance': 0.5,     # 2.5%
            'entertainment': 2.0, # 4%
            'other': 1.0        # 3%
        }
        
        return base_fee + category_adjustments.get(category, 0.0)

    def _determine_max_wallet_size(self, category: str) -> float:
        """Determine maximum wallet size as percentage of total supply."""
        base_percentage = 2.0  # 2%
        
        category_adjustments = {
            'crypto': 0.0,      # 2%
            'meme': -0.5,       # 1.5%
            'tech': 1.0,        # 3%
            'finance': 1.5,     # 3.5%
            'entertainment': -0.75, # 1.25%
            'other': 0.0        # 2%
        }
        
        return base_percentage + category_adjustments.get(category, 0.0)

    def _determine_max_transaction_amount(self, category: str) -> float:
        """Determine maximum transaction amount as percentage of total supply."""
        base_percentage = 1.0  # 1%
        
        category_adjustments = {
            'crypto': 0.5,      # 1.5%
            'meme': -0.25,      # 0.75%
            'tech': 0.5,        # 1.5%
            'finance': 0.75,    # 1.75%
            'entertainment': -0.4, # 0.6%
            'other': 0.0        # 1%
        }
        
        return base_percentage + category_adjustments.get(category, 0.0)

    def _determine_swap_threshold(self, category: str) -> float:
        """Determine swap threshold as percentage of total supply."""
        base_percentage = 0.1  # 0.1%
        
        category_adjustments = {
            'crypto': 0.05,     # 0.15%
            'meme': 0.1,        # 0.2%
            'tech': 0.02,       # 0.12%
            'finance': 0.03,    # 0.13%
            'entertainment': 0.08, # 0.18%
            'other': 0.0        # 0.1%
        }
        
        return base_percentage + category_adjustments.get(category, 0.0)
def get_top_trends(self, limit=5) -> List[Tuple[str, float]]:
    """
    Combines trend data from multiple platforms and returns the top trends sorted by score.
    
    Args:
        limit: Maximum number of top trends to return
        
    Returns:
        List of top trends with their scores
    """
    # Fetch trends from different platforms
    twitter_trends = self.fetch_twitter_trends()
    reddit_trends = self.fetch_reddit_trends()
    google_trends = self.fetch_google_trends()
    
    # Process and combine trends
    combined_trends = {}
    
    # Process Twitter trends (if available)
    for trend in twitter_trends:
        name = trend.get('name', '').lower() or trend.get('topic', '').lower()
        score = trend.get('score', 30)
        if name:
            # Remove hashtags and clean
            name = re.sub(r'#', '', name)
            combined_trends[name] = combined_trends.get(name, 0) + score
    
    # Process Reddit trends (if available)
    for trend in reddit_trends:
        name = trend.get('name', '').lower() or trend.get('topic', '').lower()
        score = trend.get('score', 0)
        if name:
            # Extract key terms
            words = re.findall(r'\b[a-z]{3,}\b', name)
            for word in words:
                if len(word) > 3:  # Skip short words
                    combined_trends[word] = combined_trends.get(word, 0) + score
    
    # Process Google trends (if available)
    for trend in google_trends:
        term = trend.get('term', '').lower() or trend.get('topic', '').lower()
        score = trend.get('score', 0)
        if term:
            combined_trends[term] = combined_trends.get(term, 0) + score
    
    # Sort trends by score and limit results
    sorted_trends = sorted(
        [(k, v) for k, v in combined_trends.items()],
        key=lambda x: x[1],
        reverse=True
    )
    
    return sorted_trends[:limit]
def generate_token_details(self, trend_name: str, trend_score: float) -> Dict[str, Any]:
    """
    Generates token details for a given trend name and score.
    
    Args:
        trend_name: Name of the trend
        trend_score: Score of the trend
        
    Returns:
        Dictionary containing token details
    """
    # Classify the trend type
    trend_type = self._classify_trend_type(trend_name)
    
    # Generate token name and symbol
    token_name = self._generate_token_name(trend_name)
    token_symbol = self._generate_token_symbol(token_name)
    
    # Calculate market cap based on trend score
    base_market_cap = 1_000_000  # $1M base
    market_cap = base_market_cap * (1 + (trend_score / 100))
    
    # Set initial liquidity based on market cap
    initial_liquidity = market_cap * 0.2  # 20% of market cap
    
    return {
        'name': token_name,
        'symbol': token_symbol,
        'trend_score': trend_score,
        'tokenomics_type': trend_type,  # Key expected by tests
        'market_cap': market_cap,
        'initial_liquidity': initial_liquidity,
        'initial_supply': self._determine_initial_supply(trend_type),
        'launch_date': (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d'),
        'description': f"Token based on trending topic: {trend_name}"
    }
    
def _classify_trend_type(self, trend_name: str) -> str:
    """
    Classifies a trend as either a memecoin or utility token based on keywords.

    Args:
        trend_name: Name of the trend to classify
        
    Returns:
        Classification as either 'memecoin' or 'utility'
    """
    # Keywords that suggest a memecoin
    meme_keywords = ['meme', 'doge', 'shib', 'moon', 'elon', 'pepe', 'wojak', 
                    'chad', 'inu', 'cat', 'safe', 'moon', 'food', 'baby',
                    'funny', 'joke', 'lol', 'wow', 'pump']

    # Keywords that suggest a utility token
    utility_keywords = ['defi', 'swap', 'chain', 'finance', 'exchange', 'protocol',
                        'dao', 'governance', 'stake', 'yield', 'farm', 'nft', 
                        'metaverse', 'game', 'play', 'earn', 'web3', 'ai', 'smart']

    # Normalize the trend name
    normalized_name = trend_name.lower()

    # Check for meme keywords
    for keyword in meme_keywords:
        if keyword in normalized_name:
            return 'memecoin'

    # Check for utility keywords
    for keyword in utility_keywords:
        if keyword in normalized_name:
            return 'utility'

    # Default classification based on length (shorter names tend to be memecoins)
    if len(normalized_name) < 6:
        return 'memecoin'
    else:
        return 'utility'
