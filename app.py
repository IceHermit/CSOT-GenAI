import os
import openai
from dotenv import load_dotenv

# for pretty printing
from rich.console import Console
from rich.markdown import Markdown
from rich.text import Text
from rich.panel import Panel


load_dotenv()

class ChatAgent:
    def __init__(self, model: str, max_turns: int = 4, system_prompt: str = "You are a helpful assistant.") -> None:


        self.client = openai.OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.environ.get("OPENROUTER_API_KEY"),
        )
        self.model: str = model
        self.max_turns: int = max_turns
        self.system_prompt: str = system_prompt
        
        self.summary_context: str = ""
        self.history: list[dict[str, str]] = [] 
        self.console = Console()


    def call_model(self, messages: list[dict[str, str]], stream: bool = True) -> str | None:

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                stream=stream
            )
            
            if stream:
                full_reply = ""
                for chunk in response:
                    token = chunk.choices[0].delta.content or ""
                    print(token, end="",flush="true")
                    full_reply += token
                
                for char in full_reply:
                    print("\b \b",end="",flush="true")
                
                md = Markdown(full_reply)
                self.console.print(md)
                return full_reply
            else:
                return response.choices[0].message.content
                
        except Exception as e:
            print(f"[API Error]: {e}")
            return None


    def compact_history(self) -> None:

        if len(self.history) < 2:
            return

        print("\n[System]: Max turns reached. Compacting oldest conversation thread...")
        
        old_pair = self.history[:2]
        self.history = self.history[2:]

        compaction_prompt = [
            {"role": "system", "content": "Summarize the core facts and context of the following dialogue concisely. Maintain key names, parameters, or choices."},
            {"role": "user", "content": f"Existing Baseline Context: {self.summary_context}\n\nNew Dialogue to merge:\nUser: {old_pair[0]['content']}\nAssistant: {old_pair[1]['content']}"}
        ]
        
        summary = self.call_model(compaction_prompt, stream=False)
        if summary:
            self.summary_context = summary
            print(f"[Current Condensed Context Memory]: {self.summary_context}\n")


    def get_full_payload(self) -> list[dict[str, str]]:

        messages = [{"role": "system", "content": self.system_prompt}]
        
        if self.summary_context:
            messages.append({
                "role": "system", 
                "content": f"Here is a summary of the earlier conversation history for context: {self.summary_context}"
            })
            
        messages.extend(self.history)
        return messages


    def interact(self, user_input: str) -> None:

        if user_input.strip().lower() == "/compact":
            self.compact_history()
            return

        if len(self.history) >= (self.max_turns * 2):
            self.compact_history()

        self.history.append({"role": "user", "content": user_input})
        
        payload = self.get_full_payload()
        
        self.console.print("AI: ", style="cornflower_blue", end="",soft_wrap=True)
        assistant_reply = self.call_model(payload, stream=True)
        
        if assistant_reply:
            self.history.append({"role": "assistant", "content": assistant_reply})


def main():
    models = {
        "1": "openai/gpt-oss-120b:free",
        "2": "google/gemma-4-31b-it:free",
        "3": "openrouter/owl-alpha"
    }

    console = Console()

    console.print(Panel.fit("Welcome to the Chatbot Setup!", title="CSOT Generative AI"))
    console.print(Markdown("__Select an active model backend:__"), style="cornflower_blue")
    for key, name in models.items():
        text = Text()
        text.append(f"[{key}] ", "bold blue")
        text.append(f"{name}", "bold")
        console.print(text)
        
    console.print(Markdown("__Select choice (Default 1)__"), style="cornflower_blue")
    choice = input().strip()
    selected_model = models.get(choice, models["1"])
    
    agent = ChatAgent(model=selected_model, max_turns=5)
    
    
    console.print(Markdown(f"\n__Agent initialized using: {selected_model}__"), style="cornflower_blue")
    console.print(Markdown("__Commands: Type 'exit' to quit, '/compact' to manually trigger context summaries.__\n"), style="cornflower_blue")

    console.print(Panel("Your chat begins here"))

    while True:
        try:
            console.print("You: ", style="spring_green3", end="", soft_wrap=True)
            user_msg = input()
            if user_msg.strip().lower() == "exit":
                console.print(Markdown("__Exiting, bye!__"), style="cornflower_blue")
                break
                
            if not user_msg.strip():
                continue
                
            agent.interact(user_msg)
            
        except KeyboardInterrupt:
            console.print(Markdown("__Session aborted__"), style="red3")
            break


if __name__ == "__main__":
    main()
