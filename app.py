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
from sqlalchemy import desc

# Import project modules
from trend_analyzer import TrendAnalyzer
from token_generator import TokenGenerator
from database import get_session, init_db
from blockchain import BlockchainService
from models import Token, User, Trend, TokenDeployment, TokenTransaction

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

# Serve the index.html from the root directory at the root path
@app.route('/')
def index():
    """Serve the new-index.html file from the root directory."""
    from flask import send_from_directory
    import os
    return send_from_directory(os.path.dirname(os.path.abspath(__file__)), 'new-index.html')

@app.route('/<path:path>')
def serve_static(path):
    """Serve static files from the root directory first, then frontend directory.
    
    This route handles requests for CSS, JavaScript, images, and other static assets.
    It first checks if the file exists in the root directory, and if not, falls back
    to checking the frontend directory.
    """
    from flask import send_from_directory
    import os
    
    root_dir = os.path.dirname(os.path.abspath(__file__))
    root_file_path = os.path.join(root_dir, path)
    
    # First check if file exists in root directory
    if os.path.isfile(root_file_path):
        return send_from_directory(root_dir, path)
    
    # Fall back to frontend directory
    return send_from_directory('frontend', path)

# Initialize TrendAnalyzer and TokenGenerator
trend_analyzer = TrendAnalyzer()
token_generator = TokenGenerator()

# Initialize the blockchain service
blockchain_service = BlockchainService(
    rpc_url=os.getenv("RPC_URL", "https://rpc-mumbai.maticvigil.com/"),
    private_key=os.getenv("PRIVATE_KEY")
)

