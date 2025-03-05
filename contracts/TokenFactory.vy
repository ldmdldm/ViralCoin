# @version ^0.3.9

"""
@title TokenFactory
@author ViralCoin
@notice Factory contract for deploying trend-based tokens
@dev Uses clone pattern to deploy tokens with minimal gas costs
"""

from vyper.interfaces import ERC20

# Events
event TokenCreated:
    token_address: indexed(address)
    token_type: String[32]
    name: String[64]
    symbol: String[32]
    initial_supply: uint256
    creator: indexed(address)
    timestamp: uint256
    trend_score: uint256
    trend_category: String[32]

# Struct for token configuration
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
owner: public(address)
token_template: public(address)
token_count: public(uint256)
creation_fee: public(uint256)  # Fee in ETH to create a token
treasury: public(address)
is_paused: public(bool)

# Mapping to track created tokens
tokens: public(HashMap[uint256, address])
token_creators: public(HashMap[address, address])
token_details: public(HashMap[address, TokenConfig])

# List of all tokens created
tokens_created: public(DynArray[address, 1000])

# Category to token mappings
category_tokens: public(HashMap[String[32], DynArray[address, 100]])

@external
def __init__(token_template_address: address):
    """
    @notice Initialize the factory with a token template
    @param token_template_address Address of the token implementation to clone
    """
    self.owner = msg.sender
    self.token_template = token_template_address
    self.token_count = 0
    self.creation_fee = 10**17  # 0.1 ETH default fee
    self.treasury = msg.sender
    self.is_paused = False

@external
@payable
def create_token(config: TokenConfig) -> address:
    """
    @notice Creates a new token based on the template and configuration
    @param config Struct containing all token configuration parameters
    @return Address of the newly created token
    """
    # Ensure contract is not paused
    assert not self.is_paused, "Contract is paused"
    
    # Ensure fee is paid
    assert msg.value >= self.creation_fee, "Insufficient fee"
    
    # Create token using the template
    token_address: address = create_minimal_proxy_to(self.token_template)
    
    # Initialize the token with provided parameters
    # We need to call initialize() on the new token contract
    raw_call(
        token_address,
        _abi_encode(
            config.name,
            config.symbol,
            config.initial_supply,
            config.max_supply,
            config.burn_rate,
            config.tax_rate,
            config.is_mintable,
            msg.sender,  # Owner of the token
            method_id=method_id("initialize(string,string,uint256,uint256,uint256,uint256,bool,address)")
        )
    )
    
    # Store token details
    self.tokens[self.token_count] = token_address
    self.token_creators[token_address] = msg.sender
    self.token_details[token_address] = config
    
    # Add to tokens array
    self.tokens_created.append(token_address)
    
    # Add to category list
    # Note: This will fail if more than 100 tokens are created in a category
    # A more robust implementation would handle this case
    if len(self.category_tokens[config.trend_category]) < 100:
        self.category_tokens[config.trend_category].append(token_address)
    
    # Increment token count
    self.token_count += 1
    
    # Transfer fee to treasury
    send(self.treasury, msg.value)
    
    # Emit creation event
    log TokenCreated(
        token_address,
        config.trend_category,
        config.name,
        config.symbol,
        config.initial_supply,
        msg.sender,
        block.timestamp,
        config.trend_score,
        config.trend_category
    )
    
    return token_address

@external
@payable
def create_trending_token(
    name: String[64],
    symbol: String[32],
    initial_supply: uint256,
    trend_score: uint256,
    trend_category: String[32]
) -> address:
    """
    @notice Simplified method to create a token with default parameters for trending topics
    @param name Token name
    @param symbol Token symbol
    @param initial_supply Initial supply of tokens
    @param trend_score Score of the trend (0-100)
    @param trend_category Category of the trend
    @return Address of the created token
    """
    # Create a TokenConfig with default values optimized for the category
    config: TokenConfig = TokenConfig({
        name: name,
        symbol: symbol,
        initial_supply: initial_supply,
        max_supply: initial_supply * 2,  # Default max is 2x initial
        burn_rate: 100,  # 1% burn rate by default
        tax_rate: 200,   # 2% tax rate by default
        is_mintable: True,
        trend_score: trend_score,
        trend_category: trend_category
    })
    
    # Customize based on category
    if trend_category == "meme":
        config.burn_rate = 200  # 2% burn rate for memes
        config.tax_rate = 300   # 3% tax for memes
        config.max_supply = initial_supply * 10  # Higher max supply for memes
    elif trend_category == "defi":
        config.burn_rate = 50   # 0.5% burn rate for DeFi
        config.tax_rate = 100   # 1% tax for DeFi
    elif trend_category == "nft":
        config.burn_rate = 150  # 1.5% burn rate for NFT
        config.tax_rate = 250   # 2.5% tax for NFT
    
    # Create the token with the configuration
    return self.create_token(config)

@view
@external
def get_token_by_index(index: uint256) -> address:
    """
    @notice Get a token address by its index
    @param index Index of the token
    @return Address of the token
    """
    assert index < self.token_count, "Invalid index"
    return self.tokens[index]

@view
@external
def get_tokens_by_category(category: String[32]) -> DynArray[address, 100]:
    """
    @notice Get all tokens of a specific category
    @param category Category name
    @return Array of token addresses for the category
    """
    return self.category_tokens[category]

@view
@external
def get_all_tokens() -> DynArray[address, 1000]:
    """
    @notice Get all tokens created by this factory
    @return Array of all token addresses
    """
    return self.tokens_created

@view
@external
def get_token_config(token_address: address) -> TokenConfig:
    """
    @notice Get the configuration details for a token
    @param token_address Address of the token
    @return Token configuration struct
    """
    return self.token_details[token_address]

@view
@external
def get_token_creator(token_address: address) -> address:
    """
    @notice Get the creator of a token
    @param token_address Address of the token
    @return Address of the creator
    """
    return self.token_creators[token_address]

@external
def set_creation_fee(new_fee: uint256):
    """
    @notice Set the fee required to create a new token
    @param new_fee New fee amount in wei
    """
    assert msg.sender == self.owner, "Only owner can set fee"
    self.creation_fee = new_fee

@external
def set_treasury(new_treasury: address):
    """
    @notice Set the treasury address where fees are sent
    @param new_treasury New treasury address
    """
    assert msg.sender == self.owner, "Only owner can set treasury"
    assert new_treasury != empty(address), "Invalid address"
    self.treasury = new_treasury

@external
def set_token_template(new_template: address):
    """
    @notice Update the token template address
    @param new_template New template address
    """
    assert msg.sender == self.owner, "Only owner can set template"
    assert new_template != empty(address), "Invalid address"
    self.token_template = new_template

@external
def pause(pause_state: bool):
    """
    @notice Pause or unpause the contract
    @param pause_state True to pause, False to unpause
    """
    assert msg.sender == self.owner, "Only owner can pause/unpause"
    self.is_paused = pause_state

@external
def transfer_ownership(new_owner: address):
    """
    @notice Transfer ownership of the contract
    @param new_owner New owner address
    """
    assert msg.sender == self.owner, "Only owner can transfer ownership"
    assert new_owner != empty(address), "Invalid address"
    self.owner = new_owner

@external
def withdraw_fees():
    """
    @notice Withdraw all fees to the treasury
    """
    assert msg.sender == self.owner, "Only owner can withdraw"
    send(self.treasury, self.balance)

@external
@payable
def __default__():
    """
    @notice Fallback function to accept ETH
    """
    pass

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
