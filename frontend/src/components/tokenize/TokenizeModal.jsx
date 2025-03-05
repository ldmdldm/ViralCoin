import React, { useState, useEffect } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Box,
  TextField,
  Button,
  Typography,
  Stepper,
  Step,
  StepLabel,
  CircularProgress,
  Chip,
  IconButton,
  InputAdornment,
  Divider,
  Slider,
  Tooltip,
  Stack,
  Alert,
  FormControl,
  FormLabel,
  RadioGroup,
  FormControlLabel,
  Radio,
  useTheme,
  Paper,
  Grid,
} from '@mui/material';
import { motion, AnimatePresence } from 'framer-motion';

// Icons
import CloseIcon from '@mui/icons-material/Close';
import TokenIcon from '@mui/icons-material/Token';
import HelpOutlineIcon from '@mui/icons-material/HelpOutline';
import AttachMoneyIcon from '@mui/icons-material/AttachMoney';
import ShowChartIcon from '@mui/icons-material/ShowChart';
import CheckCircleOutlineIcon from '@mui/icons-material/CheckCircleOutline';
import RefreshIcon from '@mui/icons-material/Refresh';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import SettingsIcon from '@mui/icons-material/Settings';
import LaunchIcon from '@mui/icons-material/Launch';

// Redux actions
import { closeModal } from '../../redux/slices/uiSlice';
import { toast } from 'react-toastify';

// Steps for token creation
const steps = ['Token Details', 'Tokenomics', 'Review & Deploy'];

// Animation variants
const variants = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.3 } },
  exit: { opacity: 0, y: -20, transition: { duration: 0.2 } }
};

