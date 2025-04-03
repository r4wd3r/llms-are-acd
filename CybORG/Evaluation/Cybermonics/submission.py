from __future__ import annotations
import os

from CybORG import CybORG
from CybORG.Agents import BaseAgent

from ray.rllib.env.multi_agent_env import MultiAgentEnv
from ray.rllib.policy.policy import Policy
from ray.tune import register_env
import torch

from CybORG.Shared.MetricsCallback import MetricsCallback

### Import custom agents here ###
from CybORG.Agents.CybermonicAgents.cage4 import load
from CybORG.Agents.Wrappers.CybermonicWrappers.graph_wrapper import GraphWrapper

from CybORG.Agents.LLMAgents.llm_agent import DefenderAgent, RLLib_shim
from CybORG.Agents.LLMAgents.llm_policy import LLMDefenderPolicy
from CybORG.Agents.LLMAgents.comm_vector import CommVectorGenerator as cvg
from CybORG.Shared.Enums import TernaryEnum

from CybORG.Agents.Wrappers.CybermonicWrappers.observation_graph import ObservationGraph
from CybORG.Agents.Wrappers import BaseWrapper
from CybORG.Agents.Wrappers.BlueFixedActionWrapper import EMPTY_MESSAGE

from CybORG.Agents.LLMAgents.config.config_vars import BLUE_AGENT_NAME, SUB_NAME, SUB_TEAM, SUB_TECHNIQUE, ALL_LLM_AGENTS, NO_LLM_AGENTS

import wandb

class Submission:
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
        AGENTS = {
            f"blue_agent_{i}": load(f'{os.path.dirname(__file__)}/weights/gnn_ppo-{i}.pt')
            for i in range(5)
        }

    if not NO_LLM_AGENTS:
        AGENTS[BLUE_AGENT_NAME] = DefenderAgent(BLUE_AGENT_NAME, LLMDefenderPolicy, [])
    

    @classmethod
    def wrap(cls, env: CybORG, path: str = ""):
        return CombinedWrapper(env)

    
class CombinedWrapper(BaseWrapper):
    def __init__(self, env):
        super().__init__(env)

        graph_env = env
        phase_env = env

        self.metrics_callback = MetricsCallback()

        # Create separate wrapped environments for different agents
        self.phase_wrapper = PhaseWrapper(phase_env)  # Only used for blue_agent_0
        self.graph_wrapper = GraphWrapper(graph_env)  # Used for blue_agent_1 to blue_agent_4

    def step(self, actions):
        """Ensures the correct wrapper processes each agent's step."""

        phase_actions = {}
        graph_actions = {}
        if ALL_LLM_AGENTS:
            phase_actions = actions
            graph_actions = {}
        else:
            # Get actions for each agents possible moves
            if not NO_LLM_AGENTS:
                phase_actions = {k: v for k, v in actions.items() if k == BLUE_AGENT_NAME}
            graph_actions = {k: v for k, v in actions.items() if k.startswith("blue_agent_") and k != BLUE_AGENT_NAME}
        # set vars for each wrappers outputs
        phase_obs, phase_rewards, phase_term, phase_trunc, phase_info = ({}, {}, {}, {}, {})
        graph_obs, graph_rewards, graph_term, graph_trunc, graph_info = ({}, {}, {}, {}, {})

        blue_agents = [a for a in self.phase_wrapper.env.agents if "blue" in a]

        combined_observations = {a: self.phase_wrapper.observation_change(a, self.phase_wrapper.env.get_observation(a)) for a in blue_agents}

        translated_graph_actions = {
            agent_name: self.graph_wrapper.action_translator(agent_name, action_id)
            for agent_name, action_id in graph_actions.items()
        }

        combined_actions = {**phase_actions, **translated_graph_actions}

        self.metrics_callback.on_step(combined_observations, combined_actions, self.phase_wrapper.env)
        if phase_actions:
            phase_obs, phase_rewards, phase_term, phase_trunc, phase_info = self.phase_wrapper.step(phase_actions)

        # cybermonics wrapper
        if graph_actions:
            graph_obs, graph_rewards, graph_term, graph_trunc, graph_info = self.graph_wrapper.step(graph_actions)
        # combine the outputs of both wrappers
        observations = {**graph_obs, **phase_obs}
        rewards = {**graph_rewards, **phase_rewards}
        terminated = {**graph_term, **phase_term}
        truncated = {**graph_trunc, **phase_trunc}
        info = {**graph_info, **phase_info}

        return observations, rewards, terminated, truncated, info

    def reset(self, *args, **kwargs):
        """Ensures each agent gets the correct observation on reset."""
        phase_obs, phase_info = self.phase_wrapper.reset(*args, **kwargs)
        graph_obs, graph_info = self.graph_wrapper.reset(*args, **kwargs)

        # Ensure blue_agent_0 is always included
        if BLUE_AGENT_NAME not in phase_obs:
            raise RuntimeError(f"PhaseWrapper did not return an observation for {BLUE_AGENT_NAME}")

        if NO_LLM_AGENTS:
            observations = {**graph_obs}
            info = {**graph_info}
        elif ALL_LLM_AGENTS:
            observations = {**phase_obs} 
            info = {**phase_info}  
        else:
            observations = {**graph_obs, **phase_obs} 
            info = {**graph_info, **phase_info}  

        self.metrics_callback.on_reset(self.phase_wrapper.env)

        return observations, info
    
    def action_space(self, agent_name: str) -> Space:
        """Returns the discrete space corresponding to the given agent."""
        return None
    
class PhaseWrapper(BaseWrapper):
    def observation_change(self, agent: str, observation: dict):
        state = self.env.environment_controller.state
        observation["phase"] = state.mission_phase
        return observation

    def reset(self, *args, **kwargs) -> tuple[dict[str, Any], dict[str, dict]]:
        self.env.reset(*args, **kwargs)
        self.agents = [a for a in self.env.agents if BLUE_AGENT_NAME in a]
        if ALL_LLM_AGENTS:
            self.agents = [a for a in self.env.agents]
        observations = {a: self.observation_change(a, self.env.get_observation(a)) for a in self.agents}
        info = {}

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

        for agent_name, status in dones.items():
            if "blue" in agent_name:
                dones[agent_name] = False

        if ALL_LLM_AGENTS:
            self.agents = [
            agent for agent, done in dones.items() if "blue" in agent and not done
        ]
        else:
            self.agents = [BLUE_AGENT_NAME]

        observations = {agent: self.observation_change(agent, o) for agent, o in obs.items() if agent in self.agents}

        rewards = {
            agent: sum(reward.values())
            for agent, reward in rews.items()
            if agent in self.agents
        }

        terminated = {agent: done for agent, done in dones.items() if agent in self.agents}
        truncated = {agent: done for agent, done in dones.items() if agent in self.agents}

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