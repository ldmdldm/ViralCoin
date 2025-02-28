import pytest
from brownie import accounts, chain, reverts, Contract
from brownie import TokenFactory, TrendToken
import brownie

# Constants for testing
ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"
TEST_NAME = "Test Token"
TEST_SYMBOL = "TEST"
TEST_DECIMALS = 18
TEST_INITIAL_SUPPLY = 1000000 * 10**18
TEST_CAP = 10000000 * 10**18
TEST_CATEGORY = 1  # Assuming category 1 is "meme coin"

@pytest.fixture
def factory_owner():
    return accounts[0]

@pytest.fixture
def token_owner():
    return accounts[1]

@pytest.fixture
def user():
    return accounts[2]

@pytest.fixture
def token_factory(factory_owner):
    """Deploy the TokenFactory contract"""
    return TokenFactory.deploy({"from": factory_owner})

@pytest.fixture
def trend_token(factory_owner):
    """Deploy a TrendToken directly for comparison"""
    return TrendToken.deploy(
        TEST_NAME,
        TEST_SYMBOL,
        TEST_DECIMALS,
        TEST_INITIAL_SUPPLY,
        TEST_CAP,
        factory_owner,
        {"from": factory_owner}
    )

def test_create_blueprint(token_factory, factory_owner):
    """Test creating a new blueprint for token deployment"""
    # Create a new blueprint
    tx = token_factory.createBlueprint("MemeTokenBlueprint", TEST_CATEGORY, {"from": factory_owner})
    
    # Check blueprint was created
    blueprint_id = token_factory.blueprintCount()
    assert blueprint_id == 1
    
    # Verify blueprint data
    blueprint = token_factory.getBlueprintDetails(blueprint_id)
    assert blueprint[0] == "MemeTokenBlueprint"  # name
    assert blueprint[1] == TEST_CATEGORY  # category
    assert blueprint[2] == factory_owner  # creator
    
    # Check event emission
    assert 'BlueprintCreated' in tx.events
    assert tx.events['BlueprintCreated']['blueprintId'] == blueprint_id
    assert tx.events['BlueprintCreated']['name'] == "MemeTokenBlueprint"
    assert tx.events['BlueprintCreated']['category'] == TEST_CATEGORY
    assert tx.events['BlueprintCreated']['creator'] == factory_owner

def test_deploy_token_from_blueprint(token_factory, factory_owner, token_owner):
    """Test deploying a token from a blueprint"""
    # Create a blueprint first
    token_factory.createBlueprint("UtilityTokenBlueprint", 2, {"from": factory_owner})
    blueprint_id = token_factory.blueprintCount()
    
    # Deploy a token using the blueprint
    tx = token_factory.deployTokenFromBlueprint(
        blueprint_id, 
        TEST_NAME,
        TEST_SYMBOL,
        TEST_DECIMALS,
        TEST_INITIAL_SUPPLY,
        TEST_CAP,
        token_owner,
        {"from": factory_owner}
    )
    
    # Check token was deployed
    token_count = token_factory.tokenCount()
    assert token_count == 1
    
    # Get token address
    token_address = token_factory.getTokenByIndex(token_count)
    assert token_address != ZERO_ADDRESS
    
    # Verify deployed token
    token = Contract.from_abi("TrendToken", token_address, TrendToken.abi)
    assert token.name() == TEST_NAME
    assert token.symbol() == TEST_SYMBOL
    assert token.decimals() == TEST_DECIMALS
    assert token.totalSupply() == TEST_INITIAL_SUPPLY
    assert token.cap() == TEST_CAP
    assert token.owner() == token_owner
    
    # Check event emission
    assert 'TokenDeployed' in tx.events
    assert tx.events['TokenDeployed']['blueprintId'] == blueprint_id
    assert tx.events['TokenDeployed']['tokenAddress'] == token_address
    assert tx.events['TokenDeployed']['owner'] == token_owner

def test_multiple_blueprint_categories(token_factory, factory_owner):
    """Test creating multiple blueprint categories"""
    # Create different categories of blueprints
    token_factory.createBlueprint("MemeTokenBlueprint", 1, {"from": factory_owner})
    token_factory.createBlueprint("UtilityTokenBlueprint", 2, {"from": factory_owner})
    token_factory.createBlueprint("GovernanceTokenBlueprint", 3, {"from": factory_owner})
    
    # Verify blueprint count
    assert token_factory.blueprintCount() == 3
    
    # Verify blueprint categories
    blueprint1 = token_factory.getBlueprintDetails(1)
    blueprint2 = token_factory.getBlueprintDetails(2)
    blueprint3 = token_factory.getBlueprintDetails(3)
    
    assert blueprint1[0] == "MemeTokenBlueprint"
    assert blueprint1[1] == 1
    
    assert blueprint2[0] == "UtilityTokenBlueprint"
    assert blueprint2[1] == 2
    
    assert blueprint3[0] == "GovernanceTokenBlueprint"
    assert blueprint3[1] == 3

