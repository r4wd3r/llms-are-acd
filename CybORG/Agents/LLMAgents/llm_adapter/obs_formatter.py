


from CybORG.Agents.LLMAgents.llm_adapter.utils.logger import Logger
from CybORG.Agents.LLMAgents.llm_adapter.utils.constants import ACTION_OBS_RESULTS

WARNING_MSG = "WARNING: Suspicious process detected"
ALERT_MSG = "ALERT: User-level compromise detected"
MAXIMUM_ALERT_MSG = "CRITICAL: Admin-level compromise detected"
NO_SUSPICIOUS_ACTIVITY_MSG = "Suspicious Activity Detected: None"

@staticmethod
def _format_comm_vector_message(agent_name: str, commvectors) -> list:
    """Format the commvector message for the LLM."""
    agent_number = int(agent_name[-1])
    agent_indices = list(set(range(5)) - {agent_number})
    
    text_obs = []
    commvector_dict = {}
    for idx, c in zip(agent_indices, commvectors):
        binary_array = [1 if x else 0 for x in c]
        commvector_dict[idx] = binary_array
        text_obs.append(f"Commvector Blue Agent {idx} Message: {binary_array}")
    return text_obs

@staticmethod
def _format_suspicious_activity(observation: dict) -> list:
    """Format the suspicious activity for the LLM."""
    suspicious_activity = []
        # Process other observation data
    for key, value in observation.items():
        if key in ["success", "action", "phase", "message"]:
            continue

        if isinstance(value, dict):
            host_info = []

            # Get hostname and IP
            if "System info" in value:
                hostname = value["System info"].get("Hostname", key)
                host_info.append(f"Hostname: {hostname}")

            if "Interface" in value and value["Interface"]:
                ip = value["Interface"][0].get("ip_address")
                if ip:
                    host_info.append(f"IP: {str(ip)}")

            # Process suspicious activities
            if "Processes" in value:
                for proc in value["Processes"]:
                    if "PID" in proc and "username" not in proc:
                        host_info.append(WARNING_MSG)

                    if "Connections" in proc:
                        for conn in proc["Connections"]:
                            remote_addr = conn.get("remote_address")
                            if remote_addr:
                                host_info.append(f"INFO: Connection to {str(remote_addr)}")
            # IOCs for CAGE. 
            ioc_files_user = ['cmd.sh', 'cmd.exe']
            ioc_files_admin = ['escalate.sh', 'escalate.exe']
            if "Files" in value:
                # The observation does not always have the hostname, so we need to store it temporarily from the key
                temp_hostname = str(key)
                for file in value["Files"]:
                    if file['File Name'] in ioc_files_admin:
                        host_info.append(f"{MAXIMUM_ALERT_MSG} in host {temp_hostname}")
                    if file['File Name'] in ioc_files_user:
                        host_info.append(f"{ALERT_MSG} in host {temp_hostname}")
            if host_info:
                suspicious_activity.append(" | ".join(host_info))
    return suspicious_activity

@staticmethod
def format_observation(observation: dict, last_action: str, agent_name: str) -> str:
        """Format the observation for the LLM."""
        if observation is None:
            return "No observation available. Choose a defensive action."

        Logger.debug(f"Received observation")
        print(f"{observation}")
        text_obs = []

        # Handle phase and success status
        phase = observation.get("phase", "unknown")
        success = observation.get("success", "unknown")
        text_obs.append(f"Mission Phase: {phase}")
        text_obs.append(f"Last Action : {last_action}")
        text_obs.append(f"Last Action Status: {success}")
        
        # Handle communication vectors
        text_obs.append(f"Communication Vectors: ")
        commvectors = observation.get("message", "unknown")
        text_obs.extend(_format_comm_vector_message(agent_name, commvectors))

        # Handle suspicious activity formatting
        suspicious_activity = _format_suspicious_activity(observation)

        if suspicious_activity:
            text_obs.append("\nSuspicious Activity Detected:")
            text_obs.extend(f"- {activity}" for activity in suspicious_activity)
        else:
            text_obs.append("\n Suspicious Activity Detected: None")

        formatted_obs = "# OBSERVATION\n\n"
        formatted_obs += "\n".join(text_obs)
        Logger.debug(f"Formatted observation:\n{formatted_obs}\n")
        return formatted_obs
