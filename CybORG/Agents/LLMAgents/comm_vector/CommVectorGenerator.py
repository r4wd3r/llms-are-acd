import numpy as np
from typing import Callable
from ipaddress import IPv4Address

from CybORG.Shared.Enums import TernaryEnum
from CybORG.Shared.Observation import Observation
from CybORG.Simulator.Actions import Action
from CybORG.Simulator.Scenarios.EnterpriseScenarioGenerator import SUBNET
from CybORG.Agents.Wrappers.BlueFixedActionWrapper import EMPTY_MESSAGE, MESSAGE_LENGTH, NUM_MESSAGES
from CybORG.Agents.LLMAgents.cyborg_helpers.subnet_map import SUBNET_AGENT_MAP
      
def _check_connections(process_events: dict) -> int:
    '''
    Checks how many processes/connections are in the process events. 
    Used to detect Aggresive Service Discovery. 
    If there are more than 2 connections from the same remote address, then it is a sign of compromise.
    
    param: process_events: dict - the event to check

    return: int - 0 if no indicator of compromise, otherwhise 2
    '''
    
    remote_addresses = set()

    for process in process_events:
        if 'Connections' in process and 'remote_address' in process['Connections'][0]:
            remote_address = process['Connections'][0]['remote_address']
            if remote_address in remote_addresses:
                return 2
            remote_addresses.add(remote_address)

    return 0

def _check_local_procs(process_events: dict) -> int:
        '''
        Checks any non-connection processes.
        If a process does not have connection data, it is either a local process
        (in which case we should have additional info about it) or something is
        trying to hide from us.
        
        param: process_events: dict - the event to check
        
        return: int - 0 if no indicator of compromise, otherwhise 2
        '''

        for process in process_events:
            # Probably not a good heuristic
            # But if we can't see at least two pieces of info that's definately bad
            if "Connections" not in process and len(process) < 2:
                return 2
        return 0

def _check_sessions(session_events: dict) -> int:
    '''
    Checks how many sessions are open in the session events.
    
    param: session_events: dict - the event to check
    
    return: int - 0 if no indicator of compromise, otherwhise 2
    '''
    MAX_NORMAL_SESSIONS = 1
    return 2 if len(session_events) > MAX_NORMAL_SESSIONS else 0

def _check_files(file_events: dict) -> int:
    '''
    Checks if a file is created in the event. Currently, these are the only possible values for CAGE 4:
    - cmd.{extension} is a user-level compromise
    - escalate.{extension} is an admin-level compromise
    
    param: file_events: dict - the events to check

    return: int - 0 if no indicator of compromise, 1 if user compromise, 2 if admin compromise
    '''
    compromise_level = 0
    ioc_files_user = ['cmd.sh', 'cmd.exe']
    ioc_files_admin = ['escalate.sh', 'escalate.exe']
    for file in file_events:
        if file['File Name'] in ioc_files_admin:
            compromise_level = 3
            break
        if file['File Name'] in ioc_files_user:
            compromise_level = 2
    return compromise_level
                    

def _calculate_compromise_level(obs: dict) -> int:
    '''
    Calculates the compromise level of the agent's network.
    The observation only contains the current state of the agent's network
    
    param: obs: dict - the observation of the agent
    
    return: int - the compromise level of the agent's network
    '''
    compromise_level = 0

    if len(obs) > 2: # Only true if there are events 
        for key in obs.keys():
            if key == 'success' or key == 'action' or key == 'phase' or key == 'message':
                continue
            else: 
                system_name = key
                for event in obs[system_name]: 
                    if event == 'Processes': # Monitor action returns Processes events
                        compromise_level = max(compromise_level, _check_connections(obs[system_name][event]))
                        compromise_level = max(compromise_level, _check_local_procs(obs[system_name][event]))
                    elif event == 'Files': # Analyze action returns Files events
                        compromise_level = max(compromise_level, _check_files(obs[system_name][event]))
                    elif event == 'Sessions': # Check who has a current session open 
                        compromise_level = max(compromise_level, _check_sessions(obs[system_name][event]))
            if compromise_level == 3:
                break  # No need to check further if admin-level compromise is detected 
    return compromise_level
  
def _validate_connections(obs: dict, host_ip_map: dict[IPv4Address]) -> np.array:
    '''
    Validate the connections to the agent's network. Then, maps the source IP to the respective agent's network
    Returns an array with the agents that have connections to the agent's network
    
    param: obs: dict - the observation of the agent
    param: host_ip_map: dict - the mapping of hostnames to IP addresses
    
    return: np.array - the list of agents that have connections to the agent's network
    '''
    remote_connections = np.zeros(5)
    for _, v in obs.items():
        if not (isinstance(v, dict) and 'Processes' in v):
            continue
        for connection in v['Processes']:
            if 'Connections' in connection and 'remote_address' in connection['Connections'][0]:
                remote_address = connection['Connections'][0]['remote_address']
                hostname = next(key for key, value in host_ip_map.items() if value == remote_address)
                hostname_subnet = f"{hostname.split('subnet')[0]}subnet"
                agent = SUBNET_AGENT_MAP[hostname_subnet]
                if agent >= 0:
                    remote_connections[agent] = 1
    
    return remote_connections
    
def create_comm_message(obs: Observation, last_action: Action, host_ip_map: dict[IPv4Address]) -> np.array:
    '''
    Creates the 1-byte message for each agent after running the Monitor action.
    Remember that Monitor action runs automatically at the end of each step.
    
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
    '''  
    # agent_name = obs['action'].agent
    message = np.zeros(8)
    
    # Calculate compromise level for agent's network and set bits 
    compromise_level = _calculate_compromise_level(obs.data)
    message[5] = (compromise_level & 0b10) >> 1
    message[6] = compromise_level & 0b01
    message[7] = obs.data["success"] == TernaryEnum.IN_PROGRESS
    
    # If compromise is detected, check connections from other networks
    if compromise_level:
        remote_connections = _validate_connections(obs.data, host_ip_map)
        for i in range(5):
            message[i] = remote_connections[i]
    
    return message