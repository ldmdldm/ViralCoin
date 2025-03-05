# @version ^0.3.7

"""
@title ViralCoin ERC-20 Token Template
@author ViralCoin Team
@notice A template for creating ERC-20 tokens with burning and minting capabilities
@dev Implementation of ERC-20 standard with added functionality for trend-based tokens
"""

from vyper.interfaces import ERC20

implements: ERC20

# Events
event Transfer:
    sender: indexed(address)
    receiver: indexed(address)
    value: uint256

event Approval:
    owner: indexed(address)
    spender: indexed(address)
    value: uint256

event Burn:
    burner: indexed(address)
    value: uint256

event Mint:
    minter: indexed(address)
    receiver: indexed(address)
    value: uint256

# Token Information
name: public(String[64])
symbol: public(String[32])
decimals: public(uint8)

# Token State
totalSupply: public(uint256)
balanceOf: public(HashMap[address, uint256])
allowance: public(HashMap[address, HashMap[address, uint256]])

# Access Control
owner: public(address)
is_minter: public(HashMap[address, bool])

# Token Configuration
max_supply: public(uint256)
burn_rate: public(uint256)  # In basis points (1 = 0.01%)
tax_rate: public(uint256)   # In basis points (1 = 0.01%)
is_mintable: public(bool)

# Trend Information
trend_score: public(uint256)
trend_category: public(String[32])  # "meme", "defi", "gaming", "social", etc.
creation_timestamp: public(uint256)

# Treasury
treasury_address: public(address)
treasury_balance: public(uint256)

# Pausing
is_paused: public(bool)

@external
def __init__(
    _name: String[64],
    _symbol: String[32],
    _initial_supply: uint256,
    _decimals: uint8,
    _max_supply: uint256,
    _burn_rate: uint256,
    _tax_rate: uint256,
    _is_mintable: bool,
    _trend_score: uint256,
    _trend_category: String[32],
    _treasury: address = ZERO_ADDRESS
):
    """
    @notice Initialize the token with basic information
    @param _name Token name
    @param _symbol Token symbol
    @param _initial_supply Initial token supply (in smallest units)
    @param _decimals Number of decimals for the token
    @param _max_supply Maximum token supply
    @param _burn_rate Burn rate in basis points (1 = 0.01%)
    @param _tax_rate Tax rate in basis points (1 = 0.01%)
    @param _is_mintable Whether the token can be minted after creation
    @param _trend_score Score of the trend (0-100)
    @param _trend_category Category of the trend
    @param _treasury Address of the treasury (defaults to owner)
    """
    self.name = _name
    self.symbol = _symbol
    self.decimals = _decimals
    self.max_supply = _max_supply
    self.burn_rate = _burn_rate
    self.tax_rate = _tax_rate
    self.is_mintable = _is_mintable
    self.trend_score = _trend_score
    self.trend_category = _trend_category
    self.creation_timestamp = block.timestamp
    
    self.owner = msg.sender
    self.is_minter[msg.sender] = True
    self.is_paused = False
    
    # Set treasury address (default to owner if not provided)
    self.treasury_address = _treasury if _treasury != ZERO_ADDRESS else msg.sender
    
    # Mint initial supply to the owner
    if _initial_supply > 0:
        self.totalSupply = _initial_supply
        self.balanceOf[msg.sender] = _initial_supply
        log Transfer(ZERO_ADDRESS, msg.sender, _initial_supply)

