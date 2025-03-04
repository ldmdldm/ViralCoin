# @version ^0.3.7
"""
@title Trend Token Base Contract
@author Your Name
@notice Base ERC20 implementation for trend-based tokens
@dev Can be extended for different trend categories
"""

from vyper.interfaces import ERC20

# Quickswap interfaces
interface IUniswapV2Factory:
    def createPair(tokenA: address, tokenB: address) -> address: nonpayable
    
interface IUniswapV2Router02:
    def factory() -> address: view
    def WETH() -> address: view
    def addLiquidityETH(token: address, amountTokenDesired: uint256, amountTokenMin: uint256, amountETHMin: uint256, to: address, deadline: uint256) -> (uint256, uint256, uint256): payable
    def swapExactTokensForETHSupportingFeeOnTransferTokens(amountIn: uint256, amountOutMin: uint256, path: DynArray[address, 3], to: address, deadline: uint256): nonpayable
    def getAmountsOut(amountIn: uint256, path: DynArray[address, 3]) -> DynArray[uint256, 3]: view

# Events
event Transfer:
    sender: indexed(address)
    receiver: indexed(address)
    amount: uint256

event Approval:
    owner: indexed(address)
    spender: indexed(address)
    amount: uint256

event TokenBurned:
    burner: indexed(address)
    amount: uint256

event TokenMinted:
    receiver: indexed(address)
    amount: uint256

    event SwapAndLiquify:
        tokens_swapped: uint256
        eth_received: uint256
        tokens_into_liquidity: uint256
        
    event TaxCollected:
    from_address: indexed(address)
    to_address: indexed(address)
    tax_amount: uint256

# ERC20 storage variables
name: public(String[64])
symbol: public(String[32])
decimals: public(uint8)
totalSupply: public(uint256)
balanceOf: public(HashMap[address, uint256])
allowance: public(HashMap[address, HashMap[address, uint256]])

# Token configuration
owner: public(address)
max_supply: public(uint256)
burn_rate: public(uint256)  # Basis points (1/100 of a percent)
tax_rate: public(uint256)   # Basis points
is_mintable: public(bool)

# Trend specific data
trend_score: public(uint256)
trend_category: public(String[32])
creation_time: public(uint256)

# Treasury for collected taxes
treasury: public(address)

# Quickswap variables
quickswap_router: public(address)
quickswap_pair: public(address)

# Liquidity settings
liquidity_fee: public(uint256)              # Basis points
swap_threshold: public(uint256)             # Minimum amount before swap and add liquidity
max_tx_amount: public(uint256)              # Maximum transaction size
tokens_for_liquidity: public(uint256)       # Tokens collected for liquidity
in_swap_and_liquify: bool                   # Reentrancy guard for swap operations

# Swap settings
swap_enabled: public(bool)                  # Enable/disable swap functionality

@external
def __init__(
    _name: String[64],
    _symbol: String[32],
    _initial_supply: uint256,
    _max_supply: uint256,
    _burn_rate: uint256,
    _tax_rate: uint256,
    _is_mintable: bool,
    _trend_score: uint256,
    _trend_category: String[32],
    _treasury: address,
    _quickswap_router: address = empty(address),
    _liquidity_fee: uint256 = 200  # Default 2%
    ):
        """
        @notice Initialize the token with its configuration
        """
        self.name = _name
        self.symbol = _symbol
        self.decimals = 18
        initial_supply_with_decimals: uint256 = _initial_supply * 10 ** 18
        self.totalSupply = initial_supply_with_decimals
        self.balanceOf[msg.sender] = initial_supply_with_decimals
        
        self.owner = msg.sender
        self.max_supply = _max_supply * 10 ** 18
        self.burn_rate = _burn_rate
        self.tax_rate = _tax_rate
        self.is_mintable = _is_mintable
        self.trend_score = _trend_score
        self.trend_category = _trend_category
        self.creation_time = block.timestamp
        self.treasury = _treasury
        
        # Initialize Quickswap variables
        self.quickswap_router = _quickswap_router
        self.liquidity_fee = _liquidity_fee
        self.max_tx_amount = initial_supply_with_decimals / 100  # 1% of total supply
        self.swap_threshold = initial_supply_with_decimals / 5000  # 0.02% of total supply
        self.tokens_for_liquidity = 0
        self.in_swap_and_liquify = False
        self.swap_enabled = True
        
        # Create pair if router specified
        if _quickswap_router != empty(address):
            router: address = self.quickswap_router
            factory: address = IUniswapV2Factory(IUniswapV2Router02(router).factory()).createPair(self, IUniswapV2Router02(router).WETH())
            self.quickswap_pair = factory
    
    log Transfer(empty(address), msg.sender, initial_supply_with_decimals)

