import React, { useEffect, useState } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { useNavigate } from 'react-router-dom';
import { 
  Box, 
  Typography, 
  Grid, 
  Card, 
  CardContent, 
  CardActions, 
  Button, 
  TextField, 
  Chip, 
  Tabs, 
  Tab, 
  Skeleton, 
  LinearProgress, 
  Avatar, 
  Divider,
  Tooltip,
  IconButton,
  Paper,
  useTheme,
  alpha,
  InputAdornment,
  Alert
} from '@mui/material';
import { motion } from 'framer-motion';

// Icons
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import TokenIcon from '@mui/icons-material/Token';
import BarChartIcon from '@mui/icons-material/BarChart';
import SearchIcon from '@mui/icons-material/Search';
import RefreshIcon from '@mui/icons-material/Refresh';
import ForumIcon from '@mui/icons-material/Forum';
import ThumbUpIcon from '@mui/icons-material/ThumbUp';
import FilterListIcon from '@mui/icons-material/FilterList';
import CategoryIcon from '@mui/icons-material/Category';

// Redux actions
import { 
  fetchTrendingTopics, 
  filterTrendingTopics, 
  searchTrendingTopics,
  setSelectedCategory,
  setSearchTerm 
} from '../../redux/slices/trendingSlice';
import { openModal } from '../../redux/slices/uiSlice';

// Animation variants
const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1
    }
  }
};

const itemVariants = {
  hidden: { y: 20, opacity: 0 },
  visible: {
    y: 0,
    opacity: 1,
    transition: {
      type: 'spring',
      stiffness: 100,
      damping: 12
    }
  }
};

