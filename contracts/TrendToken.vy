# @version ^0.3.9

"""
@title TrendToken
@author ViralCoin Team
@notice ERC-20 token with trend-specific features
@dev Extends standard ERC-20 with trend tracking, lifecycle management, and viral tokenomics
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

event TrendScoreUpdated:
    old_score: uint256
    new_score: uint256
    timestamp: uint256

event TrendLifecycleChanged:
    old_phase: String[20]
    new_phase: String[20]
    timestamp: uint256

event TaxRateChanged:
    old_rate: uint256
    new_rate: uint256
    timestamp: uint256

event TokensBurned:
    amount: uint256
    reason: String[50]
    timestamp: uint256

event TokensMinted:
    receiver: indexed(address)
    amount: uint256
    reason: String[50]
    timestamp: uint256

event LiquidityAdded:
    amount_tokens: uint256
    amount_eth: uint256
    timestamp: uint256

# Token Data
name: public(String[64])
symbol: public(String[32])
decimals: public(uint8)

# ERC-20 Data
totalSupply: public(uint256)
balanceOf: public(HashMap[address, uint256])
allowance: public(HashMap[address, HashMap[address, uint256]])

# Ownership
owner: public(address)

# Trend Tracking
trend_score: public(uint256)  # 0-100, represents viral potential
trend_category: public(String[32])  # e.g., "meme", "defi", "nft", "ai"
trend_phase: public(String[20])  # "emerging", "viral", "stable", "declining"
trend_start_time: public(uint256)
last_score_update: public(uint256)

# Tokenomics Configuration
tax_rate: public(uint256)  # basis points (1/100 of 1%)
burn_rate: public(uint256)  # basis points
is_mintable: public(bool)
max_supply: public(uint256)

# Protocol addresses
liquidity_pool: public(address)
treasury: public(address)

# Constants
MAX_TAX_RATE: constant(uint256) = 1000  # 10% max tax in basis points
MAX_BURN_RATE: constant(uint256) = 2000  # 20% max burn in basis points
MIN_LIQUIDITY_LOCK_TIME: constant(uint256) = 2592000  # 30 days in seconds
LIFECYCLE_PERIODS: constant(uint256) = 4  # Number of lifecycle phases
EMERGING_BONUS: constant(uint256) = 500  # 5% bonus for early holders
VIRAL_BONUS: constant(uint256) = 300  # 3% bonus for viral phase
DECLINING_PENALTY: constant(uint256) = 200  # 2% extra tax for declining phase

# Variables
liquidity_locked_until: public(uint256)
is_trading_enabled: public(bool)
initial_holders: public(DynArray[address, 100])
viral_milestone_reached: public(bool)

@external
def __init__(
    _name: String[64],
    _symbol: String[32],
    _decimals: uint8,
    _initial_supply: uint256,
    _max_supply: uint256,
    _owner: address,
    _trend_score: uint256,
    _trend_category: String[32],
    _tax_rate: uint256,
    _burn_rate: uint256,
    _is_mintable: bool
):
    """
    @notice Initialize the token with trend parameters
    @param _name Token name
    @param _symbol Token symbol
    @param _decimals Number of decimal places
    @param _initial_supply Initial token supply (in smallest units)
    @param _max_supply Maximum possible supply
    @param _owner Address of the token owner
    @param _trend_score Initial trend score (0-100)
    @param _trend_category Category of the trend
    @param _tax_rate Transaction tax rate in basis points
    @param _burn_rate Burn rate in basis points
    @param _is_mintable Whether the token can be minted after initial creation
    """
    self.name = _name
    self.symbol = _symbol
    self.decimals = _decimals
    self.totalSupply = _initial_supply
    self.max_supply = _max_supply
    self.balanceOf[_owner] = _initial_supply
    self.owner = _owner
    
    # Set trend parameters
    assert _trend_score <= 100, "Trend score must be <= 100"
    self.trend_score = _trend_score
    self.trend_category = _trend_category
    self.trend_phase = "emerging"
    self.trend_start_time = block.timestamp
    self.last_score_update = block.timestamp
    
    # Set tokenomics parameters
    assert _tax_rate <= MAX_TAX_RATE, "Tax rate too high"
    assert _burn_rate <= MAX_BURN_RATE, "Burn rate too high"
    self.tax_rate = _tax_rate
    self.burn_rate = _burn_rate
    self.is_mintable = _is_mintable
    
    # Set protocol parameters
    self.treasury = _owner  # Initially set to owner
    self.is_trading_enabled = False
    self.liquidity_locked_until = 0
    
    # Emit transfer event for total supply
    log Transfer(empty(address), _owner, _initial_supply)
    
    # Emit trend score set event
    log TrendScoreUpdated(0, _trend_score, block.timestamp)
    
    # Emit lifecycle event
    log TrendLifecycleChanged("", "emerging", block.timestamp)

@external
def approve(_spender: address, _value: uint256) -> bool:
    """
    @notice Allow _spender to withdraw from your account, multiple times, up to the _value amount
    @param _spender Address to be approved to spend tokens
    @param _value Amount of tokens approved to spend
    @return Success boolean
    """
    self.allowance[msg.sender][_spender] = _value
    log Approval(msg.sender, _spender, _value)
    return True

@internal
def _transfer(_from: address, _to: address, _value: uint256) -> uint256:
    """
    @dev Internal transfer function with tax and burn mechanisms
    @param _from Sender address
    @param _to Receiver address
    @param _value Amount to transfer (before tax/burn)
    @return Actual amount received after taxes
    """
    assert _to != empty(address), "Cannot transfer to zero address"
    assert _value <= self.balanceOf[_from], "Insufficient balance"
    assert self.is_trading_enabled or _from == self.owner or _to == self.owner, "Trading not enabled"
    
    # Calculate taxes and burns based on trend phase
    burn_amount: uint256 = 0
    tax_amount: uint256 = 0
    effective_tax_rate: uint256 = self.tax_rate
    effective_burn_rate: uint256 = self.burn_rate
    bonus_amount: uint256 = 0
    
    if self.trend_phase == "emerging" and (_to not in self.initial_holders):
        # Early supporters get a bonus
        bonus_amount = _value * EMERGING_BONUS / 10000
        self.initial_holders.append(_to)
    elif self.trend_phase == "viral":
        # During viral phase, reduce tax to encourage transactions
        effective_tax_rate = effective_tax_rate * 8 / 10  # 20% tax reduction
        if self.viral_milestone_reached and (_to not in self.initial_holders):
            bonus_amount = _value * VIRAL_BONUS / 10000
    elif self.trend_phase == "declining":
        # During declining phase, increase tax
        effective_tax_rate = effective_tax_rate + DECLINING_PENALTY
    
    # Calculate tax and burn amounts
    if _from != self.owner and _to != self.owner:
        tax_amount = _value * effective_tax_rate / 10000
        burn_amount = _value * effective_burn_rate / 10000
    
    # Calculate net amount
    net_amount: uint256 = _value - tax_amount - burn_amount + bonus_amount
    
    # Update balances
    self.balanceOf[_from] -= _value
    self.balanceOf[_to] += net_amount
    
    # Handle tax
    if tax_amount > 0:
        self.balanceOf[self.treasury] += tax_amount
        log Transfer(_from, self.treasury, tax_amount)
    
    # Handle burn
    if burn_amount > 0:
        self.totalSupply -= burn_amount
        log TokensBurned(burn_amount, "Transaction burn", block.timestamp)
    
    # Handle bonus
    if bonus_amount > 0 and self.is_mintable:
        # Mint new tokens for the bonus if we're under max supply
        if self.totalSupply + bonus_amount <= self.max_supply:
            self.totalSupply += bonus_amount
            log TokensMinted(_to, bonus_amount, "Trend bonus", block.timestamp)
    
    # Emit transfer event
    log Transfer(_from, _to, net_amount)
    
    return net_amount

@external
def transfer(_to: address, _value: uint256) -> bool:
    """
    @notice Transfer tokens to a specified address
    @param _to The address to transfer to
    @param _value The amount to be transferred
    @return Success boolean
    """
    self._transfer(msg.sender, _to, _value)
    return True

@external
def transferFrom(_from: address, _to: address, _value: uint256) -> bool:
    """
    @notice Transfer tokens from one address to another
    @param _from The address which you want to send tokens from
    @param _to The address which you want to transfer to
    @param _value The amount of tokens to be transferred
    @return Success boolean
    """
    assert _value <= self.allowance[_from][msg.sender], "Insufficient allowance"
    
    self.allowance[_from][msg.sender] -= _value
    self._transfer(_from, _to, _value)
    return True

@external
def update_trend_score(_new_score: uint256) -> bool:
    """
    @notice Update the trend score and potentially change the lifecycle phase
    @param _new_score New trend score value (0-100)
    @return Success boolean
    """
    assert msg.sender == self.owner, "Only owner can update trend score"
    assert _new_score <= 100, "Trend score must be <= 100"
    
    old_score: uint256 = self.trend_score
    self.trend_score = _new_score
    self.last_score_update = block.timestamp
    
    # Update trend lifecycle phase based on time and score
    time_elapsed: uint256 = block.timestamp - self.trend_start_time
    lifecycle_period: uint256 = (block.timestamp - self.trend_start_time) / (7 * 24 * 60 * 60)  # Weeks since launch
    old_phase: String[20] = self.trend_phase
    
    # Determine lifecycle based on time and score
    if lifecycle_period < 1:
        if _new_score >= 80:
            # Fast-track to viral if score is very high in first week
            self.trend_phase = "viral"
            self.viral_milestone_reached = True
        else:
            self.trend_phase = "emerging"
    elif lifecycle_period < 3:
        if _new_score >= 70:
            self.trend_phase = "viral"
            self.viral_milestone_reached = True
        elif _new_score >= 40:
            self.trend_phase = "emerging"
        else:
            self.trend_phase = "declining"
    elif lifecycle_period < 8:
        if _new_score >= 60:
            self.trend_phase = "viral"
        elif _new_score >= 30:
            self.trend_phase = "stable"
        else:
            self.trend_phase = "declining"
    else:
        if _new_score >= 50:
            self.trend_phase = "stable"
        else:
            self.trend_phase = "declining"
    
    # Log events if phase changed
    if old_phase != self.trend_phase:
        log TrendLifecycleChanged(old_phase, self.trend_phase, block.timestamp)
    
    # Log trend score update
    log TrendScoreUpdated(old_score, _new_score, block.timestamp)
    
    # Adjust tokenomics based on trend phase
    if self.trend_phase == "viral" and old_phase != "viral":
        # Lower tax rate during viral phase to encourage transactions
        old_rate: uint256 = self.tax_rate
        self.tax_rate = self.tax_rate * 8 / 10  # Reduce tax by 20%
        log TaxRateChanged(old_rate, self.tax_rate, block.timestamp)
    elif self.trend_phase == "declining" and old_phase != "declining":
        # Increase burn rate in declining phase
        self.burn_rate = min(self.burn_rate * 3 / 2, MAX_BURN_RATE)  # Increase burn by 50% up to max
    
    return True

@external
def enable_trading(_liquidity_pool: address) -> bool:
    """
    @notice Enable trading for the token and set the liquidity pool address
    @param _liquidity_pool Address of the DEX liquidity pool
    @return Success boolean
    """
    assert msg.sender == self.owner, "Only owner can enable trading"
    assert not self.is_trading_enabled, "Trading already enabled"
    assert _liquidity_pool != empty(address), "Invalid liquidity pool"
    
    self.is_trading_enabled = True
    self.liquidity_pool = _liquidity_pool
    self.liquidity_locked_until = block.timestamp + MIN_LIQUIDITY_LOCK_TIME
    
    return True

@external
def add_liquidity() -> bool:
    """
    @notice Add liquidity to the DEX pool (must send ETH/MATIC with this call)
    @return Success boolean
    """
    assert msg.sender == self.owner, "Only owner can add liquidity"
    assert self.liquidity_pool != empty(address), "Liquidity pool not set"
    assert msg.value > 0, "Must send ETH/MATIC to add liquidity"
    
    token_amount: uint256 = self.balanceOf[self.owner] / 10  # 10% of available tokens
    eth_amount: uint256 = msg.value
    
    # Transfer tokens to liquidity pool
    self._transfer(self.owner, self.liquidity_pool, token_amount)
    
    # Send ETH to liquidity pool
    send(self.liquidity_pool, eth_amount)
    
    # Log liquidity addition
    log LiquidityAdded(token_amount, eth_amount, block.timestamp)
    
    return True

@external
def set_tax_rate(_new_rate: uint256) -> bool:
    """
    @notice Set a new tax rate for the token
    @param _new_rate New tax rate in basis points
    @return Success boolean
    """
    assert msg.sender == self.owner, "Only owner can set tax rate"
    assert

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
