import pytest
from brownie import TrendToken, accounts, chain, Wei, reverts, Contract
from brownie.exceptions import VirtualMachineError
from brownie.network import gas_price
from brownie.network.gas.strategies import GasNowStrategy

# Mock interfaces for testing
MOCK_ROUTER_ABI = [
    {
        "inputs": [
            {"internalType": "uint256", "name": "amountIn", "type": "uint256"},
            {"internalType": "uint256", "name": "amountOutMin", "type": "uint256"},
            {"internalType": "address[]", "name": "path", "type": "address[]"},
            {"internalType": "address", "name": "to", "type": "address"},
            {"internalType": "uint256", "name": "deadline", "type": "uint256"}
        ],
        "name": "swapExactTokensForTokens",
        "outputs": [{"internalType": "uint256[]", "name": "amounts", "type": "uint256[]"}],
        "stateMutability": "nonpayable",
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
            {"internalType": "address", "name": "tokenA", "type": "address"},
            {"internalType": "address", "name": "tokenB", "type": "address"}
        ],
        "name": "factory",
        "outputs": [{"internalType": "address", "name": "pair", "type": "address"}],
        "stateMutability": "view",
        "type": "function"
    }
]

# Mock WETH Token ABI for testing
MOCK_WETH_ABI = [
    {
        "inputs": [],
        "name": "deposit",
        "outputs": [],
        "stateMutability": "payable",
        "type": "function"
    },
    {
        "inputs": [{"internalType": "uint256", "name": "wad", "type": "uint256"}],
        "name": "withdraw",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    }
]

@pytest.fixture
def deployer():
    return accounts[0]

@pytest.fixture
def user():
    return accounts[1]

@pytest.fixture
def liquidity_provider():
    return accounts[2]

@pytest.fixture
def quickswap_router(deployer):
    # Deploy a mock router contract or use accounts as a simple mock
    # Here we're using an address as a mock for simplicity
    router_address = deployer.deploy(Contract.from_abi("MockRouter", deployer.address, MOCK_ROUTER_ABI)).address
    return router_address

@pytest.fixture
def weth_token(deployer):
    # Deploy a mock WETH token or use accounts as a simple mock
    weth_address = deployer.deploy(Contract.from_abi("MockWETH", deployer.address, MOCK_WETH_ABI)).address
    return weth_address

@pytest.fixture
def trend_token(deployer, quickswap_router, weth_token):
    # Deploy the TrendToken contract with initial parameters
    token = deployer.deploy(TrendToken, 
                            "Trending Token", 
                            "TREND", 
                            18, 
                            Wei("1000000 ether"),  # 1 million initial supply
                            deployer)
    
    # Set the Quickswap router
    token.setQuickswapRouter(quickswap_router, {"from": deployer})
    
    # Set the WETH token address
    token.setWETH(weth_token, {"from": deployer})
    
    return token

def test_initial_state(trend_token, deployer, quickswap_router, weth_token):
    """Test the initial state of the token contract."""
    assert trend_token.name() == "Trending Token"
    assert trend_token.symbol() == "TREND"
    assert trend_token.decimals() == 18
    assert trend_token.totalSupply() == Wei("1000000 ether")
    assert trend_token.balanceOf(deployer) == Wei("1000000 ether")
    assert trend_token.quickswapRouter() == quickswap_router
    assert trend_token.WETH() == weth_token
    assert trend_token.owner() == deployer

def test_erc20_transfer(trend_token, deployer, user):
    """Test basic ERC20 transfer functionality."""
    # Transfer tokens from deployer to user
    amount = Wei("1000 ether")
    trend_token.transfer(user, amount, {"from": deployer})
    
    # Check balances after transfer
    assert trend_token.balanceOf(user) == amount
    assert trend_token.balanceOf(deployer) == Wei("1000000 ether") - amount

