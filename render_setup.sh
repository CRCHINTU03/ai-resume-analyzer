#!/bin/bash
set -e  # Exit on error

# Update pip
echo "Updating pip..."
pip install --upgrade pip

# Install Python dependencies
echo "Installing Python dependencies..."
if ! pip install --no-cache-dir -r requirements.txt; then
    echo "Failed to install Python dependencies. Exiting."
    exit 1
fi

# Download spaCy model
echo "Downloading spaCy model 'en_core_web_sm'..."
python -m spacy download en_core_web_sm

# Build the frontend
echo "Building frontend..."
cd frontend
npm install
npm audit fix --force  # Fix vulnerabilities
npm run build