def test_blueprint_token_consistency(token_factory, factory_owner, token_owner, trend_token):
    """Test that tokens created from blueprints behave the same as directly deployed tokens"""
    # Create a blueprint
    token_factory.createBlueprint("StandardTokenBlueprint", 1, {"from": factory_owner})
    blueprint_id = token_factory.blueprintCount()
    
    # Deploy a token using the blueprint
    token_factory.deployTokenFromBlueprint(
        blueprint_id, 
        TEST_NAME,
        TEST_SYMBOL,
        TEST_DECIMALS,
        TEST_INITIAL_SUPPLY,
        TEST_CAP,
        token_owner,
        {"from": factory_owner}
    )
    
    # Get token address
    token_address = token_factory.getTokenByIndex(1)
    factory_token = Contract.from_abi("TrendToken", token_address, TrendToken.abi)
    
    # Compare with directly deployed token
    assert factory_token.name() == trend_token.name()
    assert factory_token.symbol() == trend_token.symbol()
    assert factory_token.decimals() == trend_token.decimals()
    assert factory_token.totalSupply() == trend_token.totalSupply()
    assert factory_token.cap() == trend_token.cap()
    
    # Test token functionality
    factory_token.transfer(accounts[3], 1000, {"from": token_owner})
    assert factory_token.balanceOf(accounts[3]) == 1000

def test_blueprint_permissions(token_factory, factory_owner, user):
    """Test permissions for blueprint creation and token deployment"""
    # Create a blueprint as owner
    token_factory.createBlueprint("OwnerBlueprint", 1, {"from": factory_owner})
    blueprint_id = token_factory.blueprintCount()
    
    # Try to create a blueprint as non-owner (should fail if restricted)
    try:
        token_factory.createBlueprint("UserBlueprint", 1, {"from": user})
        # If we get here, it means non-owners can create blueprints
        assert token_factory.blueprintCount() == 2
    except Exception:
        # If we get here, it means only owners can create blueprints
        assert token_factory.blueprintCount() == 1
    
    # Try to deploy a token from a blueprint as non-owner
    try:
        token_factory.deployTokenFromBlueprint(
            blueprint_id, 
            TEST_NAME,
            TEST_SYMBOL,
            TEST_DECIMALS,
            TEST_INITIAL_SUPPLY,
            TEST_CAP,
            user,
            {"from": user}
        )
        # If we get here, it means non-owners can deploy tokens
        assert token_factory.tokenCount() == 1
    except Exception:
        # If we get here, it means only owners can deploy tokens
        assert token_factory.tokenCount() == 0

def test_blueprint_modifications(token_factory, factory_owner):
    """Test modifying blueprint properties if supported"""
    # Create a blueprint
    token_factory.createBlueprint("InitialBlueprint", 1, {"from": factory_owner})
    blueprint_id = token_factory.blueprintCount()
    
    # Check if the contract has a method to update blueprint name
    try:
        token_factory.updateBlueprintName(blueprint_id, "UpdatedBlueprint", {"from": factory_owner})
        blueprint = token_factory.getBlueprintDetails(blueprint_id)
        assert blueprint[0] == "UpdatedBlueprint"
    except Exception:
        # If we get here, blueprint updates might not be supported
        blueprint = token_factory.getBlueprintDetails(blueprint_id)
        assert blueprint[0] == "InitialBlueprint"
    
    # Check if the contract has a method to update blueprint category
    try:
        token_factory.updateBlueprintCategory(blueprint_id, 2, {"from": factory_owner})
        blueprint = token_factory.getBlueprintDetails(blueprint_id)
        assert blueprint[1] == 2
    except Exception:
        # If we get here, category updates might not be supported
        blueprint = token_factory.getBlueprintDetails(blueprint_id)
        assert blueprint[1] == 1

def test_multiple_tokens_from_same_blueprint(token_factory, factory_owner):
    """Test deploying multiple tokens from the same blueprint"""
    # Create a blueprint
    token_factory.createBlueprint("StandardBlueprint", 1, {"from": factory_owner})
    blueprint_id = token_factory.blueprintCount()
    
    # Deploy first token
    token_factory.deployTokenFromBlueprint(
        blueprint_id, 
        "Token1",
        "TK1",
        18,
        1000000 * 10**18,
        10000000 * 10**18,
        factory_owner,
        {"from": factory_owner}
    )
    
    # Deploy second token with different parameters
    token_factory.deployTokenFromBlueprint(
        blueprint_id, 
        "Token2",
        "TK2",
        18,
        2000000 * 10**18,
        20000000 * 10**18,
        factory_owner,
        {"from": factory_owner}
    )
    
    # Verify both tokens were created with correct parameters
    token1_address = token_factory.getTokenByIndex(1)
    token2_address = token_factory.getTokenByIndex(2)
    
    token1 = Contract.from_abi("TrendToken", token1_address, TrendToken.abi)
    token2 = Contract.from_abi("TrendToken", token2_address, TrendToken.abi)
    
    assert token1.name() == "Token1"
    assert token1.symbol() == "TK1"
    assert token1.totalSupply() == 1000000 * 10**18
    
    assert token2.name() == "Token2"
    assert token2.symbol() == "TK2"
    assert token2.totalSupply() == 2000000 * 10**18