const TrendingTopics = () => {
  const theme = useTheme();
  const dispatch = useDispatch();
  const navigate = useNavigate();
  
  // Redux state
  const { 
    allTopics,
    filteredTopics, 
    categories, 
    selectedCategory,
    searchTerm,
    loading, 
    lastUpdated,
    usingSampleData,
    error
  } = useSelector((state) => state.trending);
  const { isConnected, isDemoMode } = useSelector((state) => state.wallet);
  
  // Local state
  const [showFilterMenu, setShowFilterMenu] = useState(false);
  
  // Load trending topics on component mount
  useEffect(() => {
    if (filteredTopics.length === 0 && !loading) {
      dispatch(fetchTrendingTopics());
    }
  }, [dispatch, filteredTopics.length, loading]);
  
  // Handle category change
  const handleCategoryChange = (_, newValue) => {
    dispatch(setSelectedCategory(newValue));
    dispatch(filterTrendingTopics(newValue));
  };
  
  // Handle search
  const handleSearchChange = (event) => {
    const value = event.target.value;
    dispatch(setSearchTerm(value));
    dispatch(searchTrendingTopics(value));
  };
  
  // Handle refresh
  const handleRefresh = () => {
    dispatch(fetchTrendingTopics());
  };
  
  // Handle tokenize
  const handleTokenize = (topic) => {
    // If not connected and not in demo mode, prompt to connect
    if (!isConnected && !isDemoMode) {
      dispatch(openModal({ 
        modalType: 'walletModal', 
        data: { redirectAfterConnect: 'tokenize', topicToTokenize: topic } 
      }));
      return;
    }
    
    dispatch(openModal({ 
      modalType: 'tokenizeModal', 
      data: { topic } 
    }));
  };
  
  // Calculate how recent the data is
  const getLastUpdatedText = () => {
    if (!lastUpdated) return 'Never updated';
    
    const now = new Date();
    const updated = new Date(lastUpdated);
    const diffMinutes = Math.round((now - updated) / (1000 * 60));
    
    if (diffMinutes < 1) return 'Just now';
    if (diffMinutes === 1) return '1 minute ago';
    if (diffMinutes < 60) return `${diffMinutes} minutes ago`;
    
    const diffHours = Math.floor(diffMinutes / 60);
    if (diffHours === 1) return '1 hour ago';
    if (diffHours < 24) return `${diffHours} hours ago`;
    
    const diffDays = Math.floor(diffHours / 24);
    if (diffDays === 1) return '1 day ago';
    return `${diffDays} days ago`;
  };
  
  // Format large numbers with K/M/B suffixes
  const formatNumber = (num) => {
    if (!num && num !== 0) return '0';
    
    if (num >= 1000000000) {
      return (num / 1000000000).toFixed(1) + 'B';
    }
    if (num >= 1000000) {
      return (num / 1000000).toFixed(1) + 'M';
    }
    if (num >= 1000) {
      return (num / 1000).toFixed(1) + 'K';
    }
    return num.toString();
  };

  return (
    <Box sx={{ mb: 4 }}>
      <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap' }}>
        <Typography variant="h4" component="h1" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
          <TrendingUpIcon sx={{ mr: 1 }} fontSize="large" color="primary" />
          Trending Topics
        </Typography>
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          <Tooltip title="Refresh trending topics">
            <IconButton onClick={handleRefresh} disabled={loading} color="primary">
              <RefreshIcon />
            </IconButton>
          </Tooltip>
          {usingSampleData && (
            <Tooltip title="Using demo data">
              <Chip 
                label="Demo Data" 
                color="warning" 
                size="small" 
                sx={{ ml: 1 }} 
              />
            </Tooltip>
          )}
          <Typography variant="caption" sx={{ ml: 2, color: 'text.secondary' }}>
            Updated: {getLastUpdatedText()}
          </Typography>
        </Box>
      </Box>
      
      {/* Search and Filters */}
      <Box sx={{ mb: 4 }}>
        <Grid container spacing={2}>
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              placeholder="Search trending topics..."
              value={searchTerm}
              onChange={handleSearchChange}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <SearchIcon />
                  </InputAdornment>
                ),
              }}
              variant="outlined"
            />
          </Grid>
          <Grid item xs={12} md={6}>
            <Paper sx={{ borderRadius: 1 }}>
              <Tabs
                value={selectedCategory}
                onChange={handleCategoryChange}
                variant="scrollable"
                scrollButtons="auto"
                textColor="primary"
                indicatorColor="primary"
              >
                {categories.map((category) => (
                  <Tab 
                    key={category} 
                    label={category === 'all' ? 'All Categories' : category} 
                    value={category} 
                    icon={category === 'all' ? <FilterListIcon /> : <CategoryIcon />}
                    iconPosition="start"
                  />
                ))}
              </Tabs>
            </Paper>
          </Grid>
        </Grid>
      </Box>
      
      {/* Error alert */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}
      
      {/* Loading indicator */}
      {loading && <LinearProgress sx={{ mb: 3 }} />}
      
      {/* Trending Topics Grid */}
      <motion.div
        variants={containerVariants}
        initial="hidden"
        animate="visible"
      >
        <Grid container spacing={3}>
          {loading && filteredTopics.length === 0 ? (
            // Loading skeletons
            Array.from(new Array(8)).map((_, index) => (
              <Grid item xs={12} sm={6} md={4} lg={3} key={index}>
                <Skeleton 
                  variant="rectangular" 
                  height={200} 
                  sx={{ borderRadius: 2 }} 
                />
              </Grid>
            ))
          ) : filteredTopics.length > 0 ? (
            // Actual topic cards
            filteredTopics.map((topic) => (
              <Grid item xs={12} sm={6} md={4} lg={3} key={topic.id || `topic-${topic.name}`}>
                <motion.div variants={itemVariants} whileHover={{ scale: 1.02 }}>
                  <Card 
                    sx={{ 
                      height: '100%', 
                      display: 'flex', 
                      flexDirection: 'column',
                      transition: 'transform 0.2s, box-shadow 0.2s',
                      '&:hover': {
                        boxShadow: 6,
                      },
                      position: 'relative',
                      overflow: 'hidden',
                      '&::before': {
                        content: '""',
                        position: 'absolute',
                        top: 0,
                        left: 0,
                        right: 0,
                        height: '4px',
                        background: (theme) => 
                          topic.score > 0.95 
                            ? theme.palette.error.main 
                            : topic.score > 0.85 
                              ? theme.palette.warning.main 
                              : theme.palette.primary.main,
                      }
                    }}
                  >
                    <CardContent sx={{ flexGrow: 1 }}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
                        <Chip 
                          label={topic.category} 
                          color="primary" 
                          size="small" 
                          sx={{ borderRadius: 1 }}
                        />
                        <Tooltip title={`Trending score: ${(topic.score * 100).toFixed(0)}%`}>
                          <Box sx={{ display: 'flex', alignItems: 'center' }}>
                            <TrendingUpIcon fontSize="small" color="secondary" />
                            <Typography variant="caption" sx={{ ml: 0.5, color: 'secondary.main', fontWeight: 'bold' }}>
                              {(topic.score * 100).toFixed(0)}%
                            </Typography>
                          </Box>
                        </Tooltip>
                      </Box>
                      <Typography variant="h6" component="h2" gutterBottom>
                        {topic.name}
                      </Typography>
                      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                        {topic.description}
                      </Typography>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 'auto' }}>
                        <Tooltip title="Engagement">
                          <Box sx={{ display: 'flex', alignItems: 'center' }}>
                            <ThumbUpIcon fontSize="small" sx={{ color: 'primary.light', mr: 0.5 }} />
                            <Typography variant="caption">{formatNumber(topic.engagement)}</Typography>
                          </Box>
                        </Tooltip>
                        <Tooltip title="Mentions">
                          <Box sx={{ display: 'flex', alignItems: 'center' }}>
                            <ForumIcon fontSize="small" sx={{ color: 'primary.light', mr: 0.5 }} />
                            <Typography variant="caption">{formatNumber(topic.mentions)}</Typography>
                          </Box>
                        </Tooltip>
                      </Box>
                    </CardContent>
                    <Divider />
                    <CardActions>
                      <Button 
                        size="small" 
                        startIcon={<TokenIcon />}
                        onClick={() => handleTokenize(topic)}
                        fullWidth
                        variant="contained"
                        color="secondary"
                      >
                        Tokenize
                      </Button>
                    </CardActions>
                  </Card>
                </motion.div>
              </Grid>
            ))
          ) : (
            // No results found
            <Grid item xs={12}>
              <Box sx={{ textAlign: 'center', py: 4 }}>
                <Typography variant="h6">No trending topics found</Typography>
                <Typography variant="body2" color="text.secondary">
                  Try changing your search or filters
                </Typography>
                <Button 
                  variant="outlined" 
                  color="primary" 
                  sx={{ mt: 2 }}
                  onClick={() => {
                    dispatch(setSearchTerm(''));
                    dispatch(setSelectedCategory('all'));
                    dispatch(fetchTrendingTopics());
                  }}
                >
                  Reset Filters
                </Button>
              </Box>
            </Grid>
          )}
        </Grid>
      </motion.div>
    </Box>
  );
};

export default TrendingTopics;

