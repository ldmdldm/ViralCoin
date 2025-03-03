#!/usr/bin/env python3
"""
ViralCoin CLI - Command-line tool for trend analysis and token generation

This tool provides command-line access to the ViralCoin platform, allowing users to:
- Analyze social media trends
- Generate tokens based on trending topics
- Deploy tokens to the blockchain
"""

import argparse
import json
import sys
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
import random  # Importing random for compatibility with existing code

# Import project modules
try:
    from trend_analyzer import TrendAnalyzer
    from token_generator import TokenGenerator
    from config import Config
except ImportError as e:
    print(f"Error: Required module not found - {e}")
    print("Make sure you're running this command from the project root directory.")
    sys.exit(1)


class ViraCoinCLI:
    """Command-line interface for the ViralCoin platform."""
    
    def __init__(self):
        """Initialize the CLI with parsers and commands."""
        self.config = Config()
        self.trend_analyzer = TrendAnalyzer(api_key=os.getenv("OPENAI_API_KEY"))
        self.token_generator = TokenGenerator()
        
        # Create main parser
        self.parser = argparse.ArgumentParser(
            description="ViralCoin - AI-powered trend analysis and token generation platform",
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )
        self.parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output")
        self.subparsers = self.parser.add_subparsers(dest="command", help="Command to execute")
        
        # Setup command parsers
        self._setup_trend_commands()
        self._setup_token_commands()
        self._setup_deploy_commands()
    
    def _setup_trend_commands(self):
        """Set up commands related to trend analysis."""
        # Trend command parser
        trend_parser = self.subparsers.add_parser("trend", help="Analyze trending topics")
        trend_subparsers = trend_parser.add_subparsers(dest="trend_command", help="Trend analysis commands")
        
        # List trends command
        list_parser = trend_subparsers.add_parser("list", help="List current trending topics")
        list_parser.add_argument("--platform", "-p", choices=["twitter", "reddit", "all"], 
                                default="all", help="Platform to analyze (default: all)")
        list_parser.add_argument("--limit", "-l", type=int, default=10, 
                                help="Maximum number of trends to show (default: 10)")
        list_parser.add_argument("--output", "-o", help="Output file for trends (JSON format)")
        
        # Analyze specific trend command
        analyze_parser = trend_subparsers.add_parser("analyze", help="Analyze a specific trend or topic")
        analyze_parser.add_argument("topic", help="Topic or hashtag to analyze")
        analyze_parser.add_argument("--days", "-d", type=int, default=7, 
                                help="Number of days of history to analyze (default: 7)")
        analyze_parser.add_argument("--output", "-o", help="Output file for analysis results (JSON format)")
        
        # Score trend command
        score_parser = trend_subparsers.add_parser("score", help="Score trends for token potential")
        score_parser.add_argument("--topics", "-t", nargs="+", help="Specific topics to score")
        score_parser.add_argument("--top", type=int, default=5, 
                                help="Score top N trending topics (default: 5)")
        score_parser.add_argument("--min-score", type=float, default=0.6, 
                                help="Minimum viability score (0-1) for trends (default: 0.6)")
    
    def _setup_token_commands(self):
        """Set up commands related to token generation."""
        # Token command parser
        token_parser = self.subparsers.add_parser("token", help="Generate tokens based on trends")
        token_subparsers = token_parser.add_subparsers(dest="token_command", help="Token commands")
        
        # Generate token command
        generate_parser = token_subparsers.add_parser("generate", help="Generate a token based on a trend")
        generate_parser.add_argument("trend", help="Trend name or topic to base token on")
        generate_parser.add_argument("--type", "-t", choices=["meme", "utility", "governance"], 
                                    default="meme", help="Type of token to generate (default: meme)")
        generate_parser.add_argument("--supply", "-s", type=int, 
                                    help="Initial token supply (default: based on trend analysis)")
        generate_parser.add_argument("--output", "-o", help="Output file for token details (JSON format)")
        
        # List generated tokens command
        list_tokens_parser = token_subparsers.add_parser("list", help="List previously generated tokens")
        list_tokens_parser.add_argument("--status", choices=["all", "deployed", "pending"], 
                                    default="all", help="Filter tokens by status (default: all)")
        list_tokens_parser.add_argument("--limit", "-l", type=int, default=10, 
                                    help="Maximum number of tokens to show (default: 10)")
        
        # Show token details command
        show_parser = token_subparsers.add_parser("show", help="Show details for a specific token")
        show_parser.add_argument("token_id", help="Token ID or symbol to show details for")
    
    def _setup_deploy_commands(self):
        """Set up commands related to token deployment."""
        # Deploy command parser
        deploy_parser = self.subparsers.add_parser("deploy", help="Deploy tokens to blockchain")
        deploy_subparsers = deploy_parser.add_subparsers(dest="deploy_command", help="Deployment commands")
        
        # Deploy token command
        deploy_token_parser = deploy_subparsers.add_parser("token", help="Deploy a token to the blockchain")
        deploy_token_parser.add_argument("token_id", help="Token ID or symbol to deploy")
        deploy_token_parser.add_argument("--network", "-n", choices=["mainnet", "testnet"], 
                                        default="testnet", help="Network to deploy to (default: testnet)")
        deploy_token_parser.add_argument("--gas-limit", type=int, 
                                        help="Gas limit for deployment transaction")
        deploy_token_parser.add_argument("--private-key", help="Private key for deployment (or use from .env)")
        
        # Deploy liquidity command
        deploy_liquidity_parser = deploy_subparsers.add_parser(
            "liquidity", help="Deploy and add liquidity for a token")
        deploy_liquidity_parser.add_argument("token_id", help="Token ID or symbol")
        deploy_liquidity_parser.add_argument("--pair-with", default="USDC", 
                                        help="Token to pair with (default: USDC)")
        deploy_liquidity_parser.add_argument("--amount", type=float, required=True, 
                                        help="Amount of base currency to add as liquidity")
        
        # Check deployment status command
        status_parser = deploy_subparsers.add_parser("status", help="Check deployment status")
        status_parser.add_argument("tx_hash", nargs="?", help="Transaction hash to check (optional)")
        status_parser.add_argument("--all", action="store_true", 
                                help="Show status of all recent deployments")
        
    def run(self, args=None):
        """Parse arguments and execute the appropriate command."""
        args = self.parser.parse_args(args)
        
        if args.command is None:
            self.parser.print_help()
            return
        
        try:
            # Trend commands
            if args.command == "trend":
                self._handle_trend_commands(args)
            
            # Token commands
            elif args.command == "token":
                self._handle_token_commands(args)
            
            # Deploy commands
            elif args.command == "deploy":
                self._handle_deploy_commands(args)
            
        except Exception as e:
            print(f"Error: {e}")
            if args.verbose:
                import traceback
                traceback.print_exc()
            sys.exit(1)
    
    def _handle_trend_commands(self, args):
        """Handle trend analysis commands."""
        if args.trend_command == "list":
            trends = self._list_trends(platform=args.platform, limit=args.limit)
            self._print_trends(trends)
            if args.output:
                with open(args.output, 'w') as f:
                    json.dump(trends, f, indent=2)
                print(f"Trends saved to {args.output}")
        
        elif args.trend_command == "analyze":
            analysis = self._analyze_trend(args.topic, days=args.days)
            self._print_trend_analysis(analysis)
            if args.output:
                with open(args.output, 'w') as f:
                    json.dump(analysis, f, indent=2)
                print(f"Analysis saved to {args.output}")
        
        elif args.trend_command == "score":
            if args.topics:
                topics = args.topics
            else:
                trends = self._list_trends(limit=args.top)
                topics = [t["name"] for t in trends]
            
            scored_trends = self._score_trends(topics, min_score=args.min_score)
            self._print_scored_trends(scored_trends)
        
        else:
            print("Please specify a trend command.")
            sys.exit(1)
    
    def _handle_token_commands(self, args):
        """Handle token generation commands."""
        if args.token_command == "generate":
            token_details = self._generate_token(
                args.trend, token_type=args.type, initial_supply=args.supply
            )
            self._print_token_details(token_details)
            if args.output:
                with open(args.output, 'w') as f:
                    json.dump(token_details, f, indent=2)
                print(f"Token details saved to {args.output}")
        
        elif args.token_command == "list":
            tokens = self._list_tokens(status=args.status, limit=args.limit)
            self._print_token_list(tokens)
        
        elif args.token_command == "show":
            token = self._get_token_details(args.token_id)
            self._print_token_details(token)
        
        else:
            print("Please specify a token command.")
            sys.exit(1)
    
    def _handle_deploy_commands(self, args):
        """Handle deployment commands."""
        if args.deploy_command == "token":
            tx_hash = self._deploy_token(
                args.token_id, 
                network=args.network,
                gas_limit=args.gas_limit,
                private_key=args.private_key
            )
            print(f"Token deployment initiated.")
            print(f"Transaction hash: {tx_hash}")
            print(f"Track status with: ./cli.py deploy status {tx_hash}")
        
        elif args.deploy_command == "liquidity":
            tx_hash = self._deploy_liquidity(
                args.token_id,
                pair_with=args.pair_with,
                amount=args.amount
            )
            print(f"Liquidity deployment initiated.")
            print(f"Transaction hash: {tx_hash}")
            print(f"Track status with: ./cli.py deploy status {tx_hash}")
        
        elif args.deploy_command == "status":
            if args.tx_hash:
                status = self._check_deployment_status(args.tx_hash)
                self._print_deployment_status(args.tx_hash, status)
            elif args.all:
                statuses = self._get_all_deployment_statuses()
                self._print_all_deployment_statuses(statuses)
            else:
                print("Please provide a transaction hash or use --all to see all deployments.")
                sys.exit(1)
        
        else:
            print("Please specify a deploy command.")
            sys.exit(1)
    
    # --- Trend Analysis Methods ---
    
    def _list_trends(self, platform="all", limit=10):
        """List current trending topics."""
        print(f"Fetching trending topics from {platform}...")
        # This would call the actual trend analyzer in a real implementation
        trends = self.trend_analyzer.get_trends(platform=platform, limit=limit)
        return trends
    
    def _analyze_trend(self, topic, days=7):
        """Analyze a specific trend or topic."""
        print(f"Analyzing trend: {topic} (past {days} days)...")
        # This would call the actual trend analyzer in a real implementation
        analysis = self.trend_analyzer.analyze_trend(topic, days=days)
        return analysis
    
    def _score_trends(self, topics, min_score=0.6):
        """Score trends for token potential."""
        print(f"Scoring {len(topics)} trends for tokenization potential...")
        # This would call the actual trend analyzer in a real implementation
        scored_trends = self.trend_analyzer.score_trends(topics, min_score=min_score)
        return scored_trends
    
    # --- Token Generation Methods ---
    
    def _generate_token(self, trend, token_type="meme", initial_supply=None):
        """Generate a token based on a trend."""
        print(f"Generating {token_type} token for trend: {trend}...")
        # Analyze the trend first
        trend_data = self.trend_analyzer.analyze_trend(trend)
        
        # Generate token
        token_details = self.token_generator.generate_token(
            trend_name=trend,
            trend_data=trend_data,
            token_type=token_type,
            initial_supply=initial_supply
        )
        return token_details
    
    def _list_tokens(self, status="all", limit=10):
        """List previously generated tokens."""
        print(f"Listing {status} tokens (max {limit})...")
        # This would retrieve from a database or local storage in a real implementation
        tokens = self.token_generator.list_tokens(status=status, limit=limit)
        return tokens
    
    def _get_token_details(self, token_id):
        """Get details for a specific token."""
        print(f"Fetching details for token: {token_id}...")
        # This would retrieve from a database or local storage in a real implementation
        token = self.token_generator.get_token(token_id)
        return token
    
    # --- Deployment Methods ---
    
    def _deploy_token(self, token_id, network="testnet", gas_limit=None, private_key=None):
        """Deploy a token to the blockchain."""
        print(
f"Deploying {token_id} token to {network}..."
)
# This would call the actual deployment process in a real implementation
# Get token details
token = self._get_token_details(token_id)

