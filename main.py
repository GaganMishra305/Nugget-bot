import os
from dotenv import load_dotenv, set_key
from core.rag_agent import NuggetsBot
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.text import Text
import pyfiglet

os.environ.clear()
def main():
    console = Console()
    banner = pyfiglet.figlet_format("Nuggets Bot", font="slant")
    console.print(f"[bold cyan]{banner}[/bold cyan]")

    load_dotenv('.env')
    token = os.getenv("HUGGING_FACE_TOKEN")
    # print(token)
    if not token:
        token = Prompt.ask("[bold yellow]Enter your Hugging Face Token (which has permission for using llama:70b) [/bold yellow]")
        set_key(str('.env'), "HUGGING_FACE_TOKEN", token)
        os.environ["HUGGING_FACE_TOKEN"] = token
        console.print("[green]Token saved to .env[/green]")

    # Pass the token from CLI into the bot
    bot = NuggetsBot(api_key=token)
    console.print(Panel("[bold green]🍔 Nuggets Restaurant Bot is ready! Type 'exit' to quit.[/bold green]"))

    while True:
        try:
            query = Prompt.ask("[bold cyan]You[/bold cyan]")
            if query.strip().lower() == "exit":
                console.print("[bold magenta]Goodbye![/bold magenta]")
                break

            response = bot.process_query(query)
            console.print(Panel(Text(response), title="Nuggets", subtitle="🍔", style="blue"))
        except KeyboardInterrupt:
            console.print("\n[bold magenta]Session terminated by user. Goodbye![/bold magenta]")
            break
        except Exception as e:
            console.print(f"[bold red]Error:[/bold red] {e}")

if __name__ == "__main__":
    main()
