import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import Web3 from 'web3';
import { toast } from 'react-toastify';

// Contract ABI (simplified example)
const TokenFactoryABI = [
  {
    "inputs": [
      { "internalType": "string", "name": "name", "type": "string" },
      { "internalType": "string", "name": "symbol", "type": "string" },
      { "internalType": "uint256", "name": "initialSupply", "type": "uint256" }
    ],
    "name": "createToken",
    "outputs": [{ "internalType": "address", "name": "", "type": "address" }],
    "stateMutability": "nonpayable",
    "type": "function"
  }
];

// Network configurations
const SUPPORTED_NETWORKS = {
  1: {
    name: 'Ethereum Mainnet',
    rpcUrl: 'https://mainnet.infura.io/v3/your-infura-key',
    currency: 'ETH',
    blockExplorer: 'https://etherscan.io'
  },
  5: {
    name: 'Goerli Testnet',
    rpcUrl: 'https://goerli.infura.io/v3/your-infura-key',
    currency: 'ETH',
    blockExplorer: 'https://goerli.etherscan.io'
  },
  137: {
    name: 'Polygon Mainnet',
    rpcUrl: 'https://polygon-rpc.com',
    currency: 'MATIC',
    blockExplorer: 'https://polygonscan.com'
  },
  80001: {
    name: 'Mumbai Testnet',
    rpcUrl: 'https://rpc-mumbai.maticvigil.com',
    currency: 'MATIC',
    blockExplorer: 'https://mumbai.polygonscan.com',
    isPreferred: true
  }
};

// Contract addresses
const CONTRACT_ADDRESSES = {
  1: { tokenFactory: '0x1234567890123456789012345678901234567890' },
  5: { tokenFactory: '0x2345678901234567890123456789012345678901' },
  137: { tokenFactory: '0x3456789012345678901234567890123456789012' },
  80001: { tokenFactory: '0x4567890123456789012345678901234567890123' }
};

// Demo wallet configurations
const DEMO_WALLET = {
  address: '0xDEMO000000000000000000000000000000000000',
  balance: '1000',
  networkId: 80001
};

// Async thunk for connecting wallet
export const connectWallet = createAsyncThunk(
  'wallet/connect',
  async (_, { rejectWithValue }) => {
    try {
      // Check if MetaMask is installed
      if (!window.ethereum) {
        toast.warning('No Ethereum wallet detected. Switching to demo mode.');
        return {
          accounts: [DEMO_WALLET.address],
          isDemoMode: true,
          isConnected: false,
          networkId: DEMO_WALLET.networkId,
          networkDetails: SUPPORTED_NETWORKS[DEMO_WALLET.networkId]
        };
      }

      // Request account access
      const accounts = await window.ethereum.request({ method: 'eth_requestAccounts' });
      
      // Initialize Web3
      const web3 = new Web3(window.ethereum);
      
      // Get network ID
      const networkId = await web3.eth.net.getId();
      
      // Check if network is supported
      if (!SUPPORTED_NETWORKS[networkId]) {
        toast.warning(`Network ID ${networkId} is not supported. Please switch to a supported network.`);
      }
      
      // Initialize contract
      let tokenFactoryContract = null;
      if (CONTRACT_ADDRESSES[networkId]?.tokenFactory) {
        tokenFactoryContract = new web3.eth.Contract(
          TokenFactoryABI,
          CONTRACT_ADDRESSES[networkId].tokenFactory
        );
      }
      
      return {
        accounts,
        web3,
        networkId,
        tokenFactoryContract,
        isConnected: true,
        isDemoMode: false,
        networkDetails: SUPPORTED_NETWORKS[networkId]
      };
    } catch (error) {
      console.error('Wallet connection error:', error);
      toast.error(`Failed to connect wallet: ${error.message}. Switching to demo mode.`);
      
      // Return demo mode instead of rejecting
      return {
        accounts: [DEMO_WALLET.address],
        isDemoMode: true,
        isConnected: false,
        networkId: DEMO_WALLET.networkId,
        networkDetails: SUPPORTED_NETWORKS[DEMO_WALLET.networkId]
      };
    }
  }
);

