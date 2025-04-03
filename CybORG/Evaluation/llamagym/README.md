# How to run me?

This is how you can run this agent to do some experiments. 

1. Open the conda environment with the packages we need (e.g., `CAGE4_LLM`)
2. Configure your OpenAI key on your terminal. Use OPENROUTER_API_KEY if using Deepseek models.
```
export OPENAI_API_KEY=<your_key>
export OPENROUTER_API_KEY=<your_key>
```
3. Create a wandb account if you don't have one, then copy the API key from the browser. 
4. Auth to wandb with this command. This will create a `.netrc` file
```
wandb login
```
5. Change the model and prompts to the paths you want to use in `llm_policy.yml::MODEL_CONFIG` and `llm_policy.yml::PROMPTS_CONFIG`

6. Modify the execution variables if needed in `CybORG/Agents/LLMAgents/config/config_vars.py`. Current variables are:
```python
# Submission Information
SUB_NAME = "LLM and RL Agent"
SUB_TEAM = "UCSC Autonomous Cybersecurity Lab"
SUB_TECHNIQUE = "LLM+RL"

# LLM Agent
# Can be set to `blue_agent_0` or `blue_agent_1` or `blue_agent_2` or `blue_agent_3` or `blue_agent_4`
BLUE_AGENT_NAME = "blue_agent_0"

# Config files
CONFIG_MODEL_PATH = "CybORG/Agents/LLMAgents/config/model/tinyllama.yml"
CONFIG_PROMPT_PATH = "CybORG/Agents/LLMAgents/config/prompts/cot.yml"

# Environment variables
ENV_VAR_MODEL = "CAGE4_MODEL_CONFIG"
ENV_VAR_PROMPT = "CAGE4_PROMPTS_CONFIG"

# Extra
DEBUG_MODE = True   # Enable/Disable debugging messages
TOTAL_STEPS_PROGRESS_BAR = 1000 # TODO: Get this from the environment
```
7. Run it 
```
python3 -m CybORG.Evaluation.evaluation --max-eps 2 Evaluation/llamagym /tmp/GPT4o --wandb-entity <wandb username> --wandb-mode online
```

- To log results offline, use `offline` for `--wandb-mode`. If running offline, `--wandb-entity` is not necessary but can be used if syncing results after evaluation run. Note: Weave does not log traces in offline mode.  

```
python3 -m CybORG.Evaluation.evaluation --max-eps 2 Evaluation/llamagym /tmp/GPT4o --wandb-mode offline
```

8. Store the files and the output! We need the wandb files and the CyBORG output files to plot.

# Communication Vector
Currently, our communication vector works as described in the structure.
## Message Structure
```
Message structure:
- Bit 0 (Agent 0 status): Malicious action detected from agent 0 network (1) or not (0)
- Bit 1 (Agent 1 status): Malicious action detected from agent 1 network (1) or not (0)
- Bit 2 (Agent 2 status): Malicious action detected from agent 2 network (1) or not (0)
- Bit 3 (Agent 3 status): Malicious action detected from agent 3 network (1) or not (0)
- Bit 4 (Agent 4 status): Malicious action detected from agent 4 network (1) or not (0)
- Bits 5-6 (Compromise level of current agent's network): 
    00 - No compromise
    01 - Netscan/Remote exploit detected
    10 - User-level compromise
    11 - Admin-level compromise
- Bit 7: Are we waiting on something to complete (1) or not (0)?
```
- To log results offline, use `offline` for `--wandb-mode`. If running offline, `--wandb-entity` is not necessary but can be used if syncing results after evaluation run. Note: Weave does not log traces in offline mode.  

```
python3 -m CybORG.Evaluation.evaluation --max-eps 2 Evaluation/llamagym /tmp/GPT4o --wandb-mode offline
```

7. Store the files and the output! We need the wandb files and the CyBORG output files to plot.

# List of Deepseek Models
Currently, we are using OpenRouter to communicate with the DeepSeek API. You can create an account and obtain a [free API KEY](https://openrouter.ai/deepseek/deepseek-chat/api)

```
deepseek-v3
```


# List of OpenAI Models
These are the models we can use with our current OpenAI org. Some require using the old backend, and some require the new backend.

Usage in prompt `yml` files:
- For the old backend, use `backend: "openai"`
- For the new backend, use `backend: "new-openai"`

## Old backend
```
 "gpt-4o-mini-realtime-preview",
 "dall-e-2",
 "whisper-1",
 "dall-e-3",
 "babbage-002",
 "omni-moderation-latest",
 "omni-moderation-2024-09-26",
 "tts-1-hd-1106",
 "tts-1-hd",
 "gpt-4o-mini-2024-07-18",
 "gpt-4o-mini",
 "tts-1",
 "gpt-3.5-turbo-16k",
 "tts-1-1106",
 "davinci-002",
 "gpt-3.5-turbo-1106",
 "gpt-4o-mini-realtime-preview-2024-12-17",
 "gpt-3.5-turbo-instruct",
 "gpt-4o-realtime-preview-2024-10-01",
 "gpt-3.5-turbo-instruct-0914",
 "gpt-3.5-turbo-0125",
 "gpt-4o-realtime-preview-2024-12-17",
 "gpt-3.5-turbo",
 "text-embedding-3-large",
 "gpt-4o-realtime-preview",
 "text-embedding-3-small",
 "text-embedding-ada-002",

```
## New backend
```
 "o1-mini-2024-09-12",
 "o1-preview-2024-09-12",
 "o1-mini",
 "o1-preview",
 "o1-2024-12-17",
 "o1",
 "o3-mini",
 "o3-mini-2025-01-31",
```
