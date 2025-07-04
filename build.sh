#!/bin/bash
# Install Chromium and its dependencies
sudo apt-get update
sudo apt-get install -y chromium-browser chromium-chromedriver

# Install Python dependencies
pip install -r requirements.txt