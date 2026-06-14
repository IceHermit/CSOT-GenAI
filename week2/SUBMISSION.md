# Week 2: Research Bot

This week's objective was to make a Perplexity-style Bot which is capable of searching the web and research papers to answer queries. 

# Preview

<img width="1829" height="930" alt="image" src="https://github.com/user-attachments/assets/fb78b1f9-f79e-4fba-9e27-2b903e0b1853" />

<img width="1822" height="817" alt="image" src="https://github.com/user-attachments/assets/4da0a238-28cc-420a-94f0-6abd9cfb4c28" />

# Setup

- You need the following modules installed on your machine
```
opanai
dotenv
textual
requests
```

- You also need an OpenAI API key and a Serper API key.
- You need to create a .env file in the same folder as the main script, copy the contents of .env.example and add your API keys there.
- You can now call `python3 agent.py` to run the python script.

# Features
- A TUI-based interface in place of a simple CLI. Made using the Textual module in Python. Multiple colour themes are also supported.
- OpenAI Tool Calling, which allows the ChatBot to search the web and discover research papers in order to help answer queries.
- Chat Transcript Saving, which allows the user to save the chat history in a local file so that they can look at it later.

# How it was made
