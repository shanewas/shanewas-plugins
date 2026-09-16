import { execFileSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import path from "node:path";

const root = path.dirname(fileURLToPath(import.meta.url));
const donecheck = path.join(root, "tools", "donecheck.py");

// Run the gate over one done-claim file plus optional evidence logs.
// Returns { ok, missing } or null when python is unavailable. Never
// throws: a gate that crashes the session is worse than no gate. Block
// mode (exit 2) still reports through ok:false rather than raising.
export function checkDone(claim, evidence = [], options = {}) {
  const args = [donecheck, "check", "--claim", claim, "--json"];
  for (const log of [].concat(evidence ?? [])) {
    args.push("--evidence", log);
  }
  const env = { ...process.env };
  if (options.mode != null) env.VERIFY_DONE_MODE = options.mode;
  try {
    const out = execFileSync("python3", args, {
      encoding: "utf-8",
      timeout: 30000,
      env,
    });
    const report = JSON.parse(out);
    return { ok: report.ok, missing: report.missing };
  } catch (err) {
    if (err && err.status === 2) {
      try {
        const report = JSON.parse(String(err.stdout ?? ""));
        return { ok: false, blocked: true, missing: report.missing };
      } catch {
        return { ok: false, blocked: true };
      }
    }
    return null;
  }
}

export const plugin = async (ctx) => {
  return {
    name: "verify-done",
    description: "Zero-dependency done-claim evidence gate for OpenCode",
    version: "1.0.0",
    checkDone,
  };
};