@external
def transfer(to: address, amount: uint256) -> bool:
    """
    @notice Transfer tokens to a specified address
    @param to The address to transfer to
    @param amount The amount to be transferred
    @return Success boolean
    """
    assert not self.is_paused, "Token transfers are paused"
    assert to != ZERO_ADDRESS, "Cannot transfer to zero address"
    assert amount > 0, "Transfer amount must be greater than zero"
    assert self.balanceOf[msg.sender] >= amount, "Insufficient balance"
    
    # Calculate tax and burn amounts
    tax_amount: uint256 = amount * self.tax_rate / 10000
    burn_amount: uint256 = amount * self.burn_rate / 10000
    transfer_amount: uint256 = amount - (tax_amount + burn_amount)
    
    # Process the transfer
    self.balanceOf[msg.sender] -= amount
    
    # Add the transfer amount to the recipient
    self.balanceOf[to] += transfer_amount
    
    # Process tax (send to treasury)
    if tax_amount > 0:
        self.balanceOf[self.treasury_address] += tax_amount
        self.treasury_balance += tax_amount
        log Transfer(msg.sender, self.treasury_address, tax_amount)
    
    # Process burn (reduce total supply)
    if burn_amount > 0:
        self.totalSupply -= burn_amount
        log Burn(msg.sender, burn_amount)
    
    log Transfer(msg.sender, to, transfer_amount)
    return True

@external
def transferFrom(sender: address, recipient: address, amount: uint256) -> bool:
    """
    @notice Transfer tokens from one address to another using allowance
    @param sender The address to transfer from
    @param recipient The address to transfer to
    @param amount The amount to be transferred
    @return Success boolean
    """
    assert not self.is_paused, "Token transfers are paused"
    assert sender != ZERO_ADDRESS, "Cannot transfer from zero address"
    assert recipient != ZERO_ADDRESS, "Cannot transfer to zero address"
    assert amount > 0, "Transfer amount must be greater than zero"
    assert self.balanceOf[sender] >= amount, "Insufficient balance"
    assert self.allowance[sender][msg.sender] >= amount, "Insufficient allowance"
    
    # Calculate tax and burn amounts
    tax_amount: uint256 = amount * self.tax_rate / 10000
    burn_amount: uint256 = amount * self.burn_rate / 10000
    transfer_amount: uint256 = amount - (tax_amount + burn_amount)
    
    # Update allowance
    self.allowance[sender][msg.sender] -= amount
    
    # Process the transfer
    self.balanceOf[sender] -= amount
    
    # Add the transfer amount to the recipient
    self.balanceOf[recipient] += transfer_amount
    
    # Process tax (send to treasury)
    if tax_amount > 0:
        self.balanceOf[self.treasury_address] += tax_amount
        self.treasury_balance += tax_amount
        log Transfer(sender, self.treasury_address, tax_amount)
    
    # Process burn (reduce total supply)
    if burn_amount > 0:
        self.totalSupply -= burn_amount
        log Burn(sender, burn_amount)
    
    log Transfer(sender, recipient, transfer_amount)
    return True

@external
def approve(spender: address, amount: uint256) -> bool:
    """
    @notice Approve the passed address to spend the specified amount of tokens
    @param spender The address which will spend the funds
    @param amount The amount of tokens to be spent
    @return Success boolean
    """
    assert not self.is_paused, "Token approvals are paused"
    assert spender != ZERO_ADDRESS, "Cannot approve zero address"
    
    self.allowance[msg.sender][spender] = amount
    log Approval(msg.sender, spender, amount)
    return True

@external
def increaseAllowance(spender: address, added_value: uint256) -> bool:
    """
    @notice Increase the allowance granted to spender
    @param spender The address which will spend the funds
    @param added_value The amount of tokens to increase the allowance by
    @return Success boolean
    """
    assert not self.is_paused, "Token approvals are paused"
    assert spender != ZERO_ADDRESS, "Cannot approve zero address"
    
    self.allowance[msg.sender][spender] += added_value
    log Approval(msg.sender, spender, self.allowance[msg.sender][spender])
    return True

@external
def decreaseAllowance(spender: address, subtracted_value: uint256) -> bool:
    """
    @notice Decrease the allowance granted to spender
    @param spender The address which will spend the funds
    @param subtracted_value The amount of tokens to decrease the allowance by
    @return Success boolean
    """
    assert not self.is_paused, "Token approvals are paused"
    assert spender != ZERO_ADDRESS, "Cannot approve zero address"
    assert self.allowance[msg.sender][spender] >= subtracted_value, "Decreased allowance below zero"
    
    self.allowance[msg.sender][spender] -= subtracted_value
    log Approval(msg.sender, spender, self.allowance[msg.sender][spender])
    return True

