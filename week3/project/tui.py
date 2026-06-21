import sys
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Header, Footer, Input, RichLog
from textual.containers import Horizontal, Vertical
from agent import Agent

class TUIAgent(Agent, App):
    TITLE = "CSOT ResearchDesk - Academic Workspace"
    
    CSS = """
    Screen {
        layout: vertical;
    }
    #workspace {
        layout: horizontal;
        height: 1fr;
    }
    #chat_container {
        width: 55%;
        height: 1fr;
        border: solid #00D7FF;
    }
    #tool_container {
        width: 45%;
        height: 1fr;
        border: solid #FFAF00;
    }
    RichLog {
        height: 1fr;
        padding: 0 1;
    }
    Input {
        dock: bottom;
        height: 3;
    }
    """

    BINDINGS = [
        Binding("ctrl+l", "clear_display", "Clear Display Views"),
        Binding("ctrl+k", "clear_history", "Clear Global Memory"),
        Binding("ctrl+q", "quit", "Quit"),
    ]

    def __init__(self, session_id=None):
        Agent.__init__(self, session_id=session_id)
        App.__init__(self)

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Horizontal(id="workspace"):
            with Vertical(id="chat_container"):
                yield RichLog(id="chat_log", wrap=True, markup=True, highlight=True)
            with Vertical(id="tool_container"):
                yield RichLog(id="tool_log", wrap=True, markup=True, highlight=True)
        yield Input(placeholder="Type a question and press Enter...")
        yield Footer()


    def on_mount(self) -> None:
        chat_log = self.query_one("#chat_log", RichLog)
        chat_log.write(f"[bold green]ResearchDesk Initialized.[/bold green] Active Context: [cyan]{self.session_id}[/cyan]\n")
        
        if self.resumed_topic:
            chat_log.write(f"[bold gold3][Memory Check] Resumed:[/bold gold3] [italic white]{self.resumed_topic}[/italic white]\n")
            
        self.query_one("#tool_log", RichLog).write("[bold orange3]Tool Stream Log Connected.[/bold orange3]\n")
        self.query_one(Input).focus()


    def _emit(self, log_type: str, text: str):
        try:
            tool_log = self.query_one("#tool_log", RichLog)
            if log_type == "invoke":
                self.call_from_thread(tool_log.write, f"[bold yellow][Tool Invoke][/bold yellow] {text}")
            elif log_type == "output":
                self.call_from_thread(tool_log.write, f"[bold green][Tool Output][/bold green] {text}\n")
            elif log_type == "error":
                self.call_from_thread(tool_log.write, f"[bold red][Exception][/bold red] {text}\n")
        except Exception:
            pass

    def on_input_submitted(self, event: Input.Submitted) -> None:
        user_text = event.value.strip()
        if not user_text: return
        
        event.input.clear()
        chat_log = self.query_one("#chat_log", RichLog)
        chat_log.write(f"[bold cyan][User][/bold cyan]: {user_text}")
        chat_log.write("[italic gray]Thinking...[/italic gray]\n")
        
        event.input.disabled = True
        self.run_worker(self._async_chat_wrapper(user_text), thread=True)


    async def _async_chat_wrapper(self, text: str):
        ans = self.chat(text)
        chat_log = self.query_one("#chat_log", RichLog)
        self.call_from_thread(chat_log.write, f"[bold magenta][Agent][/bold magenta]:\n{ans}\n")
        self.call_from_thread(self._enable_input)


    def _enable_input(self):
        self.query_one(Input).disabled = False
        self.query_one(Input).focus()


    def action_clear_display(self) -> None:
        self.query_one("#chat_log", RichLog).clear()
        self.query_one("#tool_log", RichLog).clear()


    def action_clear_history(self) -> None:
        self.messages = [self.messages[0]]
        self.resumed_topic = None
        self.save_session()
        self.action_clear_display()
        self.query_one("#chat_log", RichLog).write("[bold red]Message history cleared.[/bold red]\n")


if __name__ == "__main__":
    TUIAgent().run()