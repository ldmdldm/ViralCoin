"""
Blockchain utilities for ViralCoin.

This module provides tools for interacting with the Polygon Mumbai testnet,
compiling Vyper contracts, deploying tokens, and retrieving token information.
"""

import os
import json
import logging
from typing import Dict, Any, Optional, Tuple, List
from pathlib import Path
from web3 import Web3
from web3.middleware import geth_poa_middleware
from web3.types import TxReceipt, Wei
from eth_account import Account
from eth_account.signers.local import LocalAccount
from vyper import compile_code, compile_files
from vyper.exceptions import VyperException
from hexbytes import HexBytes

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("blockchain")

# Mumbai testnet RPC URL and chain ID
MUMBAI_RPC_URL = os.getenv("RPC_URL", "https://rpc-mumbai.maticvigil.com/")
MUMBAI_CHAIN_ID = 80001

# Contract directories
CONTRACTS_DIR = Path(__file__).parent / "contracts"
TOKEN_FACTORY_PATH = CONTRACTS_DIR / "TokenFactory.vy"
TREND_TOKEN_PATH = CONTRACTS_DIR / "TrendToken.vy"
TOKEN_TEMPLATE_PATH = CONTRACTS_DIR / "token_template.vy"

# Contract ABIs directory
ABIS_DIR = Path(__file__).parent / "abis"
os.makedirs(ABIS_DIR, exist_ok=True)


