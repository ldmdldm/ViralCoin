import React, { useState, useEffect } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import {
  Box,
  Container,
  Typography,
  Button,
  Grid,
  Card,
  CardContent,
  CardHeader,
  CardActions,
  Divider,
  TextField,
  FormControl,
  FormLabel,
  InputLabel,
  Select,
  MenuItem,
  Switch,
  FormControlLabel,
  Slider,
  Tooltip,
  InputAdornment,
  Avatar,
  Chip,
  Paper,
  Tab,
  Tabs,
  Alert,
  useTheme,
  alpha,
  Stack,
  IconButton,
} from '@mui/material';
import { motion } from 'framer-motion';

// Components
import TokenizeModal from '../components/tokenize/TokenizeModal';

// Icons
import TokenIcon from '@mui/icons-material/Token';
import RocketLaunchIcon from '@mui/icons-material/RocketLaunch';
import SettingsIcon from '@mui/icons-material/Settings';
import AccountBalanceWalletIcon from '@mui/icons-material/AccountBalanceWallet';
import PreviewIcon from '@mui/icons-material/Preview';
import HelpOutlineIcon from '@mui/icons-material/HelpOutline';
import VisibilityIcon from '@mui/icons-material/Visibility';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import AddIcon from '@mui/icons-material/Add';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import BarChartIcon from '@mui/icons-material/BarChart';
import TimelineIcon from '@mui/icons-material/Timeline';
import HistoryIcon from '@mui/icons-material/History';
import LaunchIcon from '@mui/icons-material/Launch';

// Redux actions
import { connectWallet, enableDemoMode } from '../redux/slices/walletSlice';
import { openModal } from '../redux/slices/uiSlice';
import { toast } from 'react-toastify';

// Animation variants
const containerVariants = {
  hidden: { opacity: 0 },
  visible: { 
    opacity: 1,
    transition: { staggerChildren: 0.1 }
  }
};

const itemVariants = {
  hidden: { y: 20, opacity: 0 },
  visible: { 
    y: 0, 
    opacity: 1,
    transition: { type: 'spring', stiffness: 80, damping: 12 }
  }
};

// Token Template options
const tokenTemplates = [
  { id: 'standard', name: 'Standard Token', description: 'Basic ERC-20 token with standard features' },
  { id: 'social', name: 'Social Token', description: 'Token with social engagement features and royalties' },
  { id: 'governance', name: 'Governance Token', description: 'Token with voting and governance capabilities' },
  { id: 'reward', name: 'Reward Token', description: 'Token designed for rewards and loyalty programs' },
];

// Sample user tokens for UI demonstration
const sampleUserTokens = [
  {
    id: 1,
    name: 'AI Revolution Token',
    symbol: 'AIRT',
    address: '0x1234567890123456789012345678901234567890',
    supply: 10000000,
    network: 'Mumbai',
    category: 'Technology',
    tokenType: 'governance',
    deploymentDate: '2023-08-15T14:30:00Z',
    createdFromTrend: true,
    trendId: 1
  },
  {
    id: 2,
    name: 'NFT Gaming Token',
    symbol: 'NFTG',
    address: '0x2345678901234567890123456789012345678901',
    supply: 5000000,
    network: 'Mumbai',
    category: 'Entertainment',
    tokenType: 'social',
    deploymentDate: '2023-09-02T09:45:00Z',
    createdFromTrend: true,
    trendId: 3
  },
  {
    id: 3,
    name: 'MetaverseCoin',
    symbol: 'MVC',
    address: '0x3456789012345678901234567890123456789012',
    supply: 100000000,
    network: 'Mumbai',
    category: 'Crypto',
    tokenType: 'standard',
    deploymentDate: '2023-10-10T16:20:00Z',
    createdFromTrend: false,
    trendId: null
  }
];

