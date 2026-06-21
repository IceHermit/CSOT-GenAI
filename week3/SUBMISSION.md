# Week 2: Research Bot

This week's objective was to improve last week's ResearchBot and introduce features such as saving sessions which can be resumed later and integrating with CLI arguments to operate in 3 modes: Single Query, REPL, and TUI mode.

# Preview

TUI Mode:
<img width="1814" height="798" alt="image" src="https://github.com/user-attachments/assets/97e17263-3719-4823-9e91-867f64320b8f" />

REPL Mode:
<img width="1337" height="574" alt="image" src="https://github.com/user-attachments/assets/858a4943-66fa-4649-bfcf-dd8b26940add" />

Resuming Previous Sessions:
<img width="1494" height="339" alt="image" src="https://github.com/user-attachments/assets/e5b22c4b-4c34-4d4e-9b1c-8427d2bd0722" />

Single Query Mode:
<img width="1128" height="150" alt="image" src="https://github.com/user-attachments/assets/ff6403ea-5119-4948-9bd9-ce1d0e66a8f6" />


# Setup

- You need the following modules installed on your machine (call `pip install -r requirements.txt`)
```
openai
dotenv
textual
requests
beautifulsoup4
```

- You also need an OpenAI API key and a Serper API key.
- You need to create a .env file in the same folder as the main script, copy the contents of .env.example and add your API keys there.
- You can now call `python3 agent.py` to run the python script.
- Call `python3 agent.py --session [SESSION_ID]` to resume a session
- Call `python3 agent.py [QUERY]` to ask a single query then close the program
- Call `python3 agent.py --tui` to run the bot in TUI mode
- You can use a combination of these modes, `python3 agent.py --session [SESSION_ID] --tui` runs the previously saved session in TUI mode

# Features
- A TUI-based interface in place of a simple CLI. Made using the Textual module in Python. Multiple colour themes are also supported.
- OpenAI Tool Calling, which allows the ChatBot to search the web and discover research papers in order to help answer queries.
- Chat Transcript Saving, which allows the user to save the chat history in a local file so that they can look at it later.
- An option to run the program in an REPL interface, and also a quick way to ask a single query
- Ability to save and resume sessions.

# How it was made

A large part of this week's work was about cleaning up last week's advancements, and organizing them in different files to make the program more modular. This makes it easier to add more features in the future, as every new feature is just a new script that you could plug in to the existing script. <br>
A great example of this is separating the backend and frontend: `agent.py` holds the core code which runs the chatbot, meanwhile `tui.py` simply references this core code and gives it a frontend. This also means `agent.py` can run on its own via the command line, ie. the REPL method. 

The other big feature added this week was the ability to save and load sessions, which is done by simply dumping the json data of the chat history to a local file, and reading from it later. This is done with simple file I/O.