// Async thunk for checking existing connection
export const checkWalletConnection = createAsyncThunk(
  'wallet/checkConnection',
  async (_, { dispatch }) => {
    try {
      if (window.ethereum && localStorage.getItem('walletConnected') === 'true') {
        return dispatch(connectWallet()).unwrap();
      }
      
      // If previously in demo mode, restore that state
      if (localStorage.getItem('demoMode') === 'true') {
        return {
          accounts: [DEMO_WALLET.address],
          isDemoMode: true,
          isConnected: false,
          networkId: DEMO_WALLET.networkId,
          networkDetails: SUPPORTED_NETWORKS[DEMO_WALLET.networkId]
        };
      }
      
      return {
        isConnected: false,
        isDemoMode: false
      };
    } catch (error) {
      console.error('Error checking wallet connection:', error);
      return {
        isConnected: false,
        isDemoMode: false
      };
    }
  }
);

// Wallet slice
const walletSlice = createSlice({
  name: 'wallet',
  initialState: {
    accounts: [],
    web3: null,
    networkId: null,
    tokenFactoryContract: null,
    isConnected: false,
    isDemoMode: false,
    loading: false,
    error: null,
    networkDetails: null,
    balance: '0'
  },
  reducers: {
    enableDemoMode: (state) => {
      state.isDemoMode = true;
      state.accounts = [DEMO_WALLET.address];
      state.networkId = DEMO_WALLET.networkId;
      state.networkDetails = SUPPORTED_NETWORKS[DEMO_WALLET.networkId];
      state.balance = DEMO_WALLET.balance;
      localStorage.setItem('demoMode', 'true');
      toast.info('Demo mode enabled. You can explore all features without a real wallet.');
    },
    disconnectWallet: (state) => {
      state.isConnected = false;
      state.accounts = [];
      state.web3 = null;
      state.tokenFactoryContract = null;
      state.balance = '0';
      localStorage.removeItem('walletConnected');
      toast.info('Wallet disconnected.');
    },
    updateBalance: (state, action) => {
      state.balance = action.payload;
    }
  },
  extraReducers: (builder) => {
    builder
      .addCase(connectWallet.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(connectWallet.fulfilled, (state, action) => {
        state.loading = false;
        state.accounts = action.payload.accounts;
        state.web3 = action.payload.web3;
        state.networkId = action.payload.networkId;
        state.tokenFactoryContract = action.payload.tokenFactoryContract;
        state.isConnected = action.payload.isConnected;
        state.isDemoMode = action.payload.isDemoMode;
        state.networkDetails = action.payload.networkDetails;
        
        // If successfully connected, store in localStorage
        if (state.isConnected) {
          localStorage.setItem('walletConnected', 'true');
          localStorage.removeItem('demoMode');
        }
        
        // If in demo mode, store in localStorage
        if (state.isDemoMode) {
          localStorage.setItem('demoMode', 'true');
          localStorage.removeItem('walletConnected');
          state.balance = DEMO_WALLET.balance;
        }
      })
      .addCase(connectWallet.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload || 'Failed to connect wallet';
        state.isConnected = false;
      })
      .addCase(checkWalletConnection.fulfilled, (state, action) => {
        // Only update if we actually got connection details
        if (action.payload.accounts) {
          state.accounts = action.payload.accounts;
          state.web3 = action.payload.web3;
          state.networkId = action.payload.networkId;
          state.tokenFactoryContract = action.payload.tokenFactoryContract;
          state.isConnected = action.payload.isConnected;
          state.isDemoMode = action.payload.isDemoMode;
          state.networkDetails = action.payload.networkDetails;
          
          if (state.isDemoMode) {
            state.balance = DEMO_WALLET.balance;
          }
        }
      });
  }
});

export const { enableDemoMode, disconnectWallet, updateBalance } = walletSlice.actions;
export default walletSlice.reducer;

