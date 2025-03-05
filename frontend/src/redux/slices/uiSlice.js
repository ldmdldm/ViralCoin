import { createSlice } from '@reduxjs/toolkit';

// Get initial theme preference from localStorage or system preference
const getInitialTheme = () => {
  const savedTheme = localStorage.getItem('theme');
  if (savedTheme) {
    return savedTheme === 'dark';
  }
  return window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
};

// Initial UI state
const initialState = {
  darkMode: getInitialTheme(),
  sidebarOpen: window.innerWidth > 768, // Default open on desktop, closed on mobile
  isLoading: false,
  activeTab: 'home',
  notifications: [],
  modals: {
    tokenizeModal: false,
    walletModal: false,
    confirmationModal: false,
  },
  currentModal: null,
  modalData: null,
};

const uiSlice = createSlice({
  name: 'ui',
  initialState,
  reducers: {
    toggleDarkMode: (state) => {
      state.darkMode = !state.darkMode;
      localStorage.setItem('theme', state.darkMode ? 'dark' : 'light');
    },
    toggleSidebar: (state) => {
      state.sidebarOpen = !state.sidebarOpen;
    },
    setLoading: (state, action) => {
      state.isLoading = action.payload;
    },
    setActiveTab: (state, action) => {
      state.activeTab = action.payload;
    },
    addNotification: (state, action) => {
      state.notifications.push({
        id: Date.now(),
        ...action.payload,
        read: false,
        timestamp: new Date().toISOString(),
      });
    },
    clearNotifications: (state) => {
      state.notifications = [];
    },
    openModal: (state, action) => {
      const { modalType, data } = action.payload;
      state.modals[modalType] = true;
      state.currentModal = modalType;
      state.modalData = data || null;
    },
    closeModal: (state, action) => {
      const modalType = action.payload || state.currentModal;
      if (modalType) {
        state.modals[modalType] = false;
      }
      state.currentModal = null;
      state.modalData = null;
    },
  }
});

export const { 
  toggleDarkMode, 
  toggleSidebar, 
  setLoading, 
  setActiveTab, 
  addNotification, 
  clearNotifications, 
  openModal, 
  closeModal 
} = uiSlice.actions;

export default uiSlice.reducer;

