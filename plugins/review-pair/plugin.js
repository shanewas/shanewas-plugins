import { execFileSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import path from "node:path";

const root = path.dirname(fileURLToPath(import.meta.url));
const reviewfmt = path.join(root, "tools", "reviewfmt.py");

// Run the gate over review findings text (one finding per line).
// Pass { file } to check a findings file instead of piping text.
// Returns { ok, counts, malformed } or null when python is
// unavailable. Never throws: a gate that crashes the session is
// worse than no gate. Block mode (exit 2) still reports through
// ok:false rather than raising.
export function checkReview(findings, options = {}) {
  const args = [reviewfmt, "check", "--json"];
  if (options.file) args.splice(2, 0, options.file);
  const env = { ...process.env };
  if (options.mode != null) env.REVIEW_PAIR_MODE = options.mode;
  const execOptions = { encoding: "utf-8", timeout: 30000, env };
  if (!options.file) execOptions.input = findings ?? "";
  try {
    const out = execFileSync("python3", args, execOptions);
    const report = JSON.parse(out);
    const counts = report.counts ?? {};
    const ok =
      (counts.blocker ?? 0) === 0 &&
      (counts.major ?? 0) === 0 &&
      (report.malformed ?? []).length === 0;
    return { ok, counts, malformed: report.malformed ?? [] };
  } catch (err) {
    if (err && err.status === 2) {
      try {
        const report = JSON.parse(String(err.stdout ?? ""));
        return {
          ok: false,
          blocked: true,
          counts: report.counts ?? {},
          malformed: report.malformed ?? [],
        };
      } catch {
        return { ok: false, blocked: true };
      }
    }
    return null;
  }
}

export const plugin = async (ctx) => {
  return {
    name: "review-pair",
    description: "Zero-dependency review-findings shape gate for OpenCode",
    version: "1.0.0",
    checkReview,
  };
};
