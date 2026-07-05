# DBot Transpiler

A custom transpiler that converts `.dbot` domain-specific language (DSL) into JavaScript code utilizing the `discord.js` library (v14). This project is built to explore compiler construction, AST (Abstract Syntax Tree) generation, and automated Discord bot development.

## Project Overview
The transpiler automates the creation of Discord bot event handlers, slash commands, and interaction logic. By writing code in the `.dbot` DSL, users can quickly generate robust `discord.js` bots without manually writing boilerplate for gateway intents, rest command registration, or interaction routing.

## Key Features
* **Command Registration:** Automatically syncs custom commands with the Discord API.
* **Interaction Handling:** Supports chat input commands and button-based interactions.
* **DSL Modifiers:** Supports modifiers like `admin` (permission gating) and `private` (ephemeral replies).
* **Built-in Persistence:** Includes a lightweight JSON-based database helper for storing bot state.

## Getting Started

### Prerequisites
* [Node.js](https://nodejs.org/) (v16.9.0 or higher)
* [Python 3.x](https://www.python.org/)
* `discord.js` library installed in your project:
    ```bash
    npm install discord.js
    ```

### Usage
1.  **Write your script:** Create your bot logic in a `main.dbot` file.
2.  **Transpile:** Use the `Generator` class in `generator.py` to convert your `.dbot` file into a `main.js` file.
3.  **Run:** Execute your generated bot:
    ```bash
    node main.js
    ```

## Example
**Input (`main.dbot`):**
```text
command ping {
    reply "pong!"
}
