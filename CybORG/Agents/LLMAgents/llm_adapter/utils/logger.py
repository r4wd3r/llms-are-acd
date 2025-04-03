from rich.console import Console

class Logger:
    _console = Console()
    _DEBUG_MODE = False
    
    @staticmethod
    def set_debug_mode(debug_mode):
        Logger.DEBUG_MODE = debug_mode

    @staticmethod
    def info(message: str):
        Logger._console.print(f"[INFO] {message}", style="bold blue")

    @staticmethod
    def warning(message: str):
        Logger._console.print(f"[!] {message}", style="bold yellow")

    @staticmethod
    def error(message: str):
        Logger._console.print(f"[X] {message}", style="bold red")

    @staticmethod
    def success(message: str):
        Logger._console.print(f"[+] {message}", style="bold green")

    @staticmethod
    def debug(message:str):
        if Logger.DEBUG_MODE:
            Logger._console.print(f"[DEBUG] {message}", style="white")
    
    # Methods related to our use case 
    @staticmethod
    def conversation_message(role: str, message: str):
        TRUNCATE_LENGTH = 420
        truncated_message = (message[:TRUNCATE_LENGTH] + '...' + '[TRUNCATED]') if len(message) > TRUNCATE_LENGTH else message
        Logger._console.print(f"[bold magenta][{role.upper()}][/bold magenta] {truncated_message}")
        Logger._console.print("---------------------", style="bold magenta") 
        
    @staticmethod
    def new_episode():
        Logger._console.print("---------------------", style="bold yellow")
        Logger._console.print("Starting new episode", style="bold yellow")
        Logger._console.print("---------------------", style="bold yellow")