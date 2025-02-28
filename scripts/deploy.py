from brownie import accounts, network, config, Contract, TokenFactory, TrendToken
import time

def get_account():
    """Get the active account based on the network"""
    if network.show_active() == "development":
        return accounts[0]
    else:
        return accounts.add(config["wallets"]["from_key"])

def deploy_trend_token_factory():
    """Deploy the main factory contract"""
    account = get_account()
    print(f"Deploying contracts with {account}")
    
    # First deploy the base token implementation
    print("Deploying base TrendToken implementation...")
    trend_token = TrendToken.deploy(
        "Base Trend Token",
        "BTT",
        0,  # No initial supply for implementation
        10**12,  # Max supply
        0,  # No burn rate for implementation
        0,  # No tax rate for implementation
        True,  # Mintable
        0,  # No trend score for implementation
        "base",  # Base category
        account.address,  # Treasury (temporary)
        {'from': account}
    )
    print(f"TrendToken implementation deployed at: {trend_token.address}")
    
    # Deploy the factory with the implementation
    print("Deploying TokenFactory...")
    token_factory = TokenFactory.deploy(
        trend_token.address,
        account.address,  # Treasury address
        {'from': account}
    )
    print(f"TokenFactory deployed at: {token_factory.address}")
    
    # Register different token blueprints (would deploy specialized implementations first)
    print("Factory setup complete!")
    
    return token_factory, trend_token

def create_sample_token(factory, account):
    """Create a sample token using the factory"""
    print("Creating a sample token...")
    
    # Example token configuration
    token_config = {
        "name": "Trending Sample Token",
        "symbol": "TST",
        "initial_supply": 1000000,
        "max_supply": 10000000,
        "burn_rate": 100,  # 1%
        "tax_rate": 200,   # 2%
        "is_mintable": True,
        "trend_score": 850,
        "trend_category": "social"
    }
    
    tx = factory.create_token(
        token_config,
        {'from': account, 'value': factory.creation_fee()}
    )
    tx.wait(1)
    
    token_address = tx.events["TokenCreated"]["token_address"]
    print(f"Sample token created at: {token_address}")
    return token_address

def main():
    """Main deployment function"""
    account = get_account()
    factory, base_token = deploy_trend_token_factory()
    
    # Optional: create a sample token
    if input("Create a sample token? (y/n): ").lower() == 'y':
        sample_token = create_sample_token(factory, account)
    
    print("Deployment complete!")

