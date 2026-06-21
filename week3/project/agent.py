import os
import sys
import json
import uuid
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI

from tools.files import read_file, write_file, edit_file, list_files
from tools.papers import paper_search, read_paper
from tools.web import web_search, web_fetch

load_dotenv()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ.get("OPENROUTER_API_KEY"),
)

PRIMARY_MODEL = "openai/gpt-oss-120b:free"
FALLBACK_MODEL = "google/gemini-2.5-flash:free" 

WORKSPACE_ROOT = os.environ.get("WORKSPACE_ROOT", ".")
SESSIONS_DIR = os.path.abspath(os.path.join(WORKSPACE_ROOT, "sessions"))
os.makedirs(SESSIONS_DIR, exist_ok=True)

TOOLS = [
    {"type": "function", "function": {"name": "web_search", "description": "Search the live web for general facts, background news, and documentation.", "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}}},
    {"type": "function", "function": {"name": "web_fetch", "description": "Fetch the raw plaintext contents of a specific URL.", "parameters": {"type": "object", "properties": {"url": {"type": "string"}}, "required": ["url"]}}},
    {"type": "function", "function": {"name": "paper_search", "description": "Queries the HuggingFace academic repository to look up official peer-reviewed arXiv preprints.", "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}}},
    {"type": "function", "function": {"name": "read_paper", "description": "Retrieves comprehensive textual sections or markdown summaries from an explicit arXiv ID.", "parameters": {"type": "object", "properties": {"arxiv_id": {"type": "string"}}, "required": ["arxiv_id"]}}},
    {"type": "function", "function": {"name": "read_file", "description": "Read local sandboxed file lines with paginated line numbers.", "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "start_line": {"type": "integer"}, "read_lines": {"type": "integer"}}, "required": ["path"]}}},
    {"type": "function", "function": {"name": "write_file", "description": "Write a fresh content payload down to disk inside the workspace area.", "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}}, "required": ["path", "content"]}}},
    {"type": "function", "function": {"name": "list_files", "description": "List existing workspace files matching standard search patterns.", "parameters": {"type": "object", "properties": {"pattern": {"type": "string"}}, "required": []}}},
    {"type": "function", "function": {"name": "edit_file", "description": "Surgically modify specific targeted lines inside files (replace, delete, append).", "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "operation": {"type": "string"}, "start_line": {"type": "integer"}, "end_line": {"type": "integer"}, "content": {"type": "string"}}, "required": ["path", "operation", "start_line"]}}},
]

TOOL_REGISTRY = {
    "web_search": web_search, "web_fetch": web_fetch,
    "paper_search": paper_search, "read_paper": read_paper,
    "read_file": read_file, "write_file": write_file,
    "list_files": list_files, "edit_file": edit_file
}

class Agent:
    def __init__(self, session_id=None):
        self.session_id = session_id or uuid.uuid4().hex[:8]
        self.messages = []
        self.resumed_topic = None
        self.active_model = PRIMARY_MODEL
        self.load_or_create_session()

    def load_or_create_session(self):
        self.session_file = os.path.join(SESSIONS_DIR, f"{self.session_id}.json")
        base_prompt = "You are a world-class Perplexity-style research tool. Answer questions combining web search, academic preprints, and file tools."
        
        for rules_path in ("AGENTS.md", ".agent/AGENTS.md"):
            if os.path.isfile(rules_path):
                with open(rules_path, "r", encoding="utf-8") as f:
                    base_prompt += f"\n\n## Project Rules\n{f.read()}"
                break

        if os.path.exists(self.session_file):
            with open(self.session_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.messages = data.get("messages", [])
            
            for msg in self.messages:
                if isinstance(msg, dict) and msg.get("role") == "user":
                    content = msg.get("content", "")
                    self.resumed_topic = content[:40] + "..." if len(content) > 40 else content
                    break
                elif not isinstance(msg, dict) and getattr(msg, "role", None) == "user":
                    content = getattr(msg, "content", "")
                    self.resumed_topic = content[:40] + "..." if len(content) > 40 else content
                    break
            if not self.resumed_topic:
                self.resumed_topic = "Existing Active Workspace Thread"
        else:
            self.messages = [{"role": "system", "content": base_prompt}]
            self.save_session()

    def save_session(self):
        serializable_messages = []
        for m in self.messages:
            if isinstance(m, dict):
                serializable_messages.append(m)
            else:
                d = {"role": getattr(m, "role", "assistant"), "content": getattr(m, "content", "") or ""}
                if getattr(m, "tool_calls", None):
                    d["tool_calls"] = [
                        {"id": tc.id, "type": "function", "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
                        for tc in m.tool_calls
                    ]
                serializable_messages.append(d)

        payload = {
            "id": self.session_id,
            "updated_at": datetime.now().isoformat(),
            "messages": serializable_messages
        }
        with open(self.session_file, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

    def _emit(self, log_type: str, text: str):
        pass

    def chat(self, user_text: str) -> str:
        self.messages.append({"role": "user", "content": user_text})
        self.save_session()
        
        max_loops = 8
        for _ in range(max_loops):
            try:
                response = client.chat.completions.create(
                    model=self.active_model, 
                    messages=self.messages, 
                    tools=TOOLS
                )
                msg = response.choices[0].message
                finish = response.choices[0].finish_reason

                if finish == "tool_calls" or msg.tool_calls:
                    self.messages.append(msg)
                    for tc in msg.tool_calls:
                        self._emit("invoke", f"Tool: {tc.function.name} -> {tc.function.arguments}")
                        func = TOOL_REGISTRY.get(tc.function.name)
                        if func:
                            try:
                                args = json.loads(tc.function.arguments)
                                res = func(**args)
                            except Exception as ex:
                                res = {"error": f"Invalid arguments format layout: {str(ex)}"}
                        else:
                            res = {"error": f"Tool {tc.function.name} is missing in registry."}

                        res_str = json.dumps(res)
                        self._emit("output", f"Returned chunk size: {len(res_str)} chars.")
                        
                        self.messages.append({
                            "role": "tool",
                            "tool_call_id": tc.id,
                            "name": tc.function.name,
                            "content": res_str
                        })
                    continue

                if msg.content:
                    self.messages.append({"role": "assistant", "content": msg.content})
                    self.save_session()
                    return msg.content

            except Exception as e:
                err_str = str(e)
                if "429" in err_str and self.active_model == PRIMARY_MODEL:
                    self._emit("error", f"Rate Limit 429 caught. Dynamically failing over to: {FALLBACK_MODEL}")
                    self.active_model = FALLBACK_MODEL
                    continue
                
                err_msg = f"Network pipeline execution loop crashed: {err_str}"
                self._emit("error", err_msg)
                return err_msg
                
        return "Iteration depth cutoff triggered before final convergence answer reached."


class REPLAgent(Agent):
    def _emit(self, log_type: str, text: str):
        print(f"   [{log_type.upper()}] {text}")

    def run_once(self, text: str):
        if self.resumed_topic:
            print(f"[Memory Check] Resumed: {self.resumed_topic}")
        print(f"\nUser: {text}\nThinking...")
        ans = self.chat(text)
        print(f"\nAI:\n{ans}\n")

    def run(self):
        if self.resumed_topic:
            print(f"[Memory Check] Resumed: {self.resumed_topic}")
        print(f"ResearchDesk REPL Environment Shell Active. [Session ID: {self.session_id}]")
        print("Available workspace commands: /sessions, /resume <id>, exit")
        
        while True:
            try:
                inp = input("\n> ").strip()
                if not inp: 
                    continue
                
                if inp.startswith("/"):
                    parts = inp.split(maxsplit=1)
                    command = parts[0].lower()
                    
                    if command == "/sessions":
                        if not os.path.exists(SESSIONS_DIR):
                            print("No session records found matching the workspace.")
                            continue
                        files = [f for f in os.listdir(SESSIONS_DIR) if f.endswith(".json")]
                        if not files:
                            print("No active historical context sessions found on disk.")
                            continue
                        
                        print("\n--- Available Tracked Sessions ---")
                        for file_name in sorted(files):
                            sid = file_name.replace(".json", "")
                            marker = " (Active)" if sid == self.session_id else ""
                            
                            topic = "Empty Workspace Context"
                            try:
                                with open(os.path.join(SESSIONS_DIR, file_name), "r", encoding="utf-8") as sf:
                                    sdata = json.load(sf)
                                    for msg in sdata.get("messages", []):
                                        if msg.get("role") == "user":
                                            content = msg.get("content", "")
                                            topic = content[:45] + "..." if len(content) > 45 else content
                                            break
                            except Exception:
                                pass
                            print(f"  ID: {sid:<10} | Topic: {topic}{marker}")
                        continue
                    
                    elif command == "/resume":
                        if len(parts) < 2:
                            print("Syntax error. Usage layout: /resume <session_id>")
                            continue
                        
                        target_id = parts[1].strip()
                        target_file = os.path.join(SESSIONS_DIR, f"{target_id}.json")
                        
                        if not os.path.exists(target_file):
                            print(f"Error: Session sequence ID '{target_id}' could not be located on disk.")
                            continue
                        
                        self.session_id = target_id
                        self.messages = []
                        self.resumed_topic = None
                        self.load_or_create_session()
                        
                        if self.resumed_topic:
                            print(f"Resumed: {self.resumed_topic}")
                        else:
                            print(f"Switched over context. Context ID: {self.session_id}")
                        continue
                    
                    else:
                        print(f"Unknown workspace macro action command line choice: {command}")
                        continue

                if inp.lower() in ["quit", "exit"]: 
                    break
                    
                ans = self.chat(inp)
                print(f"\nAI:\n{ans}")
                
            except (KeyboardInterrupt, EOFError):
                print("\nExiting ResearchDesk REPL shell loop environment.")
                break


if __name__ == "__main__":
    args = sys.argv[1:]
    
    target_session = None
    if "--session" in args:
        idx = args.index("--session")
        if idx + 1 < len(args):
            target_session = args[idx + 1]
            args = [a for i, a in enumerate(args) if i not in (idx, idx + 1)]
            
    if "--tui" in args:
        from tui import TUIAgent
        TUIAgent(session_id=target_session).run()
    elif len(args) > 0:
        REPLAgent(session_id=target_session).run_once(" ".join(args))
    else:
        REPLAgent(session_id=target_session).run()
