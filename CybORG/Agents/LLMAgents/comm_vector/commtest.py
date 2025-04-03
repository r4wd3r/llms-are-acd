from pprint import pprint

from CybORG import CybORG
from CybORG.Simulator.Scenarios import EnterpriseScenarioGenerator
from CybORG.Agents import SleepAgent, FiniteStateRedAgent, EnterpriseGreenAgent
from CybORG.Simulator.Actions import Monitor, Analyse, DiscoverNetworkServices, AggressiveServiceDiscovery, DiscoverDeception, ExploitRemoteService, PrivilegeEscalate, Impact
import numpy as np
from CybORG.Simulator.Scenarios.EnterpriseScenarioGenerator import SUBNET, Subnet
import CybORG.Agents.LLMAgents.comm_vector.CommVectorGenerator as cvg

MAX_STEPS = 500



sg = EnterpriseScenarioGenerator(blue_agent_class=SleepAgent, 
                                green_agent_class=SleepAgent, 
                                red_agent_class=FiniteStateRedAgent,
                                steps=MAX_STEPS)
cyborg = CybORG(scenario_generator=sg, seed=1000)

blue_agent_name = 'blue_agent_4'
reset = cyborg.reset(agent=blue_agent_name)
initial_obs = reset.observation
pprint(initial_obs)

action = Monitor(0, blue_agent_name)
results = cyborg.step(agent=blue_agent_name, action=action)

step = 1
base_obs = results.observation
new_obs = base_obs

while new_obs == base_obs and step < MAX_STEPS:
    results = cyborg.step(agent=blue_agent_name, action=action)
    message = cvg.create_comm_message(new_obs, cyborg.environment_controller.hostname_ip_map) # CommVector: Create the communication message for each new observation
    step = step + 1
    new_obs = results.observation

# CommVector: Create Message after detecting a malicious action
print(f"Step count: {step}")
pprint(new_obs)
message = cvg.create_comm_message(new_obs, cyborg.environment_controller.hostname_ip_map)
print(f"Message: {message}")

while step < MAX_STEPS:
    results = cyborg.step(agent=blue_agent_name, action=action)
    message = cvg.create_comm_message(new_obs, cyborg.environment_controller.hostname_ip_map) # CommVector: Create the communication message for each new observation
    step = step + 1
    new_obs = results.observation
    print(f"Message: {message}")