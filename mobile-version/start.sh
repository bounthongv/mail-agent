#!/bin/bash

# 1. Initialize the database (create tables)
echo "Initializing database..."
python init_db.py

# 2. Start the background mail-checker (Worker)
echo "Starting background Mail Agent Worker..."
python worker.py &

# 3. Start the Streamlit Dashboard (Face)
# Hugging Face Spaces always run on port 7860
echo "Starting Streamlit Dashboard..."
streamlit run dashboard.py --server.port 7860 --server.address 0.0.0.0