@external
def transfer(_to: address, _value: uint256) -> bool:
    """
    @notice Transfer tokens to a specified address
    @param _to The address to transfer to
    @param _value The amount to be transferred
    @return Success flag
    """
    return self._transfer(msg.sender, _to, _value)

@internal
def _swapAndLiquify() -> bool:
    """
    @dev Swap half of the tokens for ETH and add to liquidity
    """
    # Avoid recursive loop when transferring
    self.in_swap_and_liquify = True
    
    # Calculate token amounts
    tokens_to_swap: uint256 = self.tokens_for_liquidity
    half_tokens: uint256 = tokens_to_swap / 2
    other_half: uint256 = tokens_to_swap - half_tokens
    
    # Get initial ETH balance
    initial_balance: uint256 = self.balance
    
    # Create path for token -> WETH
    path: DynArray[address, 3] = [self, IUniswapV2Router02(self.quickswap_router).WETH()]
    
    # Approve router to spend tokens
    self.allowance[self][self.quickswap_router] = half_tokens
    
    # Swap tokens for ETH
    IUniswapV2Router02(self.quickswap_router).swapExactTokensForETHSupportingFeeOnTransferTokens(
        half_tokens,
        0,  # Accept any amount of ETH
        path,
        self,
        block.timestamp + 300  # 5 minute deadline
    )
    
    # Get ETH received from swap
    eth_received: uint256 = self.balance - initial_balance
    
    # Add liquidity
    if other_half > 0 and eth_received > 0:
        self.allowance[self][self.quickswap_router] = other_half
        IUniswapV2Router02(self.quickswap_router).addLiquidityETH(
            self,
            other_half,
            0,  # Accept any amount of tokens
            0,  # Accept any amount of ETH
            self.owner,
            block.timestamp + 300  # 5 minute deadline
        )
    
    # Reset tokens for liquidity
    self.tokens_for_liquidity = 0
    
    # Emit event
    log SwapAndLiquify(half_tokens, eth_received, other_half)
    
    # Reset swap flag
    self.in_swap_and_liquify = False
    
    return True

@internal
def _transfer(_from: address, _to: address, _value: uint256) -> bool:
    """
    @dev Internal transfer function with tax and burn logic
    """
    assert _to != empty(address), "Invalid recipient"
    assert _value <= self.balanceOf[_from], "Insufficient balance"
    
    # Check if transaction exceeds max transaction amount
    # Owner and contract itself are exempt from the limit
    if _from != self.owner and _to != self.owner and _from != self and _to != self:
        assert _value <= self.max_tx_amount, "Transfer amount exceeds the max tx amount"
    
    # Check if we should swap and liquify
    # Skip if:
    # 1. swap is disabled
    # 2. we're already in a swap
    # 3. sender is the pair (don't liquify on buy)
    # 4. sender is the owner (allow owner to transfer without triggering liquify)
    # 5. not enough tokens collected for liquidity
    should_swap: bool = (
        self.swap_enabled and
        not self.in_swap_and_liquify and
        _from != self.quickswap_pair and
        _from != self.owner and
        self.tokens_for_liquidity >= self.swap_threshold
    )
    
    # Swap and liquify if conditions are met
    if should_swap and self.quickswap_router != empty(address):
        self._swapAndLiquify()
    
    # Calculate tax, burn, and liquidity fee amounts
    tax_amount: uint256 = _value * self.tax_rate / 10000
    burn_amount: uint256 = _value * self.burn_rate / 10000
    liquidity_amount: uint256 = 0
    
    # Only apply liquidity fee for non-excluded addresses and if router is set
    if self.quickswap_router != empty(address) and _from != self.owner and _to != self.owner:
        liquidity_amount = _value * self.liquidity_fee / 10000
    
    # Calculate final transfer amount
    transfer_amount: uint256 = _value - tax_amount - burn_amount - liquidity_amount
    
    # Update balances
    self.balanceOf[_from] -= _value
    self.balanceOf[_to] += transfer_amount
    
    # Handle tax
    if tax_amount > 0:
        self.balanceOf[self.treasury] += tax_amount
        log TaxCollected(_from, _to, tax_amount)
    
    # Handle burn
    if burn_amount > 0:
        self.totalSupply -= burn_amount
        log TokenBurned(_from, burn_amount)
    
    # Handle liquidity fee
    if liquidity_amount > 0:
        self.balanceOf[self] += liquidity_amount
        self.tokens_for_liquidity += liquidity_amount
    
    log Transfer(_from, _to, transfer_amount)
    return True

