#!/bin/bash
# Update pip to the latest version
pip install --upgrade pip
# Install Python dependencies
pip install -r requirements.txt
# Pre-download spaCy model to avoid runtime download
python -m spacy download en_core_web_sm
# Build the frontend
cd frontend && npm install && npm run build