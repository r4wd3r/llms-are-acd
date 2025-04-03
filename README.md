# Large Language Models are Autonomous Cyber Defenders 🛡️

Code artifact for the paper "Large Language Models are Autonomous Cyber Defenders." We provide the first study on the
use of Large Language Models (LLMs) and Reinforcement Learning (RL) for Autonomous Cyber Defense (ACD) in multi-agent environments.

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

**Authors:** 
- Sebastián R. Castro
- Roberto Campbell
- Nancy Lau 
- Octavio Villalobos
- Jiaqi Duan 
- Alvaro A. Cárdenas
**Affiliation:** University of California, Santa Cruz (UCSC).

# Installation
## Directory Structure

The main new additions to the original `cage-challenge-4` in the extended installation are:

- `CybORG/Agents/CybermonicAgents/` - Cybermonic agent implementation
- `CybORG/Agents/LLMAgents/` - LLM integration framework
- `CybORG/Agents/Wrappers/CybermonicWrappers/` - Graph wrappers for observations
- `CybORG/Evaluation/` - Evaluation folder, which contains Cybermonics and the llamagym folder
- `cybermonic_train.py` - Training script for Cybermonic agents

## System Requirements

- **Python**: 3.7+ required (3.10 recommended)
- **OS**: Compatible with Linux and macOS
- **GPU**: Not required, but helpful for training Cybermonic agents

## Changing red agents and our prompt

To change the red agents, the guide is linked here for the [Red Agent and LLM configuration guide](README_RED_AGENTS.md), and our ACD prompt can be found [here](base.yml).

## Simplified Installation

This repository contains an installation script that simplifies the setup process. Please make sure to have Python installed. You may also optionally install `pip install wandb weave` for Wandb integration. Packages will be handled by the install script. After you have run all the below instructions, you will be ready to run the code in the `cage-challenge-4` folder.

First, run:

```bash
chmod +x install_unified.sh && ./install_unified.sh
```

This script will:
1. Clone the CAGE-4 repository if needed
2. Create and set up a virtual environment
3. Install the CybORG package
4. Install extensions if available
5. Configure all dependencies with compatible versions

### IMPORTANT: Activating the Environment

After installation is complete, you **MUST** activate the virtual environment before running any commands:

```bash
# Activate the virtual environment
source cage-env/bin/activate

# Now you can run CAGE-4 commands in the cage-challenge-4 folder
python -m CybORG.Evaluation.evaluation
```

The activation step is required each time you open a new terminal session to work with CAGE-4.

### Installation Modes

The script automatically detects which type of installation you need. Currently, the default is extended mode.

- **Core Mode**: Basic CAGE-4 with standard agents
- **Extended Mode**: CAGE-4 with additional Cybermonic and LLM agents

You may see warnings about package version conflicts during installation. These warnings are expected and shouldn't affect functionality.

## API Keys Setup

For LLM-based agents, you'll need to set up API keys in the `.env` file created during installation:

```bash
export OPENAI_API_KEY="your_openai_api_key_here"
export OPENROUTER_API_KEY="your_openrouter_api_key_here"
```

Then source the file before running experiments:
```bash
source .env
```

## Running Experiments

The installation script automatically sets up your system, but you should check and update the configuration files for your specific needs:

If using LLM agents and custom agents, please review `CybORG/Agents/LLMAgents/config/config_vars.py` and `evaluation.py`.

### Running Evaluations

After installation, you can run evaluations using:

```bash
source cage-env/bin/activate
source .env  # Only needed for LLM agents

# Run basic evaluation
python -m CybORG.Evaluation.evaluation --max-eps 2 [submission_path] [output_path]

# Run with Wandb logging
python -m CybORG.Evaluation.evaluation --max-eps 2 [submission_path] [output_path] --wandb-entity <wandb_username> --wandb-mode online
```

Example using the StealthyFSMAgent (if available in the extended installation):
```bash
python -m CybORG.Evaluation.evaluation --max-eps 2 CybORG/Evaluation/Cybermonics CybORG/Evaluation/Cybermonics/StealthyFSMAgent
```

### Training Cybermonic Agents

If you have the extended installation with Cybermonic agents, you can train them:

```bash
source cage-env/bin/activate
source .env

python cybermonic_train.py my_agent

# Train with custom parameters
python cybermonic_train.py my_agent --hidden 512 --embedding 256
```

Training checkpoints will be saved to the `checkpoints/` directory.

### Exploring the Documentation

The CAGE-4 repository includes comprehensive documentation:

```bash
cd cage-challenge-4/documentation
pip install mkdocs
mkdocs serve
```

Then open `http://127.0.0.1:8000` in your browser.

## Troubleshooting
You can check if your installation detected the extensions with `python -c "from importlib.util import find_spec; print(find_spec('CybORG.Agents.CybermonicAgents') is not None)"`