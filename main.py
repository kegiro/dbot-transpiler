import argparse
import sys
import os
import subprocess
from lexer import Lexer
from parser import Parser
from generator import Generator

def compile_file(dbot_path):
    if not os.path.exists(dbot_path):
        print(f"Error: File not found: {dbot_path}", file=sys.stderr)
        sys.exit(1)
        
    # Verify extension
    if not dbot_path.endswith('.dbot'):
        print(f"Warning: File {dbot_path} does not have a .dbot extension.", file=sys.stderr)
        
    print(f"Compiling {dbot_path}...")
    with open(dbot_path, "r", encoding="utf-8") as f:
        source = f.read()
        
    lexer = Lexer(source)
    try:
        tokens = lexer.tokenize()
    except Exception as e:
        print(f"Compilation Failed (Lexer):\n{e}", file=sys.stderr)
        sys.exit(1)
        
    parser = Parser(tokens)
    try:
        ast = parser.parse()
    except Exception as e:
        print(f"Compilation Failed (Parser):\n{e}", file=sys.stderr)
        sys.exit(1)
        
    generator = Generator()
    try:
        js_code = generator.transpile(ast)
    except Exception as e:
        print(f"Compilation Failed (Code Generator):\n{e}", file=sys.stderr)
        sys.exit(1)
        
    # Output target path (.js)
    base, _ = os.path.splitext(dbot_path)
    js_path = base + ".js"
    
    with open(js_path, "w", encoding="utf-8") as f:
        f.write(js_code)
        
    print(f"Successfully compiled {dbot_path} -> {js_path}")
    return js_path

def load_env_file(directory):
    env_path = os.path.join(directory, '.env')
    env_vars = {}
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' in line:
                    key, val = line.split('=', 1)
                    env_vars[key.strip()] = val.strip()
    return env_vars

def run_js(js_path):
    if not os.path.exists(js_path):
        print(f"Error: Target JavaScript file not found: {js_path}", file=sys.stderr)
        sys.exit(1)
        
    # Load .env variables from the directory of the JS file
    js_dir = os.path.dirname(os.path.abspath(js_path))
    env_vars = load_env_file(js_dir if js_dir else '.')
    
    # Also load from the current directory, just in case
    current_dir_vars = load_env_file(os.getcwd())
    
    # Combine env
    run_env = os.environ.copy()
    run_env.update(env_vars)
    run_env.update(current_dir_vars)
    
    print(f"Launching bot: node {js_path}")
    try:
        # Use subprocess to execute the compiled Node.js file
        subprocess.run(["node", js_path], env=run_env)
    except FileNotFoundError:
        print("Error: 'node' executable not found in PATH. Please install Node.js.", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nBot process stopped by user.")

def create_project(project_name):
    # 1. Create a new local directory named <project_name>
    if os.path.exists(project_name):
        print(f"Error: Directory '{project_name}' already exists.", file=sys.stderr)
        sys.exit(1)
        
    try:
        os.makedirs(project_name)
    except Exception as e:
        print(f"Error: Failed to create directory '{project_name}': {e}", file=sys.stderr)
        sys.exit(1)
        
    # 2. Interactively prompt the user in the console to type in their Discord Bot Token and their Client ID.
    print("=== Initialize new DBot Project ===")
    try:
        token = input("Enter your Discord Bot Token: ").strip()
        client_id = input("Enter your Discord Client ID: ").strip()
    except (KeyboardInterrupt, EOFError):
        print("\nProject creation cancelled.")
        sys.exit(1)
        
    # 3. Generate a .env or configuration file inside that new folder containing the Token and Client ID
    env_path = os.path.join(project_name, ".env")
    try:
        with open(env_path, "w", encoding="utf-8") as f:
            f.write(f"DISCORD_TOKEN={token}\n")
            f.write(f"DISCORD_CLIENT_ID={client_id}\n")
        print("Created .env configuration file.")
    except Exception as e:
        print(f"Error: Failed to write .env file: {e}", file=sys.stderr)
        sys.exit(1)
        
    # 4. Run `npm init -y` and `npm install discord.js` inside that target folder using Python's `subprocess` module.
    print("Initializing Node.js project...")
    try:
        use_shell = os.name == 'nt'
        subprocess.run(["npm", "init", "-y"], cwd=project_name, shell=use_shell, check=True)
        print("Installing discord.js...")
        subprocess.run(["npm", "install", "discord.js"], cwd=project_name, shell=use_shell, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error: npm setup failed: {e}", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print("Error: 'npm' executable not found. Please install Node.js and npm.", file=sys.stderr)
        sys.exit(1)
        
    # 5. Generate a default template `main.dbot` file inside the directory
    dbot_template = """# Starter template generated by dbot create

When player use command /yo:
    Send msg: "Yo! Welcome to your new DBot project. Click the button below to test interactivity:"
    Attach button name "Click Me!" with id "btn_click_me"

When player click "btn_click_me":
    Answer: "Yo! You clicked the button! It works perfectly!"
"""
    main_dbot_path = os.path.join(project_name, "main.dbot")
    try:
        with open(main_dbot_path, "w", encoding="utf-8") as f:
            f.write(dbot_template)
        print(f"Created template file: {main_dbot_path}")
    except Exception as e:
        print(f"Error: Failed to write main.dbot: {e}", file=sys.stderr)
        sys.exit(1)
        
    print(f"\nProject '{project_name}' successfully initialized!")
    print(f"To run your bot, run: dbot {os.path.join(project_name, 'main.dbot')}")

def main():
    parser = argparse.ArgumentParser(
        prog="dbot",
        description="DBot Compiler & Runner CLI"
    )
    
    # We use positional arguments to handle the custom syntax:
    # 1. dbot <file.dbot> (first arg is file, second is None)
    # 2. dbot compile <file.dbot> (first arg is 'compile', second is file)
    # 3. dbot run <file.dbot> (first arg is 'run', second is file)
    # 4. dbot create <project_name> (first arg is 'create', second is project_name)
    parser.add_argument("first", help="Action ('compile', 'run', or 'create') or the .dbot file to compile and run.")
    parser.add_argument("second", nargs="?", default=None, help="The file or project name.")
    
    args = parser.parse_args()
    
    action = None
    target_file = None
    
    if args.second is None:
        # Pattern: dbot <file.dbot> (or dbot <action> where action requires a target)
        if args.first in ("compile", "run", "create"):
            parser.error(f"The '{args.first}' command requires a target argument.")
        action = "compile_and_run"
        target_file = args.first
    else:
        # Pattern: dbot <action> <target>
        action = args.first
        target_file = args.second
        if action not in ("compile", "run", "create"):
            parser.error(f"Invalid action '{action}'. Supported actions are 'compile', 'run', 'create', or omit it to compile and run.")
            
    if action == "create":
        create_project(target_file)
    elif action == "compile":
        compile_file(target_file)
    elif action == "run":
        # Resolve target file to .js if user passed a .dbot file
        if target_file.endswith('.dbot'):
            base, _ = os.path.splitext(target_file)
            js_path = base + ".js"
        else:
            js_path = target_file
        run_js(js_path)
    elif action == "compile_and_run":
        js_path = compile_file(target_file)
        run_js(js_path)

if __name__ == "__main__":
    main()
