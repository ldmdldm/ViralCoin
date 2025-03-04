/**
* ViralCoin Interface - Main JavaScript
* This file handles all functionality for the ViralCoin dApp including:
* - Web3/Ethereum wallet integration
* - Smart contract interactions
* - Form handling
* - Dynamic UI updates
* - Data fetching and display
*/

// Contract ABIs - These would typically be imported from JSON files
// Simplified versions for demonstration
const TokenFactoryABI = [
{
    "inputs": [
    {"name": "name", "type": "string"},
    {"name": "symbol", "type": "string"},
    {"name": "initialSupply", "type": "uint256"},
    {"name": "blueprintId", "type": "uint256"}
    ],
    "name": "createToken",
    "outputs": [{"name": "", "type": "address"}],
    "stateMutability": "nonpayable",
    "type": "function"
},
{
    "inputs": [],
    "name": "getAllBlueprints",
    "outputs": [{"name": "", "type": "uint256[]"}],
    "stateMutability": "view",
    "type": "function"
},
{
    "inputs": [{"name": "blueprintId", "type": "uint256"}],
    "name": "getBlueprintDetails",
    "outputs": [
    {"name": "category", "type": "string"},
    {"name": "description", "type": "string"},
    {"name": "tokenType", "type": "uint8"}
    ],
    "stateMutability": "view",
    "type": "function"
}
];

const TrendTokenABI = [
{
    "inputs": [],
    "name": "name",
    "outputs": [{"name": "", "type": "string"}],
    "stateMutability": "view",
    "type": "function"
},
{
    "inputs": [],
    "name": "symbol",
    "outputs": [{"name": "", "type": "string"}],
    "stateMutability": "view",
    "type": "function"
},
{
    "inputs": [],
    "name": "totalSupply",
    "outputs": [{"name": "", "type": "uint256"}],
    "stateMutability": "view",
    "type": "function"
},
{
    "inputs": [{"name": "account", "type": "address"}],
    "name": "balanceOf",
    "outputs": [{"name": "", "type": "uint256"}],
    "stateMutability": "view",
    "type": "function"
}
];

// Global variables
let web3;
let accounts = [];
let tokenFactoryContract;
let userTokens = [];
let isConnected = false;
let trendingTopics = [];

// Contract addresses (these would be network-specific)
const CONTRACT_ADDRESSES = {
tokenFactory: '0x1234567890123456789012345678901234567890' // Replace with actual deployed address
};

// DOM Elements
const connectButton = document.getElementById('connect-wallet-btn');
const accountDisplay = document.getElementById('account-display');
const deployForm = document.getElementById('deploy-token-form');
const trendingTopicsContainer = document.getElementById('trending-topics');
const tokenPreview = document.getElementById('token-preview');
const deployedTokensContainer = document.getElementById('deployed-tokens');
const statusMessage = document.getElementById('status-message');
const blueprintSelect = document.getElementById('token-blueprint');
const loadingSpinner = document.getElementById('loading-spinner');

/**
* Initialize the application
*/
async function init() {
console.log('Initializing ViralCoin dApp...');

// Set up event listeners
connectButton.addEventListener('click', connectWallet);

if (deployForm) {
    deployForm.addEventListener('submit', handleTokenDeployment);
    
    // Set up form preview events
    const formInputs = deployForm.querySelectorAll('input, select');
    formInputs.forEach(input => {
    input.addEventListener('change', updateTokenPreview);
    });
}

// Check if MetaMask is installed
if (window.ethereum) {
    console.log('MetaMask detected');
    
    // Handle account changes
    window.ethereum.on('accountsChanged', handleAccountsChanged);
    
    // Handle chain changes
    window.ethereum.on('chainChanged', () => window.location.reload());
    
    // Auto-connect if previously connected
    if (localStorage.getItem('walletConnected') === 'true') {
    connectWallet();
    }
} else {
    updateStatus('Please install MetaMask to use this dApp', 'error');
    if (connectButton) {
    connectButton.disabled = true;
    connectButton.innerHTML = 'MetaMask Not Detected';
    }
}

// Load trending topics regardless of wallet connection
await loadTrendingTopics();
}

