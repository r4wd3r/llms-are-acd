#!/usr/bin/env bash
set -e

echo "============================================================"
echo " Installation Script"
echo "============================================================"

if [ ! -d "cage-challenge-4" ]; then
    echo " Cloning CAGE-4 repository..."
    git clone https://github.com/cage-challenge/cage-challenge-4 || { echo "Error cloning repository"; exit 1; }
fi

if [ ! -d "cage-env" ]; then
    echo " Creating virtual environment..."
    python -m venv cage-env || { echo "Error creating virtual environment"; exit 1; }
fi
source cage-env/bin/activate || { echo "Error activating virtual environment"; exit 1; }
echo "Virtual environment activated: $(which python)"

PYTHON_VERSION=$(python --version | cut -d ' ' -f 2)
echo "Using Python $PYTHON_VERSION"
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d '.' -f 1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d '.' -f 2)
if [[ "$PYTHON_MAJOR" -lt 3 ]] || [[ "$PYTHON_MAJOR" -eq 3 && "$PYTHON_MINOR" -lt 7 ]]; then
    echo "Error: CybORG requires Python 3.7 or higher"
    exit 1
fi

echo "Ensuring pip tools are up to date..."
pip install --upgrade pip setuptools wheel || { echo "Warning: Could not upgrade pip tools"; }

echo "Installing base dependencies first..."
cd cage-challenge-4
python -m pip install -r Requirements.txt || { echo "Warning: Could not install some original dependencies"; }

echo "Installing CybORG from repository (with pip develop mode)..."
python -m pip install -e . || { echo "Error installing CybORG from repo"; exit 1; }
cd ..

# Must use CybORG wheel file, it just makes CybORG installation much smoother
if [ -f "CybORG-4.0-py3-none-any.whl" ]; then
    echo " Installing CybORG extensions wheel..."
    python -m pip install ./CybORG-4.0-py3-none-any.whl --force-reinstall || { echo "Warning: Failed to install CybORG extensions wheel"; }
fi

# By the way, we edited the requirements.txt to have more relaxed constraints compared to the original cage-4 repo.
echo "Updating repository's Requirements.txt with relaxed constraints..."
cp requirements.txt cage-challenge-4/Requirements.txt

echo "Installing dependencies..."
pip install -r requirements.txt || { echo " Error installing dependencies"; exit 1; }

echo "Setting up environment files..."
cat > .env << 'EOF'
# CAGE-4 Extensions Environment Variables
# Add your API keys here:
# export OPENAI_API_KEY="your_key_here"
# export OPENROUTER_API_KEY="your_key_here"
# export ANTHROPIC_API_KEY="your_key_here"
EOF

EXTENSION_MODE="extended"
echo "Installing mode: $EXTENSION_MODE (basic CAGE-4)"

# check imports
echo " Creating import verification script..."
cat > verify_imports.py << 'EOF'
import sys

def check_import(module_path, message, required=True):
    try:
        exec(f"import {module_path}")
        print(f"{message}")
        return True
    except Exception as e:
        if required:
            print(f"Failed to import {module_path}: {e}")
            return False
        else:
            print(f"Optional module not available: {module_path}")
            return True

success = True
success &= check_import("CybORG", "CybORG core package")
success &= check_import("CybORG.Agents.SimpleAgents", "SimpleAgents")  
success &= check_import("CybORG.Simulator.Scenarios", "Scenarios")
success &= check_import("torch", "PyTorch")
success &= check_import("torch_geometric", "PyTorch Geometric")
success &= check_import("numpy", "NumPy")
success &= check_import("gym", "Gym")
success &= check_import("gymnasium", "Gymnasium")
success &= check_import("ray", "Ray")

if success:
    print("\n Core packages imported successfully!")
    sys.exit(0)
else:
    print("\n Some core imports failed. Please check the error messages above.")
    sys.exit(1)
EOF

# simple test to check imports
echo "Creating verification test..."
cat > test_cyborg.py << 'EOF'
print("Testing a basic CybORG import...")

try:
    from CybORG import CybORG
    from CybORG.Agents.SimpleAgents import EnterpriseGreenAgent
    from CybORG.Simulator.Scenarios import EnterpriseScenarioGenerator
    
    print("CybORG imports worked successfully!")
    print("Installation successful!")
    exit(0)
except Exception as e:
    print(f"\n Test failed: {e}")
    exit(1)
EOF

export PYTHONPATH=$PYTHONPATH:$(pwd):$(pwd)/cage-challenge-4

echo "Verifying base imports..."
python verify_imports.py || { echo " Import verification failed"; }

