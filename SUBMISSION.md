# CSOT-GenAI

A chatbot interface which uses OpenAI models to set up a chat instance in your terminal. <br>
(Refer to <href>https://github.com/ishananand06/CSOT26_GenAI-Agentic/</href>) <br><hr>

<img width="1652" height="883" alt="Demo" src="https://github.com/user-attachments/assets/a7b7ce64-e197-4d90-8952-bda8676e27f1" />

<hr>
<h2>Features</h2>
<br>
<ul>
<li>Multiple openAI models</li>
<li>Text streaming</li>
<li>Markdown rendering (may not work on some terminals)</li>
</ul>

<hr>
<h2>The building process</h2> <br>

First, three free models were chosen from the openAI catalogue of AI models. These models were then implemented into the program. The user first sees a setup screen where they can choose the model they want to use. Then the user enters the chat instance, where a history of recent messages is maintained (the payload) and it is prompted to the model so that it can reply to the user messages with context. A maximum limit of messages is present, and once it is reached, the program automatically summarises the previous messages and replaces the history with just one summarised message. This way the context is not entirely lost and topics from several messages ago can still be understood by the model. <br>
<br>
Next, text streaming was implemented. Without text streaming, the user has to look at a blank screen for long before any response from the model appears. With text streaming, that wait time is replaced with a live stream of text that the model is generating. <br>
<br>
One thing that this terminal-based chat instance lacked that browser-based chat instances don't was markdown rendering. For example, if you ask the model to help you with programming, it will generate code blocks but those code blocks will not appear with syntax highlighting by default. To fix this, python's Rich module was used. However, this is not easily compatible with text streaming, as markdown rendering requires you to know the full text beforehand. As a workaround, it was made so that the text is first streamed without any markdown rendering, then when it is fully loaded, it is quickly deleted and replaced with the markdown rendering enabled. Note that this may not work on some terminals, as not all terminals are able to interpret '\b' or rich text.