/**
* Connect to Ethereum wallet (MetaMask)
*/
async function connectWallet() {
showLoading(true);
updateStatus('Connecting to wallet...', 'info');

try {
    // Request account access
    accounts = await window.ethereum.request({ method: 'eth_requestAccounts' });
    
    // Create Web3 instance
    web3 = new Web3(window.ethereum);
    
    // Get current network ID
    const networkId = await web3.eth.net.getId();
    console.log(`Connected to network ID: ${networkId}`);
    
    // Initialize contract instances
    initializeContracts(networkId);
    
    // Update UI
    handleAccountsChanged(accounts);
    
    // Set connected flag
    isConnected = true;
    localStorage.setItem('walletConnected', 'true');
    
    updateStatus('Wallet connected successfully', 'success');
    
    // Load user-specific data
    await loadUserTokens();
    await loadBlueprints();
    
    // Update UI based on connection
    updateUIForConnectedState();
} catch (error) {
    console.error('Error connecting wallet:', error);
    updateStatus(`Connection failed: ${error.message}`, 'error');
    isConnected = false;
    localStorage.removeItem('walletConnected');
} finally {
    showLoading(false);
}
}

/**
* Initialize contract instances
*/
function initializeContracts(networkId) {
// In a production app, you would select the contract address based on the network ID
tokenFactoryContract = new web3.eth.Contract(
    TokenFactoryABI,
    CONTRACT_ADDRESSES.tokenFactory
);

console.log('Contracts initialized');
}

/**
* Handle changes to connected accounts
*/
function handleAccountsChanged(newAccounts) {
if (newAccounts.length === 0) {
    // User disconnected
    updateStatus('Wallet disconnected', 'info');
    isConnected = false;
    localStorage.removeItem('walletConnected');
    updateUIForDisconnectedState();
    return;
}

accounts = newAccounts;
const shortenedAccount = `${accounts[0].substring(0, 6)}...${accounts[0].substring(38)}`;

if (accountDisplay) {
    accountDisplay.textContent = shortenedAccount;
}

if (connectButton) {
    connectButton.innerHTML = 'Connected';
    connectButton.classList.remove('btn-primary');
    connectButton.classList.add('btn-success');
}

console.log(`Connected account: ${accounts[0]}`);
}

/**
* Update the UI for connected state
*/
function updateUIForConnectedState() {
document.querySelectorAll('.needs-connection').forEach(el => {
    el.classList.remove('disabled');
});

document.querySelectorAll('.connected-only').forEach(el => {
    el.style.display = 'block';
});

document.querySelectorAll('.disconnected-only').forEach(el => {
    el.style.display = 'none';
});
}

/**
* Update the UI for disconnected state
*/
function updateUIForDisconnectedState() {
document.querySelectorAll('.needs-connection').forEach(el => {
    el.classList.add('disabled');
});

document.querySelectorAll('.connected-only').forEach(el => {
    el.style.display = 'none';
});

document.querySelectorAll('.disconnected-only').forEach(el => {
    el.style.display = 'block';
});

if (connectButton) {
    connectButton.innerHTML = 'Connect Wallet';
    connectButton.classList.remove('btn-success');
    connectButton.classList.add('btn-primary');
}

if (accountDisplay) {
    accountDisplay.textContent = 'Not connected';
}
}

/**
* Load trending topics from the API
*/
async function loadTrendingTopics() {
showLoading(true);
updateStatus('Loading trending topics...', 'info');

try {
    // In a real app, you would fetch this from your backend API
    // For now, we'll simulate a fetch with setTimeout
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    // Sample trending topics (in production, this would come from your TrendAnalyzer API)
    trendingTopics = [
    { name: 'Artificial Intelligence', score: 0.95, category: 'Technology' },
    { name: 'SpaceX Launch', score: 0.89, category: 'Space' },
    { name: 'NFT Art', score: 0.82, category: 'Crypto' },
    { name: 'Quantum Computing', score: 0.78, category: 'Technology' },
    { name: 'DeFi Revolution', score: 0.76, category: 'Finance' }
    ];
    
    displayTrendingTopics();
    updateStatus('Trending topics loaded', 'success');
} catch (error) {
    console.error('Error loading trending topics:', error);
    updateStatus('Failed to load trending topics', 'error');
} finally {
    showLoading(false);
}
}

