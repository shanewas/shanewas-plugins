import { execFileSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import path from "node:path";

const root = path.dirname(fileURLToPath(import.meta.url));
const slop = path.join(root, "tools", "slop.py");

// Run the gate over one file. Returns { score, band } or null when the
// file is missing or python is unavailable. Never throws: a gate that
// crashes the session is worse than no gate.
export function checkSlop(file, threshold = 20) {
  try {
    const out = execFileSync(
      "python3",
      [slop, "score", file, "--json", "--no-profile"],
      { encoding: "utf-8", timeout: 30000 }
    );
    const report = JSON.parse(out);
    if (report.score >= threshold) {
      return { tripped: true, score: report.score, band: report.band };
    }
    return { tripped: false, score: report.score, band: report.band };
  } catch {
    return null;
  }
}

export const plugin = async (ctx) => {
  return {
    name: "slop-gate",
    description: "Zero-dependency AI-slop scorer and edit gate for OpenCode",
    version: "1.0.0",
    checkSlop,
  };
};
