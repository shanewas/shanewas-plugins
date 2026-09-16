import { execFileSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import path from "node:path";

const root = path.dirname(fileURLToPath(import.meta.url));
const ledger = path.join(root, "tools", "ledger.py");

// Log one hook event to the ledger. Returns true on a logged record,
// false when the event carried nothing to log. Never throws: a logger
// that crashes the session is worse than no logger.
export function appendAudit(event) {
  try {
    execFileSync("python3", [ledger, "append"], {
      input: JSON.stringify(event ?? {}),
      encoding: "utf-8",
      timeout: 30000,
    });
    return true;
  } catch {
    return null;
  }
}

export const plugin = async (ctx) => {
  return {
    name: "audit-trail",
    description: "Zero-dependency edit ledger and review digest for OpenCode",
    version: "1.1.0",
    appendAudit,
  };
};