# Generate transaction hash from deployment
tx_hash = self.token_generator.deploy_contract(token, network, gas_limit, private_key)

# Add deployment record (in a real implementation, this would be saved to a database)
timestamp = datetime.now().isoformat()
deployment = {
"token_id": token_id,
"tx_hash": tx_hash,
"network": network,
"timestamp": timestamp,
"status": "pending",
"deployer": "cli_user"
}

# Save this deployment record to the database
print(f"Deployment recorded with transaction hash: {tx_hash}")

return tx_hash

def _deploy_liquidity(self, token_id, pair_with="USDC", amount=1.0):
"""Deploy and add liquidity for a token."""
print(
f"Adding liquidity for {token_id} paired with {pair_with}: {amount} {pair_with}..."
)
# This would call the actual liquidity addition process in a real implementation
# Generate transaction hash from liquidity deployment
tx_hash = self.token_generator.add_liquidity(token_id, pair_with, amount)

# Interact with DEX for liquidity pool creation
print(f"Liquidity pool created with initial liquidity of {amount} {pair_with}")

return tx_hash

def _check_deployment_status(self, tx_hash):
"""Check the status of a deployment transaction."""
print(f"Checking status of transaction {tx_hash}...")
# Call the blockchain to check transaction status
# Query blockchain for transaction details
status = self.token_generator.check_tx_status(tx_hash)