class BlockchainService:
    """Service for interacting with blockchain networks, specifically Polygon Mumbai."""

    def __init__(self, rpc_url: str = MUMBAI_RPC_URL, private_key: Optional[str] = None):
        """
        Initialize the blockchain service.

        Args:
            rpc_url: RPC URL for the blockchain network
            private_key: Private key for signing transactions (optional)
        """
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        
        # Apply middleware for POA chains like Polygon
        self.w3.middleware_onion.inject(geth_poa_middleware, layer=0)
        
        # Check connection
        if not self.w3.is_connected():
            logger.error(f"Failed to connect to the network at {rpc_url}")
            raise ConnectionError(f"Could not connect to the network at {rpc_url}")
        
        logger.info(f"Connected to network: {rpc_url}")
        logger.info(f"Current block number: {self.w3.eth.block_number}")

        # Set up account if private key is provided
        self.account: Optional[LocalAccount] = None
        if private_key:
            try:
                self.account = Account.from_key(private_key)
                logger.info(f"Account set up: {self.account.address}")
            except Exception as e:
                logger.error(f"Failed to setup account: {str(e)}")
                raise

        # Cache for compiled contracts
        self._compiled_contracts = {}
        self._contract_instances = {}
    
    def get_account(self) -> Optional[LocalAccount]:
        """Get the current account."""
        return self.account
    
    def set_account(self, private_key: str) -> LocalAccount:
        """
        Set the account using a private key.
        
        Args:
            private_key: Private key for the account
            
        Returns:
            LocalAccount: The account object
        """
        self.account = Account.from_key(private_key)
        logger.info(f"Account set up: {self.account.address}")
        return self.account
    
    def get_balance(self, address: Optional[str] = None) -> float:
        """
        Get the balance of an address in MATIC.
        
        Args:
            address: Address to check balance for (defaults to the current account)
            
        Returns:
            float: Balance in MATIC
        """
        if address is None:
            if self.account is None:
                raise ValueError("No account set and no address provided")
            address = self.account.address
            
        balance_wei = self.w3.eth.get_balance(address)
        balance_matic = self.w3.from_wei(balance_wei, 'ether')
        return float(balance_matic)
    
    def compile_contract(self, contract_path: Path, optimize: bool = True) -> Dict[str, Any]:
        """
        Compile a Vyper contract.
        
        Args:
            contract_path: Path to the Vyper contract
            optimize: Whether to optimize the contract
            
        Returns:
            Dict: Compiled contract data
        """
        if str(contract_path) in self._compiled_contracts:
            return self._compiled_contracts[str(contract_path)]
        
        if not contract_path.exists():
            raise FileNotFoundError(f"Contract file not found: {contract_path}")
        
        try:
            # Read the contract source code
            with open(contract_path, 'r') as file:
                source_code = file.read()
            
            # Compile the contract
            compiled_contract = compile_code(
                source_code,
                ["abi", "bytecode"],
                optimize=optimize
            )
            
            # Cache the compiled contract
            self._compiled_contracts[str(contract_path)] = compiled_contract
            
            # Save ABI to file for future reference
            contract_name = contract_path.stem
            abi_path = ABIS_DIR / f"{contract_name}.json"
            with open(abi_path, 'w') as abi_file:
                json.dump(compiled_contract['abi'], abi_file, indent=2)
            
            logger.info(f"Compiled contract: {contract_path.name}")
            return compiled_contract
        
        except VyperException as e:
            logger.error(f"Failed to compile contract {contract_path}: {str(e)}")
            raise
    
    def compile_contracts(self) -> Dict[str, Dict[str, Any]]:
        """
        Compile all contracts in the contracts directory.
        
        Returns:
            Dict: Mapping of contract names to compiled contracts
        """
        compiled_contracts = {}
        contract_files = list(CONTRACTS_DIR.glob("*.vy"))
        
        for contract_path in contract_files:
            contract_name = contract_path.stem
            compiled_contracts[contract_name] = self.compile_contract(contract_path)
        
        return compiled_contracts
    
    def deploy_contract(
        self, 
        contract_path: Path, 
        constructor_args: Optional[list] = None,
        gas_limit: Optional[int] = None,
        gas_price: Optional[int] = None,
        value: int = 0
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Deploy a contract to the blockchain.
        
        Args:
            contract_path: Path to the Vyper contract
            constructor_args: Arguments for the contract constructor
            gas_limit: Gas limit for the transaction
            gas_price: Gas price for the transaction
            value: ETH value to send with the transaction
            
        Returns:
            Tuple[str, Dict]: Contract address and transaction receipt
        """
        if self.account is None:
            raise ValueError("No account set for transaction signing")
        
        # Compile the contract if not already compiled
        compiled_contract = self.compile_contract(contract_path)
        
        # Prepare constructor arguments
        constructor_args = constructor_args or []
        
        # Prepare contract deployment transaction
        contract = self.w3.eth.contract(
            abi=compiled_contract['abi'],
            bytecode=compiled_contract['bytecode']
        )
        
        # Estimate gas if not provided
        if gas_limit is None:
            try:
                gas_limit = contract.constructor(*constructor_args).estimate_gas(
                    {'from': self.account.address, 'value': value}
                )
                gas_limit = int(gas_limit * 1.2)  # Add 20% buffer
            except Exception as e:
                logger.warning(f"Gas estimation failed: {str(e)}. Using default gas limit.")
                gas_limit = 5000000  # Default gas limit
        
        # Get gas price if not provided
        if gas_price is None:
            gas_price = self.w3.eth.gas_price
        
        # Prepare transaction
        transaction = {
            'from': self.account.address,
            'gas': gas_limit,
            'gasPrice': gas_price,
            'nonce': self.w3.eth.get_transaction_count(self.account.address),
            'chainId': MUMBAI_CHAIN_ID,
            'value': value
        }
        
        # Build and sign transaction
        construct_txn = contract.constructor(*constructor_args).build_transaction(transaction)
        signed_txn = self.account.sign_transaction(construct_txn)
        
        # Send transaction
        logger.info(f"Deploying contract: {contract_path.name}")
        tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        logger.info(f"Transaction hash: {tx_hash.hex()}")
        
        # Wait for transaction receipt
        tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        contract_address = tx_receipt.contractAddress
        
        logger.info(f"Contract deployed at: {contract_address}")
        
        return contract_address, tx_receipt
    
    def deploy_token_factory(
        self, 
        token_template_address: Optional[str] = None,
        treasury_address: Optional[str] = None,
        gas_limit: Optional[int] = None,
        gas_price: Optional[int] = None
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Deploy the TokenFactory contract.
        
        Args:
            token_template_address: Address of the token template contract
            treasury_address: Address of the treasury
            gas_limit: Gas limit for the transaction
            gas_price: Gas price for the transaction
            
        Returns:
            Tuple[str, Dict]: Contract address and transaction receipt
        """
        # If no token template address is provided, deploy the template first
        if token_template_address is None:
            token_template_address, _ = self.deploy_contract(TOKEN_TEMPLATE_PATH)
        
        # If no treasury address is provided, use the current account
        if treasury_address is None and self.account is not None:
            treasury_address = self.account.address
        
        # Prepare constructor arguments
        constructor_args = [token_template_address]
        if treasury_address:
            constructor_args.append(treasury_address)
        
        # Deploy the factory contract
        return self.deploy_contract(
            TOKEN_FACTORY_PATH,
            constructor_args=constructor_args,
            gas_limit=gas_limit,
            gas_price=gas_price
        )
    
    def deploy_trend_token(
        self,
        name: str,
        symbol: str,
        initial_supply: int,
        decimals: int = 18,
        receiver: Optional[str] = None,
        factory_address: Optional[str] = None,
        gas_limit: Optional[int] = None,
        gas_price: Optional[int] = None
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Deploy a new token using the TokenFactory contract.
        
        Args:
            name: Token name
            symbol: Token symbol
            initial_supply: Initial token supply
            decimals: Token decimals
            receiver: Address to receive the initial token supply
            factory_address: Address of the TokenFactory contract
            gas_limit: Gas limit for the transaction
            gas_price: Gas price for the transaction
            
        Returns:
            Tuple[str, Dict]: Token address and transaction receipt
        """
        if self.account is None:
            raise ValueError("No account set for transaction signing")
        
        # If no receiver is provided, use the current account
        if receiver is None:
            receiver = self.account.address
        
        # If no factory address is provided, deploy the factory first
        if factory_address is None:
            factory_address, _ = self.deploy_token_factory()
        
        # Get the TokenFactory contract ABI
        abi_path = ABIS_DIR / "TokenFactory.json"
        if not abi_path.exists():
            # Compile the contract to generate the ABI
            self.compile_contract(TOKEN_FACTORY_PATH)
        
        with open(abi_path, 'r') as abi_file:
            factory_abi = json.load(abi_file)
        
        # Create contract instance
        factory_contract = self.w3.eth.contract(address=factory_address, abi=factory_abi)
        
        # Get the creation fee
        creation_fee = factory_contract.functions.creation_fee().call()
        
        # Prepare transaction
        if gas_limit is None:
            try:
                gas_limit = factory_contract.functions.create_token(
                    name, symbol, initial_supply, decimals, receiver
                ).estimate_gas({'from': self.account.address, 'value': creation_fee})
                gas_limit = int(gas_limit * 1.2)  # Add 20% buffer
            except Exception as e:
                logger.warning(f"Gas estimation failed: {str(e)}. Using default gas limit.")
                gas_limit = 3000000  # Default gas limit
        
        # Get gas price if not provided
        if gas_price is None:
            gas_price = self.w3.eth.gas_price
        
        # Prepare transaction
        transaction = {
            'from': self.account.address,
            'gas': gas_limit,
            'gasPrice': gas_price,
            'nonce': self.w3.eth.get_transaction_count(self.account.address),
            'chainId': MUMBAI_CHAIN_ID,
            'value': creation_fee
        }
        
        # Build and sign transaction
        function_call = factory_contract.functions.create_token(
            name, symbol, initial_supply, decimals, receiver
        )
        txn = function_call.build_transaction(transaction)
        signed_txn = self.account.sign_transaction(txn)
        
        # Send transaction
        logger.info(f"Creating token: {name} ({symbol})")
        tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        logger.info(f"Transaction hash: {tx_hash.hex()}")
        
        # Wait for transaction receipt
        tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        
        # Get the token address from the event logs
        token_address = None
        for log in tx_receipt['logs']:
            # Try to decode the log using the factory contract
            try:
                decoded_log = factory_contract.events.TokenCreated().process_log(log)
                token_address = decoded_log['args']['token_address']
                break
            except:
                continue
        
        if token_address:
            logger.info(f"Token deployed at: {token_address}")
        else:
            logger.warning("Could not determine token address from logs")
        
        return token_address, tx_receipt

    def deploy_trend_token_from_config(
        self,
        config: Dict[str, Any],
        factory_address: Optional[str] = None,
        gas_limit: Optional[int] = None,
        gas_price: Optional[int] = None
    ) -> Tuple[str, Dict[str, Any]]:
        

