#!/usr/bin/env bash
#
# Installer script for AI Code Review Assistant VS Code Extension
# CEP Project AD3 - AI Code Review System
# Team: Pranjal Kute, Janhavi Phadke, Siyona Pande, Anushka Kadam
#

set -e

SOURCE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/vscode-extension" && pwd)"
TARGET_DIR="$HOME/.vscode/extensions/ad3-team.ai-code-reviewer-1.0.0"

echo "========================================================"
echo "  Installing AI Code Review Assistant into VS Code...   "
echo "========================================================"
echo "Source: $SOURCE_DIR"
echo "Target: $TARGET_DIR"

mkdir -p "$HOME/.vscode/extensions"

# Remove existing version if present
if [ -d "$TARGET_DIR" ] || [ -L "$TARGET_DIR" ]; then
    echo "Updating existing extension installation..."
    rm -rf "$TARGET_DIR"
fi

# Create symlink or copy
if ln -s "$SOURCE_DIR" "$TARGET_DIR" 2>/dev/null; then
    echo "✓ Successfully linked extension directory to ~/.vscode/extensions"
else
    cp -R "$SOURCE_DIR" "$TARGET_DIR"
    echo "✓ Successfully copied extension directory to ~/.vscode/extensions"
fi

echo ""
echo "🎉 Installation complete!"
echo "Next steps in VS Code:"
echo " 1. Open Visual Studio Code"
echo " 2. Open any Python file (e.g., in this project folder)"
echo " 3. Look at the bottom-right status bar: '$(zap) AI Review: --'"
echo " 4. Press 'Cmd+Alt+R' (Mac) or 'Ctrl+Alt+R' (Windows/Linux) to review!"
echo " 5. All issues will appear in the editor & VS Code 'Problems' panel (Cmd+Shift+M)"
echo "========================================================"
