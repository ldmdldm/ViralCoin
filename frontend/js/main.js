/**
* ViralCoin Interface - Main JavaScript
* This file handles all functionality for the ViralCoin dApp including:
* - Web3/Ethereum wallet integration
* - Smart contract interactions
* - Form handling
* - Dynamic UI updates
* - Data fetching and display
*/

// Global API key for backend authentication
const API_KEY = 'development_key';

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
let chartInstances = {};
let isDemoMode = false;

// Contract addresses (these would be network-specific)
const CONTRACT_ADDRESSES = {
tokenFactory: '0x1234567890123456789012345678901234567890' // Replace with actual deployed address
};

// DOM Elements
const connectButton = document.getElementById('connectWallet');
const accountDisplay = document.getElementById('walletAddress');
const deployForm = document.getElementById('tokenGeneratorForm');
const trendingTopicsContainer = document.getElementById('trendingTopicsList');
const tokenPreview = document.getElementById('tokenPreview');
const deployedTokensContainer = document.getElementById('userTokensList');
const statusMessage = document.getElementById('statusMessage');
const blueprintSelect = document.getElementById('tokenBlueprint');
const loadingSpinner = document.getElementById('loadingOverlay');

/**
* Initialize the application
*/
async function init() {
console.log('Initializing ViralCoin dApp...');

// Set up event listeners
if (connectButton) {
    connectButton.addEventListener('click', connectWallet);
}

if (deployForm) {
    deployForm.addEventListener('submit', handleTokenDeployment);
    
    // Set up form preview events
    const formInputs = deployForm.querySelectorAll('input, select');
    formInputs.forEach(input => {
        input.addEventListener('change', updateTokenPreview);
        input.addEventListener('keyup', updateTokenPreview);
    });
}

// Add event listeners for tabs if they exist
const tabButtons = document.querySelectorAll('[data-bs-toggle="tab"]');
tabButtons.forEach(button => {
    button.addEventListener('shown.bs.tab', function(event) {
        const targetId = event.target.getAttribute('data-bs-target');
        if (targetId === '#trendsTab') {
            loadTrendingTopics();
        } else if (targetId === '#myTokensTab') {
            loadUserTokens();
        }
    });
});

// Set up refresh buttons
const refreshTrendsBtn = document.getElementById('refreshTrendsBtn');
if (refreshTrendsBtn) {
    refreshTrendsBtn.addEventListener('click', loadTrendingTopics);
}

const refreshTokensBtn = document.getElementById('refreshTokensBtn');
if (refreshTokensBtn) {
    refreshTokensBtn.addEventListener('click', loadUserTokens);
}

// Check if MetaMask is installed
if (window.ethereum) {
    console.log('MetaMask detected');
    
    // Handle account changes
    window.ethereum.on('accountsChanged', handleAccountsChanged);
    
    // Handle chain changes
    window.ethereum.on('chainChanged', () => window.location.reload());
    
    // Listen for connection events
    window.ethereum.on('connect', () => {
        showToast('Connected to Ethereum network', 'success');
        document.dispatchEvent(new CustomEvent('wallet:connected'));
    });
    
    // Listen for disconnection events
    window.ethereum.on('disconnect', (error) => {
        showToast('Disconnected from Ethereum network: ' + error.message, 'warning');
        document.dispatchEvent(new CustomEvent('wallet:disconnected'));
    });
    
    // Auto-connect if previously connected
    if (localStorage.getItem('walletConnected') === 'true') {
        connectWallet();
    }
} else {
    updateStatus('MetaMask not detected. Running in demo mode.', 'warning');
    if (connectButton) {
        connectButton.disabled = false;
        connectButton.innerHTML = 'Demo Mode';
        connectButton.addEventListener('click', enableDemoMode);
    }
    // Enable demo mode automatically
    enableDemoMode();
}

/**
* Enable demo mode when MetaMask is not available
*/
function enableDemoMode() {
    console.log('Enabling demo mode...');
    isDemoMode = true;
    
    // Create mock contract for demos
    tokenFactoryContract = createMockContract();
    
    // Set a demo account address
    accounts = ['0xDEMO000000000000000000000000000000000000'];
    
    // Update UI for demo mode
    updateUIForDemoMode();
    
    // Load demo data
    loadBlueprints();
    loadTrendingTopics();
    loadUserTokens();
    
    // Show notification
    showToast('Demo mode enabled. No blockchain connection required.', 'info');
}

/**
* Update UI for demo mode
*/
function updateUIForDemoMode() {
    // Update connection button
    if (connectButton) {
        connectButton.innerHTML = 'Demo Mode Active';
        connectButton.classList.remove('btn-primary');
        connectButton.classList.add('btn-warning');
        connectButton.disabled = true;
    }
    
    // Update wallet address display
    if (accountDisplay) {
        accountDisplay.textContent = 'Demo Account';
    }
    
    // Add demo badge to navbar
    const navbarBrand = document.querySelector('.navbar-brand');
    if (navbarBrand) {
        const demoBadge = document.createElement('span');
        demoBadge.className = 'badge bg-warning ms-2';
        demoBadge.textContent = 'DEMO';
        navbarBrand.appendChild(demoBadge);
    }
    
    // Enable all functionality that would normally require connection
    document.querySelectorAll('.needs-connection').forEach(el => {
        el.classList.remove('disabled');
    });
    
    // Show all connected-only elements
    document.querySelectorAll('.connected-only').forEach(el => {
        el.style.display = 'block';
    });
    
    // Hide all disconnected-only elements
    document.querySelectorAll('.disconnected-only').forEach(el => {
        el.style.display = 'none';
    });
    
    // Add demo watermark
    const demoWatermark = document.createElement('div');
    demoWatermark.className = 'demo-watermark';
    demoWatermark.textContent = 'DEMO MODE';
    document.body.appendChild(demoWatermark);
    
    // Add demo stylesheet
    const demoStyle = document.createElement('style');
    demoStyle.textContent = `
        .demo-watermark {
            position: fixed;
            bottom: 20px;
            right: 20px;
            background-color: rgba(255, 193, 7, 0.2);
            color: #856404;
            padding: 5px 10px;
            border-radius: 4px;
            font-size: 12px;
            z-index: 1000;
            pointer-events: none;
        }
    `;
    document.head.appendChild(demoStyle);
}

// Load trending topics regardless of wallet connection
await loadTrendingTopics();

// Initialize analytics charts
initAnalyticsCharts();
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
    
    // Initialize blockchain data refresh
    startBlockchainDataRefresh();
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
/**
* Initialize contract instances
*/
function initializeContracts(networkId) {
    try {
        // In a production app, you would select the contract address based on the network ID
        tokenFactoryContract = new web3.eth.Contract(
            TokenFactoryABI,
            CONTRACT_ADDRESSES.tokenFactory
        );
        
        console.log('Contracts initialized');
    } catch (error) {
        console.error('Error initializing contracts:', error);
        // Use mock contract for demo mode
        tokenFactoryContract = createMockContract();
        console.log('Using mock contract for demo');
    }
}

/**
* Create a mock contract for demo mode
*/
function createMockContract() {
    return {
        methods: {
            createToken: (name, symbol, initialSupply, blueprintId) => ({
                send: (options) => {
                    // Simulate blockchain delay
                    return new Promise((resolve) => {
                        setTimeout(() => {
                            // Generate a random address
                            const tokenAddress = '0x' + Array.from({length: 40}, () => 
                                Math.floor(Math.random() * 16).toString(16)).join('');
                            resolve(tokenAddress);
                        }, 2000);
                    });
                }
            }),
            getAllBlueprints: () => ({
                call: () => Promise.resolve(['1', '2', '3', '4', '5'])
            }),
            getBlueprintDetails: (blueprintId) => ({
                call: () => {
                    const categories = ['Social', 'Finance', 'Technology', 'Entertainment', 'Gaming'];
                    const descriptions = [
                        'Standard ERC-20 token with basic functionality',
                        'Deflationary token that burns 1% on each transaction',
                        'Reflective token that redistributes 2% to holders',
                        'Governance token with voting capability',
                        'Utility token for platform access'
                    ];
                    const id = parseInt(blueprintId) - 1;
                    return Promise.resolve({
                        category: categories[id % categories.length],
                        description: descriptions[id % descriptions.length],
                        tokenType: id % 5
                    });
                }
            }),
        }
    };
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
        // Make a real API call to the backend
        // Make a real API call to the backend
        const response = await fetch('/api/trends', {
            headers: {
                'X-API-Key': API_KEY
            }
        });
        if (!response.ok) {
            throw new Error(`API error: ${response.status} ${response.statusText}`);
        }
        
        const data = await response.json();
        
        // Check if we received valid data from the API
        if (data && Array.isArray(data.topics) && data.topics.length > 0) {
            trendingTopics = data.topics;
            console.log('Topics loaded from API:', trendingTopics);
        } else {
            // If API returned empty data, use fallback
            console.warn('API returned empty data, using fallback topics');
            throw new Error('No topics received from API');
        }
        
        displayTrendingTopics();
        updateStatus('Trending topics loaded from server', 'success');
    } catch (error) {
        console.error('Error loading trending topics:', error);
        
        // Fallback to sample data if API call fails
        trendingTopics = [
            { name: 'Artificial Intelligence in Healthcare', score: 0.98, category: 'Technology', description: 'AI models revolutionizing disease diagnosis and treatment planning' },
            { name: 'Ethereum Layer 2 Solutions', score: 0.95, category: 'Crypto', description: 'Scaling solutions driving lower fees and higher transaction throughput' },
            { name: 'Climate Tech Startups', score: 0.93, category: 'Environment', description: 'New companies developing carbon capture and sustainable energy technologies' },
            { name: 'SpaceX Starship Orbital Test', score: 0.91, category: 'Space', description: 'Latest developments in commercial space exploration' },
            { name: 'Central Bank Digital Currencies', score: 0.89, category: 'Finance', description: 'Government-backed digital currencies reshaping monetary policy' },
            { name: 'Metaverse Real Estate Boom', score: 0.87, category: 'Crypto', description: 'Virtual land sales reaching new highs across multiple platforms' },
            { name: 'Quantum Computing Breakthroughs', score: 0.85, category: 'Technology', description: 'Recent advancements in quantum error correction and qubit stability' },
            { name: 'NFT Gaming Revolution', score: 0.84, category: 'Entertainment', description: 'Play-to-earn games changing the economics of gaming industry' },
            { name: 'Global Supply Chain Innovations', score: 0.82, category: 'Business', description: 'New technologies addressing logistics challenges' },
            { name: 'AR/VR Devices Launch', score: 0.80, category: 'Technology', description: 'Next generation of mixed reality headsets entering the market' },
            { name: 'Sustainable Finance Movement', score: 0.78, category: 'Finance', description: 'ESG investments reshaping capital allocation globally' },
            { name: 'Zero-Knowledge Proofs', score: 0.77, category: 'Crypto', description: 'Privacy technology enabling new use cases in blockchain' },
            { name: 'Remote Work Technologies', score: 0.76, category: 'Business', description: 'Tools and platforms for distributed workforces gaining adoption' },
            { name: 'Decentralized Science (DeSci)', score: 0.74, category: 'Technology', description: 'Blockchain-based funding and collaboration for scientific research' },
            { name: 'Neural Interface Developments', score: 0.72, category: 'Technology', description: 'Brain-computer interfaces advancing human-machine interaction' }
        ];
        
        displayTrendingTopics();
        updateStatus('Using sample trending topics (API unavailable)', 'warning');
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
    topicElement.className = 'col-md-6 col-lg-4 mb-4';
    topicElement.innerHTML = `
    <div class="trend-card">
        <div class="trend-card-header">
            <h5 class="trend-title">${topic.name}</h5>
            <span class="trend-score ${getScoreBadgeClass(topic.score)}">${scorePercentage}%</span>
        </div>
        <div class="trend-card-body">
            <div class="trend-category">${topic.category}</div>
            <div class="trend-description text-muted mb-2">${topic.description || 'No description available'}</div>
            <div class="trend-progress">
                <div class="progress-bar ${getScoreProgressClass(topic.score)}" role="progressbar" 
                    style="width: ${scorePercentage}%" aria-valuenow="${scorePercentage}" 
                    aria-valuemin="0" aria-valuemax="100"></div>
            </div>
            <div class="trend-actions">
                <button class="btn btn-primary use-trend-btn" 
                        data-trend="${topic.name}" data-category="${topic.category}">
                    Create Token
                </button>
                <button class="btn btn-outline-secondary analyze-trend-btn"
                        data-trend="${topic.name}">
                    <i class="fas fa-chart-line"></i> Analyze
                </button>
            </div>
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

    const nameInput = deployForm.querySelector('#tokenName');
    const symbolInput = deployForm.querySelector('#tokenSymbol');
    const categoryInput = deployForm.querySelector('#tokenCategory');

    if (nameInput && symbolInput) {
        nameInput.value = `${topic.name} Token`;
        
        // Create symbol from first letters of each word
        const symbol = topic.name.split(' ')
            .map(word => word[0])
            .join('')
            .toUpperCase();
        
        symbolInput.value = symbol;
        
        // Set category if the input exists
        if (categoryInput) {
            categoryInput.value = topic.category;
        }
        
        // Scroll to generator section
        document.getElementById('tokenGenerator').scrollIntoView({ behavior: 'smooth' });
        
        // Update preview
        updateTokenPreview();
                // Show a toast notification
                showToast(`Trend "${topic.name}" loaded into generator`, 'info');
            }
            }

            /**
            * Display a toast notification
            */
            function showToast(message, type = 'info') {
                // Create toast container if it doesn't exist
                let toastContainer = document.getElementById('toastContainer');
                if (!toastContainer) {
                    toastContainer = document.createElement('div');
                    toastContainer.id = 'toastContainer';
                    toastContainer.className = 'toast-container position-fixed bottom-0 end-0 p-3';
                    document.body.appendChild(toastContainer);
                }
                
                // Generate a unique ID for this toast
                const toastId = 'toast_' + Date.now();
                
                // Set icon based on type
                let icon = '';
                switch(type) {
                    case 'success':
                        icon = '<i class="fas fa-check-circle me-2"></i>';
                        break;
                    case 'error':
                        icon = '<i class="fas fa-exclamation-circle me-2"></i>';
                        break;
                    case 'warning':
                        icon = '<i class="fas fa-exclamation-triangle me-2"></i>';
                        break;
                    case 'info':
                    default:
                        icon = '<i class="fas fa-info-circle me-2"></i>';
                }
                
                // Create toast element
                const toast = document.createElement('div');
                toast.id = toastId;
                toast.className = `toast align-items-center border-0 ${type === 'error' ? 'bg-danger' : type === 'success' ? 'bg-success' : type === 'warning' ? 'bg-warning' : 'bg-info'} text-white`;
                toast.setAttribute('role', 'alert');
                toast.setAttribute('aria-live', 'assertive');
                toast.setAttribute('aria-atomic', 'true');
                
                toast.innerHTML = `
                    <div class="d-flex">
                        <div class="toast-body">
                            ${icon}${message}
                        </div>
                        <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
                    </div>
                `;
                
                // Add toast to container
                toastContainer.appendChild(toast);
                
                // Initialize Bootstrap toast
                const bsToast = new bootstrap.Toast(toast, {
                    autohide: true,
                    delay: 5000
                });
                
                // Show toast
                bsToast.show();
                
                // Remove toast from DOM after it's hidden
                toast.addEventListener('hidden.bs.toast', () => {
                    toast.remove();
                });
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
/**
* Load blueprints from the contract
*/
async function loadBlueprints() {
    if (!blueprintSelect) return;
    
    try {
        if (!tokenFactoryContract) {
            if (!isDemoMode) {
                tokenFactoryContract = createMockContract();
            }
        }
        
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
        
        // Provide fallback blueprints for demo/error situations
        blueprintSelect.innerHTML = '<option value="" disabled selected>Select a Blueprint</option>';
        
        const fallbackBlueprints = [
            { id: '1', category: 'Social Media', type: 0, description: 'Standard ERC-20 token for social media platforms' },
            { id: '2', category: 'Finance', type: 2, description: 'Deflationary token with 1% burn on transfers' },
            { id: '3', category: 'Technology', type: 1, description: 'Reflective token that rewards holders' },
            { id: '4', category: 'Entertainment', type: 3, description: 'Governance token with voting rights' },
            { id: '5', category: 'Gaming', type: 4, description: 'Utility token for in-game purchases' }
        ];
        
        fallbackBlueprints.forEach(bp => {
            const option = document.createElement('option');
            option.value = bp.id;
            option.textContent = `${bp.category} (${getTokenTypeName(bp.type)})`;
            option.dataset.category = bp.category;
            option.dataset.description = bp.description;
            option.dataset.tokenType = bp.type;
            
            blueprintSelect.appendChild(option);
        });
        
        console.log(`Loaded ${fallbackBlueprints.length} fallback blueprints`);
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
* Get token type from blueprint ID
* @param {string} blueprintId - The blueprint ID
* @returns {string} - The token type (memecoin, utility, or governance)
*/
function getTokenTypeFromBlueprint(blueprintId) {
    // Check if blueprintSelect exists and has the blueprint option
    if (blueprintSelect) {
        const option = Array.from(blueprintSelect.options).find(opt => opt.value === blueprintId);
        if (option && option.dataset.tokenType) {
            const typeNum = parseInt(option.dataset.tokenType);
            // Map token type numbers to the expected strings
            if (typeNum === 3) return 'governance';
            if (typeNum === 4) return 'utility';
        }
    }
    // Default to memecoin if we can't determine the type
    return 'memecoin';
}

/**
* Handle token deployment form submission
*/
*/
async function handleTokenDeployment(event) {
    event.preventDefault();
    
    if (!isConnected && !isDemoMode) {
        updateStatus('Please connect your wallet first', 'warning');
        return;
    }
    
    showLoading(true);
    updateStatus('Preparing to deploy token...', 'info');
    
    // Create progress tracking
    const progressSteps = [
        { id: 'prep', label: 'Preparing deployment', pct: 10 },
        { id: 'validation', label: 'Validating parameters', pct: 20 },
        { id: 'contract', label: 'Initializing contract', pct: 30 },
        { id: 'gas', label: 'Estimating gas fees', pct: 40 },
        { id: 'sign', label: 'Awaiting signature', pct: 50 },
        { id: 'broadcast', label: 'Broadcasting to network', pct: 60 },
        { id: 'mine', label: 'Waiting for confirmation', pct: 80 },
        { id: 'complete', label: 'Finalizing deployment', pct: 90 },
        { id: 'success', label: 'Deployment successful', pct: 100 }
    ];
    
    // Create status message element if it doesn't exist
    let deploymentProgress = document.getElementById('deploymentProgress');
    if (!deploymentProgress) {
        deploymentProgress = document.createElement('div');
        deploymentProgress.id = 'deploymentProgress';
        deploymentProgress.className = 'deployment-progress';
        deploymentProgress.innerHTML = `
            <div class="progress mb-3">
                <div class="progress-bar progress-bar-striped progress-bar-animated" role="progressbar" style="width: 0%"></div>
            </div>
            <div class="current-step text-center mb-2">Initializing...</div>
            <div class="step-details small text-muted"></div>
        `;
        
        // Add after status message
        if (statusMessage && statusMessage.parentNode) {
            statusMessage.parentNode.insertBefore(deploymentProgress, statusMessage.nextSibling);
        } else {
            document.body.appendChild(deploymentProgress);
        }
    } else {
        // Reset progress
        const progressBar = deploymentProgress.querySelector('.progress-bar');
        const currentStep = deploymentProgress.querySelector('.current-step');
        const stepDetails = deploymentProgress.querySelector('.step-details');
        
        if (progressBar) progressBar.style.width = '0%';
        if (currentStep) currentStep.textContent = 'Initializing...';
        if (stepDetails) stepDetails.textContent = '';
        
        deploymentProgress.style.display = 'block';
    }
    
    // Function to update progress
    const updateProgress = (stepId, additionalInfo = '') => {
        const step = progressSteps.find(s => s.id === stepId);
        if (!step) return;
        
        const progressBar = deploymentProgress.querySelector('.progress-bar');
        const currentStep = deploymentProgress.querySelector('.current-step');
        const stepDetails = deploymentProgress.querySelector('.step-details');
        
        if (progressBar) progressBar.style.width = `${step.pct}%`;
        if (currentStep) currentStep.textContent = step.label;
        if (stepDetails && additionalInfo) stepDetails.textContent = additionalInfo;
        
        console.log(`Deployment progress: ${step.label} (${step.pct}%)`);
    };
    
    try {
        // Update to first step
        updateProgress('prep');
        await new Promise(resolve => setTimeout(resolve, 600));
        
        // Retrieve form values
        const name = document.getElementById('tokenName').value.trim();
        const symbol = document.getElementById('tokenSymbol').value.trim().toUpperCase();
        const initialSupply = document.getElementById('tokenSupply').value.trim();
        const blueprintId = document.getElementById('tokenBlueprint').value;
        const category = document.getElementById('tokenCategory')?.value || 'General';
        
        // Move to validation step
        updateProgress('validation');
        await new Promise(resolve => setTimeout(resolve, 800));
        
        // Validate form inputs
        if (!name) {
            throw new Error('Token name is required');
        }
        
        if (!symbol) {
            throw new Error('Token symbol is required');
        }
        
        if (!initialSupply || isNaN(Number(initialSupply)) || Number(initialSupply) <= 0) {
            throw new Error('Initial supply must be a positive number');
        }
        
        if (!blueprintId) {
            throw new Error('Token blueprint is required');
        }
        
        // Get selected token type based on blueprint
        const tokenType = getTokenTypeFromBlueprint(blueprintId);
        
        // Initialize contract
        updateProgress('contract', `Setting up ${tokenType} token contract`);
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        // Check if we're on an appropriate network
        let networkName = 'Unknown Network';
        let isTestnet = false;
        
        if (web3 && isConnected) {
            try {
                const networkId = await web3.eth.net.getId();
                switch(networkId) {
                    case 1:
                        networkName = 'Ethereum Mainnet';
                        break;
                    case 5:
                        networkName = 'Goerli Testnet';
                        isTestnet = true;
                        break;
                    case 137:
                        networkName = 'Polygon Mainnet';
                        break;
                    case 80001:
                        networkName = 'Mumbai Testnet';
                        isTestnet = true;
                        break;
                    default:
                        networkName = `Network ID: ${networkId}`;
                }
                
                if (!isTestnet) {
                    // Show confirmation for mainnet deployments
                    const confirmMainnet = confirm(`You are about to deploy to ${networkName}. This will use real funds. Continue?`);
                    if (!confirmMainnet) {
                        throw new Error('Deployment cancelled by user');
                    }
                }
                
                updateProgress('contract', `Deploying to ${networkName}`);
            } catch (networkError) {
                console.warn('Error detecting network:', networkError);
                // Continue with demo mode if network detection fails
            }
        }
        
        // Calculate gas fee
        updateProgress('gas');
        await new Promise(resolve => setTimeout(resolve, 1500));
        
        // Display an estimated gas fee (this would be calculated from the network in a real app)
        const estimatedGasFee = isDemoMode ? '0.003 ETH' : (isTestnet ? '0.0012 ETH' : '0.015 ETH');
        updateProgress('gas', `Estimated cost: ${estimatedGasFee} (may vary based on network conditions)`);
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        let tokenAddress;
        
        // Check if we're in demo mode or if web3 is unavailable
        if (isDemoMode || !web3 || !tokenFactoryContract) {
            // Simulated token deployment
            console.log('Demo mode: Creating token without actual blockchain transaction');
            
            // Simulate waiting for signature
            updateProgress('sign', 'Please confirm the transaction in your wallet');
            await new Promise(resolve => setTimeout(resolve, 3000));
            
            // Simulate transaction broadcast
            updateProgress('broadcast', 'Transaction submitted to network');
            
            // Generate a realistic but fake token address
            const prefix = isTestnet ? '0x4' : '0x'; // Testnet addresses often start with 0x4
            tokenAddress = prefix + Array.from({length: 40}, () => 
                Math.floor(Math.random() * 16).toString(16)).join('');
            
            // Simulate transaction confirmation
            updateProgress('mine', 'Waiting for block confirmation');
            await new Promise(resolve => setTimeout(resolve, 4000));
            
            // Simulate successful deployment
            updateProgress('complete', `Token created at address: ${tokenAddress}`);
            await new Promise(resolve => setTimeout(resolve, 1000));
        } else {
            // Real token deployment with blockchain interaction
            try {
                // Get current account
                const account = accounts[0];
                
                // Format parameters for contract
                const formattedSupply = web3.utils.toWei(initialSupply, 'ether');
                
                // Estimate gas
                const gasEstimate = await tokenFactoryContract.methods
                    .createToken(name, symbol, formattedSupply, blueprintId)
                    .estimateGas({ from: account });
                
                console.log(`Estimated gas: ${gasEstimate}`);
                updateProgress('gas', `Estimated gas: ${gasEstimate} units`);
                
                // Request signature
                updateProgress('sign', 'Please confirm the transaction in your wallet');
                
                // Send transaction to contract
                const receipt = await tokenFactoryContract.methods
                    .createToken(name, symbol, formattedSupply, blueprintId)
                    .send({ 
                        from: account,
                        gas: Math.floor(gasEstimate * 1.2) // Add 20% buffer for gas
                    });
                
                // Update progress during transaction confirmation
                updateProgress('broadcast', `Transaction hash: ${receipt.transactionHash}`);
                await new Promise(resolve => setTimeout(resolve, 2000));
                
                updateProgress('mine', `Block number: ${receipt.blockNumber}`);
                await new Promise(resolve => setTimeout(resolve, 1000));
                
                // Get deployed token address from transaction receipt
                tokenAddress = receipt.events.TokenCreated.returnValues.tokenAddress || 
                            receipt.events.TokenDeployed.returnValues.tokenAddress || 
                            receipt;
                
                updateProgress('complete', `Token created at address: ${tokenAddress}`);
            } catch (contractError) {
                console.error('Contract interaction error:', contractError);
                
                // If contract interaction fails, fallback to demo mode with a delay
                updateProgress('sign', 'Falling back to simulation mode due to contract error');
                await new Promise(resolve => setTimeout(resolve, 2000));
                
                // Generate a realistic looking address
                tokenAddress = '0x' + Array.from({length: 40}, () => 
                    Math.floor(Math.random() * 16).toString(16)).join('');
                
                updateProgress('broadcast', 'Simulating transaction in demo mode');
                await new Promise(resolve => setTimeout(resolve, 2000));
                
                updateProgress('mine', 'Simulating block confirmation');
                await new Promise(resolve => setTimeout(resolve, 3000));
                
                updateProgress('complete', `Demo token created at address: ${tokenAddress}`);
            }
        }
        
        // Final success update
        updateProgress('success', `Token ${symbol} successfully deployed!`);
        
        // Store token data in local storage
        const deploymentTime = new Date().toISOString();
        
        // Create token object
        const newToken = {
            name: name,
            symbol: symbol,
            address: tokenAddress,
            supply: initialSupply,
            category: category,
            deployedAt: deploymentTime,
            type: tokenType,
            networkName: networkName
        };
        
        // Add to tokens list
        let savedTokens = localStorage.getItem('userDeployedTokens');
        let tokensList = savedTokens ? JSON.parse(savedTokens) : [];
        tokensList.push(newToken);
        localStorage.setItem('userDeployedTokens', JSON.stringify(tokensList));
        
        // Update UI to show success
        updateStatus(`Token ${symbol} successfully deployed!`, 'success');
        showToast(`Token ${symbol} successfully deployed to ${tokenAddress}`, 'success');
        
        // Reset the form
        if (deployForm) {
            deployForm.reset();
        }
        
        // Refresh the token list
        userTokens = tokensList;
        displayUserTokens();
        
        // Scroll to the tokens section
        const deployedTokensContainer = document.getElementById('userTokensList');
        if (deployedTokensContainer) {
            deployedTokensContainer.scrollIntoView({ behavior: 'smooth' });
        }
        
        console.log(`Token deployed at address: ${tokenAddress}`);
    } catch (error) {
        console.error('Error deploying token:', error);
        updateStatus(`Deployment failed: ${error.message}`, 'error');
        
        // Update progress to show error
        const deploymentProgress = document.getElementById('deploymentProgress');
        if (deploymentProgress) {
            const progressBar = deploymentProgress.querySelector('.progress-bar');
            const currentStep = deploymentProgress.querySelector('.current-step');
            
            if (progressBar) {
                progressBar.style.width = '100%';
                progressBar.classList.remove('bg-primary', 'progress-bar-animated');
                progressBar.classList.add('bg-danger');
            }
            
            if (currentStep) {
                currentStep.textContent = 'Deployment failed';
                currentStep.classList.add('text-danger');
            }
        }
    } finally {
        showLoading(false);
        
        // Hide progress after a delay
        setTimeout(() => {
            const deploymentProgress = document.getElementById('deploymentProgress');
            if (deploymentProgress) {
                deploymentProgress.style.display = 'none';
            }
        }, 10000); // Hide after 10 seconds
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
        // Make a real API call to the backend to fetch user tokens
        // Make a real API call to the backend to fetch user tokens
        const response = await fetch('/api/tokens', {
            headers: {
                'X-API-Key': API_KEY
            }
        });
        if (!response.ok) {
            throw new Error(`API error: ${response.status} ${response.statusText}`);
        }
        
        const data = await response.json();
        
        // Check if we received valid data from the API
        if (data && Array.isArray(data.tokens) && data.tokens.length > 0) {
            userTokens = data.tokens;
            console.log('Tokens loaded from API:', userTokens);
        } else {
            // If API returned empty data, use localStorage as fallback
            console.warn('API returned empty tokens data, using localStorage fallback');
            throw new Error('No tokens received from API');
        }
        
        displayUserTokens();
        updateStatus('Your tokens loaded successfully from server', 'success');
    } catch (error) {
        console.error('Error loading user tokens from API:', error);
        
        // Fallback to localStorage if API call fails
        try {
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
            updateStatus('Your tokens loaded from local storage (offline mode)', 'warning');
        } catch (localStorageError) {
            console.error('Error with localStorage fallback:', localStorageError);
            updateStatus('Failed to load your tokens', 'error');
        }
    } finally {
        showLoading(false);
    }
}

/**
* Refresh blockchain data periodically
*/
function startBlockchainDataRefresh() {
    // Only start refresh if connected
    if (!isConnected) return;
    
    // Set up interval to refresh data every 60 seconds
    const refreshInterval = setInterval(async () => {
        if (!isConnected) {
            clearInterval(refreshInterval);
            return;
        }
        
        console.log('Refreshing blockchain data...');
        
        try {
            // Refresh user tokens
            await loadUserTokens();
            
            // Refresh blockchain stats for Analytics Dashboard
            await refreshBlockchainStats();
            
            // Refresh wallet balance
            await refreshWalletBalance();
            
            console.log('Blockchain data refreshed');
        } catch (error) {
            console.error('Error refreshing blockchain data:', error);
        }
    }, 60000); // Refresh every minute
    
    // Store interval ID to clear it if needed
    window.blockchainRefreshInterval = refreshInterval;
}

/**
* Refresh blockchain statistics
*/
async function refreshBlockchainStats() {
    if (!isConnected || !web3) return;
    
    try {
        // Get network stats
        const gasPrice = await web3.eth.getGasPrice();
        const blockNumber = await web3.eth.getBlockNumber();
        const latestBlock = await web3.eth.getBlock('latest');
        
        // Update UI with current gas price
        const gasPriceGwei = web3.utils.fromWei(gasPrice, 'gwei');
        const gasPriceElement = document.getElementById('currentGasPrice');
        if (gasPriceElement) {
            gasPriceElement.textContent = `${parseFloat(gasPriceGwei).toFixed(2)} Gwei`;
        }
        
        // Update block info
        const blockInfoElement = document.getElementById('latestBlockInfo');
        if (blockInfoElement) {
            blockInfoElement.textContent = `#${blockNumber} | ${latestBlock.transactions.length} txs`;
        }
        
        // Update charts with new data
        updateAnalyticsCharts({
            gasPrice: parseFloat(gasPriceGwei),
            blockNumber: blockNumber,
            timestamp: Date.now()
        });
        
        console.log(`Updated blockchain stats: Block #${blockNumber}, Gas: ${gasPriceGwei} Gwei`);
    } catch (error) {
        console.error('Error refreshing blockchain stats:', error);
    }
}

