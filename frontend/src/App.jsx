import React, { useEffect, Suspense, lazy } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import { ThemeProvider } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import CircularProgress from '@mui/material/CircularProgress';
import Box from '@mui/material/Box';

// Theme
import { lightTheme, darkTheme } from './theme';

// Layout
import Layout from './components/layout/Layout';

// Redux
import { checkWalletConnection } from './redux/slices/walletSlice';
import { fetchTrendingTopics } from './redux/slices/trendingSlice';

// Lazy-loaded components for code splitting
const HomePage = lazy(() => import('./pages/HomePage'));
const TrendingPage = lazy(() => import('./pages/TrendingPage'));
const TokenizePage = lazy(() => import('./pages/TokenizePage'));
const LeaderboardPage = lazy(() => import('./pages/LeaderboardPage'));
const ProfilePage = lazy(() => import('./pages/ProfilePage'));
const NotFoundPage = lazy(() => import('./pages/NotFoundPage'));

const LoadingFallback = () => (
  <Box 
    sx={{ 
      display: 'flex', 
      justifyContent: 'center', 
      alignItems: 'center', 
      height: '100vh' 
    }}
  >
    <CircularProgress color="primary" />
  </Box>
);

function App() {
  const dispatch = useDispatch();
  const { darkMode } = useSelector((state) => state.ui);
  
  useEffect(() => {
    // Check wallet connection status on app load
    dispatch(checkWalletConnection());
    
    // Fetch initial trending topics
    dispatch(fetchTrendingTopics());
    
    // Set up interval to periodically refresh trending topics
    const interval = setInterval(() => {
      dispatch(fetchTrendingTopics());
    }, 300000); // 5 minutes
    
    return () => clearInterval(interval);
  }, [dispatch]);

  return (
    <ThemeProvider theme={darkMode ? darkTheme : lightTheme}>
      <CssBaseline />
      <Layout>
        <Suspense fallback={<LoadingFallback />}>
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/trending" element={<TrendingPage />} />
            <Route path="/tokenize" element={<TokenizePage />} />
            <Route path="/leaderboard" element={<LeaderboardPage />} />
            <Route path="/profile" element={<ProfilePage />} />
            <Route path="/404" element={<NotFoundPage />} />
            <Route path="*" element={<Navigate to="/404" replace />} />
          </Routes>
        </Suspense>
      </Layout>
    </ThemeProvider>
  );
}

export default App;

