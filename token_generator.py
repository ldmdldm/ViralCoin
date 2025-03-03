#!/usr/bin/env python3
"""
ViralCoin Token Generator

This module handles the generation of Vyper smart contracts for tokens based on
trend analysis. It creates customizable ERC20 token contracts that can be
deployed on the Polygon network.
"""

import os
import json
import subprocess
from typing import Dict, Any, Optional
from datetime import datetime

# Default token parameters
DEFAULT_PARAMS = {
    "initial_supply": 1000000000,  # 1 billion tokens
    "decimals": 18,
    "tax_fee": 3,  # 3% tax fee
    "liquidity_fee": 2,  # 2% liquidity fee
    "marketing_fee": 2,  # 2% marketing fee
    "max_transaction": 5000000,  # Max 0.5% of supply per transaction
    "max_wallet": 20000000,  # Max 2% of supply per wallet
    "liquidity_threshold": 5000000,  # 0.5% of supply triggers liquidity add
}

# Base directory for contract templates
CONTRACTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "contracts")

class TokenGenerator:
    """Class for generating and managing token contracts"""
    
    def __init__(self, trend_data: Optional[Dict[str, Any]] = None):
        """
        Initialize the token generator with optional trend data
        
        Args:
            trend_data: Data from trend analysis to inform token creation
        """
        self.trend_data = trend_data
        self.contract_template = self._load_contract_template()
        
    def _load_contract_template(self) -> str:
        """Load the Vyper contract template"""
        template_path = os.path.join(CONTRACTS_DIR, "token_template.vy")
        try:
            with open(template_path, "r") as file:
                return file.read()
        except FileNotFoundError:
            # Create directory if it doesn't exist
            os.makedirs(CONTRACTS_DIR, exist_ok=True)
            
            # Return a basic template if file doesn't exist
            return self._get_default_template()
    
    def _get_default_template(self) -> str:
        """Return a default Vyper ERC20 template"""
        return """
# @version ^0.3.7
# @dev Implementation of ERC-20 token standard with additional features
# Based on Snekmate library implementation

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

event SwapAndLiquify:
    tokens_swapped: uint256
    eth_received: uint256
    tokens_into_liquidity: uint256

# State variables
name: public(String[64])
symbol: public(String[32])
decimals: public(uint8)

balances: HashMap[address, uint256]
allowances: HashMap[address, HashMap[address, uint256]]
total_supply: uint256

# Token parameters
tax_fee: public(uint256)
liquidity_fee: public(uint256)
marketing_fee: public(uint256)
max_tx_amount: public(uint256)
max_wallet_size: public(uint256)
liquidity_threshold: public(uint256)

# Owner and privileged addresses
owner: public(address)
marketing_wallet: public(address)
liquidity_wallet: public(address)

# Exemption status
is_excluded_from_fee: public(HashMap[address, bool])
is_excluded_from_max_tx: public(HashMap[address, bool])

# Initialization
@external
def __init__(
    _name: String[64],
    _symbol: String[32],
    _decimals: uint8,
    _initial_supply: uint256,
    _tax_fee: uint256,
    _liquidity_fee: uint256,
    _marketing_fee: uint256,
    _max_tx_amount: uint256,
    _max_wallet_size: uint256,
    _liquidity_threshold: uint256,
    _marketing_wallet: address,
    _liquidity_wallet: address
):
    self.name = _name
    self.symbol = _symbol
    self.decimals = _decimals
    
    self.tax_fee = _tax_fee
    self.liquidity_fee = _liquidity_fee
    self.marketing_fee = _marketing_fee
    self.max_tx_amount = _max_tx_amount
    self.max_wallet_size = _max_wallet_size
    self.liquidity_threshold = _liquidity_threshold
    
    self.owner = msg.sender
    self.marketing_wallet = _marketing_wallet
    self.liquidity_wallet = _liquidity_wallet
    
    # Mint initial supply to the contract creator
    initial_supply_with_decimals: uint256 = _initial_supply * 10 ** convert(_decimals, uint256)
    self.total_supply = initial_supply_with_decimals
    self.balances[msg.sender] = initial_supply_with_decimals
    
    # Exempt owner, marketing and liquidity wallets from fees and limits
    self.is_excluded_from_fee[msg.sender] = True
    self.is_excluded_from_fee[_marketing_wallet] = True
    self.is_excluded_from_fee[_liquidity_wallet] = True
    
    self.is_excluded_from_max_tx[msg.sender] = True
    self.is_excluded_from_max_tx[_marketing_wallet] = True
    self.is_excluded_from_max_tx[_liquidity_wallet] = True
    
    log Transfer(ZERO_ADDRESS, msg.sender, initial_supply_with_decimals)

# View functions required by ERC20 interface
@view
@external
def totalSupply() -> uint256:
    return self.total_supply

@view
@external
def balanceOf(_owner: address) -> uint256:
    return self.balances[_owner]

@view
@external
def allowance(_owner: address, _spender: address) -> uint256:
    return self.allowances[_owner][_spender]

# Transfer and approval functions with custom tokenomics
@external
def transfer(_to: address, _value: uint256) -> bool:
    self._transfer(msg.sender, _to, _value)
    return True

@external
def transferFrom(_from: address, _to: address, _value: uint256) -> bool:
    self.allowances[_from][msg.sender] -= _value
    self._transfer(_from, _to, _value)
    return True

@external
def approve(_spender: address, _value: uint256) -> bool:
    self.allowances[msg.sender][_spender] = _value
    log Approval(msg.sender, _spender, _value)
    return True

# Internal transfer function with fee handling
@internal
def _transfer(_from: address, _to: address, _value: uint256):
    assert _from != ZERO_ADDRESS, "ERC20: transfer from the zero address"
    assert _to != ZERO_ADDRESS, "ERC20: transfer to the zero address"
    assert _value > 0, "Transfer amount must be greater than zero"
    
    # Check max transaction amount if not excluded
    if not self.is_excluded_from_max_tx[_from] and not self.is_excluded_from_max_tx[_to]:
        assert _value <= self.max_tx_amount, "Transfer amount exceeds the maximum transaction limit"
    
    # Check max wallet size for recipient if not excluded
    if not self.is_excluded_from_max_tx[_to]:
        assert self.balances[_to] + _value <= self.max_wallet_size, "Exceeds maximum wallet size"
    
    # Take fees if applicable
    if not self.is_excluded_from_fee[_from] and not self.is_excluded_from_fee[_to]:
        fee_amount: uint256 = _value * (self.tax_fee + self.liquidity_fee + self.marketing_fee) / 100
        tax_amount: uint256 = _value * self.tax_fee / 100
        liquidity_amount: uint256 = _value * self.liquidity_fee / 100
        marketing_amount: uint256 = _value * self.marketing_fee / 100
        
        # Send tax to burn address (zero address)
        if tax_amount > 0:
            self.balances[_from] -= tax_amount
            self.total_supply -= tax_amount
            log Transfer(_from, ZERO_ADDRESS, tax_amount)
        
        # Send liquidity fee to liquidity wallet
        if liquidity_amount > 0:
            self.balances[_from] -= liquidity_amount
            self.balances[self.liquidity_wallet] += liquidity_amount
            log Transfer(_from, self.liquidity_wallet, liquidity_amount)
        
        # Send marketing fee to marketing wallet
        if marketing_amount > 0:
            self.balances[_from] -= marketing_amount
            self.balances[self.marketing_wallet] += marketing_amount
            log Transfer(_from, self.marketing_wallet, marketing_amount)
        
        # Transfer remaining amount
        transfer_amount: uint256 = _value - fee_amount
        self.balances[_from] -= transfer_amount
        self.balances[_to] += transfer_amount
        log Transfer(_from, _to, transfer_amount)
    else:
        # Transfer full amount if excluded from fees
        self.balances[_from] -= _value
        self.balances[_to] += _value
        log Transfer(_from, _to, _value)

# Owner functions to manage fees and exclusions
@external
def setTaxFee(_taxFee: uint256):
    assert msg.sender == self.owner, "Only owner can call this function"
    assert _taxFee <= 10, "Fee cannot exceed 10%"
    self.tax_fee = _taxFee

@external
def setLiquidityFee(_liquidityFee: uint256):
    assert msg.sender == self.owner, "Only owner can call this function"
    assert _liquidityFee <= 10, "Fee cannot exceed 10%"
    self.liquidity_fee = _liquidityFee

@external
def setMarketingFee(_marketingFee: uint256):
    assert msg.sender == self.owner, "Only owner can call this function"
    assert _marketingFee <= 10, "Fee cannot exceed 10%"
    self.marketing_fee = _marketingFee

@external
def excludeFromFee(_address: address):
    assert msg.sender == self.owner, "Only owner can call this function"
    self.is_excluded_from_fee[_address] = True

@external
def includeInFee(_address: address):
    assert msg.sender == self.owner, "Only owner can call this function"
    self.is_excluded_from_fee[_address] = False

@external
def excludeFromMaxTx(_address: address):
    assert msg.sender == self.owner, "Only owner can call this function"
    self.is_excluded_from_max_tx[_address] = True

@external
def includeInMaxTx(_address: address):
    assert msg.sender == self.owner, "Only owner can call this function"
    self.is_excluded_from_max_tx[_address] = False
"""

    def generate_token_contract(self, name: str, symbol: str, params: Optional[Dict[str, Any]] = None) -> str:
        """
        Generate a token contract based on the template and provided parameters
        
        Args:
            name: Token name
            symbol: Token symbol
            params: Optional dictionary of contract parameters to override defaults
        
        Returns:
            String containing the Vyper contract code
        """
        # Merge default parameters with any provided ones
        token_params = DEFAULT_PARAMS.copy()
        if params:
            token_params.update(params)
        
        # Replace placeholders in the template
        contract = self.contract_template
        
        # Save the generated contract to a file
        output_file = os.path.join(CONTRACTS_DIR, f"{symbol.lower()}_token.vy")
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        with open(output_file, "w") as file:
            file.write(contract)
        
        return output_file
    
    def generate_token_from_trend(self, with_metadata: bool = True) -> Dict[str, Any]:
        """
        Generate a token based on trend data
        
        Args:
            with_metadata: Whether to include token metadata
        
        Returns:
            Dictionary with token details and contract file path
        """
        if not self.trend_data:
            raise ValueError("No trend data provided")
        
        # Extract trend information to create token details
        trend_name = self.trend_data.get("name", "Viral Token")
        description = self.trend_data.get("description", "A token based on trending topics")
        
        # Generate token name and symbol
        token_name = f"{trend_name.title()} Token"
        token_symbol = self._generate_symbol(trend_name)
        
        # Generate custom parameters based on trend virality and potential
        virality_score = self.trend_data.get("virality_score", 50) / 100
        params = DEFAULT_PARAMS.copy()
        
        # Adjust parameters based on virality
        params["initial_supply"] = int(1_000_000_000 * (0.5 + virality_score))
        params["tax_fee"] = max(1, min(5, int(3 * virality_score)))
        params["liquidity_fee"] = max(1, min(5, int(2 * virality_score)))
        
        # Generate the contract
        contract_file = self.generate_token_contract(token_name, token_symbol, params)
        
        # Prepare token metadata
        token_data = {
            "name": token_name,
            "symbol": token_symbol,
            "description": description,
            "created_at": datetime.now().isoformat(),
            "trend_source": self.trend_data.get("source", "AI Analysis"),
            "virality_score": self.trend_data.get("virality_score", 50),
            "contract_file": contract_file,
            "parameters": params
        }
        
        # Save metadata if requested
        if with_metadata:
            metadata_file = os.path.join(CONTRACTS_DIR, f"{token_symbol.lower()}_metadata.json")
            with open(metadata_file, "w") as file:
                json.dump(token_data, file, indent=2)
            token_data["metadata_file"] = metadata_file
        
        return token_data
    
    def _generate_symbol(self, name: str) -> str:
        """Generate a token symbol from a name"""
        # Extract first letters of each word, up to 5 characters
        words = name.split()
        if len(words) == 1:
            

