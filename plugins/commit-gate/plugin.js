import { execFileSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import path from "node:path";

const root = path.dirname(fileURLToPath(import.meta.url));
const commitcheck = path.join(root, "tools", "commitcheck.py");

// Run the gate over one commit message plus staged paths.
// Returns { ok, violations } or null when python is unavailable. Never
// throws: a gate that crashes the session is worse than no gate. Block
// mode (exit 2) still reports through ok:false rather than raising.
export function checkCommit(messageFile, staged = [], options = {}) {
  const args = [commitcheck, "check", "--message-file", messageFile, "--json"];
  const list = [].concat(staged ?? []);
  if (list.length) {
    args.push("--staged", list.join("\n"));
  }
  if (options.ban) {
    args.push("--ban", [].concat(options.ban).join(","));
  }
  if (options.allow) {
    args.push("--allow", [].concat(options.allow).join(","));
  }
  if (options.ticketRegex) {
    args.push("--ticket-regex", options.ticketRegex);
  }
  const env = { ...process.env };
  if (options.mode != null) env.COMMIT_GATE_MODE = options.mode;
  try {
    const out = execFileSync("python3", args, {
      encoding: "utf-8",
      timeout: 30000,
      env,
    });
    const report = JSON.parse(out);
    return { ok: report.ok, violations: report.violations };
  } catch (err) {
    if (err && err.status === 2) {
      try {
        const report = JSON.parse(String(err.stdout ?? ""));
        return { ok: false, blocked: true, violations: report.violations };
      } catch {
        return { ok: false, blocked: true };
      }
    }
    return null;
  }
}

export const plugin = async (ctx) => {
  return {
    name: "commit-gate",
    description: "Zero-dependency commit-message and staged-file gate for OpenCode",
    version: "1.1.0",
    checkCommit,
  };
};
