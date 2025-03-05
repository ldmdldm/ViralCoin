import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useSelector, useDispatch } from 'react-redux';
import {
  Box,
  Container,
  Typography,
  Button,
  Grid,
  Card,
  CardContent,
  CardMedia,
  CardActions,
  Divider,
  Paper,
  useTheme,
  alpha,
  Stack,
  Avatar,
  Chip,
} from '@mui/material';
import { motion } from 'framer-motion';

// Components
import TrendingTopics from '../components/trending/TrendingTopics';

// Icons
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import TokenIcon from '@mui/icons-material/Token';
import ShowChartIcon from '@mui/icons-material/ShowChart';
import PeopleIcon from '@mui/icons-material/People';
import AccountBalanceWalletIcon from '@mui/icons-material/AccountBalanceWallet';
import KeyboardArrowRightIcon from '@mui/icons-material/KeyboardArrowRight';
import MonetizationOnIcon from '@mui/icons-material/MonetizationOn';
import ShieldIcon from '@mui/icons-material/Shield';
import SpeedIcon from '@mui/icons-material/Speed';

// Redux actions
import { connectWallet, enableDemoMode } from '../redux/slices/walletSlice';

// Animation variants
const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.2,
      delayChildren: 0.1,
    },
  },
};

const itemVariants = {
  hidden: { y: 20, opacity: 0 },
  visible: {
    y: 0,
    opacity: 1,
    transition: {
      type: 'spring',
      stiffness: 100,
      damping: 12,
    },
  },
};

// Features data
const features = [
  {
    title: 'Trend Detection',
    description: 'Our AI algorithms scan the web to identify the most viral trends before they hit mainstream.',
    icon: <TrendingUpIcon fontSize="large" />,
    color: '#8a2be2', // Primary purple
  },
  {
    title: 'Token Creation',
    description: 'Create custom tokens for any trending topic with just a few clicks. No coding required.',
    icon: <TokenIcon fontSize="large" />,
    color: '#ff8c00', // Secondary orange
  },
  {
    title: 'Market Dynamics',
    description: 'Token value dynamically responds to the continued virality and engagement of the trend.',
    icon: <ShowChartIcon fontSize="large" />,
    color: '#00bfff', // Blue
  },
  {
    title: 'Community Trading',
    description: 'Buy, sell, and trade trend tokens with other users through integrated DEX functionality.',
    icon: <PeopleIcon fontSize="large" />,
    color: '#32cd32', // Green
  },
];

// How it works steps
const steps = [
  {
    title: 'Connect Your Wallet',
    description: 'Link your Ethereum wallet to the platform with a single click',
    icon: <AccountBalanceWalletIcon fontSize="large" />,
    color: '#8a2be2',
  },
  {
    title: 'Discover Trending Topics',
    description: 'Browse our curated list of trending topics across different categories',
    icon: <TrendingUpIcon fontSize="large" />,
    color: '#ff8c00',
  },
  {
    title: 'Create Your Token',
    description: 'Select a trend and configure your token parameters with our easy interface',
    icon: <TokenIcon fontSize="large" />,
    color: '#00bfff',
  },
  {
    title: 'Start Earning',
    description: 'As your trend gains popularity, watch your token's value grow',
    icon: <MonetizationOnIcon fontSize="large" />,
    color: '#32cd32',
  },
];

