import pytest
import brownie
from brownie import accounts, chain, Contract, TrendToken, TokenFactory, interface
from decimal import Decimal

# Constants for tests
TEST_TOKEN_NAME = "Trend Test Token"
TEST_TOKEN_SYMBOL = "TTT"
INITIAL_SUPPLY = 1_000_000 * 10**18  # 1 million tokens with 18 decimals
LIQUIDITY_AMOUNT = 100_000 * 10**18  # 100k tokens for liquidity
ETH_AMOUNT = 10 * 10**18  # 10 ETH for liquidity
TRADE_AMOUNT = 1000 * 10**18  # 1000 tokens for testing trading

@pytest.fixture
def deployer():
    """Return the account that will deploy the contracts"""
    return accounts[0]

@pytest.fixture
def user():
    """Return a user account for testing"""
    return accounts[1]

@pytest.fixture
def quickswap_router(deployer):
    """
    Mock Quickswap router for testing.
    In a real test, you would use the actual Quickswap router address
    or deploy a mock router contract.
    """
    # For this test, we'll simulate a Quickswap router with a mock contract
    # You might replace this with the actual Quickswap router in a real test
    router_abi = [
        {
            "inputs": [
                {"internalType": "uint256", "name": "amountIn", "type": "uint256"},
                {"internalType": "uint256", "name": "amountOutMin", "type": "uint256"},
                {"internalType": "address[]", "name": "path", "type": "address[]"},
                {"internalType": "address", "name": "to", "type": "address"},
                {"internalType": "uint256", "name": "deadline", "type": "uint256"}
            ],
            "name": "swapExactTokensForETH",
            "outputs": [{"internalType": "uint256[]", "name": "amounts", "type": "uint256[]"}],
            "stateMutability": "nonpayable",
            "type": "function"
        },
        {
            "inputs": [
                {"internalType": "uint256", "name": "amountOutMin", "type": "uint256"},
                {"internalType": "address[]", "name": "path", "type": "address[]"},
                {"internalType": "address", "name": "to", "type": "address"},
                {"internalType": "uint256", "name": "deadline", "type": "uint256"}
            ],
            "name": "swapExactETHForTokens",
            "outputs": [{"internalType": "uint256[]", "name": "amounts", "type": "uint256[]"}],
            "stateMutability": "payable",
            "type": "function"
        },
        {
            "inputs": [
                {"internalType": "address", "name": "tokenA", "type": "address"},
                {"internalType": "address", "name": "tokenB", "type": "address"},
                {"internalType": "uint256", "name": "amountADesired", "type": "uint256"},
                {"internalType": "uint256", "name": "amountBDesired", "type": "uint256"},
                {"internalType": "uint256", "name": "amountAMin", "type": "uint256"},
                {"internalType": "uint256", "name": "amountBMin", "type": "uint256"},
                {"internalType": "address", "name": "to", "type": "address"},
                {"internalType": "uint256", "name": "deadline", "type": "uint256"}
            ],
            "name": "addLiquidity",
            "outputs": [
                {"internalType": "uint256", "name": "amountA", "type": "uint256"},
                {"internalType": "uint256", "name": "amountB", "type": "uint256"},
                {"internalType": "uint256", "name": "liquidity", "type": "uint256"}
            ],
            "stateMutability": "nonpayable",
            "type": "function"
        },
        {
            "inputs": [
                {"internalType": "address", "name": "token", "type": "address"},
                {"internalType": "uint256", "name": "amountTokenDesired", "type": "uint256"},
                {"internalType": "uint256", "name": "amountTokenMin", "type": "uint256"},
                {"internalType": "uint256", "name": "amountETHMin", "type": "uint256"},
                {"internalType": "address", "name": "to", "type": "address"},
                {"internalType": "uint256", "name": "deadline", "type": "uint256"}
            ],
            "name": "addLiquidityETH",
            "outputs": [
                {"internalType": "uint256", "name": "amountToken", "type": "uint256"},
                {"internalType": "uint256", "name": "amountETH", "type": "uint256"},
                {"internalType": "uint256", "name": "liquidity", "type": "uint256"}
            ],
            "stateMutability": "payable",
            "type": "function"
        }
    ]
    
    # Deploy a mock contract or use a pre-deployed one
    mock_router = deployer.deploy(Contract, abi=router_abi)
    return mock_router

@pytest.fixture
def factory(deployer):
    """Deploy the TokenFactory contract"""
    return TokenFactory.deploy({'from': deployer})

@pytest.fixture
def trend_blueprint(factory, deployer):
    """Create a trend token blueprint using the factory"""
    tx = factory.createTrendTokenBlueprint({'from': deployer})
    blueprint_id = tx.events['BlueprintCreated']['blueprintId']
    return blueprint_id

@pytest.fixture
def trend_token(factory, trend_blueprint, quickswap_router, deployer):
    """Deploy a trend token from the blueprint"""
    # Deploy a new trend token using the blueprint
    tx = factory.deployTrendToken(
        trend_blueprint,
        TEST_TOKEN_NAME,
        TEST_TOKEN_SYMBOL,
        INITIAL_SUPPLY,
        deployer,  # Initial holder
        quickswap_router,  # Quickswap router address
        {'from': deployer}
    )
    
    # Get the deployed token address from the event
    token_address = tx.events['TokenDeployed']['tokenAddress']
    
    # Return the token contract instance
    return TrendToken.at(token_address)

