# Week 2: Research Bot

This week's objective was to make a Perplexity-style Bot which is capable of searching the web and research papers to answer queries. 

# Preview

<img width="1829" height="930" alt="image" src="https://github.com/user-attachments/assets/fb78b1f9-f79e-4fba-9e27-2b903e0b1853" />

<img width="1822" height="817" alt="image" src="https://github.com/user-attachments/assets/4da0a238-28cc-420a-94f0-6abd9cfb4c28" />

<img width="1814" height="839" alt="image" src="https://github.com/user-attachments/assets/8ef878b0-6f39-4e72-9672-60a210e01d26" />

<img width="1809" height="835" alt="image" src="https://github.com/user-attachments/assets/28b2e1c4-483e-4662-9c6b-f8322080a22d" />

<img width="1816" height="842" alt="image" src="https://github.com/user-attachments/assets/81e79b54-ef58-4c77-8dee-d1f6efa7fb51" />

# Setup

- You need the following modules installed on your machine (call `pip install -r requirements.txt`)
```
opanai
dotenv
textual
requests
beautifulsoup4
```

- You also need an OpenAI API key and a Serper API key.
- You need to create a .env file in the same folder as the main script, copy the contents of .env.example and add your API keys there.
- You can now call `python3 agent.py` to run the python script.

# Features
- A TUI-based interface in place of a simple CLI. Made using the Textual module in Python. Multiple colour themes are also supported.
- OpenAI Tool Calling, which allows the ChatBot to search the web and discover research papers in order to help answer queries.
- Chat Transcript Saving, which allows the user to save the chat history in a local file so that they can look at it later.

# How it was made

Builds 1, 2, and 3, helped teach the required modules which were then commpiled into `agent.py` to create a full-fledged ResearchBot.

- Build 1 taught tool calling, which was first done by asking the model to print a specific format to call a tool
```
<tool_call>
{"name": "tool_name", "arguments": {"arg1": "val1"}}
</tool_call>
```
then repeatedly looking for such tool calls in the model's response using regex
- Later this was replaced with OpenAI's native solution for tool calling, which is a far cleaner way to handle this problem.
- A tool dispatcher was made next, which holds the data structure mapping a tool call to the corresponding function.
- 4 tools were implemented: `web_search`, `web_fetch`, `discover_papers`, `get_paper_content`.
- `web_search` uses the Serper API to search the web and return results (check the first preview image).
- `web_fetch` handles requests and HTML cleanup using the `BeautifulSoup` module.
- `discover_papers` and `get_paper_content` use the AlphaXiv MCP server to look through research papers (check the second preview image).

- Next up was presentation, a TUI was composed using the `textual` module. I needed a lot of help from Google Gemini to complete the TUI frontend.
- Two main windows were set up: Chat-log and Tool-log. The Chat-log showed all the messages from the user and ResearchBot, whereas the Tool-log showed all the tool calls made by the bot.
- 5 keybinds were added, `^Q` = quit, `^L` = clear display, `^K` = clear history, `^S` = save transcript, `^P` = palette (change theme).
- The keybinds were made functional, and the `save transcript` function was implemented by writing the chat log to a local file.
- Everything was then finalized, and previous week's gitHub repository was updated to include week-2's project as well.

# Challenges

I was unable to make tool calling compatible with streaming, because of which a massive downside of the current implementation is long wait-times between queries.
Every implementation I tried seemed to break the code in one way or the other, I assume this is because of the fact that tool calling is baked into the model's response, so it is hard to detect when the final message begins and the tool calling stops. Due to limited time, I decided to submit my project without featuring text streaming, and this is something I would like to revisit in week-3 and hopefully implement it properly in next week's project.
