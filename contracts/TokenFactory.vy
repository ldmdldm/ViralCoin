# @version 0.3.7

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
    name: String[64]
    symbol: String[32]
    initial_supply: uint256
    creator: indexed(address)
    timestamp: uint256

# Contract Variables
token_template: public(address)
owner: public(address)
token_count: public(uint256)
is_paused: public(bool)

# Mapping to track created tokens
tokens: public(HashMap[uint256, address])
token_details: public(HashMap[address, HashMap[String[10], String[64]]])

# Fee for token creation (in wei)
creation_fee: public(uint256)

@external
def __init__(token_template_address: address):
    """
    @notice Initialize the factory with a token template
    @param token_template_address Address of the token implementation to clone
    """
    self.token_template = token_template_address
    self.owner = msg.sender
    self.token_count = 0
    self.is_paused = False
    self.creation_fee = 10**17  # 0.1 ETH default fee

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
    
    # Increment token count
    self.token_count += 1
    
    # Emit creation event
    log TokenCreated(
        token_address,
        name,
        symbol,
        initial_supply,
        msg.sender,
        block.timestamp
    )
    
    return token_address

@external
def set_creation_fee(new_fee: uint256):
    """
    @notice Set the fee required to create a new token
    @param new_fee New fee amount in wei
    """
    assert msg.sender == self.owner, "Only owner"
    self.creation_fee = new_fee

@external
def withdraw_fees():
    """
    @notice Withdraw accumulated fees to the owner
    """
    assert msg.sender == self.owner, "Only owner"
    send(self.owner, self.balance)

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
    assert new_owner != ZERO_ADDRESS, "Zero address not allowed"
    self.owner = new_owner

@external
def update_token_template(new_template: address):
    """
    @notice Update the token template address
    @param new_template Address of the new template
    """
    assert msg.sender == self.owner, "Only owner"
    assert new_template != ZERO_ADDRESS, "Zero address not allowed"
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
    result: DynArray[address, 100] = []
    
    for i in range(min(self.token_count, 100)):
        result.append(self.tokens[i])
        
    return result