echo "Verifying CybORG functionality..."
python test_cyborg.py || { echo " Functionality test failed"; }

echo "Copying required module directories..."
mkdir -p cage-challenge-4/CybORG/Agents/CybermonicAgents
mkdir -p cage-challenge-4/CybORG/Agents/Wrappers/CybermonicWrappers
mkdir -p cage-challenge-4/CybORG/Agents/LLMAgents
mkdir -p cage-challenge-4/CybORG/Agents/SimpleAgents

cp -rv CybORG/Agents/CybermonicAgents/* cage-challenge-4/CybORG/Agents/CybermonicAgents/
cp -rv CybORG/Agents/Wrappers/CybermonicWrappers/* cage-challenge-4/CybORG/Agents/Wrappers/CybermonicWrappers/
cp -rv CybORG/Agents/LLMAgents/* cage-challenge-4/CybORG/Agents/LLMAgents/
cp -rv CybORG/Agents/SimpleAgents/* cage-challenge-4/CybORG/Agents/SimpleAgents/

echo "Contents of CybermonicAgents after copying:"
ls -la cage-challenge-4/CybORG/Agents/CybermonicAgents/

echo "Contents of CybermonicWrappers after copying:"
ls -la cage-challenge-4/CybORG/Agents/Wrappers/CybermonicWrappers/

echo "Contents of LLMAgents after copying:"
ls -la cage-challenge-4/CybORG/Agents/LLMAgents/

echo "Contents of SimpleAgents after copying:"
ls -la cage-challenge-4/CybORG/Agents/SimpleAgents

echo "Verifying module imports after copying..."
python verify_imports.py || { echo " Module import verification failed"; }

echo "Testing specific module imports..."
python -c "from CybORG.Agents.CybermonicAgents.cage4 import InductiveGraphPPOAgent; print('CybermonicAgents import successful!')" || echo "Failed to import CybermonicAgents"
python -c "from CybORG.Agents.Wrappers.CybermonicWrappers.graph_wrapper import GraphWrapper; print('CybermonicWrappers import successful!')" || echo "Failed to import CybermonicWrappers"
python -c "from CybORG.Agents.LLMAgents.llm_agent import DefenderAgent; print('LLMAgents import successful!')" || echo "Failed to import LLMAgents"
python -c "from CybORG.Agents.SimpleAgents.BaseAgent import BaseAgent; from unittest.mock import MagicMock, patch; print('SimpleAgents testing imports successful!')" || echo "Failed to import SimpleAgents testing modules"

mkdir -p checkpoints
mkdir -p logs

if [ "$EXTENSION_MODE" = "extended" ]; then
    echo "Setting up extended mode components..."
    
    # copy cybermonic training script
    if [ -f "cybermonic_train.py" ]; then
        cp cybermonic_train.py cage-challenge-4/ || { echo "Warning: Could not copy cybermonic_train.py"; }
    fi
    
    # copy llamagym directory to Evaluation
    if [ -d "CybORG/Evaluation/llamagym" ]; then
        echo "Copying LlamaGym directory..."
        mkdir -p cage-challenge-4/CybORG/Evaluation/llamagym
        cp -rv CybORG/Evaluation/llamagym/* cage-challenge-4/CybORG/Evaluation/llamagym/ || { echo "Warning: Could not copy llamagym directory"; }
    fi
    
    # copy Cybermonics directory to Evaluation
    if [ -d "CybORG/Evaluation/Cybermonics" ]; then
        echo "Copying Cybermonics directory..."
        mkdir -p cage-challenge-4/CybORG/Evaluation/Cybermonics
        cp -rv CybORG/Evaluation/Cybermonics/* cage-challenge-4/CybORG/Evaluation/Cybermonics/ || { echo "Warning: Could not copy Cybermonics directory"; }
    fi
    
    mkdir -p cage-challenge-4/checkpoints
    mkdir -p cage-challenge-4/logs
fi

echo "============================================================"
echo " Installation complete!"
echo " Next steps:"
echo "  IMPORTANT: You MUST activate the virtual environment before running any commands:"
echo "    source cage-env/bin/activate"
echo " Also, the code we are using is in the cage-challenge-4 folder"
echo ""
echo "Then you can:"
echo "1. Run a basic experiment: python -m CybORG.Evaluation.evaluation"
echo "2. Try training examples: cd cage-challenge-4 && python CybORG/Evaluation/training_example/TrainingSB3.py"
echo "3. Read documentation: cd cage-challenge-4/documentation && pip install mkdocs && mkdocs serve"
echo "============================================================"