const TokenizePage = () => {
  const theme = useTheme();
  const dispatch = useDispatch();
  
  // Redux state
  const { isConnected, isDemoMode, networkDetails, accounts } = useSelector(state => state.wallet);
  const { allTopics } = useSelector(state => state.trending);
  
  // Local state
  const [tokenForm, setTokenForm] = useState({
    name: '',
    symbol: '',
    description: '',
    initialSupply: 1000000,
    templateId: 'standard',
    category: '',
    mintable: true,
    burnable: true,
    taxFee: 2,
    transferDelay: 0
  });
  const [advancedMode, setAdvancedMode] = useState(false);
  const [currentTab, setCurrentTab] = useState(0);
  const [userTokens, setUserTokens] = useState([]);
  
  // Load user tokens on mount
  useEffect(() => {
    // In a real app, you would fetch these from an API or blockchain
    // Here we're using sample data for demonstration
    setUserTokens(sampleUserTokens);
  }, []);
  
  // Handle form changes
  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setTokenForm(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };
  
  // Handle slider changes
  const handleSliderChange = (name) => (_, value) => {
    setTokenForm(prev => ({
      ...prev,
      [name]: value
    }));
  };

  // Handle tab change
  const handleTabChange = (_, newValue) => {
    setCurrentTab(newValue);
  };

  // Handle deploy button click
  const handleDeploy = () => {
    // If not connected, prompt to connect wallet
    if (!isConnected && !isDemoMode) {
      dispatch(openModal({ modalType: 'walletModal' }));
      return;
    }
    
    // Otherwise, open tokenize modal with form data
    dispatch(openModal({ 
      modalType: 'tokenizeModal',
      data: { 
        topic: {
          name: tokenForm.name,
          description: tokenForm.description
        },
        tokenDetails: tokenForm
      }
    }));
  };

  // Copy address to clipboard
  const copyAddress = (address) => {
    navigator.clipboard.writeText(address);
    toast.success('Address copied to clipboard!');
  };

  // Check if form is valid
  const isFormValid = () => {
    return (
      tokenForm.name.trim() !== '' && 
      tokenForm.symbol.trim() !== '' && 
      tokenForm.description.trim() !== '' &&
      tokenForm.category !== '' &&
      tokenForm.initialSupply > 0
    );
  };

  // Format a date string
  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    }).format(date);
  };

  // Get network color based on network name
  const getNetworkColor = (network) => {
    const networks = {
      'Ethereum': '#627EEA',
      'Polygon': '#8247E5',
      'Mumbai': '#8247E5',
      'BSC': '#F3BA2F',
      'Arbitrum': '#28A0F0'
    };
    
    return networks[network] || theme.palette.primary.main;
  };

  // Get explorer URL for a token address
  const getExplorerUrl = (address) => {
    if (!address) return '#';
    const explorerUrl = networkDetails?.blockExplorer || 'https://mumbai.polygonscan.com';
    return `${explorerUrl}/token/${address}`;
  };

  // Generate token symbol from name
  const generateSymbolFromName = (name) => {
    if (!name) return '';
    
    // Get first letters of each word
    const words = name.trim().split(/\s+/);
    let symbol = words.map(word => word[0]?.toUpperCase() || '').join('');
    
    // If less than 3 letters, use first 3 letters of first word
    if (symbol.length < 3 && words[0]?.length >= 3) {
      symbol = words[0].substring(0, 3).toUpperCase();
    }
    
    // If still not enough, add T for "Token"
    if (symbol.length < 3) {
      symbol = symbol + 'T'.repeat(3 - symbol.length);
    }
    
    return symbol.substring(0, 5); // Limit to 5 characters
  };

  // Update symbol when name changes
  useEffect(() => {
    if (tokenForm.name && (!tokenForm.symbol || tokenForm.symbol === '')) {
      setTokenForm(prev => ({
        ...prev,
        symbol: generateSymbolFromName(prev.name)
      }));
    }
  }, [tokenForm.name]);

  return (
    <Container maxWidth="xl">
      <Box sx={{ py: 4 }}>
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <Typography 
            variant="h3" 
            component="h1" 
            gutterBottom
            sx={{ 
              display: 'flex', 
              alignItems: 'center',
              fontWeight: 'bold'
            }}
          >
            <TokenIcon sx={{ mr: 2, fontSize: 40 }} color="primary" />
            Token Generator
          </Typography>
          <Typography variant="h6" color="text.secondary" gutterBottom sx={{ mb: 4 }}>
            Create, deploy, and manage viral tokens on the blockchain
          </Typography>
        </motion.div>

        {!isConnected && !isDemoMode && (
          <Alert 
            severity="info" 
            sx={{ mb: 4 }}
            action={
              <Stack direction="row" spacing={1}>
                <Button 
                  size="small" 
                  color="primary" 
                  variant="outlined"
                  onClick={() => dispatch(connectWallet())}
                  startIcon={<AccountBalanceWalletIcon />}
                >
                  Connect Wallet
                </Button>
                <Button 
                  size="small" 
                  color="secondary"
                  onClick={() => dispatch(enableDemoMode())}
                >
                  Try Demo
                </Button>
              </Stack>
            }
          >
            Connect your wallet or use demo mode to deploy tokens
          </Alert>
        )}

        {/* Tabs for Create/Manage */}
        <Paper sx={{ mb: 4 }}>
          <Tabs 
            value={currentTab} 
            onChange={handleTabChange}
            variant="fullWidth"
            indicatorColor="primary"
            textColor="primary"
          >
            <Tab icon={<AddIcon />} label="Create Token" />
            <Tab icon={<HistoryIcon />} label="My Tokens" />
          </Tabs>
        </Paper>

        {/* Create Token Tab */}
        {currentTab === 0 && (
          <motion.div
            variants={containerVariants}
            initial="hidden"
            animate="visible"
          >
            <Grid container spacing={4}>
              {/* Token Form */}
              <Grid item xs={12} md={8}>
                <motion.div variants={itemVariants}>
                  <Paper
                    elevation={3}
                    sx={{ 
                      p: 3, 
                      borderRadius: 2,
                      height: '100%',
                    }}
                  >
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
                      <Typography variant="h5" fontWeight="bold">
                        Token Details
                      </Typography>
                      <Box sx={{ display: 'flex', alignItems: 'center' }}>
                        <Typography variant="body2" sx={{ mr: 1 }}>Advanced Mode</Typography>
                        <Switch
                          checked={advancedMode}
                          onChange={(e) => setAdvancedMode(e.target.checked)}
                          color="primary"
                        />
                      </Box>
                    </Box>
                    
                    <Grid container spacing={3}>
                      <Grid item xs={12} sm={6}>
                        <TextField
                          label="Token Name"
                          name="name"
                          value={tokenForm.name}
                          onChange={handleChange}
                          fullWidth
                          required
                          helperText="Name of your token (e.g., 'Bitcoin')"
                        />
                      </Grid>
                      <Grid item xs={12} sm={6}>
                        <TextField
                          label="Token Symbol"
                          name="symbol"
                          value={tokenForm.symbol}
                          onChange={handleChange}
                          fullWidth
                          required
                          inputProps={{ maxLength: 5 }}
                          helperText="3-5 character symbol (e.g., 'BTC')"
                        />
                      </Grid>
                      <Grid item xs={12}>
                        <TextField
                          label="Description"
                          name="description"
                          value={tokenForm.description}
                          onChange={handleChange}
                          fullWidth
                          required
                          multiline
                          rows={3}
                          helperText="Brief description of your token's purpose"
                        />
                      </Grid>
                      <Grid item xs={12} sm={6}>
                        <TextField
                          label="Initial Supply"
                          name="initialSupply"
                          type="number"
                          value={tokenForm.initialSupply}
                          onChange={handleChange}
                          fullWidth
                          required
                          InputProps={{
                            endAdornment: <InputAdornment position="end">tokens</InputAdornment>,
                          }}
                          helperText="Total number of tokens to create"
                        />
                      </Grid>
                      <Grid item xs={12} sm={6}>

