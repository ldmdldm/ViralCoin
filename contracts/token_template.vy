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

