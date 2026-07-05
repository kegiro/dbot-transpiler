# .dbot Compiler & Runtime

`.dbot` is an elegant, domain-specific language (DSL) written from scratch. It compiles clean, minimal, indentation-based pseudocode directly into modern, asynchronous JavaScript targeting **discord.js v14** on Node.js.

The language completely abstracts away complex asynchronous APIs, brackets, and boilerplate, while remaining 100% powerful by supporting loops, variables, custom functions, dynamic channel creation, and raw JavaScript escapes.

---

## Features

- **Clean Syntax**: Block structures defined by indentation. No curly braces (`{}`) or semicolons (`;`) required.
- **Auto-managed Asynchrony**: Seamlessly handles Discord's asynchronous nature. All generated routines are sequential and self-awaiting.
- **Dynamic Command Registration**: Slash commands used in your code are dynamically registered with the Discord API on boot.
- **Safe Messaging**: Handles deferred or already-replied interaction states automatically.
- **JavaScript Escape Hatch (`$`)**: Prefix any line with `$` (or use it inline) to inject raw, unparsed JavaScript directly.

---

## Installation & Setup

### 1. Prerequisites
- **Python 3.x** (for the compiler pipeline)
- **Node.js** (to run the compiled Discord bot)
- **Discord Bot Token**: Set up a bot application in the [Discord Developer Portal](https://discord.com/developers/applications) and obtain a token.

### 2. Node.js Environment Setup
Initialize your bot project directory and install the required `discord.js` dependency:
```bash
npm init -y
npm install discord.js
```

### 3. Register the CLI Tool Globally
To run the `.dbot` compiler globally from any command line, run the setup script matching your OS:

- **Windows (CMD/PowerShell)**:
  ```cmd
  setup.bat
  ```
  *(Note: restart your terminal or run `refreshenv` to apply PATH changes).*

- **macOS / Linux**:
  ```bash
  chmod +x setup.sh
  ./setup.sh
  source ~/.zshrc  # or source ~/.bashrc depending on your shell
  ```

---

## CLI Usage

The `dbot` command-line utility supports the following actions:

### Initialize a Project
Create a new project workspace directory with all boilerplate files (including Node.js initialization, `discord.js` installation, a `.env` configuration file, and a starter template):
```bash
dbot create <project_name>
```
During project initialization, the CLI will prompt you to enter your **Discord Bot Token** and **Client ID**. It then writes these to a local `.env` configuration file inside the new project directory. When executing compiled code, the CLI automatically loads variables from this `.env` file.

### Compile and Run
Automatically compiles the `.dbot` file to a `.js` target and immediately starts it with Node.js:
```bash
dbot sample.dbot
```

### Compile Only
Transpiles the `.dbot` file to a `.js` target file without running it:
```bash
dbot compile sample.dbot
```

### Run Pre-compiled Code
Runs an already-compiled JavaScript bot directly without a fresh compilation step:
```bash
dbot run sample.dbot
# or
dbot run sample.js
```

### Authentication
Provide your Discord bot token via the `DISCORD_TOKEN` environment variable:
```bash
# Windows (CMD)
set DISCORD_TOKEN=your_bot_token_here
dbot sample.dbot

# Windows (PowerShell)
$env:DISCORD_TOKEN="your_bot_token_here"
dbot sample.dbot

# macOS / Linux
export DISCORD_TOKEN="your_bot_token_here"
dbot sample.dbot
```

---

## Syntax Guide

### 1. Variables & Expressions
Assign variables inside scopes. Variable paths like `user.name` are automatically mapped to discord.js attributes.
```dbot
username = user.name
score = 0
score = score + 1
```

### 2. Slash Commands (`When player use command`)
Defines a slash command trigger. The compiler registers this command automatically.
```dbot
When player use command /ping:
    Answer: "Pong!"
```

### 3. Permissions Check
Allows guarding command logic behind roles. `Admin` resolves to server administrator privileges.
```dbot
If player != Admin:
    Answer: "Access Denied!"
```

### 4. Sending Messages & Ephemeral Answers
- `Send msg: "<text>"`: Sends a standard message reply.
- `Answer: "<text>"`: Sends a private (ephemeral) reply only visible to the user.
```dbot
Send msg: "This is public."
Answer: "This is private."
```

### 5. Interactive Buttons
Attach Success-style (green) buttons to your messages, and listen to clicks:
```dbot
Send msg: "Click below!"
Attach button name "Confirm" with id "btn_confirm"

When player click "btn_confirm":
    Answer: "Confirmed!"
```

### 6. Create Channels
Create server channels with custom parameters. `.isPrivate = true` configures permission overwrites so only the command execution user can view it.
```dbot
Create channel:
    .name = "private-chat"
    .isPrivate = true
```

### 7. Loops
Repeat execution blocks:
```dbot
repeat 3 times:
    Send msg: "Broadcast iteration!"
```

### 8. Custom Functions
Define reusable routines. Behind the scenes, these are compiled to asynchronous JS functions passing the Discord interaction context down automatically.
```dbot
function alert_user():
    Answer: "Alert triggered!"

When player use command /alert:
    alert_user()
```

### 9. Raw JavaScript Escape Hatch (`$`)
Strip the `$` symbol and inject raw, unparsed JS directly into the output:
```dbot
$console.log("This is printed in the Node.js terminal!")
timestamp = $Date.now()
```
"# dbot-transpiler" 
"# dbot-transpiler" 
