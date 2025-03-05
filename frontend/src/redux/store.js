import { configureStore } from '@reduxjs/toolkit';
import walletReducer from './slices/walletSlice';
import trendingReducer from './slices/trendingSlice';
import uiReducer from './slices/uiSlice';

export const store = configureStore({
  reducer: {
    wallet: walletReducer,
    trending: trendingReducer,
    ui: uiReducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: false, // Required for Web3 objects
    }),
});

