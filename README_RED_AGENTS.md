# Using Different Red Agents and LLM Configuration

This guide explains how to configure different red agents and LLM options in your CybORG evaluations.

## Available Red Agents

The following red agents are available:

- `FiniteStateRedAgent` (default)
- `ImpactFSMAgent`
- `AggressiveFSMAgent`
- `StealthyFSMAgent`
- `DegradeServiceFSMAgent`
- `RandomSelectRedAgent`

## Changing the Red Agent

To use a different red agent, you need to modify two key files:

### 1. Changes in evaluation.py

After running the installation script, locate `evaluation.py` inside your `cage-challenge-4` directory. You'll need to make the following changes:

#### Step 1: Import the desired red agent

For example, if we are trying to use ImpactFSMAgent. First, find the imports section at the top of the file and add the import for your chosen red agent. For example:

```python
from CybORG.Agents import SleepAgent, EnterpriseGreenAgent, FiniteStateRedAgent
```

Change to (for ImpactFSMAgent):

```python
from CybORG.Agents import SleepAgent, EnterpriseGreenAgent, ImpactFSMAgent
```

#### Step 2: Replace the red agent class in the scenario generator

Find the `run_eval_thread` function and locate where the scenario generator is created:

```python
sg = EnterpriseScenarioGenerator(
    blue_agent_class=SleepAgent,
    green_agent_class=EnterpriseGreenAgent,
    red_agent_class=FiniteStateRedAgent,
    steps=EPISODE_LENGTH,
)
```

Change `red_agent_class=FiniteStateRedAgent` to your desired agent. For example:

```python
sg = EnterpriseScenarioGenerator(
    blue_agent_class=SleepAgent,
    green_agent_class=EnterpriseGreenAgent,
    red_agent_class=ImpactFSMAgent,
    steps=EPISODE_LENGTH,
)
```

### 2. Adjusting config_vars.py (Optional for LLM usage)

So if you're using the LLM agent, you can update the configuration in `CybORG/Agents/LLMAgents/config/config_vars.py` to reflect your agent choices. Make sure to make your desired changes at:

```python
ALL_LLM_AGENTS = False              # DANGER: Do you want all the LLM agents to play?
NO_LLM_AGENTS = False                # Do not enable both at the same time!
```

## Red Agent Behaviors

- **FiniteStateRedAgent**: Default agent, uses a finite state machine with a balance of exploration and exploitation
- **ImpactFSMAgent**: Focuses on actions that maximize impact on target systems
- **AggressiveFSMAgent**: Aggressively attacks targets with less emphasis on stealth
- **StealthyFSMAgent**: Prioritizes stealth over speed of attacks
- **DegradeServiceFSMAgent**: Focuses on degrading services rather than gaining control
- **RandomSelectRedAgent**: Uses random action selection for less predictable behavior

## Example Workflow

1. Run the installation script to set up CybORG and required components
2. Modify `evaluation.py` in the cage-challenge-4 directory to use your chosen red agent
3. Run your evaluations to see how your defense performs against different attack styles

You can run your evaluations by:

```python
python3 -m CybORG.Evaluation.evaluation --max-eps 2 CybORG/Evaluation/Cybermonics [FILE PATH NAME]
```

If you wish to use Wandb logging, you can run something like:
```python
python -m CybORG.Evaluation.evaluation --max-eps 2 CybORG/Evaluation/Cybermonics CybORG/Evaluation/Cybermonics/ImpactFSMAgent --wandb-entity <wandb_username> --wandb-mode online
```