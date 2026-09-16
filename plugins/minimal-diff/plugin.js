import { execFileSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import path from "node:path";

const root = path.dirname(fileURLToPath(import.meta.url));
const diffgate = path.join(root, "tools", "diffgate.py");

// Run the gate over one unified diff string. Returns { tripped, output }
// or null when python is unavailable. Never throws: a gate that crashes
// the session is worse than no gate. Block mode (exit 2) still reports
// through tripped rather than raising.
export function checkDiff(diff, options = {}) {
  const args = [diffgate, "check"];
  if (options.maxFiles != null) args.push("--max-files", String(options.maxFiles));
  if (options.maxLines != null) args.push("--max-lines", String(options.maxLines));
  if (options.maxConcerns != null) args.push("--max-concerns", String(options.maxConcerns));
  try {
    const out = execFileSync("python3", args, {
      input: diff ?? "",
      encoding: "utf-8",
      timeout: 30000,
    });
    return { tripped: out.trim().length > 0, output: out.trim() };
  } catch (err) {
    if (err && err.status === 2) {
      const out = String((err.stdout ?? "") + (err.stderr ?? "")).trim();
      return { tripped: true, blocked: true, output: out };
    }
    return null;
  }
}

export const plugin = async (ctx) => {
  return {
    name: "minimal-diff",
    description: "Zero-dependency diff-size gate for OpenCode",
    version: "1.1.0",
    checkDiff,
  };
};
