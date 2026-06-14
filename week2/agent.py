import os
import sys
import json
from datetime import datetime
import requests
from openai import OpenAI
from dotenv import load_dotenv
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Header, Footer, Input, RichLog
from textual.containers import Horizontal, Vertical

load_dotenv()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
)

MODEL = "openai/gpt-oss-120b:free"
MAX_HISTORY_TURNS = 20

REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the live web for general facts, background news, and trending information using Serper.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The exact search query terms."}
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "discover_papers",
            "description": "Queries the AlphaXiv academic repository to look up official peer-reviewed arXiv preprints.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Semantic research concepts or paper keywords."}
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_paper_content",
            "description": "Retrieves deep textual sections or markdown structured summaries from an explicit arXiv ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "arxiv_id": {"type": "string", "description": "The target unique paper ID (e.g., '2411.12345')."}
                },
                "required": ["arxiv_id"],
            },
        },
    },
]


def web_search(query: str) -> dict:
    
    serper_key = os.environ.get("SERPER_API_KEY")
    if not serper_key:
        return {"error": "Missing SERPER_API_KEY inside your system environment file."}
    
    try:
        url = "https://google.serper.dev/search"
        payload = json.dumps({"q": query, "num": 5})
        headers = {"X-API-KEY": serper_key, "Content-Type": "application/json"}
        
        response = requests.post(url, headers=headers, data=payload, timeout=10)
        if response.status_code != 200:
            return {"error": f"Serper API rejected request with status code: {response.status_code}"}
            
        data = response.json()
        simplified_results = []
        
        for item in data.get("organic", []):
            simplified_results.append({
                "title": item.get("title"),
                "url": item.get("link"),
                "snippet": item.get("snippet")
            })
        return {"results": simplified_results}
    
    except Exception as e:
        return {"error": f"Serper operations aborted: {str(e)}"}
    

def discover_papers(query: str) -> dict:
    try:
        url = "https://api.alphaxiv.org/mcp/v1/search" 
        payload = {"query": query, "limit": 4}
        response = requests.post(url, json=payload, timeout=12)
        
        if response.status_code == 200:
            return response.json()
        return {"error": f"AlphaXiv server fallback failure. Status: {response.status_code}"}
    except Exception as e:
        return {"error": f"AlphaXiv network connection dropped: {str(e)}"}


def get_paper_content(arxiv_id: str) -> dict:
    try:
        url = "https://api.alphaxiv.org/mcp/v1/paper"
        payload = {"arxiv_id": arxiv_id}
        response = requests.post(url, json=payload, timeout=12)
        
        if response.status_code == 200:
            raw_data = response.json()
            text_str = str(raw_data)
            return {"arxiv_id": arxiv_id, "content": text_str[:4000] + "..." if len(text_str) > 4000 else text_str}
        return {"error": f"AlphaXiv document index error. Code: {response.status_code}"}
    except Exception as e:
        return {"error": f"Failed compiling text extraction blocks for target document: {str(e)}"}


TOOL_REGISTRY = {
    "web_search": web_search,
    "discover_papers": discover_papers,
    "get_paper_content": get_paper_content,
}


def dispatch_tool(tool_call) -> str:
    name = tool_call.function.name
    if name not in TOOL_REGISTRY:
        return json.dumps({"error": f"Unknown tool parameter reference: {name}"})
    try:
        args = json.loads(tool_call.function.arguments)
        result = TOOL_REGISTRY[name](**args)
        return json.dumps(result)
    except Exception as e:
        return json.dumps({"error": str(e)})



def trim_history(messages: list, max_turns: int) -> list:
    if len(messages) <= 1:
        return messages
    system_msg = messages[0]
    chat_history = messages[1:]
    max_elements = max_turns * 2
    if len(chat_history) > max_elements:
        chat_history = chat_history[-max_elements:]
    return [system_msg] + chat_history