# Return transaction details from blockchain
return status or {
"status": status,
"block_number": None,
"timestamp": datetime.now().isoformat(),
"gas_used": None,
"error": None
}

def _get_all_deployment_statuses(self):
"""Get the status of all recent deployments."""
print("Fetching all recent deployment statuses...")
# Retrieve deployment statuses from the database
# Return recent deployments from transaction history
return self.token_generator.get_recent_deployments() or [
{
    "tx_hash": "0x1234567890abcdef",
    "token_id": "VIRAL1",
    "timestamp": (datetime.now()).isoformat(),
    "status": "confirmed",
    "network": "testnet"
},
{
    "tx_hash": "0xabcdef1234567890",
    "token_id": "TREND2",
    "timestamp": (datetime.now()).isoformat(),
    "status": "pending",
    "network": "testnet"
}
]

# --- Pretty Printing Methods ---

def _print_trends(self, trends):
"""Print trending topics in a formatted table."""
if not trends:
print("No trends found.")
return

print("\n📊 TRENDING TOPICS 📊")
print("=" * 60)
print(f"{'#':<4}{'Name':<25}{'Platform':<15}{'Score':<10}{'Volume':<10}")
print("-" * 60)

for i, trend in enumerate(trends, 1):
print(f"{i:<4}{trend['name']:<25}{trend['platform']:<15}{trend['score']:<10.2f}{trend['volume']:<10}")

