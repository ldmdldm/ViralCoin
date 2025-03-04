#!/usr/bin/env python3
"""
ViralCoin API - Main Application Entry Point

This module serves as the main entry point for the ViralCoin application,
providing a Flask API that integrates trend analysis and token generation
functionalities.
"""

import os
import json
import logging
from datetime import datetime
from functools import wraps
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from dotenv import load_dotenv

# Import project modules
from trend_analyzer import TrendAnalyzer
from token_generator import TokenGenerator

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("viral_coin.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Initialize TrendAnalyzer and TokenGenerator
trend_analyzer = TrendAnalyzer()
token_generator = TokenGenerator()

# Store generated tokens in memory (in a production environment, use a database)
generated_tokens = {}


# Authentication decorator (placeholder for real authentication)
def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if not api_key or api_key != os.getenv("VIRALCOIN_API_KEY", "development_key"):
            return jsonify({"error": "Unauthorized access. Valid API key required."}), 401
        return f(*args, **kwargs)
    return decorated_function


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint to verify API is running."""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    })


@app.route('/api/trends', methods=['GET'])
@require_api_key
def get_trends():
    """
    Get current trending topics with their viral potential scores.
    
    Query Parameters:
    - platforms: Comma-separated list of platforms to analyze (default: all)
    - limit: Maximum number of trends to return (default: 10)
    """
    try:
        platforms = request.args.get('platforms', 'all')
        limit = int(request.args.get('limit', 10))
        
        platforms_list = platforms.split(',') if platforms != 'all' else ['twitter', 'reddit', 'tiktok']
        
        # Analyze trends
        trends = trend_analyzer.get_trending_topics(platforms=platforms_list, limit=limit)
        
        return jsonify({
            "status": "success",
            "count": len(trends),
            "data": trends
        })
        
    except Exception as e:
        logger.error(f"Error processing trend request: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@app.route('/api/analyze', methods=['POST'])
@require_api_key
def analyze_trend():
    """
    Analyze a specific trend or topic for tokenization potential.
    
    Expected JSON body:
    {
        "topic": "string",
        "description": "string (optional)"
    }
    """
    try:
        data = request.json
        
        if not data or 'topic' not in data:
            return jsonify({
                "status": "error",
                "message": "Missing required parameter: topic"
            }), 400
        
        topic = data['topic']
        description = data.get('description', '')
        
        # Analyze the specific trend
        analysis = trend_analyzer.analyze_topic(topic, description)
        
        return jsonify({
            "status": "success",
            "data": analysis
        })
        
    except Exception as e:
        logger.error(f"Error analyzing trend: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@app.route('/api/generate-token', methods=['POST'])
@require_api_key
def generate_token():
    """
    Generate token details based on trend analysis.
    
    Expected JSON body:
    {
        "trend_data": {
            "topic": "string",
            "description": "string",
            "score": float (optional)
        },
        "token_type": "memecoin|utility|governance" (optional, default: memecoin)
    }
    """
    try:
        data = request.json
        
        if not data or 'trend_data' not in data:
            return jsonify({
                "status": "error",
                "message": "Missing required parameter: trend_data"
            }), 400
        
        trend_data = data['trend_data']
        token_type = data.get('token_type', 'memecoin')
        
        # Generate token details
        token_details = token_generator.generate_token(
            trend_data['topic'],
            trend_data.get('description', ''),
            token_type=token_type
        )
        
        # Store the generated token
        token_id = f"{token_details['symbol'].lower()}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        generated_tokens[token_id] = {
            "details": token_details,
            "created_at": datetime.now().isoformat(),
            "trend_data": trend_data,
            "status": "generated"
        }
        
        return jsonify({
            "status": "success",
            "token_id": token_id,
            "data": token_details
        })
        
    except Exception as e:
        logger.error(f"Error generating token: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@app.route('/api/deploy-token', methods=['POST'])
@require_api_key
def deploy_token():
    """
    Deploy a generated token to the blockchain.
    
    Expected JSON body:
    {
        "token_id": "string",
        "network": "string (optional, default: testnet)",
        "liquidity": float (optional, default: 0.1)
    }
    """
    try:
        data = request.json
        
        if not data or 'token_id' not in data:
            return jsonify({
                "status": "error",
                "message": "Missing required parameter: token_id"
            }), 400
        
        token_id = data['token_id']
        network = data.get('network', 'testnet')
        liquidity = float(data.get('liquidity', 0.1))
        
        if token_id not in generated_tokens:
            return jsonify({
                "status": "error",
                "message": f"Token ID {token_id} not found"
            }), 404
        
        # In a real implementation, this would connect to blockchain
        # and deploy the token using the token contract template
        
        # For demonstration, we'll just update the status
        generated_tokens[token_id]["status"] = "deployed"
        generated_tokens[token_id]["network"] = network
        generated_tokens[token_id]["contract_address"] = f"0x{os.urandom(20).hex()}"
        generated_tokens[token_id]["transaction_hash"] = f"0x{os.urandom(32).hex()}"
        generated_tokens[token_id]["deployed_at"] = datetime.now().isoformat()
        
        return jsonify({
            "status": "success",
            "message": f"Token {token_id} deployed successfully",
            "data": {
                "token_id": token_id,
                "contract_address": generated_tokens[token_id]["contract_address"],
                "transaction_hash": generated_tokens[token_id]["transaction_hash"],
                "network": network
            }
        })
        
    except Exception as e:
        logger.error(f"Error deploying token: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@app.route('/api/tokens', methods=['GET'])
@require_api_key
def list_tokens():
    """List all generated and deployed tokens."""
    try:
        status_filter = request.args.get('status')
        
        tokens = generated_tokens
        if status_filter:
            tokens = {k: v for k, v in tokens.items() if v.get('status') == status_filter}
        
        return jsonify({
            "status": "success",
            "count": len(tokens),
            "data": tokens
        })
        
    except Exception as e:
        logger.error(f"Error listing tokens: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@app.route('/api/token/<token_id>', methods=['GET'])
@require_api_key
def get_token(token_id):
    """Get details for a specific token."""
    try:
        if token_id not in generated_tokens:
            return jsonify({
                "status": "error",
                "message": f"Token ID {token_id} not found"
            }), 404
        
        return jsonify({
            "status": "success",
            "data": generated_tokens[token_id]
        })
        
    except Exception as e:
        logger.error(f"Error retrieving token details: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@app.errorhandler(404)
def not_found(e):
    """Handle 404 errors."""
    return jsonify({
        "status": "error",
        "message": "The requested resource was not found"
    }), 404


@app.errorhandler(500)
def server_error(e):
    """Handle 500 errors."""
    logger.error(f"Server error: {str(e)}")
    return jsonify({
        "status": "error",
        "message": "Internal server error"
    }), 500


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "False").lower() == "true"
    
    logger.info(f"Starting ViralCoin API on port {port}, debug mode: {debug}")
    app.run(host="0.0.0.0", port=port, debug=debug)