@external
def mint(recipient: address, amount: uint256) -> bool:
    """
    @notice Mint tokens to the recipient address
    @param recipient The address that will receive the minted tokens
    @param amount The amount of tokens to mint
    @return Success boolean
    """
    assert self.is_mintable, "Token is not mintable"
    assert self.is_minter[msg.sender], "Caller is not a minter"
    assert recipient != ZERO_ADDRESS, "Cannot mint to zero address"
    assert self.totalSupply + amount <= self.max_supply, "Exceeds maximum supply"
    
    self.totalSupply += amount
    self.balanceOf[recipient] += amount
    
    log Mint(msg.sender, recipient, amount)
    log Transfer(ZERO_ADDRESS, recipient, amount)
    return True

@external
def burn(amount: uint256) -> bool:
    """
    @notice Burn tokens from caller's address
    @param amount The amount of tokens to burn
    @return Success boolean
    """
    assert amount > 0, "Burn amount must be greater than zero"
    assert self.balanceOf[msg.sender] >= amount, "Insufficient balance"
    
    self.balanceOf[msg.sender] -= amount
    self.totalSupply -= amount
    
    log Burn(msg.sender, amount)
    log Transfer(msg.sender, ZERO_ADDRESS, amount)
    return True

@external
def add_minter(minter: address) -> bool:
    """
    @notice Add a new minter
    @param minter The address to add as a minter
    @return Success boolean
    """
    assert msg.sender == self.owner, "Only owner can add minters"
    assert minter != ZERO_ADDRESS, "Cannot add zero address as minter"
    
    self.is_minter[minter] = True
    return True

@external
def remove_minter(minter: address) -> bool:
    """
    @notice Remove a minter
    @param minter The address to remove as a minter
    @return Success boolean
    """
    assert msg.sender == self.owner, "Only owner can remove minters"
    
    self.is_minter[minter] = False
    return True

@external
def set_treasury(new_treasury: address) -> bool:
    """
    @notice Update the treasury address
    @param new_treasury The new treasury address
    @return Success boolean
    """
    assert msg.sender == self.owner, "Only owner can update treasury"
    assert new_treasury != ZERO_ADDRESS, "Cannot set zero address as treasury"
    
    self.treasury_address = new_treasury
    return True

@external
def set_burn_rate(new_rate: uint256) -> bool:
    """
    @notice Update the burn rate
    @param new_rate The new burn rate in basis points (1 = 0.01%)
    @return Success boolean
    """
    assert msg.sender == self.owner, "Only owner can update burn rate"
    assert new_rate <= 1000, "Burn rate cannot exceed 10%"
    
    self.burn_rate = new_rate
    return True

@external
def set_tax_rate(new_rate: uint256) -> bool:
    """
    @notice Update the tax rate
    @param new_rate The new tax rate in basis points (1 = 0.01%)
    @return Success boolean
    """
    assert msg.sender == self.owner, "Only owner can update tax rate"
    assert new_rate <= 1000, "Tax rate cannot exceed 10%"
    
    self.tax_rate = new_rate
    return True

@external
def pause() -> bool:
    """
    @notice Pause token transfers
    @return Success boolean
    """
    assert msg.sender == self.owner, "Only owner can pause"
    assert not self.is_paused, "Token is already paused"
    
    self.is_paused = True
    return True

@external
def unpause() -> bool:
    """
    @notice Unpause token transfers
    @return Success boolean
    """
    assert msg.sender == self.owner, "Only owner can unpause"
    assert self.is_paused, "Token is not paused"
    
    self.is_paused = False
    return True

@external
def transfer_ownership(new_owner: address) -> bool:
    """
    @notice Transfer ownership of the contract
    @param new_owner The address of the new owner
    @return Success boolean
    """
    assert msg.sender == self.owner, "Only owner can transfer ownership"
    assert new_owner != ZERO_ADDRESS, "Cannot transfer to zero address"
    
    self.owner = new_owner
    return True

