import { createTheme } from '@mui/material/styles';

// Common theme settings
const commonSettings = {
  typography: {
    fontFamily: [
      'Poppins',
      'Roboto',
      '"Helvetica Neue"',
      'Arial',
      'sans-serif'
    ].join(','),
    h1: {
      fontWeight: 700,
    },
    h2: {
      fontWeight: 600,
    },
    h3: {
      fontWeight: 600,
    },
    h4: {
      fontWeight: 500,
    },
    h5: {
      fontWeight: 500,
    },
    h6: {
      fontWeight: 500,
    },
    button: {
      textTransform: 'none',
      fontWeight: 500,
    },
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          padding: '8px 16px',
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 12,
          boxShadow: '0 4px 12px rgba(0,0,0,0.05)',
        },
      },
    },
  },
};

// Light theme
export const lightTheme = createTheme({
  ...commonSettings,
  palette: {
    mode: 'light',
    primary: {
      main: '#8a2be2', // ViralCoin Purple
      light: '#a16de8',
      dark: '#6a20b8',
      contrastText: '#ffffff',
    },
    secondary: {
      main: '#ff8c00', // ViralCoin Orange
      light: '#ffa533',
      dark: '#cc7000',
      contrastText: '#ffffff',
    },
    background: {
      default: '#f8f9fa',
      paper: '#ffffff',
    },
  },
});

// Dark theme
export const darkTheme = createTheme({
  ...commonSettings,
  palette: {
    mode: 'dark',
    primary: {
      main: '#9c4dff', // Lighter Purple for dark mode
      light: '#b980ff',
      dark: '#7c3dcc',
      contrastText: '#ffffff',
    },
    secondary: {
      main: '#ff9e2c', // Lighter Orange for dark mode
      light: '#ffb860',
      dark: '#cc7e22',
      contrastText: '#ffffff',
    },
    background: {
      default: '#121212',
      paper: '#1e1e1e',
    },
  },
});