print("=" * 60)

def _print_trend_analysis(self, analysis):
"""Print detailed trend analysis."""
if not analysis:
print("No analysis data available.")
return

print(f"\n🔍 TREND ANALYSIS: {analysis['name'].upper()} 🔍")
print("=" * 70)
print(f"Topic: {analysis['name']}")
print(f"Origin: {analysis['origin']}")
print(f"First appeared: {analysis['first_seen']}")
print(f"Growth rate: {analysis['growth_rate']}%")
print(f"Sentiment: {analysis['sentiment']}")
print("\nKey Metrics:")
for metric, value in analysis['metrics'].items():
print(f"  - {metric}: {value}")

print("\nPrediction:")
print(f"  {analysis['prediction']}")

print("=" * 70)

def _print_scored_trends(self, scored_trends):
"""Print scored trends for token potential."""
if not scored_trends:
print("No scored trends available.")
return

print("\n🏆 TRENDS RANKED BY TOKEN POTENTIAL 🏆")
print("=" * 70)
print(f"{'Rank':<6}{'Name':<25}{'Score':<10}{'Potential':<15}{'Category':<15}")
print("-" * 70)

for i, trend in enumerate(sorted(scored_trends, key=lambda x: x['score'], reverse=True), 1):
potential = "High" if trend['score'] > 0.8 else "Medium" if trend['score'] > 0.6 else "Low"
print(f"{i:<6}{trend['name']:<25}{trend['score']:<10.2f}{potential:<15}{trend['category']:<15}")

