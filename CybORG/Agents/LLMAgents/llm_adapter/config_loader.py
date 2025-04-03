import yaml

class ConfigLoader:
    @staticmethod
    def load_model_configuration(config_path) -> dict:
        with open(config_path, 'r') as file:
            return yaml.safe_load(file)
    
    @staticmethod
    def load_prompts(prompts_path) -> dict:
        with open(prompts_path, 'r') as file:
            parsed = yaml.safe_load(file)
        prompts = parsed.get('prompts', [])
        return prompts