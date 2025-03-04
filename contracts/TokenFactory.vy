# @version ^0.3.7

"""
@title TokenFactory
@author ViralCoin Team
@notice Factory contract for deploying trend-based tokens
@dev Uses create_minimal_proxy_to from vyper's built-in function to deploy tokens
"""

from vyper.interfaces import ERC20

implements: ERC20

# Events
event TokenCreated:
    token_address: indexed(address)
    token_type: String[32]
    name: String[64]
    symbol: String[32]
    initial_supply: uint256
    creator: indexed(address)
    timestamp: uint256

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

# Contract Variables
token_template: public(address)
owner: public(address)
token_count: public(uint256)
tokens_created: public(DynArray[address, 100])
is_paused: public(bool)

# Mapping to track created tokens
tokens: public(HashMap[uint256, address])
token_details: public(HashMap[address, HashMap[String[10], String[64]]])

# Blueprint storage
blueprints: public(HashMap[uint256, address])
blueprint_count: public(uint256)

# Token type blueprints
token_blueprints: public(HashMap[String[32], address])

# Fee configuration
creation_fee: public(uint256)  # Fee in ETH to create a token
treasury: public(address)

@external
def __init__(token_template_address: address, _treasury: address = empty(address)):
    """
    @notice Initialize the factory with a token template
    @param token_template_address Address of the token implementation to clone
    @param _treasury Address where fees will be sent
    """
    self.token_template = token_template_address
    self.owner = msg.sender
    self.token_count = 0
    self.is_paused = False
    self.creation_fee = 10**17  # 0.1 ETH default fee
    self.treasury = _treasury if _treasury != empty(address) else msg.sender

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
    self.blueprints[blueprint_id] = create_copy_of(_implementation)
    self.blueprint_count += 1
    
    log BlueprintCreated(_category, blueprint_id)

@external
@payable
def create_token(
    name: String[64],
    symbol: String[32],
    initial_supply: uint256,
    decimals: uint8,
    receiver: address
) -> address:
    """
    @notice Creates a new token based on the template
    @param name Token name
    @param symbol Token symbol
    @param initial_supply Initial token supply
    @param decimals Number of decimals for the token
    @param receiver Address to receive the initial supply
    @return Address of the created token
    """
    # Ensure contract is not paused
    assert not self.is_paused, "Contract is paused"
    
    # Ensure fee is paid
    assert msg.value >= self.creation_fee, "Insufficient fee"
    
    # Create token using the template
    token_address: address = create_minimal_proxy_to(self.token_template)
    
    # Initialize the token with provided parameters
    raw_call(
        token_address,
        _abi_encode(
            name, 
            symbol, 
            initial_supply, 
            decimals, 
            receiver,
            method_id=method_id("initialize(string,string,uint256,uint8,address)")
        )
    )
    
    # Store token details
    self.tokens[self.token_count] = token_address
    self.token_details[token_address]["name"] = name
    self.token_details[token_address]["symbol"] = symbol
    self.tokens_created.append(token_address)
    
    # Increment token count
    self.token_count += 1
    
    # Transfer fee to treasury
    send(self.treasury, msg.value)
    
    # Emit creation event
    log TokenCreated(
        token_address,
        "standard",
        name,
        symbol,
        initial_supply,
        msg.sender,
        block.timestamp
    )
    
    return token_address

@external
@payable
def create_trend_token(config: TokenConfig) -> address:
    """
    @notice Create a new token based on trend data
    @param config The configuration for the token
    @return The address of the newly created token
    @dev Uses the Blueprint pattern to efficiently deploy token contracts
    """
    assert not self.is_paused, "Contract is paused"
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
        blueprint = create_copy_of(self.token_template)
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
    self.tokens[self.token_count] = new_token
    self.token_count += 1
    
    # Transfer fee to treasury
    send(self.treasury, msg.value)
    
    log TokenCreated(
        new_token,
        config.trend_category,
        config.name,
        config.symbol,
        config.initial_supply,
        msg.sender,
        block.timestamp
    )
    
    return new_token

@external
def set_creation_fee(new_fee: uint256):
    """
    @notice Set the fee required to create a new token
    @param new_fee New fee amount in wei
    """
    assert msg.sender == self.owner, "Only owner"
    self.creation_fee = new_fee

@external
def set_treasury(_treasury: address):
    """
    @notice Update the treasury address
    @param _treasury The new treasury address
    """
    assert msg.sender == self.owner, "Only owner"
    assert _treasury != empty(address), "Zero address not allowed"
    self.treasury = _treasury

@external
def withdraw_fees():
    """
    @notice Withdraw accumulated fees to the treasury
    """
    assert msg.sender == self.owner, "Only owner"
    send(self.treasury, self.balance)

@external
def pause(should_pause: bool):
    """
    @notice Pause or unpause the contract
    @param should_pause True to pause, False to unpause
    """
    assert msg.sender == self.owner, "Only owner"
    self.is_paused = should_pause

@external
def transfer_ownership(new_owner: address):
    """
    @notice Transfer ownership of the contract
    @param new_owner Address of the new owner
    """
    assert msg.sender == self.owner, "Only owner"
    assert new_owner != empty(address), "Zero address not allowed"
    self.owner = new_owner

@external
def update_token_template(new_template: address):
    """
    @notice Update the token template address
    @param new_template Address of the new template
    """
    assert msg.sender == self.owner, "Only owner"
    assert new_template != empty(address), "Zero address not allowed"
    self.token_template = new_template

@view
@external
def get_token_address(index: uint256) -> address:
    """
    @notice Get token address by index
    @param index Index of the token
    @return Address of the token
    """
    assert index < self.token_count, "Invalid index"
    return self.tokens[index]

@view
@external
def get_all_tokens() -> DynArray[address, 100]:
    """
    @notice Get all tokens created by this factory (limited to 100)
    @return List of token addresses
    """
    return self.tokens_created

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