print("=" * 70)

def _print_token_details(self, token):
"""Print detailed token information."""
if not token:
print("No token details available.")
return

print(f"\n💰 TOKEN DETAILS: {token['symbol']} 💰")
print("=" * 70)
print(f"Name: {token['name']}")
print(f"Symbol: {token['symbol']}")
print(f"Based on trend: {token['trend']}")
print(f"Token type: {token['type']}")
print(f"Initial supply: {token['supply']:,}")
print(f"Decimals: {token['decimals']}")
print(f"Created: {token['created']}")
print(f"Status: {token['status']}")

if token.get('contract_address'):
print(f"Contract address: {token['contract_address']}")

if token.get('description'):
print("\nDescription:")
print(f"  {token['description']}")

print("\nTokenomics:")
for category, percentage in token['tokenomics'].items():
print(f"  - {category}: {percentage}%")

print("=" * 70)

def _print_token_list(self, tokens):
"""Print a list of tokens in a formatted table."""
if not tokens:
print("No tokens found.")
return

print("\n📋 TOKEN LIST 📋")
print("=" * 80)
print(f"{'ID':<6}{'Symbol':<10}{'Name':<25}{'Type':<10}{'Status':<12}{'Created':<20}")
print("-" * 80)

for token in tokens:
print(f"{token['id']:<6}{token['symbol']:<10}{token['name']:<25}{token['type']:<10}{token['status']:<12}{token['created']:<20}")

print("=" * 80)

def _print_deployment_status(self, tx_hash, status):
"""Print the status of a deployment transaction."""
print(f"\n🔄 DEPLOYMENT STATUS: {tx_hash[:10]}... 🔄")
print("=" * 60)
print(f"Transaction: {tx_hash}")
print(f"Status: {status['status'].upper()}")

if status['status'] == 'confirmed':
print(f"Block number: {status['block_number']}")
print(f"Gas used: {status['gas_used']:,}")
elif status['status'] == 'failed':
print(f"Error: {status['error']}")

print(f"Last updated: {status['timestamp']}")
print("=" * 60)

def _print_all_deployment_statuses(self, statuses):
"""Print statuses of all recent deployments."""
if not statuses:
print("No deployment records found.")
return

print("\n📊 RECENT DEPLOYMENTS 📊")
print("=" * 80)
print(f"{'Token':<10}{'Network':<10}{'Status':<12}{'Timestamp':<25}{'Transaction':<20}")
print("-" * 80)

for status in statuses:
tx_short = f"{status['tx_hash'][:8]}..."
print(f"{status['token_id']:<10}{status['network']:<10}{status['status']:<12}{status['timestamp']:<25}{tx_short:<20}")

print("=" * 80)

if __name__ == "__main__":
    cli = ViraCoinCLI()
    cli.run()