/**
* Display trending topics in the UI
*/
function displayTrendingTopics() {
if (!trendingTopicsContainer) return;

trendingTopicsContainer.innerHTML = '';

trendingTopics.forEach(topic => {
    const scorePercentage = Math.round(topic.score * 100);
    
    const topicElement = document.createElement('div');
    topicElement.className = 'trend-item card mb-3';
    topicElement.innerHTML = `
    <div class="card-body">
        <div class="d-flex justify-content-between align-items-center">
        <h5 class="card-title">${topic.name}</h5>
        <span class="badge ${getScoreBadgeClass(topic.score)}">${scorePercentage}%</span>
        </div>
        <p class="card-text small text-muted">${topic.category}</p>
        <div class="progress">
        <div class="progress-bar ${getScoreProgressClass(topic.score)}" role="progressbar" 
            style="width: ${scorePercentage}%" aria-valuenow="${scorePercentage}" 
            aria-valuemin="0" aria-valuemax="100"></div>
        </div>
        <div class="mt-3">
        <button class="btn btn-sm btn-outline-primary use-trend-btn" 
                data-trend="${topic.name}" data-category="${topic.category}">
            Use For Token
        </button>
        </div>
    </div>
    `;
    
    trendingTopicsContainer.appendChild(topicElement);
    
    // Add event listener to "Use For Token" button
    const useButton = topicElement.querySelector('.use-trend-btn');
    useButton.addEventListener('click', () => {
    populateTokenForm(topic);
    });
});
}

/**
* Populate the token form with trend data
*/
function populateTokenForm(topic) {
if (!deployForm) return;

const nameInput = deployForm.querySelector('#token-name');
const symbolInput = deployForm.querySelector('#token-symbol');

if (nameInput && symbolInput) {
    nameInput.value = `${topic.name} Token`;
    
    // Create symbol from first letters of each word
    const symbol = topic.name.split(' ')
    .map(word => word[0])
    .join('')
    .toUpperCase();
    
    symbolInput.value = symbol;
    
    // Scroll to form
    deployForm.scrollIntoView({ behavior: 'smooth' });
    
    // Update preview
    updateTokenPreview();
}
}

/**
* Get appropriate badge class based on score
*/
function getScoreBadgeClass(score) {
if (score >= 0.9) return 'bg-success';
if (score >= 0.7) return 'bg-primary';
if (score >= 0.5) return 'bg-info';
if (score >= 0.3) return 'bg-warning';
return 'bg-danger';
}

/**
* Get appropriate progress bar class based on score
*/
function getScoreProgressClass(score) {
if (score >= 0.9) return 'bg-success';
if (score >= 0.7) return 'bg-primary';
if (score >= 0.5) return 'bg-info';
if (score >= 0.3) return 'bg-warning';
return 'bg-danger';
}

/**
* Load blueprints from the contract
*/
async function loadBlueprints() {
if (!tokenFactoryContract || !blueprintSelect) return;

try {
    const blueprintIds = await tokenFactoryContract.methods.getAllBlueprints().call();
    
    blueprintSelect.innerHTML = '<option value="" disabled selected>Select a Blueprint</option>';
    
    for (const id of blueprintIds) {
    const details = await tokenFactoryContract.methods.getBlueprintDetails(id).call();
    
    const option = document.createElement('option');
    option.value = id;
    option.textContent = `${details.category} (${getTokenTypeName(details.tokenType)})`;
    option.dataset.category = details.category;
    option.dataset.description = details.description;
    option.dataset.tokenType = details.tokenType;
    
    blueprintSelect.appendChild(option);
    }
    
    console.log(`Loaded ${blueprintIds.length} blueprints`);
} catch (error) {
    console.error('Error loading blueprints:', error);
    updateStatus('Failed to load token blueprints', 'error');
}
}

/**
* Get token type name from the numeric value
*/
function getTokenTypeName(tokenType) {
const types = ['Standard', 'Reflective', 'Deflationary', 'Governance', 'Utility'];
return types[tokenType] || 'Unknown';
}