class ResearchBotTUI(App):
    TITLE = "CSOT ResearchBot"
    
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
        border: solid $primary;
    }
    #tool_container {
        width: 45%;
        height: 1fr;
        border: solid $warning;
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
        Binding("ctrl+s", "save_research", "Save Research Session"),
        Binding("ctrl+q", "quit", "Quit"),
    ]

    def __init__(self):
        super().__init__()
        self.messages = [
            {"role": "system", "content": "You are a world-class Perplexity-style research tool. Answer questions by combining broad web queries via web_search with strict academic preprint discovery via discover_papers. Synthesise facts into a cleanly structured, cited, and comprehensive output answer."}
        ]

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
        self.query_one("#chat_log", RichLog).write("[bold green]ResearchBot Ready[/bold green] Start asking!\n")
        self.query_one("#tool_log", RichLog).write("[bold orange3]Tool Stream Log Connected.[/bold orange3]\n")
        self.query_one(Input).focus()


    def on_input_submitted(self, event: Input.Submitted) -> None:
        user_text = event.value.strip()
        if not user_text:
            return

        event.input.clear()
        
        chat_log = self.query_one("#chat_log", RichLog)
        chat_log.write(f"[bold cyan][You][/bold cyan] {user_text}")
        chat_log.write("[italic gray]Thinking...[/italic gray]\n")

        self.messages.append({"role": "user", "content": user_text})
        self.messages = trim_history(self.messages, MAX_HISTORY_TURNS)

        self.run_worker(self._agent_execution_loop(), thread=True)
        

    async def _agent_execution_loop(self) -> None:
        chat_log = self.query_one("#chat_log", RichLog)
        tool_log = self.query_one("#tool_log", RichLog)
        
        max_iterations = 8
        
        for iteration in range(max_iterations):
            try:
                response = client.chat.completions.create(
                    model=MODEL,
                    messages=self.messages,
                    tools=TOOLS
                )
                
                message = response.choices[0].message
                finish_reason = response.choices[0].finish_reason

                if finish_reason == "tool_calls" or message.tool_calls:
                    self.messages.append(message)
                    
                    for tool_call in message.tool_calls:
                        t_name = tool_call.function.name
                        t_args = tool_call.function.arguments
                        
                        self.call_from_thread(
                            tool_log.write, 
                            f"[bold yellow][Tool Invoke][/bold yellow] Function: [bold white]{t_name}[/bold white]\nParams: {t_args}"
                        )
                        
                        result_json = dispatch_tool(tool_call)
                        
                        self.call_from_thread(
                            tool_log.write, 
                            f"[bold green][Tool Output Log][/bold green] Success. Returned payload block: {len(result_json)} chars.\n"
                        )

                        self.messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "name": t_name,
                            "content": result_json
                        })
                    continue

                elif finish_reason == "stop" or message.content:
                    self.messages.append({"role": "assistant", "content": message.content})
                    self.messages = trim_history(self.messages, MAX_HISTORY_TURNS)
                    
                    self.call_from_thread(
                        chat_log.write, 
                        f"[bold magenta][AI][/bold magenta]\n{message.content}\n"
                    )
                    return

            except Exception as e:
                self.call_from_thread(
                    chat_log.write, 
                    f"[bold red][Runtime Exception][/bold red] Network pipeline error: {str(e)}\n"
                )
                return

        self.call_from_thread(
            chat_log.write, 
            "[bold red][System Notice][/bold red] Ceiling tracking depth reached without final answer convergence.\n"
        )


    def action_clear_display(self) -> None:
        self.query_one("#chat_log", RichLog).clear()
        self.query_one("#tool_log", RichLog).clear()
        self.query_one("#chat_log", RichLog).write("[bold yellow]Display layout cleared.[/bold yellow]\n")


    def action_clear_history(self) -> None:
        self.messages = [
            {"role": "system", "content": "You are a world-class Perplexity-style research tool. Answer questions by combining broad web queries via web_search with strict academic preprint discovery via discover_papers. Synthesise facts into a cleanly structured, cited, and comprehensive output answer."}
        ]
        self.query_one("#chat_log", RichLog).clear()
        self.query_one("#tool_log", RichLog).clear()
        self.query_one("#chat_log", RichLog).write("[bold red]Conversation context completely reset.[/bold red]\n")


    def action_save_research(self) -> None:
        chat_log = self.query_one("#chat_log", RichLog)
        filename = f"research_note_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        
        try:
            with open(filename, "w", encoding="utf-8") as f:
                f.write(f"# Research Notes Export — {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
                for entry in self.messages:
                    if isinstance(entry, dict):
                        role = entry.get("role", "unknown").upper()
                        content = entry.get("content", "")
                    else:
                        role = getattr(entry, "role", "unknown").upper()
                        content = getattr(entry, "content", "")
                        
                    if content and role != "SYSTEM":
                        f.write(f"### {role}\n{content}\n\n---\n\n")
            chat_log.write(f"[bold green][System Saved][/bold green] File generated successfully: [underline]{filename}[/underline]\n")
        except Exception as e:
            chat_log.write(f"[bold red][Save Failure][/bold red] Failed to write file down to disk: {str(e)}\n")



if __name__ == "__main__":
    if "SERPER_API_KEY" not in os.environ:
        print("CRITICAL: Please export your SERPER_API_KEY environment variable before launch.", file=sys.stderr)
    ResearchBotTUI().run()