@external
def transferFrom(_from: address, _to: address, _value: uint256) -> bool:
    """
    @notice Transfer tokens from one address to another
    @param _from The address which you want to send tokens from
    @param _to The address which you want to transfer to
    @param _value The amount of tokens to be transferred
    @return Success flag
    """
    assert _value <= self.allowance[_from][msg.sender], "Insufficient allowance"
    self.allowance[_from][msg.sender] -= _value
    return self._transfer(_from, _to, _value)

@external
def approve(_spender: address, _value: uint256) -> bool:
    """
    @notice Approve the passed address to spend the specified amount of tokens
    @param _spender The address which will spend the funds
    @param _value The amount of tokens to be spent
    @return Success flag
    """
    self.allowance[msg.sender][_spender] = _value
    log Approval(msg.sender, _spender, _value)
    return True

@external
def mint(_to: address, _value: uint256) -> bool:
    """
    @notice Mint new tokens (if allowed)
    @param _to Recipient of the minted tokens
    @param _value Amount to mint
    @return Success flag
    """
    assert msg.sender == self.owner, "Only owner"
    assert self.is_mintable, "Minting disabled"
    assert self.totalSupply + _value <= self.max_supply, "Exceeds max supply"
    
    self.totalSupply += _value
    self.balanceOf[_to] += _value
    
    log TokenMinted(_to, _value)
    log Transfer(empty(address), _to, _value)
    return True

@external
def burn(_value: uint256) -> bool:
    """
    @notice Burn tokens
    @param _value Amount to burn
    @return Success flag
    """
    assert _value <= self.balanceOf[msg.sender], "Insufficient balance"
    
    self.balanceOf[msg.sender] -= _value
    self.totalSupply -= _value
    
    log TokenBurned(msg.sender, _value)
    log Transfer(msg.sender, empty(address), _value)
    return True

@external
def update_trend_score(_score: uint256):
    """
    @notice Update the trend score (only owner)
    @param _score New trend score
    """
    assert msg.sender == self.owner, "Only owner"
    self.trend_score = _score

@external
def set_tax_rate(_rate: uint256):
    """
    @notice Update the tax rate (only owner)
    @param _rate New tax rate in basis points
    """
    assert msg.sender == self.owner, "Only owner"
    assert _rate <= 1000, "Max 10%"  # Limit to 10%
    self.tax_rate = _rate

@external
def set_burn_rate(_rate: uint256):
    """
    @notice Update the burn rate (only owner)
    @param _rate New burn rate in basis points
    """
    assert msg.sender == self.owner, "Only owner"
    assert _rate <= 1000, "Max 10%"  # Limit to 10%
    self.burn_rate = _rate

@external
def setQuickswapRouter(_router: address):
    """
    @notice Set the Quickswap router address
    @param _router The router address
    """
    assert msg.sender == self.owner, "Only owner"
    self.quickswap_router = _router
    
    # Create pair if not already created
    if self.quickswap_pair == empty(address) and _router != empty(address):
        factory: address = IUniswapV2Factory(IUniswapV2Router02(_router).factory()).createPair(
            self, 
            IUniswapV2Router02(_router).WETH()
        )
        self.quickswap_pair = factory

@external
def setLiquidityFee(_fee: uint256):
    """
    @notice Update the liquidity fee
    @param _fee New liquidity fee in basis points
    """
    assert msg.sender == self.owner, "Only owner"
    assert _fee <= 500, "Max 5%"  # Limit to 5%
    self.liquidity_fee = _fee

@external
def setSwapThreshold(_threshold: uint256):
    """
    @notice Update the swap threshold
    @param _threshold New threshold amount
    """
    assert msg.sender == self.owner, "Only owner"
    self.swap_threshold = _threshold

@external
def setMaxTxAmount(_amount: uint256):
    """
    @notice Update the maximum transaction amount
    @param _amount New max tx amount
    """
    assert msg.sender == self.owner, "Only owner"
    assert _amount >= self.totalSupply / 1000, "Cannot set below 0.1% of total supply"
    self.max_tx_amount = _amount

@external
def setSwapEnabled(_enabled: bool):
    """
    @notice Enable or disable swap functionality
    @param _enabled Whether to enable swaps
    """
    assert msg.sender == self.owner, "Only owner"
    self.swap_enabled = _enabled

@external
@payable
def rescueETH():
    """
    @notice Rescue ETH accidentally sent to the contract
    """
    assert msg.sender == self.owner, "Only owner"
    send(self.owner, self.balance)

@external
def rescueTokens(_token: address):
    """
    @notice Rescue tokens accidentally sent to the contract
    @param _token Token to rescue
    """
    assert msg.sender == self.owner, "Only owner"
    assert _token != self, "Cannot rescue self"
    
    token_balance: uint256 = ERC20(_token).balanceOf(self)
    ERC20(_token).transfer(self.owner, token_balance)