/**
* Handle token deployment form submission
*/
async function handleTokenDeployment(event) {
    event.preventDefault();

    if (!isConnected) {
        updateStatus('Please connect your wallet first', 'warning');
        return;
    }

    showLoading(true);
    updateStatus('Preparing to deploy token...', 'info');

    try {
        // Get form values
        const name = document.getElementById('token-name').value.trim();
        const symbol = document.getElementById('token-symbol').value.trim().toUpperCase();
        const initialSupply = document.getElementById('token-supply').value;
        const blueprintId = document.getElementById('token-blueprint').value;

        // Validate form values
        if (!name || !symbol || !initialSupply || !blueprintId) {
            updateStatus('Please fill in all required fields', 'warning');
            return;
        }

        // Convert supply to wei (18 decimals)
        const supplyInWei = web3.utils.toWei(initialSupply);

        // Call the contract to deploy the token
        updateStatus('Deploying token to blockchain...', 'info');

        const tokenAddress = await tokenFactoryContract.methods.createToken(
            name,
            symbol,
            supplyInWei,
            blueprintId
        ).send({ 
            from: accounts[0],
            gas: 5000000 // Gas limit
        });

        // Success! Update the UI
        updateStatus(`Token ${name} (${symbol}) deployed successfully!`, 'success');
        
        // Add token to user's deployed tokens list
        await loadUserTokens();
        
        // Reset the form
        deployForm.reset();
        updateTokenPreview();
        
        // Scroll to deployed tokens section
        if (deployedTokensContainer) {
            deployedTokensContainer.scrollIntoView({ behavior: 'smooth' });
        }
    } catch (error) {
        console.error('Error deploying token:', error);
        updateStatus(`Token deployment failed: ${error.message}`, 'error');
    } finally {
        showLoading(false);
    }
}
/**
* Load tokens deployed by the user
*/
async function loadUserTokens() {
    if (!isConnected || !accounts.length) {
        return;
    }

    showLoading(true);
    updateStatus('Loading your tokens...', 'info');

    try {
        // In a real dApp, you would query events from the blockchain
        // to find tokens created by the user
        // For demo purposes, we'll simulate this with a timeout
        await new Promise(resolve => setTimeout(resolve, 1000));

        // For demonstration, we'll use local storage to track deployed tokens
        // In a real dApp, you would query the blockchain
        let savedTokens = localStorage.getItem('userDeployedTokens');
        let userTokenArray = savedTokens ? JSON.parse(savedTokens) : [];

        // If empty, add some sample tokens
        if (userTokenArray.length === 0 && accounts.length > 0) {
            // Only add sample tokens if none exist yet
            userTokenArray = [
                {
                    name: 'AI Revolution Token',
                    symbol: 'AIT',
                    address: '0x1234567890123456789012345678901234567890',
                    supply: '1000000',
                    category: 'Technology',
                    deployedAt: new Date().toISOString()
                },
                {
                    name: 'Space Exploration Token',
                    symbol: 'SET',
                    address: '0x2345678901234567890123456789012345678901',
                    supply: '500000',
                    category: 'Space',
                    deployedAt: new Date(Date.now() - 86400000).toISOString()
                }
            ];
            localStorage.setItem('userDeployedTokens', JSON.stringify(userTokenArray));
        }

        userTokens = userTokenArray;
        displayUserTokens();
        updateStatus('Your tokens loaded successfully', 'success');
    } catch (error) {
        console.error('Error loading user tokens:', error);
        updateStatus('Failed to load your tokens', 'error');
    } finally {
        showLoading(false);
    }
}

/**
* Display user's deployed tokens in the UI
*/
function displayUserTokens() {
    if (!deployedTokensContainer) return;

    deployedTokensContainer.innerHTML = '';

    if (userTokens.length === 0) {
        deployedTokensContainer.innerHTML = `
            <div class="alert alert-info">
                <i class="fas fa-info-circle me-2"></i>
                You haven't deployed any tokens yet. Use the form above to create your first token!
            </div>
        `;
        return;
    }

    // Create a token card for each token
    userTokens.forEach(token => {
        const deployDate = new Date(token.deployedAt);
        const formattedDate = deployDate.toLocaleDateString() + ' at ' + 
                            deployDate.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        
        const tokenCard = document.createElement('div');
        tokenCard.className = 'card mb-3 token-card';
        tokenCard.innerHTML = `
            <div class="card-body">
                <div class="d-flex justify-content-between align-items-center mb-2">
                    <h5 class="card-title">${token.name}</h5>
                    <span class="badge bg-primary">${token.symbol}</span>
                </div>
                <div class="d-flex justify-content-between align-items-center mb-2">
                    <span class="text-muted small">Category: ${token.category}</span>
                    <span class="text-muted small">Supply: ${Number(token.supply).toLocaleString()}</span>
                </div>
                <div class="d-flex align-items-center">
                    <span class="text-truncate small me-2 text-secondary">
                        ${token.address}
                    </span>
                    <button class="btn btn-sm btn-outline-secondary copy-address" 
                            data-address="${token.address}">
                        <i class="fas fa-copy"></i>
                    </button>
                </div>
                <div class="mt-3 d-flex justify-content-between">
                    <span class="text-muted small">Deployed: ${formattedDate}</span>
                    <div>
                        <a href="#" class="btn btn-sm btn-outline-primary view-token-btn"
                            data-address="${token.address}">View</a>
                        <a href="#" class="btn btn-sm btn-outline-success add-liquidity-btn"
                            data-address="${token.address}" data-symbol="${token.symbol}">Add Liquidity</a>
                    </div>
                </div>
            </div>
        `;
        
        deployedTokensContainer.appendChild(tokenCard);
        
        // Add event listener to copy button
        const copyButton = tokenCard.querySelector('.copy-address');
        copyButton.addEventListener('click', () => {
            navigator.clipboard.writeText(token.address);
            updateStatus('Address copied to clipboard', 'success');
        });
        
        // Add event listeners to action buttons
        const viewButton = tokenCard.querySelector('.view-token-btn');
        viewButton.addEventListener('click', (e) => {
            e.preventDefault();
            // In a real dApp, you would redirect to token details page or blockchain explorer
            window.open(`https://polygonscan.com/token/${token.address}`, '_blank');
        });
        
        const liquidityButton = tokenCard.querySelector('.add-liquidity-btn');
        liquidityButton.addEventListener('click', (e) => {
            e.preventDefault();
            // In a real dApp, you would open a liquidity provision modal
            updateStatus(`Liquidity feature coming soon for ${token.symbol}!`, 'info');
        });
    });
}