@external
@view
def get_token_info() -> (String[64], String[32], uint256, uint8, uint256, uint256, uint256, bool, uint256, String[32], uint256):
    """
    @notice Get comprehensive token information
    @return Tuple containing all token information
    """
    return (
        self.name,
        self.symbol,
        self.totalSupply,
        self.decimals,
        self.max_supply,
        self.burn_rate,
        self.tax_rate,
        self.is_mintable,
        self.trend_score,
        self.trend_category,
        self.creation_timestamp
    )

@external
@view
def get_treasury_info() -> (address, uint256):
    """
    @notice Get treasury information
    @return Treasury address and balance
    """
    return (self.treasury_address, self.treasury_balance)

# @version ^0.3.7
"""
@title ViralCoin Token Template
@author ViralCoin Team
@notice ERC20 implementation for automatically generated memecoins
@dev Implements ERC20 standard with additional features for viral tokens
"""

from vyper.interfaces import ERC20

implements: ERC20

# Events
event Transfer:
    sender: indexed(address)
    receiver: indexed(address)
    value: uint256

event Approval:
    owner: indexed(address)
    spender: indexed(address)
    value: uint256

# State Variables
name: public(String[64])
symbol: public(String[32])
decimals: public(uint8)

balanceOf: public(HashMap[address, uint256])
allowance: public(HashMap[address, HashMap[address, uint256]])
totalSupply: public(uint256)

# Admin/configuration variables
owner: public(address)
marketingWallet: public(address)
liquidityWallet: public(address)

# Fee structure (in basis points, 100 = 1%)
marketingFee: public(uint256)
liquidityFee: public(uint256)
burnFee: public(uint256)

# Trading control
tradingEnabled: public(bool)

# Constants
BASIS_POINTS: constant(uint256) = 10000
MAX_FEE: constant(uint256) = 2000  # 20% max combined fee

@external
def __init__(
    _name: String[64],
    _symbol: String[32],
    _initial_supply: uint256,
    _marketing_wallet: address,
    _liquidity_wallet: address,
    _marketing_fee: uint256,
    _liquidity_fee: uint256,
    _burn_fee: uint256
):
    """
    @notice Contract constructor
    @param _name Token name
    @param _symbol Token symbol
    @param _initial_supply Initial token supply (will be minted to msg.sender)
    @param _marketing_wallet Address to receive marketing fees
    @param _liquidity_wallet Address to receive liquidity fees
    @param _marketing_fee Marketing fee in basis points
    @param _liquidity_fee Liquidity fee in basis points
    @param _burn_fee Burn fee in basis points
    """
    self.name = _name
    self.symbol = _symbol
    self.decimals = 18
    
    # Validate fee parameters
    assert _marketing_fee + _liquidity_fee + _burn_fee <= MAX_FEE, "Fees too high"
    
    # Set fees
    self.marketingFee = _marketing_fee
    self.liquidityFee = _liquidity_fee
    self.burnFee = _burn_fee
    
    # Set wallets
    self.owner = msg.sender
    self.marketingWallet = _marketing_wallet
    self.liquidityWallet = _liquidity_wallet
    
    # Mint initial supply to creator
    self.totalSupply = _initial_supply
    self.balanceOf[msg.sender] = _initial_supply
    
    # Trading disabled by default
    self.tradingEnabled = False
    
    # Emit transfer event for initial supply
    log Transfer(ZERO_ADDRESS, msg.sender, _initial_supply)

@external
def transfer(_to: address, _value: uint256) -> bool:
    """
    @notice Transfer tokens to a specified address
    @param _to The address to transfer to
    @param _value The amount to be transferred
    @return Success boolean
    """
    return self._transfer(msg.sender, _to, _value)

@external
def transferFrom(_from: address, _to: address, _value: uint256) -> bool:
    """
    @notice Transfer tokens from one address to another
    @param _from The address which you want to send tokens from
    @param _to The address which you want to transfer to
    @param _value The amount of tokens to be transferred
    @return Success boolean
    """
    self.allowance[_from][msg.sender] -= _value
    return self._transfer(_from, _to, _value)

