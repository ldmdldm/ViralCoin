import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import axios from 'axios';
import { toast } from 'react-toastify';

// API URL from environment or fallback
const API_URL = process.env.REACT_APP_API_URL || 'https://viralcoin-demo.herokuapp.com';
const API_KEY = process.env.REACT_APP_API_KEY || 'development_key';

// Sample trending topics for fallback
const sampleTrendingTopics = [
  { 
    id: 1,
    name: 'Artificial Intelligence in Healthcare', 
    score: 0.98, 
    category: 'Technology', 
    description: 'AI models revolutionizing disease diagnosis and treatment planning',
    mentions: 15243,
    engagement: 32984
  },
  { 
    id: 2,
    name: 'Ethereum Layer 2 Solutions', 
    score: 0.95, 
    category: 'Crypto', 
    description: 'Scaling solutions driving lower fees and higher transaction throughput',
    mentions: 12876,
    engagement: 28934
  },
  { 
    id: 3,
    name: 'Climate Tech Startups', 
    score: 0.93, 
    category: 'Environment', 
    description: 'New companies developing carbon capture and sustainable energy technologies',
    mentions: 10932,
    engagement: 24321
  },
  { 
    id: 4,
    name: 'SpaceX Starship Orbital Test', 
    score: 0.91, 
    category: 'Space', 
    description: 'Latest developments in commercial space exploration',
    mentions: 9876,
    engagement: 22543
  },
  { 
    id: 5,
    name: 'Central Bank Digital Currencies', 
    score: 0.89, 
    category: 'Finance', 
    description: 'Government-backed digital currencies reshaping monetary policy',
    mentions: 8765,
    engagement: 19876
  },
  { 
    id: 6,
    name: 'Metaverse Real Estate Boom', 
    score: 0.87, 
    category: 'Crypto', 
    description: 'Virtual land sales reaching new highs across multiple platforms',
    mentions: 7654,
    engagement: 17654
  },
  { 
    id: 7,
    name: 'Quantum Computing Breakthroughs', 
    score: 0.85, 
    category: 'Technology', 
    description: 'Recent advancements in quantum error correction and qubit stability',
    mentions: 6543,
    engagement: 15432
  },
  { 
    id: 8,
    name: 'NFT Gaming Revolution', 
    score: 0.84, 
    category: 'Entertainment', 
    description: 'Play-to-earn games changing the economics of gaming industry',
    mentions: 5432,
    engagement: 13210
  }
];

// Async thunk for fetching trending topics
export const fetchTrendingTopics = createAsyncThunk(
  'trending/fetchTopics',
  async (_, { rejectWithValue }) => {
    try {
      const response = await axios.get(`${API_URL}/api/trends`, {
        headers: {
          'X-API-Key': API_KEY
        }
      });
      
      // Check if response data is valid
      if (response.data && Array.isArray(response.data.topics) && response.data.topics.length > 0) {
        return { topics: response.data.topics, usingSampleData: false };
      }
      
      // Fallback to sample data if API returns empty array
      console.warn('API returned empty data, using fallback topics');
      return { topics: sampleTrendingTopics, usingSampleData: true };
    } catch (error) {
      console.error('Error fetching trending topics:', error);
      // Instead of rejecting, return the sample data as fallback
      return { topics: sampleTrendingTopics, usingSampleData: true };
    }
  }
);

// Filter trending topics by category
export const filterTrendingTopics = createAsyncThunk(
  'trending/filterTopics',
  async (category, { getState }) => {
    const { allTopics } = getState().trending;
    
    if (!category || category === 'all') {
      return allTopics;
    }
    
    return allTopics.filter(topic => 
      topic.category.toLowerCase() === category.toLowerCase()
    );
  }
);

// Search trending topics
export const searchTrendingTopics = createAsyncThunk(
  'trending/searchTopics',
  async (searchTerm, { getState }) => {
    const { allTopics } = getState().trending;
    
    if (!searchTerm || searchTerm.trim() === '') {
      return allTopics;
    }
    
    const term = searchTerm.toLowerCase().trim();
    return allTopics.filter(topic => 
      topic.name.toLowerCase().includes(term) || 
      topic.description.toLowerCase().includes(term)
    );
  }
);

// Trending slice
const trendingSlice = createSlice({
  name: 'trending',
  initialState: {
    allTopics: [],
    filteredTopics: [],
    categories: [],
    selectedCategory: 'all',
    searchTerm: '',
    loading: false,
    error: null,
    lastUpdated: null,
    usingSampleData: false
  },
  reducers: {
    setSelectedCategory: (state, action) => {
      state.selectedCategory = action.payload;
    },
    setSearchTerm: (state, action) => {
      state.searchTerm = action.payload;
    }
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchTrendingTopics.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchTrendingTopics.fulfilled, (state, action) => {
        state.loading = false;
        state.allTopics = action.payload.topics;
        state.filteredTopics = action.payload.topics;
        state.lastUpdated = new Date().toISOString();
        state.usingSampleData = action.payload.usingSampleData;
        
        // Extract unique categories
        const categorySet = new Set(action.payload.topics.map(topic => topic.category));
        state.categories = ['all', ...Array.from(categorySet)];
      })
      .addCase(fetchTrendingTopics.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload || 'Failed to fetch trending topics';
        toast.error('Failed to fetch trending topics. Using sample data instead.');
      })
      .addCase(filterTrendingTopics.fulfilled, (state, action) => {
        state.filteredTopics = action.payload;
      })
      .addCase(searchTrendingTopics.fulfilled, (state, action) => {
        state.filteredTopics = action.payload;
      });
  }
});

export const { setSelectedCategory, setSearchTerm } = trendingSlice.actions;
export default trendingSlice.reducer;