/**
* Update the token preview based on form input values
*/
function updateTokenPreview() {
    if (!deployForm || !tokenPreview) return;
    
    const name = document.getElementById('token-name').value.trim() || 'Token Name';
    const symbol = document.getElementById('token-symbol').value.trim().toUpperCase() || 'SYMBOL';
    const supply = document.getElementById('token-supply').value || '1000000';
    
    // Get selected blueprint details
    const blueprintSelect = document.getElementById('token-blueprint');
    let category = 'Category';
    let description = 'No description available';
    
    if (blueprintSelect && blueprintSelect.selectedIndex > 0) {
        const selectedOption = blueprintSelect.options[blueprintSelect.selectedIndex];
        category = selectedOption.dataset.category || category;
        description = selectedOption.dataset.description || description;
    }
    
    // Format supply with commas
    const formattedSupply = Number(supply).toLocaleString();
    
    // Generate a random color for the token preview
    const hue = (name.split('').reduce((sum, char) => sum + char.charCodeAt(0), 0) % 360);
    const color = `hsl(${hue}, 70%, 60%)`;
    
    // Update the preview
    tokenPreview.innerHTML = `
        <div class="card-body token-preview-inner" style="border-left: 5px solid ${color};">
            <div class="d-flex justify-content-between align-items-center">
                <h5 class="card-title">${name}</h5>
                <span class="badge bg-primary">${symbol}</span>
            </div>
            <div class="token-preview-details">
                <p class="mb-1"><strong>Supply:</strong> ${formattedSupply}</p>
                <p class="mb-1"><strong>Category:</strong> ${category}</p>
                <p class="small text-muted">${description}</p>
            </div>
        </div>
    `;
    
    // Add animation effect
    tokenPreview.classList.add('pulse-animation');
    setTimeout(() => {
        tokenPreview.classList.remove('pulse-animation');
    }, 500);
}

/**
* Update status message in the UI
*/
function updateStatus(message, type = 'info') {
    if (!statusMessage) return;
    
    statusMessage.textContent = message;
    statusMessage.className = 'alert';
    
    // Add appropriate Bootstrap alert class based on status type
    switch(type) {
        case 'success':
            statusMessage.classList.add('alert-success');
            break;
        case 'error':
            statusMessage.classList.add('alert-danger');
            break;
        case 'warning':
            statusMessage.classList.add('alert-warning');
            break;
        case 'info':
        default:
            statusMessage.classList.add('alert-info');
    }
    
    // Show the status message
    statusMessage.style.opacity = '1';
    
    // Auto-hide success and info messages after 5 seconds
    if (type === 'success' || type === 'info') {
        setTimeout(() => {
            statusMessage.style.opacity = '0';
        }, 5000);
    }
}

/**
* Show or hide loading spinner
*/
function showLoading(show) {
    if (!loadingSpinner) return;
    
    if (show) {
        loadingSpinner.style.display = 'flex';
        document.body.classList.add('loading');
    } else {
        loadingSpinner.style.display = 'none';
        document.body.classList.remove('loading');
    }
}

// Initialize the application when the DOM is fully loaded
document.addEventListener('DOMContentLoaded', init);