@internal
def _transfer(_from: address, _to: address, _value: uint256) -> bool:
    """
    @dev Internal function to handle transfers with fees
    @param _from Sender address
    @param _to Recipient address
    @param _value Amount to transfer
    @return Success boolean
    """
    assert _to != ZERO_ADDRESS, "Zero address"
    assert self.balanceOf[_from] >= _value, "Insufficient balance"
    
    # Check if trading is enabled for non-owner transfers
    if _from != self.owner and _to != self.owner:
        assert self.tradingEnabled, "Trading not enabled"
    
    # Calculate fees (if applicable)
    marketingAmount: uint256 = 0
    liquidityAmount: uint256 = 0
    burnAmount: uint256 = 0
    
    # Apply fees only for non-owner transactions
    if _from != self.owner and _to != self.owner:
        marketingAmount = _value * self.marketingFee / BASIS_POINTS
        liquidityAmount = _value * self.liquidityFee / BASIS_POINTS
        burnAmount = _value * self.burnFee / BASIS_POINTS
    
    # Calculate amount after fees
    transferAmount: uint256 = _value - marketingAmount - liquidityAmount - burnAmount
    
    # Update balances
    self.balanceOf[_from] -= _value
    self.balanceOf[_to] += transferAmount
    
    # Handle fees
    if marketingAmount > 0:
        self.balanceOf[self.marketingWallet] += marketingAmount
        log Transfer(_from, self.marketingWallet, marketingAmount)
        
    if liquidityAmount > 0:
        self.balanceOf[self.liquidityWallet] += liquidityAmount
        log Transfer(_from, self.liquidityWallet, liquidityAmount)
        
    if burnAmount > 0:
        self.totalSupply -= burnAmount
        log Transfer(_from, ZERO_ADDRESS, burnAmount)
    
    # Emit transfer event
    log Transfer(_from, _to, transferAmount)
    
    return True

@external
def approve(_spender: address, _value: uint256) -> bool:
    """
    @notice Approve the passed address to spend the specified amount of tokens
    @param _spender The address which will spend the funds
    @param _value The amount of tokens to be spent
    @return Success boolean
    """
    assert _spender != ZERO_ADDRESS, "Zero address"
    
    self.allowance[msg.sender][_spender] = _value
    log Approval(msg.sender, _spender, _value)
    
    return True

@external
def enableTrading() -> bool:
    """
    @notice Enable trading for everyone
    @dev Can only be called by owner and cannot be reversed
    @return Success boolean
    """
    assert msg.sender == self.owner, "Only owner"
    self.tradingEnabled = True
    return True

@external
def updateFees(_marketing_fee: uint256, _liquidity_fee: uint256, _burn_fee: uint256) -> bool:
    """
    @notice Update fee structure
    @dev Can only be called by owner
    @param _marketing_fee New marketing fee
    @param _liquidity_fee New liquidity fee
    @param _burn_fee New burn fee
    @return Success boolean
    """
    assert msg.sender == self.owner, "Only owner"
    assert _marketing_fee + _liquidity_fee + _burn_fee <= MAX_FEE, "Fees too high"
    
    self.marketingFee = _marketing_fee
    self.liquidityFee = _liquidity_fee
    self.burnFee = _burn_fee
    
    return True

@external
def updateWallets(_marketing_wallet: address, _liquidity_wallet: address) -> bool:
    """
    @notice Update fee recipient wallets
    @dev Can only be called by owner
    @param _marketing_wallet New marketing wallet
    @param _liquidity_wallet New liquidity wallet
    @return Success boolean
    """
    assert msg.sender == self.owner, "Only owner"
    assert _marketing_wallet != ZERO_ADDRESS, "Zero address"
    assert _liquidity_wallet != ZERO_ADDRESS, "Zero address"
    
    self.marketingWallet = _marketing_wallet
    self.liquidityWallet = _liquidity_wallet
    
    return True

@external
@view
def getFeeInfo() -> (uint256, uint256, uint256):
    """
    @notice Get current fee structure
    @return Tuple of (marketingFee, liquidityFee, burnFee)
    """
    return (self.marketingFee, self.liquidityFee, self.burnFee)