const TokenizeModal = () => {
  const theme = useTheme();
  const dispatch = useDispatch();

  // Redux state
  const { isConnected, isDemoMode, networkDetails, web3, tokenFactoryContract, accounts } = useSelector((state) => state.wallet);
  const { modals, modalData } = useSelector((state) => state.ui);

  // Local state
  const [activeStep, setActiveStep] = useState(0);
  const [isDeploying, setIsDeploying] = useState(false);
  const [deployedTokenAddress, setDeployedTokenAddress] = useState('');
  const [deploymentError, setDeploymentError] = useState('');
  const [advancedMode, setAdvancedMode] = useState(false);
  const [txHash, setTxHash] = useState('');

  // Form state
  const [tokenDetails, setTokenDetails] = useState({
    name: '',
    symbol: '',
    description: '',
    initialSupply: 1000000,
    tokenType: 'standard', // standard, governance, social
    royaltyFee: 2.5, // percentage
    mintable: true,
    burnable: true,
  });

  // Get topic from modal data
  const topic = modalData?.topic || {};

  // Set initial token details based on topic
  useEffect(() => {
    if (topic && topic.name) {
      // Create abbreviation for token symbol
      const createSymbol = (name) => {
        // Get first letters of each word and capitalize
        const words = name.split(' ');
        let symbol = words.map(word => word[0]?.toUpperCase() || '').join('');
        
        // If less than 3 letters, use first 3 letters of first word
        if (symbol.length < 3 && words[0]?.length >= 3) {
          symbol = words[0].substring(0, 3).toUpperCase();
        }
        
        // If still not enough, add T for "Token"
        if (symbol.length < 3) {
          symbol = symbol + 'T'.repeat(3 - symbol.length);
        }
        
        return symbol;
      };

      setTokenDetails({
        ...tokenDetails,
        name: `${topic.name} Token`,
        symbol: createSymbol(topic.name),
        description: `Token representing the trending topic: ${topic.name}. ${topic.description || ''}`,
      });
    }
  }, [topic]);

  // Handle form changes
  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setTokenDetails({
      ...tokenDetails,
      [name]: type === 'checkbox' ? checked : value,
    });
  };

  // Handle slider changes
  const handleSliderChange = (name) => (_, value) => {
    setTokenDetails({
      ...tokenDetails,
      [name]: value,
    });
  };

  // Handle radio changes
  const handleRadioChange = (e) => {
    setTokenDetails({
      ...tokenDetails,
      tokenType: e.target.value,
    });
  };

  // Step navigation
  const handleNext = () => {
    setActiveStep((prevActiveStep) => prevActiveStep + 1);
  };

  const handleBack = () => {
    setActiveStep((prevActiveStep) => prevActiveStep - 1);
  };

  // Token deployment
  const handleDeploy = async () => {
    setIsDeploying(true);
    setDeploymentError('');

    try {
      if (isDemoMode) {
        // Simulate deployment process
        await simulateDeployment();
      } else if (isConnected && tokenFactoryContract) {
        // Real deployment
        await deployToken();
      } else {
        throw new Error('Wallet not connected or contract not initialized.');
      }
    } catch (error) {
      console.error('Deployment error:', error);
      setDeploymentError(error.message || 'Failed to deploy token.');
    } finally {
      setIsDeploying(false);
    }
  };

  // Simulate deployment process for demo mode
  const simulateDeployment = async () => {
    // Step 1: Preparing
    await sleep(1000);
    
    // Step 2: Validation
    await sleep(800);
    
    // Step 3: Contract initialization
    await sleep(1200);
    
    // Step 4: Generate mock address and tx hash
    const mockAddress = '0x' + Array(40).fill(0).map(() => Math.floor(Math.random() * 16).toString(16)).join('');
    const mockTxHash = '0x' + Array(64).fill(0).map(() => Math.floor(Math.random() * 16).toString(16)).join('');
    
    setDeployedTokenAddress(mockAddress);
    setTxHash(mockTxHash);
  };

  // Real token deployment
  const deployToken = async () => {
    try {
      const account = accounts[0];
      const supply = web3.utils.toWei(tokenDetails.initialSupply.toString(), 'ether');
      
      // Get token type ID
      const tokenTypeId = 
        tokenDetails.tokenType === 'governance' ? 2 : 
        tokenDetails.tokenType === 'social' ? 3 : 1;
      
      // Estimate gas
      const gasEstimate = await tokenFactoryContract.methods
        .createToken(
          tokenDetails.name,
          tokenDetails.symbol,
          supply,
          tokenTypeId
        )
        .estimateGas({ from: account });
      
      // Send transaction
      const tx = await tokenFactoryContract.methods
        .createToken(
          tokenDetails.name,
          tokenDetails.symbol, 
          supply,
          tokenTypeId
        )
        .send({ 
          from: account,
          gas: Math.floor(gasEstimate * 1.2) // Add 20% buffer
        });
      
      // Save transaction hash
      setTxHash(tx.transactionHash);
      
      // Get token address from events
      const tokenAddress = tx.events.TokenCreated?.returnValues.tokenAddress;
      setDeployedTokenAddress(tokenAddress);
    } catch (error) {
      throw error;
    }
  };

  // Utility sleep function
  const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms));

  // Validate current step
  const validateStep = () => {
    switch (activeStep) {
      case 0:
        return !tokenDetails.name || !tokenDetails.symbol || !tokenDetails.description;
      case 1:
        return tokenDetails.initialSupply <= 0;
      default:
        return false;
    }
  };

  // Copy to clipboard
  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    toast.success('Copied to clipboard!');
  };

  // Handle close
  const handleClose = () => {
    dispatch(closeModal('tokenizeModal'));
  };

  // View on explorer
  const getExplorerUrl = (address, type = 'address') => {
    if (!address) return '#';
    
    const explorerUrl = networkDetails?.blockExplorer || 'https://mumbai.polygonscan.com';
    return `${explorerUrl}/${type}/${address}`;
  };

  return (
    <Dialog
      open={modals.tokenizeModal}
      onClose={isDeploying ? undefined : handleClose}
      maxWidth="md"
      fullWidth
      PaperProps={{
        sx: {
          borderRadius: 2,
          background: theme.palette.background.paper,
        },
      }}
    >
      {/* Dialog Header */}
      <DialogTitle sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', pb: 1 }}>
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          <TokenIcon color="secondary" sx={{ mr: 1 }} />
          <Typography variant="h6">
            {deployedTokenAddress 
              ? 'Token Deployed Successfully' 
              : `Tokenize "${topic.name || 'Trend'}"`}
          </Typography>
        </Box>
        <IconButton onClick={isDeploying ? undefined : handleClose} size="small" disabled={isDeploying}>
          <CloseIcon />
        </IconButton>
      </DialogTitle>
      <Divider />

      {/* Stepper */}
      {!deployedTokenAddress && (
        <Box sx={{ p: 2, pb: 0 }}>
          <Stepper activeStep={activeStep} alternativeLabel>
            {steps.map((label) => (
              <Step key={label}>
                <StepLabel>{label}</StepLabel>
              </Step>
            ))}
          </Stepper>
        </Box>
      )}
      
      {/* Dialog Content */}
      <DialogContent sx={{ pt: 2 }}>
        {deploymentError && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {deploymentError}
          </Alert>
        )}

        <AnimatePresence mode="wait">
          <motion.div
            key={activeStep}
            variants={variants}
            initial="hidden"
            animate="visible"
            exit="exit"
          >
            {/* Step 1: Token Details */}
            {activeStep === 0 && !deployedTokenAddress && (
              <Box>
                <Box sx={{ mb: 3 }}>
                  <Typography variant="subtitle1" gutterBottom>
                    Basic Information
                  </Typography>
                  <TextField
                    fullWidth
                    label="Token Name"
                    name="name"
                    value={tokenDetails.name}
                    onChange={handleChange}
                    margin="normal"
                    variant="outlined"
                    required
                    helperText="The full name of your token"
                  />
                  <TextField
                    fullWidth
                    label="Token Symbol"
                    name="symbol"
                    value={tokenDetails.symbol}
                    onChange={handleChange}
                    margin="normal"
                    variant="outlined"
                    required
                    inputProps={{ maxLength: 5 }}
                    helperText="3-5 capital letters (e.g., BTC, ETH)"
                  />
                  <TextField
                    fullWidth
                    label="Description"
                    name="description"
                    value={tokenDetails.description}
                    onChange={handleChange}
                    margin="normal"
                    variant="outlined"
                    required
                    multiline
                    rows={3}
                    helperText="Describe your token's purpose and utility"
                  />
                </Box>

                <Box sx={{ mt: 3 }}>
                  <Typography variant="subtitle1" gutterBottom>
                    Token Type
                  </Typography>
                  <FormControl component="fieldset">
                    <RadioGroup
                      name="tokenType"
                      value={tokenDetails.tokenType}
                      onChange={handleRadioChange}
                      row
                    >
                      <FormControlLabel
                        value="standard"
                        control={<Radio />}
                        label="Standard"
                      />
                      <FormControlLabel
                        value="governance"
                        control={<Radio />}
                        label="Governance"
                      />
                      <FormControlLabel
                        value="social"
                        control={<Radio />}
                        label="Social"
                      />
                    </RadioGroup>
                  </FormControl>
                  <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                    {tokenDetails.tokenType === 'standard' && "Standard tokens have basic ERC-20 functionality. Good for simple use cases."}
                    {tokenDetails.tokenType === 'governance' && "Governance tokens come with voting capabilities. Good for community-driven projects."}
                    {tokenDetails.tokenType === 'social' && "Social tokens include engagement tracking and royalty features. Good for creators."}
                  </Typography>
                </Box>
              </Box>
            )}
            
            {/* Step 2: Tokenomics */}
            {activeStep === 1 && !deployedTokenAddress && (
              <Box>
                <Typography variant="subtitle1" gutterBottom>
                  Supply & Distribution
                </Typography>
                
                <Box sx={{ mb: 4 }}>
                  <Typography variant="body2" gutterBottom>
                    Initial Supply
                  </Typography>
                  <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    <TextField
                      type="number"
                      name="initialSupply"
                      value={tokenDetails.initialSupply}
                      onChange={handleChange}
                      variant="outlined"
                      InputProps={{
                        endAdornment: <InputAdornment position="end">tokens</InputAdornment>,
                      }}
                      sx={{ width: '200px', mr: 2 }}
                    />
                    <Box sx={{ flexGrow: 1 }}>
                      <Slider
                        value={tokenDetails.initialSupply}
                        onChange={handleSliderChange('initialSupply')}
                        min={100000}
                        max={10000000000}
                        step={100000}
                        valueLabelDisplay="auto"
                        valueLabelFormat={(value) =>

