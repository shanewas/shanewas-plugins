#!/usr/bin/env bash
# Bash port of add-plugin.ps1: scaffold a new cross-agent plugin package.
# Requires only bash + python3. Usage:
#   ./add-plugin.sh --name NAME [--description TEXT] [--category CAT] [--root DIR]
set -euo pipefail

NAME=""
DESCRIPTION="Plugin description"
CATEGORY="productivity"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

while [ $# -gt 0 ]; do
  case "$1" in
    --name)
      [ $# -ge 2 ] || { echo "error: --name needs a value" >&2; exit 1; }
      NAME="$2"; shift 2 ;;
    --description)
      [ $# -ge 2 ] || { echo "error: --description needs a value" >&2; exit 1; }
      DESCRIPTION="$2"; shift 2 ;;
    --category)
      [ $# -ge 2 ] || { echo "error: --category needs a value" >&2; exit 1; }
      CATEGORY="$2"; shift 2 ;;
    --root)
      [ $# -ge 2 ] || { echo "error: --root needs a value" >&2; exit 1; }
      ROOT="$2"; shift 2 ;;
    -h|--help)
      echo "Usage: $0 --name NAME [--description TEXT] [--category CAT] [--root DIR]"
      exit 0 ;;
    *)
      echo "error: unknown argument: $1" >&2; exit 1 ;;
  esac
done

if [ -z "$NAME" ]; then
  echo "error: --name is required" >&2
  exit 1
fi

PLUGIN_DIR="$ROOT/plugins/$NAME"

if [ -e "$PLUGIN_DIR" ]; then
  echo "Plugin directory already exists: $PLUGIN_DIR" >&2
  exit 1
fi

echo "Creating plugin scaffold at $PLUGIN_DIR..."

# 1. Directories
mkdir -p "$PLUGIN_DIR/.claude-plugin" "$PLUGIN_DIR/skills/$NAME" \
  "$PLUGIN_DIR/commands" "$PLUGIN_DIR/agents"

# 2-4. JSON manifests (plugin.json, gemini-extension.json, package.json)
python3 - "$PLUGIN_DIR" "$NAME" "$DESCRIPTION" <<'EOF'
import json
import sys

plugin_dir, name, description = sys.argv[1], sys.argv[2], sys.argv[3]

claude_plugin = {
    "name": name,
    "description": description,
    "version": "1.0.0",
    "author": {
        "name": "Shanewas Ahmed",
        "email": "shanewasahmed@gmail.com",
    },
}

gemini_ext = {
    "name": name,
    "description": description,
    "version": "1.0.0",
    "contextFileName": "GEMINI.md",
}

pkg_json = {
    "name": "@shanewas/plugin-%s" % name,
    "version": "1.0.0",
    "description": description,
    "author": "Shanewas Ahmed <shanewasahmed@gmail.com>",
    "license": "MIT",
    "main": "plugin.js",
    "dependencies": {
        "@opencode-ai/plugin": "^1.17.8",
    },
}

for filename, payload in (
    (".claude-plugin/plugin.json", claude_plugin),
    ("gemini-extension.json", gemini_ext),
    ("package.json", pkg_json),
):
    with open("%s/%s" % (plugin_dir, filename), "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)
        fh.write("\n")
EOF

# 5. OpenCode plugin.js stub
cat >"$PLUGIN_DIR/plugin.js" <<EOF
export const plugin = async (ctx) => {
  return {
    name: "$NAME",
    description: "$DESCRIPTION",
    version: "1.0.0"
  };
};
EOF

# 6. Starter SKILL.md
cat >"$PLUGIN_DIR/skills/$NAME/SKILL.md" <<EOF
---
name: $NAME
description: $DESCRIPTION
---

# $NAME Skill

$DESCRIPTION
EOF

# 7. Register in root .claude-plugin/marketplace.json
python3 - "$ROOT/.claude-plugin/marketplace.json" "$NAME" "$DESCRIPTION" "$CATEGORY" <<'EOF'
import json
import sys

marketplace_path, name, description, category = (
    sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])

with open(marketplace_path, encoding="utf-8") as fh:
    marketplace = json.load(fh)

marketplace["plugins"].append({
    "name": name,
    "description": description,
    "version": "1.0.0",
    "author": {
        "name": "Shanewas Ahmed",
        "email": "shanewasahmed@gmail.com",
    },
    "source": "./plugins/%s" % name,
    "category": category,
    "homepage": "https://github.com/shanewas/shanewas-plugins",
})

with open(marketplace_path, "w", encoding="utf-8") as fh:
    json.dump(marketplace, fh, indent=2)
    fh.write("\n")
EOF

echo "Plugin '$NAME' created and registered in .claude-plugin/marketplace.json!"
