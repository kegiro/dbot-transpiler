#!/bin/bash
echo "==========================================="
echo "  DBot Mac/Linux CLI Auto-Setup"
echo "==========================================="
echo

# 1. Create the dbot wrapper script
echo "[1/3] Creating dbot launcher wrapper..."
cat << 'EOF' > dbot
#!/bin/bash
python3 "$(dirname "$0")/main.py" "$@"
EOF
chmod +x dbot
echo "Done."

# 2. Append to Path in Shell Profiles
echo "[2/3] Adding current directory to PATH in shell profile..."
DIR="$(pwd)"
SHELL_FILES=()

# Determine profile targets
if [ -f "$HOME/.bashrc" ]; then
    SHELL_FILES+=("$HOME/.bashrc")
fi
if [ -f "$HOME/.zshrc" ]; then
    SHELL_FILES+=("$HOME/.zshrc")
fi
if [ -f "$HOME/.profile" ]; then
    SHELL_FILES+=("$HOME/.profile")
fi
if [ -f "$HOME/.bash_profile" ]; then
    SHELL_FILES+=("$HOME/.bash_profile")
fi

if [ ${#SHELL_FILES[@]} -eq 0 ]; then
    echo "Warning: No shell configuration file (~/.bashrc, ~/.zshrc, etc.) was found."
    echo "Please add: export PATH=\"\$PATH:$DIR\" to your shell configuration manually."
else
    for file in "${SHELL_FILES[@]}"; do
        if ! grep -q "$DIR" "$file"; then
            echo "" >> "$file"
            echo "# DBot Compiler Alias path" >> "$file"
            echo "export PATH=\"\$PATH:$DIR\"" >> "$file"
            echo "Success: Added to $file"
        else
            echo "Info: Already configured in $file"
        fi
    done
fi

echo
echo "[3/3] Setup Completed!"
echo "==========================================="
echo "Please restart your terminal or run:"
echo "   source <profile_file> (e.g. source ~/.zshrc)"
echo "Then verify by running: dbot --help"
echo "==========================================="