const HomePage = () => {
  const theme = useTheme();
  const navigate = useNavigate();
  const dispatch = useDispatch();
  
  // Redux state
  const { isConnected, isDemoMode } = useSelector((state) => state.wallet);
  const { filteredTopics } = useSelector((state) => state.trending);
  
  // Handlers
  const handleConnectWallet = () => {
    dispatch(connectWallet());
  };
  
  const handleTryDemo = () => {
    dispatch(enableDemoMode());
  };

  return (
    <Box>
      {/* Hero Section */}
      <Box 
        sx={{ 
          pt: 12, 
          pb: 10,
          background: `linear-gradient(135deg, ${alpha(theme.palette.primary.main, 0.1)}, ${alpha(theme.palette.secondary.main, 0.1)})`,
          borderRadius: '0 0 24px 24px',
          overflow: 'hidden',
          position: 'relative',
        }}
      >
        <motion.div
          initial={{ opacity: 0.3, scale: 1.2 }}
          animate={{ opacity: 0.05, scale: 1 }}
          transition={{ duration: 1.5 }}
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'url(/img/pattern-bg.svg)',
            backgroundSize: 'cover',
            zIndex: 0,
          }}
        />
        <Container maxWidth="xl" sx={{ position: 'relative', zIndex: 1 }}>
          <Grid container spacing={4} alignItems="center">
            <Grid item xs={12} md={6}>
              <motion.div
                initial={{ opacity: 0, x: -30 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.7 }}
              >
                <Typography 
                  variant="h2" 
                  component="h1" 
                  gutterBottom
                  sx={{ 
                    fontWeight: 800,
                    background: `linear-gradient(135deg, ${theme.palette.primary.main}, ${theme.palette.secondary.main})`,
                    WebkitBackgroundClip: 'text',
                    WebkitTextFillColor: 'transparent',
                    mb: 3,
                  }}
                >
                  Turn Viral Trends Into Digital Assets
                </Typography>
                <Typography variant="h5" paragraph color="text.secondary" sx={{ mb: 4, maxWidth: '90%' }}>
                  ViralCoin helps you discover, tokenize, and monetize trending topics 
                  before they go mainstream.
                </Typography>
                <Box sx={{ mt: 5 }}>
                  {!isConnected && !isDemoMode ? (
                    <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
                      <Button 
                        variant="contained" 
                        size="large" 
                        color="primary"
                        onClick={handleConnectWallet}
                        startIcon={<AccountBalanceWalletIcon />}
                        sx={{ px: 4, py: 1.5, borderRadius: 2, fontWeight: 600 }}
                      >
                        Connect Wallet
                      </Button>
                      <Button 
                        variant="outlined" 
                        size="large" 
                        color="secondary"
                        onClick={handleTryDemo}
                        sx={{ px: 4, py: 1.5, borderRadius: 2, fontWeight: 600 }}
                      >
                        Try Demo Mode
                      </Button>
                    </Stack>
                  ) : (
                    <Button 
                      variant="contained" 
                      size="large" 
                      color="primary"
                      onClick={() => navigate('/trending')}
                      endIcon={<KeyboardArrowRightIcon />}
                      sx={{ px: 4, py: 1.5, borderRadius: 2, fontWeight: 600 }}
                    >
                      Explore Trends
                    </Button>
                  )}
                </Box>
              </motion.div>
            </Grid>
            <Grid item xs={12} md={6}>
              <motion.div
                initial={{ opacity: 0, y: 30 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.7, delay: 0.2 }}
              >
                <Box 
                  component="img"
                  src="/img/hero-illustration.svg"
                  alt="ViralCoin concept"
                  sx={{ 
                    width: '100%',
                    height: 'auto',
                    filter: 'drop-shadow(0px 10px 20px rgba(0, 0, 0, 0.15))',
                  }}
                />
              </motion.div>
            </Grid>
          </Grid>
        </Container>
      </Box>

      {/* Stats Section */}
      <Container maxWidth="xl">
        <Box 
          sx={{ 
            mt: -5, 
            mb: 10,
            p: 3,
            borderRadius: 4,
            boxShadow: 3,
            bgcolor: 'background.paper',
          }}
        >
          <Grid container spacing={3} justifyContent="center">
            <Grid item xs={6} md={3}>
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.3 }}
              >
                <Box textAlign="center">
                  <Typography variant="h3" color="primary" fontWeight="bold">500+</Typography>
                  <Typography variant="body1" color="text.secondary">Active Trends</Typography>
                </Box>
              </motion.div>
            </Grid>
            <Grid item xs={6} md={3}>
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.5 }}
              >
                <Box textAlign="center">
                  <Typography variant="h3" color="primary" fontWeight="bold">12K+</Typography>
                  <Typography variant="body1" color="text.secondary">Tokens Created</Typography>
                </Box>
              </motion.div>
            </Grid>
            <Grid item xs={6} md={3}>
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.7 }}
              >
                <Box textAlign="center">
                  <Typography variant="h3" color="primary" fontWeight="bold">$2.5M</Typography>
                  <Typography variant="body1" color="text.secondary">Trading Volume</Typography>
                </Box>
              </motion.div>
            </Grid>
            <Grid item xs={6} md={3}>
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.9 }}
              >
                <Box textAlign="center">
                  <Typography variant="h3" color="primary" fontWeight="bold">50K+</Typography>
                  <Typography variant="body1" color="text.secondary">Community Members</Typography>
                </Box>
              </motion.div>
            </Grid>
          </Grid>
        </Box>
      </Container>

      {/* Features Section */}
      <Container maxWidth="xl" sx={{ my: 8 }}>
        <Box sx={{ mb: 8, textAlign: 'center' }}>
          <Typography 
            variant="h3" 
            component="h2" 
            fontWeight="bold"
            gutterBottom
          >
            Why Choose ViralCoin
          </Typography>
          <Typography 
            variant="h6" 
            color="text.secondary" 
            sx={{ maxWidth: 700, mx: 'auto' }}
          >
            Our platform combines trend analysis with blockchain technology to create new monetization opportunities
          </Typography>
        </Box>
        
        <motion.div
          variants={containerVariants}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, amount: 0.2 }}
        >
          <Grid container spacing={4}>
            {features.map((feature, index) => (
              <Grid item xs={12} sm={6} md={3} key={index}>
                <motion.div variants={itemVariants}>
                  <Card 
                    sx={{ 
                      height: '100%',
                      display: 'flex',
                      flexDirection: 'column',
                      transition: 'transform 0.3s, box-shadow 0.3s',
                      '&:hover': {
                        transform: 'translateY(-12px)',
                        boxShadow: 6,
                      },
                      borderRadius: 4,
                      overflow: 'hidden',
                      border: `1px solid ${alpha(feature.color, 0.2)}`,
                    }}
                  >
                    <Box
                      sx={{
                        height: 12,
                        bgcolor: feature.color,
                      }}
                    />
                    <Box
                      sx={{
                        p: 3,
                        display: 'flex',
                        justifyContent: 'center',
                      }}
                    >
                      <Avatar
                        sx={{
                          width: 70,
                          height: 70,
                          bgcolor: alpha(feature.color, 0.1),
                          color: feature.color,
                          border: `2px solid ${feature.color}`,
                        }}
                      >
                        {feature.icon}
                      </Avatar>
                    </Box>
                    <CardContent sx={{ flexGrow: 1, textAlign: 'center', px: 3 }}>
                      <Typography gutterBottom variant="h5" component="h3" fontWeight="bold">
                        {feature.title}
                      </Typography>
                      <Typography color="text.secondary">
                        {feature.description}
                      </Typography>
                    </CardContent>
                  </Card>
                </motion.div>
              </Grid>
            ))}
          </Grid>
        </motion.div>
      </Container>

      {/* How It Works Section */}
      <Box sx={{ py: 10, bgcolor: alpha(theme.palette.primary.main, 0.05), borderRadius: '24px 24px 0 0' }}>
        <Container maxWidth="xl">
          <Box sx={{ mb: 8, textAlign: 'center' }}>
            <Typography 
              variant="h3" 
              component="h2" 
              fontWeight="bold"
              gutterBottom
            >
              How It Works
            </Typography>
            <Typography 
              variant="h6" 
              color="text.secondary" 
              sx={{ maxWidth: 700, mx: 'auto' }}
            >
              Four simple steps to start monetizing trending topics
            </Typography>
          </Box>
          
          <motion.div

