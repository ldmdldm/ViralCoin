#!/bin/bash

# ViralCoin Application Setup Script
# This script installs dependencies, sets up environment variables,
# and starts the development server for the ViralCoin application.

# Set text colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print welcome message
echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}    ViralCoin Application Setup Script     ${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

# Check if running with correct permissions
if [ "$(id -u)" = "0" ]; then
   echo -e "${RED}This script should not be run as root${NC}" 
   exit 1
fi

# Check for required tools
echo -e "${YELLOW}Checking prerequisites...${NC}"

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo -e "${RED}Error: npm is not installed.${NC}"
    echo "Please install Node.js and npm from https://nodejs.org/"
    exit 1
fi

# Check npm version
NPM_VERSION=$(npm -v)
echo -e "npm version: ${GREEN}$NPM_VERSION${NC}"

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo -e "${RED}Error: node is not installed.${NC}"
    echo "Please install Node.js from https://nodejs.org/"
    exit 1
fi

# Check Node.js version
NODE_VERSION=$(node -v)
echo -e "Node.js version: ${GREEN}$NODE_VERSION${NC}"

# Create .env file with environment variables
echo ""
echo -e "${YELLOW}Setting up environment variables...${NC}"

cat > .env << EOL
# API Configuration
REACT_APP_API_URL=https://viralcoin-demo-f07e7b13dc33.herokuapp.com
REACT_APP_API_KEY=development_api_key

# Blockchain Configuration
REACT_APP_DEFAULT_NETWORK=80001
REACT_APP_INFURA_KEY=your_infura_key_here
REACT_APP_FACTORY_ADDRESS=0x9876543210987654321098765432109876543210

# Application Configuration
REACT_APP_ENABLE_DEMO_MODE=true
REACT_APP_REFRESH_INTERVAL=300000
EOL

echo -e "${GREEN}Environment variables configured.${NC}"

# Install dependencies
echo ""
echo -e "${YELLOW}Installing dependencies...${NC}"
echo "This may take a few minutes depending on your internet speed."
echo ""

npm install

# Check if installation was successful
if [ $? -ne 0 ]; then
    echo ""
    echo -e "${RED}Error: Failed to install dependencies.${NC}"
    echo "Please check your internet connection and try again."
    exit 1
fi

echo ""
echo -e "${GREEN}Dependencies installed successfully!${NC}"

# Create missing directories if they don't exist
echo ""
echo -e "${YELLOW}Setting up directory structure...${NC}"

mkdir -p public/img
mkdir -p frontend/src/components
mkdir -p frontend/src/pages

echo -e "${GREEN}Directory structure set up successfully.${NC}"

# Create default index.html if it doesn't exist
if [ ! -f "public/index.html" ]; then
    echo ""
    echo -e "${YELLOW}Creating default index.html...${NC}"
    
    cat > public/index.html << EOL
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8" />
    <link rel="icon" href="%PUBLIC_URL%/favicon.ico" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <meta name="theme-color" content="#8a2be2" />
    <meta name="description" content="ViralCoin - Monetize Your Viral Content" />
    <link rel="apple-touch-icon" href="%PUBLIC_URL%/logo192.png" />
    <link rel="manifest" href="%PUBLIC_URL%/manifest.json" />
    <title>ViralCoin</title>
</head>
<body>
    <noscript>You need to enable JavaScript to run this app.</noscript>
    <div id="root"></div>
</body>
</html>
EOL

    echo -e "${GREEN}Default index.html created.${NC}"
fi

# Setup complete
echo ""
echo -e "${BLUE}============================================${NC}"
echo -e "${GREEN}Setup complete! Your ViralCoin application is ready.${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""
echo -e "To start the development server, run:"
echo -e "  ${YELLOW}npm start${NC}"
echo ""
echo -e "To build for production, run:"
echo -e "  ${YELLOW}npm run build${NC}"
echo ""
echo -e "To learn more about the ViralCoin application, visit:"
echo -e "  ${BLUE}https://github.com/viralcoin/frontend${NC}"
echo ""
echo -e "${GREEN}Happy coding! 🚀${NC}"

# Make script executable if it isn't already
chmod +x setup.sh