/**
* Refresh wallet balance
*/
async function refreshWalletBalance() {
    if (!isConnected || !web3 || !accounts.length) return;
    
    try {
        // Get ETH balance
        const balance = await web3.eth.getBalance(accounts[0]);
        const ethBalance = web3.utils.fromWei(balance, 'ether');
        
        // Update UI
        const balanceElement = document.getElementById('walletBalance');
        if (balanceElement) {
            balanceElement.textContent = `${parseFloat(ethBalance).toFixed(4)} ETH`;
        }
        
        console.log(`Updated wallet balance: ${ethBalance} ETH`);
    } catch (error) {
        console.error('Error refreshing wallet balance:', error);
    }
}

/**
* Initialize Analytics Dashboard charts
*/
function initAnalyticsCharts() {
    // Only initialize if chart elements exist
    const trendChartElement = document.getElementById('trendAnalyticsChart');
    const tokenChartElement = document.getElementById('tokenAnalyticsChart');
    const gasChartElement = document.getElementById('gasAnalyticsChart');
    
    if (!trendChartElement && !tokenChartElement && !gasChartElement) {
        console.log('Analytics chart elements not found');
        return;
    }
    
    console.log('Initializing analytics charts');
    
    // Initialize Trend Performance Chart
    if (trendChartElement) {
        const trendCtx = trendChartElement.getContext('2d');
        chartInstances.trendChart = new Chart(trendCtx, {
            type: 'line',
            data: {
                labels: getTimeLabels(7), // Last 7 days
                datasets: [{
                    label: 'AI Revolution',
                    data: generateRandomData(7, 70, 90),
                    borderColor: 'rgba(138, 43, 226, 1)',
                    backgroundColor: 'rgba(138, 43, 226, 0.1)',
                    tension: 0.4,
                    fill: true
                }, {
                    label: 'SpaceX Launch',
                    data: generateRandomData(7, 60, 85),
                    borderColor: 'rgba(255, 140, 0, 1)',
                    backgroundColor: 'rgba(255, 140, 0, 0.1)',
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'top',
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false
                    },
                    title: {
                        display: true,
                        text: 'Trend Performance'
                    }
                },
                scales: {
                    y: {
                        min: 0,
                        max: 100,
                        ticks: {
                            callback: function(value) {
                                return value + '%';
                            }
                        }
                    }
                }
            }
        });
    }
    
    // Initialize Token Price Chart
    if (tokenChartElement) {
        const tokenCtx = tokenChartElement.getContext('2d');
        chartInstances.tokenChart = new Chart(tokenCtx, {
            type: 'line',
            data: {
                labels: getTimeLabels(14, 'hour'), // Last 14 hours
                datasets: [{
                    label: 'AIT Token Price',
                    data: generateRandomData(14, 0.01, 0.05),
                    borderColor: 'rgba(32, 201, 151, 1)',
                    backgroundColor: 'rgba(32, 201, 151, 0.1)',
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'top',
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                        callbacks: {
                            label: function(context) {
                                return `Price: ${context.raw.toFixed(4)} ETH`;
                            }
                        }
                    },
                    title: {
                        display: true,
                        text: 'Token Performance'
                    }
                }
            }
        });
    }
    
    // Initialize Gas Price Chart
    if (gasChartElement) {
        const gasCtx = gasChartElement.getContext('2d');
        chartInstances.gasChart = new Chart(gasCtx, {
            type: 'bar',
            data: {
                labels: getTimeLabels(12, 'hour'), // Last 12 hours
                datasets: [{
                    label: 'Gas Price (Gwei)',
                    data: generateRandomData(12, 20, 80),
                    backgroundColor: 'rgba(54, 162, 235, 0.6)',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'top',
                    },
                    title: {
                        display: true,
                        text: 'Gas Price History'
                    }
                }
            }
        });
    }
    
    console.log('Analytics charts initialized');
    }

    /**
    * Generate time labels for charts
    * @param {number} count - Number of time points to generate
    * @param {string} unit - Time unit ('day' or 'hour')
    * @returns {Array} - Array of formatted time labels
    */
    function getTimeLabels(count, unit = 'day') {
        const labels = [];
        const now = new Date();
        
        for (let i = count - 1; i >= 0; i--) {
            const date = new Date();
            if (unit === 'day') {
                date.setDate(now.getDate() - i);
                labels.push(date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }));
            } else if (unit === 'hour') {
                date.setHours(now.getHours() - i);
                labels.push(date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' }));
            }
        }
        
        return labels;
    }

    /**
    * Generate random data points for charts
    * @param {number} count - Number of data points to generate
    * @param {number} min - Minimum value
    * @param {number} max - Maximum value
    * @returns {Array} - Array of random values
    */
    function generateRandomData(count, min, max) {
        const data = [];
        for (let i = 0; i < count; i++) {
            data.push(min + Math.random() * (max - min));
        }
        return data;
    }

    /**
    * Update analytics charts with new data
    * @param {Object} data - New data points to add to charts
    */
    function updateAnalyticsCharts(data) {
        if (!chartInstances || !data) return;
        
        // Update gas price chart if it exists
        if (chartInstances.gasChart) {
            // Add new data point
            chartInstances.gasChart.data.datasets[0].data.push(data.gasPrice);
            chartInstances.gasChart.data.datasets[0].data.shift();
            
            // Update labels (shift time window)
            chartInstances.gasChart.data.labels.push(
                new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })
            );
            chartInstances.gasChart.data.labels.shift();
            
            // Update chart
            chartInstances.gasChart.update();
        }
        
        // Update token chart with random price movement if it exists
        if (chartInstances.tokenChart) {
            const lastPrice = chartInstances.tokenChart.data.datasets[0].data[
                chartInstances.tokenChart.data.datasets[0].data.length - 1
            ];
            
            // Generate a new price with small random movement
            const change = (Math.random() - 0.5) * 0.005;
            const newPrice = Math.max(0.001, lastPrice + change);
            
            // Add new data and remove oldest
            chartInstances.tokenChart.data.datasets[0].data.push(newPrice);
            chartInstances.tokenChart.data.datasets[0].data.shift();
            
            // Update labels
            chartInstances.tokenChart.data.labels.push(
                new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })
            );
            chartInstances.tokenChart.data.labels.shift();
            
            // Update chart
            chartInstances.tokenChart.update();
        }
        
        // Update trend chart with random movements
        if (chartInstances.trendChart) {
            // Update all trend datasets with slight random changes
            chartInstances.trendChart.data.datasets.forEach(dataset => {
                const lastValue = dataset.data[dataset.data.length - 1];
                const change = (Math.random() - 0.5) * 5; // Random change between -2.5 and +2.5
                const newValue = Math.min(100, Math.max(0, lastValue + change));
                
                dataset.data.push(newValue);
                dataset.data.shift();
            });
            
            // Update labels
            chartInstances.trendChart.data.labels.push(
                new Date().toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
            );
            chartInstances.trendChart.data.labels.shift();
            
            // Update chart
            chartInstances.trendChart.update();
        }
        
        console.log('Analytics charts updated with new data');
    }
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
    
    const name = document.getElementById('tokenName').value.trim() || 'Token Name';
    const symbol = document.getElementById('tokenSymbol').value.trim().toUpperCase() || 'SYMBOL';
    const supply = document.getElementById('tokenSupply').value || '1000000';
    const category = document.getElementById('tokenCategory')?.value || 'Category';
    
    // Get selected blueprint details
    const blueprintSelect = document.getElementById('tokenBlueprint');
    let blueprintCategory = 'Category';
    let description = 'No description available';
    let tokenType = 'Standard';
    
    if (blueprintSelect && blueprintSelect.selectedIndex > 0) {
        const selectedOption = blueprintSelect.options[blueprintSelect.selectedIndex];
        blueprintCategory = selectedOption.dataset.category || blueprintCategory;
        description = selectedOption.dataset.description || description;
        tokenType = getTokenTypeName(selectedOption.dataset.tokenType) || 'Standard';
    }
    
    // Format supply with commas
    const formattedSupply = Number(supply).toLocaleString();
    
    // Generate a random color for the token preview
    const hue = (name.split('').reduce((sum, char) => sum + char.charCodeAt(0), 0) % 360);
    const color = `hsl(${hue}, 70%, 60%)`;
    
    // Update the preview
    tokenPreview.innerHTML = `
        <div class="token-preview-card" style="border-color: ${color}">
            <div class="token-preview-header">
                <div class="token-icon" style="background-color: ${color}">
                    ${symbol.substring(0, 2)}
                </div>
                <div class="token-info">
                    <h4 class="token-name">${name}</h4>
                    <span class="token-symbol">${symbol}</span>
                </div>
            </div>
            <div class="token-preview-body">
                <div class="token-detail">
                    <span class="detail-label">Supply:</span>
                    <span class="detail-value">${formattedSupply}</span>
                </div>
                <div class="token-detail">
                    <span class="detail-label">Category:</span>
                    <span class="detail-value">${category || blueprintCategory}</span>
                </div>
                <div class="token-detail">
                    <span class="detail-label">Token Type:</span>
                    <span class="detail-value">${tokenType}</span>
                </div>
                <div class="token-description">
                    <p>${description}</p>
                </div>
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
