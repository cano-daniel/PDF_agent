#!/bin/bash
# setup_env.sh
# Bash script to create or recreate a Python virtual environment for Dash_wildfire
# source venv_vi/bin/activate    # On Linux/Mac

ENV_DIR="venv_agent"
REQ_FILE="requirements.txt"

echo "=== Agent Environment Setup ==="

# Check if virtual environment exists
if [ -d "$ENV_DIR" ]; then
    echo "Virtual environment '$ENV_DIR' already exists."
    read -p "Do you want to delete and recreate it? (y/n): " choice
    if [[ "$choice" == "y" || "$choice" == "Y" ]]; then
        echo "Deleting existing environment..."
        rm -rf "$ENV_DIR"
    else
        echo "Keeping existing environment. Exiting setup."
        exit 0
    fi
fi

# Create new virtual environment
echo "Creating new virtual environment..."
python3 -m venv "$ENV_DIR"

# Activate it
source "$ENV_DIR/bin/activate"

# Upgrade pip
pip install --upgrade pip

# Install requirements
if [ -f "$REQ_FILE" ]; then
    echo "Installing dependencies from $REQ_FILE..."
    pip install -r "$REQ_FILE"
else
    echo "No requirements.txt found! Creating default one..."
    cat <<EOL > requirements.txt
langchain
langgraph
langchain_google_genai
python-dotenv
EOL
    pip install -r requirements.txt
fi

echo "✅ Environment setup complete!"
echo "To activate it later, run: source $ENV_DIR/bin/activate"