# Initialize the database
init_db()


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
    - refresh: Whether to refresh trend data (default: false)
    """
    try:
        platforms = request.args.get('platforms', 'all')
        limit = int(request.args.get('limit', 10))
        refresh = request.args.get('refresh', 'false').lower() == 'true'
        
        platforms_list = platforms.split(',') if platforms != 'all' else ['twitter', 'reddit', 'tiktok']
        
        # Check if we have recent trends in the database
        if not refresh:
            with get_session() as session:
                db_trends = session.query(Trend)\
                    .filter(Trend.is_active == True)\
                    .order_by(desc(Trend.score), desc(Trend.detected_at))\
                    .limit(limit)\
                    .all()
                
                if db_trends:
                    trend_list = [
                        {
                            "id": trend.id,
                            "name": trend.name,
                            "description": trend.description,
                            "category": trend.category,
                            "source": trend.source,
                            "score": trend.score,
                            "momentum": trend.momentum,
                            "sentiment": trend.sentiment,
                            "detected_at": trend.detected_at.isoformat() if trend.detected_at else None
                        }
                        for trend in db_trends
                    ]
                    
                    return jsonify({
                        "status": "success",
                        "count": len(trend_list),
                        "data": trend_list,
                        "source": "database"
                    })
        
        # Analyze trends from external sources
        trends = trend_analyzer.get_trending_topics(platforms=platforms_list, limit=limit)
        
        # Store trends in the database
        with get_session() as session:
            for trend_data in trends:
                # Check if trend already exists
                existing_trend = session.query(Trend)\
                    .filter(Trend.name == trend_data["name"])\
                    .first()
                
                if existing_trend:
                    # Update existing trend
                    existing_trend.score = trend_data.get("score", existing_trend.score)
                    existing_trend.momentum = trend_data.get("momentum", existing_trend.momentum)
                    existing_trend.sentiment = trend_data.get("sentiment", existing_trend.sentiment)
                    existing_trend.is_active = True
                else:
                    # Create new trend
                    new_trend = Trend(
                        name=trend_data["name"],
                        description=trend_data.get("description", ""),
                        category=trend_data.get("category", "general"),
                        source=trend_data.get("source", "api"),
                        score=trend_data.get("score", 0.0),
                        momentum=trend_data.get("momentum", 0.0),
                        sentiment=trend_data.get("sentiment", 0.0),
                        keywords=trend_data.get("keywords", []),
                        is_active=True
                    )
                    session.add(new_trend)
        
        return jsonify({
            "status": "success",
            "count": len(trends),
            "data": trends,
            "source": "api"
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
        "token_type": "memecoin|utility|governance" (optional, default: memecoin),
        "user_id": int (optional)
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
        user_id = data.get('user_id')
        
        # Generate token details
        token_details = token_generator.generate_token(
            trend_data['topic'],
            trend_data.get('description', ''),
            token_type=token_type
        )
        
        # Save trend data if it doesn't exist
        trend_id = None
        with get_session() as session:
            # Check if trend exists
            trend_name = trend_data.get('topic', token_details['name'])
            existing_trend = session.query(Trend)\
                .filter(Trend.name == trend_name)\
                .first()
            
            if existing_trend:
                trend_id = existing_trend.id
            else:
                # Create new trend
                new_trend = Trend(
                    name=trend_name,
                    description=trend_data.get('description', ''),
                    category=token_type,
                    source=trend_data.get('source', 'user'),
                    score=trend_data.get('score', 0.5),
                    is_active=True
                )
                session.add(new_trend)
                session.flush()  # Get the ID without committing
                trend_id = new_trend.id
            
            # Create token in database
            token = Token(
                name=token_details['name'],
                symbol=token_details['symbol'],
                description=token_details.get('description', ''),
                creator_id=user_id,
                trend_id=trend_id,
                initial_supply=token_details['initial_supply'],
                max_supply=token_details.get('max_supply', token_details['initial_supply']),
                decimals=token_details.get('decimals', 18),
                burn_rate=token_details.get('burn_rate', 0),
                tax_rate=token_details.get('tax_rate', 0),
                is_mintable=token_details.get('is_mintable', False),
                liquidity_allocation=token_details.get('liquidity_allocation', 0.5),
                marketing_allocation=token_details.get('marketing_allocation', 0.1),
                team_allocation=token_details.get('team_allocation', 0.1),
                is_generated=True,
                is_deployed=False,
                is_active=True
            )
            session.add(token)
            session.flush()  # Get the ID without committing
            token_id = token.id
            
            # Store generated token data
            token_details['id'] = token_id
            token_details['trend_id'] = trend_id
            
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
    Deploy a generated token to the Polygon Mumbai testnet.
    
    Expected JSON body:
    {
        "token_id": int,
        "deployer_address": "string",
        "initial_liquidity": float (optional),
        "gas_price": int (optional)
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
        deployer_address = data.get('deployer_address')
        initial_liquidity = data.get('initial_liquidity', 0.01)  # Default to 0.01 MATIC
        gas_price = data.get('gas_price')  # Optional gas price in gwei
        
        # Get token details from database
        with get_session() as session:
            token = session.query(Token).filter(Token.id == token_id).first()
            
            if not token:
                return jsonify({
                    "status": "error",
                    "message": f"Token ID {token_id} not found"
                }), 404
            
            if token.is_deployed:
                return jsonify({
                    "status": "error",
                    "message": f"Token with ID {token_id} is already deployed"
                }), 400
            
            # Deploy token to Polygon Mumbai using blockchain service
            deployment_args = {
                "name": token.name,
                "symbol": token.symbol,
                "initial_supply": token.initial_supply,
                "decimals": token.decimals,
                "burn_rate": token.burn_rate,
                "tax_rate": token.tax_rate,
                "is_mintable": token.is_mintable,
                "liquidity_allocation": token.liquidity_allocation,
                "deployer_address": deployer_address,
                "initial_liquidity": initial_liquidity
            }
            
            if gas_price:
                deployment_args["gas_price"] = gas_price
            
            # Perform the actual deployment using blockchain service
            deployment_result = blockchain_service.deploy_token(**deployment_args)
            
            # Record deployment in database
            token_deployment = TokenDeployment(
                token_id=token.id,
                transaction_hash=deployment_result["transaction_hash"],
                contract_address=deployment_result["contract_address"],
                deployer_address=deployment_result["deployer_address"],
                network="polygon-mumbai",
                block_number=deployment_result["block_number"],
                block_timestamp=deployment_result.get("timestamp"),
                gas_used=deployment_result.get("gas_used"),
                gas_price=deployment_result.get("gas_price"),
                status="success",
                deployment_data=json.dumps(deployment_result),
                deployment_args=json.dumps(deployment_args)
            )
            session.add(token_deployment)
            
            # Update token status in database
            token.is_deployed = True
            token.contract_address = deployment_result["contract_address"]
            token.deployment_date = datetime.now()
            
            # Create initial transaction record
            token_transaction = TokenTransaction(
                token_id=token.id,
                transaction_hash=deployment_result["transaction_hash"],
                transaction_type="deployment",
                from_address=deployment_result["deployer_address"],
                to_address=deployment_result["contract_address"],
                amount=token.initial_supply,
                fee=deployment_result.get("gas_used", 0) * deployment_result.get("gas_price", 0),
                timestamp=datetime.now(),
                status="success"
            )
            session.add(token_transaction)
            
            # Commit all changes
            session.commit()
            
            # Prepare response with deployment details
            response_data = {
                "token_id": token.id,
                "name": token.name,
                "symbol": token.symbol,
                "contract_address": token.contract_address,
                "transaction_hash": deployment_result["transaction_hash"],
                "block_number": deployment_result["block_number"],
                "network": "polygon-mumbai",
                "explorer_url": f"https://mumbai.polygonscan.com/address/{token.contract_address}",
                "transaction_url": f"https://mumbai.polygonscan.com/tx/{deployment_result['transaction_hash']}",
                "deployment_timestamp": token.deployment_date.isoformat() if token.deployment_date else None
            }
            
            return jsonify({
                "status": "success",
                "message": f"Token {token.name} successfully deployed to Polygon Mumbai",
                "data": response_data
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
        # Parse query parameters
        status_filter = request.args.get('status')
        is_deployed = request.args.get('deployed')
        limit = int(request.args.get('limit', 100))
        offset = int(request.args.get('offset', 0))
        sort_by = request.args.get('sort_by', 'created_at')
        sort_order = request.args.get('sort_order', 'desc')
        trend_id = request.args.get('trend_id')
        creator_id = request.args.get('creator_id')
        
        with get_session() as session:
            # Start building the query
            query = session.query(Token)
            
            # Apply filters based on query parameters
            if status_filter:
                if status_filter.lower() == 'active':
                    query = query.filter(Token.is_active == True)
                elif status_filter.lower() == 'inactive':
                    query = query.filter(Token.is_active == False)
            
            if is_deployed is not None:
                is_deployed_bool = is_deployed.lower() == 'true'
                query = query.filter(Token.is_deployed == is_deployed_bool)
            
            if trend_id:
                query = query.filter(Token.trend_id == trend_id)
            
            if creator_id:
                query = query.filter(Token.creator_id == creator_id)
            
            # Apply sorting
            if sort_order.lower() == 'asc':
                query = query.order_by(getattr(Token, sort_by))
            else:
                query = query.order_by(desc(getattr(Token, sort_by)))
            
            # Apply pagination
            query = query.limit(limit).offset(offset)
            
            # Execute query
            tokens = query.all()
            
            # Format tokens for response
            token_list = []
            for token in tokens:
                token_data = {
                    "id": token.id,
                    "name": token.name,
                    "symbol": token.symbol,
                    "description": token.description,
                    "initial_supply": token.initial_supply,
                    "decimals": token.decimals,
                    "burn_rate": token.burn_rate,
                    "tax_rate": token.tax_rate,
                    "is_deployed": token.is_deployed,
                    "contract_address": token.contract_address,
                    "created_at": token.created_at.isoformat() if token.created_at else None,
                    "deployment_date": token.deployment_date.isoformat() if token.deployment_date else None,
                    "trend_id": token.trend_id,
                    "explorer_url": f"https://mumbai.polygonscan.com/address/{token.contract_address}" if token.contract_address else None
                }
                token_list.append(token_data)
            
            return jsonify({
                "status": "success",
                "count": len(token_list),
                "data": token_list,
                "pagination": {
                    "limit": limit,
                    "offset": offset,
                    "total": session.query(Token).count()
                }
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
        with get_session() as session:
            token = session.query(Token).filter(Token.id == token_id).first()
            
            if not token:
                return jsonify({
                    "status": "error",
                    "message": f"Token ID {token_id} not found"
                }), 404
            
            # Get deployment information if token is deployed
            deployment = None
            if token.is_deployed:
                deployment = session.query(TokenDeployment)\
                    .filter(TokenDeployment.token_id == token.id)\
                    .order_by(TokenDeployment.created_at.desc())\
                    .first()
            
            # Get transactions for this token
            transactions = session.query(TokenTransaction)\
                .filter(TokenTransaction.token_id == token.id)\
                .order_by(TokenTransaction.timestamp.desc())\
                .limit(10)\
                .all()
            
            # Prepare detailed token data
            token_data = {
                "id": token.id,
                "name": token.name,
                "symbol": token.symbol,
                "description": token.description,
                "initial_supply": token.initial_supply,
                "max_supply": token.max_supply,
                "decimals": token.decimals,
                "burn_rate": token.burn_rate,
                "tax_rate": token.tax_rate,
                "is_mintable": token.is_mintable,
                "liquidity_allocation": token.liquidity_allocation,
                "marketing_allocation": token.marketing_allocation,
                "team_allocation": token.team_allocation,
                "is_generated": token.is_generated,
                "is_deployed": token.is_deployed,
                "contract_address": token.contract_address,
                "created_at": token.created_at.isoformat() if token.created_at else None,
                "deployment_date": token.deployment_date.isoformat() if token.deployment_date else None,
                "is_active": token.is_active,
                "trend_id": token.trend_id
            }
            
            # Add deployment info if available
            if deployment:
                token_data["deployment"] = {
                    "transaction_hash": deployment.transaction_hash,
                    "contract_address": deployment.contract_address,
                    "deployer_address": deployment.deployer_address,
                    "network": deployment.network,
                    "block_number": deployment.block_number,
                    "timestamp": deployment.block_timestamp.isoformat() if deployment.block_timestamp else None,
                    "gas_used": deployment.gas_used,
                    "gas_price": deployment.gas_price,
                    "explorer_url": f"https://mumbai.polygonscan.com/address/{deployment.contract_address}",
                    "transaction_url": f"https://mumbai.polygonscan.com/tx/{deployment.transaction_hash}"
                }
            
            # Add transaction history if available
            if transactions:
                token_data["transactions"] = [{
                    "transaction_hash": tx.transaction_hash,
                    "transaction_type": tx.transaction_type,
                    "from_address": tx.from_address,
                    "to_address": tx.to_address,
                    "amount": tx.amount,
                    "fee": tx.fee,
                    "timestamp": tx.timestamp.isoformat() if tx.timestamp else None,
                    "status": tx.status
                } for tx in transactions]
            
            return jsonify({
                "status": "success",
                "data": token_data
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