def test_token_creation_via_factory(factory, trend_blueprint, deployer, user):
    """Test creating a token using the blueprint pattern via the factory"""
    # Deploy a new trend token
    tx = factory.deployTrendToken(
        trend_blueprint,
        TEST_TOKEN_NAME,
        TEST_TOKEN_SYMBOL,
        INITIAL_SUPPLY,
        deployer,  # Initial holder
        deployer.address,  # Placeholder for router address
        {'from': deployer}
    )
    
    # Verify event was emitted
    assert 'TokenDeployed' in tx.events
    
    # Get the deployed token address from the event
    token_address = tx.events['TokenDeployed']['tokenAddress']
    
    # Verify token was created with correct parameters
    token = TrendToken.at(token_address)
    assert token.name() == TEST_TOKEN_NAME
    assert token.symbol() == TEST_TOKEN_SYMBOL
    assert token.totalSupply() == INITIAL_SUPPLY
    assert token.balanceOf(deployer) == INITIAL_SUPPLY

def test_quickswap_integration(trend_token, quickswap_router, deployer):
    """Test that the created token properly integrates with Quickswap"""
    # Verify Quickswap router is set correctly
    assert trend_token.quickswapRouter() == quickswap_router.address
    
    # Test setting a new router address
    trend_token.setQuickswapRouter(deployer.address, {'from': deployer})
    assert trend_token.quickswapRouter() == deployer.address
    
    # Reset to original router for other tests
    trend_token.setQuickswapRouter(quickswap_router.address, {'from': deployer})

def test_liquidity_provisioning(trend_token, quickswap_router, deployer):
    """Test adding liquidity to Quickswap"""
    # Setup: Approve tokens for the router
    trend_token.approve(quickswap_router.address, LIQUIDITY_AMOUNT, {'from': deployer})
    
    # Mock deadline (30 minutes from now)
    deadline = chain.time() + 1800
    
    # In a real test, we would call the router's addLiquidityETH function
    # For this test, we'll just verify the approvals and token balances
    
    # Verify approval was set correctly
    assert trend_token.allowance(deployer, quickswap_router.address) == LIQUIDITY_AMOUNT
    
    # In a real test, you would make the actual addLiquidityETH call:
    # quickswap_router.addLiquidityETH(
    #     trend_token.address,
    #     LIQUIDITY_AMOUNT,
    #     LIQUIDITY_AMOUNT,  # Min amount
    #     ETH_AMOUNT,  # Min ETH
    #     deployer,
    #     deadline,
    #     {'from': deployer, 'value': ETH_AMOUNT}
    # )

def test_complete_workflow(factory, trend_blueprint, quickswap_router, deployer, user):
    """Test a complete workflow including token creation, liquidity, and trading"""
    # Step 1: Deploy a new trend token from blueprint
    tx = factory.deployTrendToken(
        trend_blueprint,
        "Complete Workflow Token",
        "CWT",
        INITIAL_SUPPLY,
        deployer,  # Initial holder
        quickswap_router.address,
        {'from': deployer}
    )
    
    token_address = tx.events['TokenDeployed']['tokenAddress']
    token = TrendToken.at(token_address)
    
    # Step 2: Approve and transfer some tokens to the user
    token.transfer(user, TRADE_AMOUNT, {'from': deployer})
    assert token.balanceOf(user) == TRADE_AMOUNT
    
    # Step 3: Set up liquidity (approval)
    token.approve(quickswap_router.address, LIQUIDITY_AMOUNT, {'from': deployer})
    
    # Step 4: Verify Quickswap integration
    assert token.quickswapRouter() == quickswap_router.address
    
    # Step 5: Simulate trading (in a real test, you would make actual router calls)
    # For this test, we'll just verify that the user can approve tokens for trading
    token.approve(quickswap_router.address, TRADE_AMOUNT, {'from': user})
    assert token.allowance(user, quickswap_router.address) == TRADE_AMOUNT
    
    # In a real test with a properly mocked or real router:
    # 1. User would call swapExactTokensForETH to sell tokens
    # 2. Another user would call swapExactETHForTokens to buy tokens
    # 3. You would verify the resulting balances

def test_multiple_token_deployments(factory, trend_blueprint, deployer):
    """Test deploying multiple tokens from the same blueprint"""
    # Deploy first token
    tx1 = factory.deployTrendToken(
        trend_blueprint,
        "First Token",
        "FT1",
        INITIAL_SUPPLY,
        deployer,
        deployer.address,  # Router placeholder
        {'from': deployer}
    )
    
    token1_address = tx1.events['TokenDeployed']['tokenAddress']
    
    # Deploy second token with different parameters
    tx2 = factory.deployTrendToken(
        trend_blueprint,
        "Second Token",
        "FT2",
        INITIAL_SUPPLY * 2,  # Double supply
        deployer,
        deployer.address,  # Router placeholder
        {'from': deployer}
    )
    
    token2_address = tx2.events['TokenDeployed']['tokenAddress']
    
    # Verify tokens are different
    assert token1_address != token2_address
    
    # Verify correct parameters for each token
    token1 = TrendToken.at(token1_address)
    token2 = TrendToken.at(token2_address)
    
    assert token1.name() == "First Token"
    assert token1.symbol() == "FT1"
    assert token1.totalSupply() == INITIAL_SUPPLY
    
    assert token2.name() == "Second Token"
    assert token2.symbol() == "FT2"
    assert token2.totalSupply() == INITIAL_SUPPLY * 2

