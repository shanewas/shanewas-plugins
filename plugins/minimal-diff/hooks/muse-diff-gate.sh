#!/bin/sh
# Muse native hook wrapper: native hook commands are structured argv with
# no shell, so the git-diff pipeline (inlined in the Claude/Codex shell
# hooks) lives here. Muse runs hooks with cwd set to the session
# workspace and MUSE_PLUGIN_ROOT pointing at this plugin's root.
root="${MUSE_PLUGIN_ROOT:-$(dirname "$0")/..}"
git diff HEAD -- | python3 "$root/tools/diffgate.py" check --hook