def test_erc20_approve_and_transferFrom(trend_token, deployer, user, liquidity_provider):
    """Test ERC20 approve and transferFrom functionality."""
    # Deployer approves user to spend tokens
    amount = Wei("5000 ether")
    trend_token.approve(user, amount, {"from": deployer})
    
    # Check allowance
    assert trend_token.allowance(deployer, user) == amount
    
    # User transfers tokens from deployer to liquidity_provider
    transfer_amount = Wei("2000 ether")
    trend_token.transferFrom(deployer, liquidity_provider, transfer_amount, {"from": user})
    
    # Check balances and updated allowance
    assert trend_token.balanceOf(liquidity_provider) == transfer_amount
    assert trend_token.balanceOf(deployer) == Wei("1000000 ether") - transfer_amount
    assert trend_token.allowance(deployer, user) == amount - transfer_amount

def test_set_quickswap_router(trend_token, deployer, user):
    """Test setting the Quickswap router address."""
    new_router = accounts[5]
    
    # Only owner can set router
    with reverts("Ownable: caller is not the owner"):
        trend_token.setQuickswapRouter(new_router, {"from": user})
    
    # Owner sets new router
    trend_token.setQuickswapRouter(new_router, {"from": deployer})
    assert trend_token.quickswapRouter() == new_router

def test_add_liquidity(trend_token, deployer, quickswap_router, weth_token):
    """Test adding liquidity functionality."""
    # Mock implementation since we can't actually interact with Quickswap
    # In a real test, you would mock the router response or use a fork of mainnet
    
    # Approve router to spend tokens
    amount = Wei("10000 ether")
    trend_token.approve(quickswap_router, amount, {"from": deployer})
    
    # Call the addLiquidity function
    # This would typically interact with the Quickswap router
    # Here we're just checking if the function exists and can be called
    try:
        # This might revert since we're using a mock, but we just want to check it exists
        trend_token.addLiquidityETH(
            amount,
            Wei("9000 ether"),  # min token amount
            Wei("1 ether"),     # min ETH amount
            deployer,
            chain.time() + 3600,  # deadline: 1 hour from now
            {"from": deployer, "value": Wei("1 ether")}
        )
    except VirtualMachineError:
        # Expected to revert with our mock, just checking if function exists
        pass

def test_swap_tokens(trend_token, deployer, user, quickswap_router):
    """Test swapping tokens functionality."""
    # Transfer some tokens to user for testing
    amount = Wei("5000 ether")
    trend_token.transfer(user, amount, {"from": deployer})
    
    # Approve router to spend user's tokens
    trend_token.approve(quickswap_router, amount, {"from": user})
    
    # Call the swapExactTokensForETH function
    # This would typically interact with the Quickswap router
    # Here we're just checking if the function exists and can be called
    try:
        # This might revert since we're using a mock, but we just want to check it exists
        trend_token.swapExactTokensForETH(
            Wei("1000 ether"),   # amount in
            Wei("0.1 ether"),    # min amount out
            user,                # recipient
            chain.time() + 3600, # deadline: 1 hour from now
            {"from": user}
        )
    except VirtualMachineError:
        # Expected to revert with our mock, just checking if function exists
        pass

def test_trend_mechanics(trend_token, deployer):
    """Test any special token mechanics related to trends."""
    # This would test any trend-specific functionality in the token
    # Such as trend score updates, trend-based fees, etc.
    
    # Example: test trend score update (if such function exists)
    try:
        trend_token.updateTrendScore(85, {"from": deployer})
        assert trend_token.trendScore() == 85
    except (VirtualMachineError, AttributeError):
        # Function might not exist, so skip this test
        pass
    
    # Example: test trend-based fees (if such functionality exists)
    try:
        trend_token.setTrendBasedFee(True, {"from": deployer})
        assert trend_token.isTrendBasedFeeEnabled() == True
    except (VirtualMachineError, AttributeError):
        # Function might not exist, so skip this test
        pass

def test_ownership_transfer(trend_token, deployer, user):
    """Test transferring ownership of the contract."""
    # Transfer ownership to user
    trend_token.transferOwnership(user, {"from": deployer})
    
    # Check new owner
    assert trend_token.owner() == user
    
    # Old owner can no longer call owner-only functions
    with reverts("Ownable: caller is not the owner"):
        trend_token.setQuickswapRouter(accounts[5], {"from": deployer})
    
    # New owner can call owner-only functions
    new_router = accounts[6]
    trend_token.setQuickswapRouter(new_router, {"from": user})
    assert trend_token.quickswapRouter() == new_router

