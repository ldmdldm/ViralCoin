# @version ^0.3.7
"""
@title Trend-Based Token Factory
@author Your Name
@notice Factory contract for creating trend-based tokens
@dev Creates customized tokens based on trend data
"""

from vyper.interfaces import ERC20

# Events
event TokenCreated:
    token_address: address
    token_type: String[32]
    token_name: String[64]
    token_symbol: String[32]
    creator: address
    creation_time: uint256
    
# Blueprint creation event
event BlueprintCreated:
    category: String[32]
    blueprint_id: uint256

# Structs
struct TokenConfig:
    name: String[64]
    symbol: String[32]
    initial_supply: uint256
    max_supply: uint256
    burn_rate: uint256  # Basis points (1/100 of a percent)
    tax_rate: uint256   # Basis points
    is_mintable: bool
    trend_score: uint256
    trend_category: String[32]  # "meme", "defi", "gaming", "social", etc.

# Storage variables
owner: public(address)
token_implementation: public(address)
tokens_created: public(DynArray[address, 100])
token_count: public(uint256)

# Blueprint storage
blueprints: public(HashMap[uint256, address])
blueprint_count: public(uint256)

# Token type blueprints
token_blueprints: public(HashMap[String[32], address])

# Fee configuration
creation_fee: public(uint256)  # Fee in ETH to create a token
treasury: public(address)

@external
def __init__(_implementation: address, _treasury: address):
    """
    @notice Initialize the factory with a token implementation
    @param _implementation The address of the token implementation contract
    @param _treasury Address where fees will be sent
    """
    self.owner = msg.sender
    self.token_implementation = _implementation
    self.treasury = _treasury
    self.creation_fee = 0.01 * 10**18  # 0.01 ETH default fee
    self.token_count = 0

@external
def register_token_blueprint(_category: String[32], _implementation: address):
    """
    @notice Register a new token blueprint for a specific category
    @param _category The category name (e.g., "meme", "defi")
    @param _implementation The implementation contract address
    @dev Creates a blueprint from the implementation contract to be used later
    """
    assert msg.sender == self.owner, "Only owner"
    self.token_blueprints[_category] = _implementation
    
    # Create a blueprint from the implementation
    blueprint_id: uint256 = self.blueprint_count
    self.blueprints[blueprint_id] = self._create_blueprint(_implementation)
    self.blueprint_count += 1
    
    log BlueprintCreated(_category, blueprint_id)

@external
@payable
def create_token(config: TokenConfig) -> address:
    """
    @notice Create a new token based on trend data
    @param config The configuration for the token
    @return The address of the newly created token
    @dev Uses the Blueprint pattern to efficiently deploy token contracts
    """
    assert msg.value >= self.creation_fee, "Insufficient fee"
    
    # Select the appropriate implementation based on category
    blueprint_id: uint256 = 0
    # Find the blueprint for this category if it exists
    for i in range(self.blueprint_count):
        if self.token_blueprints[config.trend_category] != empty(address):
            blueprint_id = i
            break
            
    # Use default if no specific blueprint
    blueprint: address = self.blueprints[blueprint_id]
    if blueprint == empty(address):
        # If no blueprint exists, create one from the default implementation
        blueprint = self._create_blueprint(self.token_implementation)
        self.blueprints[blueprint_id] = blueprint
    
    # Deploy a new token instance from the blueprint
    # Encode constructor arguments
    init_code: Bytes[1024] = _abi_encode(
        config.name,
        config.symbol,
        config.initial_supply,
        config.max_supply,
        config.burn_rate,
        config.tax_rate,
        config.is_mintable,
        config.trend_score,
        config.trend_category,
        msg.sender  # token creator becomes the owner
    )
    
    # Create new token from blueprint with constructor arguments
    new_token: address = create_from_blueprint(
        blueprint,
        init_code
    )
    
    self.tokens_created.append(new_token)
    self.token_count += 1
    
    # Transfer fee to treasury
    send(self.treasury, msg.value)
    
    log TokenCreated(
        new_token,
        config.trend_category,
        config.name,
        config.symbol,
        msg.sender,
        block.timestamp
    )
    
    return new_token

@external
def set_creation_fee(_fee: uint256):
    """
    @notice Set the fee for creating a token
    @param _fee The new fee amount in wei
    """
    assert msg.sender == self.owner, "Only owner"
    self.creation_fee = _fee

@external
def set_treasury(_treasury: address):
    """
    @notice Update the treasury address
    @param _treasury The new treasury address
    """
    assert msg.sender == self.owner, "Only owner"
    self.treasury = _treasury

@external
@view
def get_created_tokens() -> DynArray[address, 100]:
    """
    @notice Get a list of all created tokens
    @return Array of token addresses
    """
    return self.tokens_created

@internal
def _create_blueprint(_implementation: address) -> address:
    """
    @notice Internal function to create a blueprint from an implementation contract
    @param _implementation The address of the implementation contract
    @return The address of the created blueprint
    @dev Uses create_copy_of() to efficiently create blueprints
    """
    # Create a blueprint of the implementation contract
    return create_copy_of(_implementation)

@external
def get_blueprint_count() -> uint256:
    """
    @notice Get the total number of blueprints registered
    @return The count of blueprints
    """
    return self.blueprint_count

@external
def get_blueprint(blueprint_id: uint256) -> address:
    """
    @notice Get the address of a specific blueprint
    @param blueprint_id The ID of the blueprint
    @return The address of the blueprint
    """
    assert blueprint_id < self.blueprint_count, "Invalid blueprint ID"
    return self.blueprints[blueprint_id]
