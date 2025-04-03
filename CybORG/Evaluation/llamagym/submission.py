from __future__ import annotations
import os
from CybORG import CybORG
from CybORG.Agents import BaseAgent

from ray.rllib.policy.policy import Policy
from ray.tune import register_env
import torch
import wandb

# Import your custom agents here.
from dummy_agent import ReactRemoveBlueAgent
from CybORG.Agents.LLMAgents.llm_agent import DefenderAgent, RLLib_shim
from CybORG.Agents.LLMAgents.llm_policy import LLMDefenderPolicy
from CybORG.Shared.MetricsCallback import MetricsCallback

from CybORG.Agents.Wrappers import BaseWrapper 
from CybORG.Agents.Wrappers.BlueFixedActionWrapper import EMPTY_MESSAGE
from CybORG.Agents.LLMAgents.comm_vector import CommVectorGenerator as cvg

from CybORG.Agents.LLMAgents.config.config_vars import BLUE_AGENT_NAME, SUB_NAME, SUB_TEAM, SUB_TECHNIQUE, ALL_LLM_AGENTS

class Submission:
    torch.cuda.is_available = lambda: False
    # Submission name
    NAME: str = SUB_NAME
    
    # Name of your team
    TEAM: str = SUB_TEAM

    # What is the name of the technique used? (e.g. Masked PPO)
    TECHNIQUE: str = SUB_TECHNIQUE
    
    if ALL_LLM_AGENTS:  # Are you nuts?
        AGENTS: dict[str, BaseAgent] = {
            f"blue_agent_{agent}": DefenderAgent(f"blue_agent_{agent}", LLMDefenderPolicy, []) for agent in range(5)
        }
    else:
        AGENTS: dict[str, BaseAgent] = {
            f"blue_agent_{agent}": ReactRemoveBlueAgent(f"blue_agent_{agent}") for agent in range(5)
        }

        AGENTS[BLUE_AGENT_NAME] = DefenderAgent(BLUE_AGENT_NAME, LLMDefenderPolicy, [])

    # Use this function to wrap CybORG with your custom wrapper(s).
    @classmethod
    def wrap(cls, env: CybORG, path: str = ""):
        return PhaseWrapper(env)

class PhaseWrapper(BaseWrapper):
    def __init__(self, env: CybORG = None):
        super().__init__(env)
        self.metrics_callback = MetricsCallback()

    def observation_change(self, agent: str, observation: dict):
        state = self.env.environment_controller.state
        observation["phase"] = state.mission_phase
        return observation

    def reset(self, *args, **kwargs) -> tuple[dict[str, Any], dict[str, dict]]:
        self.env.reset(*args, **kwargs)
        self.agents = [a for a in self.env.agents if "blue" in a]
        observations = {a: self.observation_change(a, self.env.get_observation(a)) for a in self.agents}
        info = {}

        self.metrics_callback.on_reset(self.env)
        
        return observations, info

    def step(
        self,
        actions: dict[str, Action] = {},
        messages: dict[str, Any] = None,
        **kwargs,
    ) -> tuple[
        dict[str, Any],
        dict[str, float],
        dict[str, bool],
        dict[str, bool],
        dict[str, dict],
    ]:
        # Communication Vector Generation for each agent
        ec = self.env.unwrapped.environment_controller
        if messages is None:
            messages = {
                a: cvg.create_comm_message(ec.get_last_observation(a), ec.get_last_action(a), self.env.environment_controller.hostname_ip_map)
                for a, v in Submission.AGENTS.items()
            }    
        
        obs, rews, dones, info = self.env.parallel_step(
            actions, messages=messages, **kwargs
        )

        self.agents = [
            agent for agent, done in dones.items() if "blue" in agent and not done
        ]

        observations = {agent: self.observation_change(agent, o) for agent, o in obs.items() if "blue" in agent}

        rewards = {
            agent: sum(reward.values())
            for agent, reward in rews.items()
            if "blue" in agent
        }

        self.metrics_callback.on_step(observations, actions, self.env)

        terminated = {agent: done for agent, done in dones.items() if "blue" in agent}
        truncated = {agent: done for agent, done in dones.items() if "blue" in agent}

        return observations, rewards, terminated, truncated, {}

    def action_space(self, agent_name: str) -> Space:
        """Returns the discrete space corresponding to the given agent."""
        return None

class MessageWrapper(BaseWrapper):
    def step(self,
        actions: dict[str, Action] = {},
        messages: dict[str, Any] = None,
        **kwargs,
    ) -> tuple[
        dict[str, Any],
        dict[str, float],
        dict[str, bool],
        dict[str, bool],
        dict[str, dict],
    ]:
        if messages is None:
            env = self.env.unwrapped.environment_controller
            messages = {
                a: v.get_message(env.get_last_observation(a), env.get_message_space(a))
                for a, v in Submission.AGENTS.items()
            }
        return super().step(actions, messages, **kwargs)