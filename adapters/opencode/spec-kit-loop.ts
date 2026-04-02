/**
 * Forja adapter for OpenCode
 *
 * Integrates the Ralph Loop and Autoresearch Loop with OpenCode's
 * session.compacting hooks and plugin system.
 */

import { z } from "zod";
import { execSync } from "child_process";
import { readFileSync, existsSync } from "fs";
import { join } from "path";

// ── Types ──────────────────────────────────────────────────────────────────────

const BuildStatusSchema = z.object({
  done: z.number(),
  pending: z.number(),
  blocked: z.number(),
  total: z.number(),
  nextTask: z.string().nullable(),
});

type BuildStatus = z.infer<typeof BuildStatusSchema>;

// ── Helpers ───────────────────────────────────────────────────────────────────

function getProjectRoot(): string {
  let dir = process.cwd();
  while (dir !== "/") {
    if (existsSync(join(dir, "pyproject.toml"))) return dir;
    dir = join(dir, "..");
  }
  return process.cwd();
}

function runForja(args: string[]): string {
  const root = getProjectRoot();
  try {
    return execSync(["forja", ...args].join(" "), {
      cwd: root,
      encoding: "utf-8",
      timeout: 30_000,
    });
  } catch (e: unknown) {
    if (e instanceof Error) return e.message;
    return String(e);
  }
}

function parseBuildStatus(): BuildStatus {
  const root = getProjectRoot();
  const tasksFile = join(root, ".specify", "tasks.md");

  if (!existsSync(tasksFile)) {
    return { done: 0, pending: 0, blocked: 0, total: 0, nextTask: null };
  }

  const content = readFileSync(tasksFile, "utf-8");
  const lines = content.split("\n");

  let done = 0;
  let pending = 0;
  let blocked = 0;
  let nextTask: string | null = null;

  for (const line of lines) {
    if (/^- \[x\]/i.test(line)) done++;
    else if (/^- \[ \]/.test(line)) {
      pending++;
      if (nextTask === null) nextTask = line.replace(/^- \[ \] /, "").trim();
    } else if (/^- \[BLOCKED\]/i.test(line)) blocked++;
  }

  return { done, pending, blocked, total: done + pending + blocked, nextTask };
}

// ── OpenCode Plugin Definition ────────────────────────────────────────────────

export const forjaPlugin = {
  name: "forja",
  version: "0.1.0",
  description: "Ralph Loop + Autoresearch integration for OpenCode",

  tools: [
    {
      name: "forja_build_status",
      description: "Get the current Ralph Loop build progress",
      parameters: z.object({}),
      execute: async () => {
        const status = parseBuildStatus();
        return {
          done: status.done,
          pending: status.pending,
          blocked: status.blocked,
          total: status.total,
          nextTask: status.nextTask,
          allDone: status.pending === 0,
        };
      },
    },

    {
      name: "forja_build_next",
      description: "Get the next pending task from tasks.md",
      parameters: z.object({}),
      execute: async () => {
        const status = parseBuildStatus();
        return { nextTask: status.nextTask, allDone: status.nextTask === null };
      },
    },

    {
      name: "forja_optimize_status",
      description: "Get the current Autoresearch optimize progress",
      parameters: z.object({}),
      execute: async () => {
        const output = runForja(["optimize", "status"]);
        return { output: output.trim() };
      },
    },

    {
      name: "forja_optimize_history",
      description: "Get recent optimization experiment history",
      parameters: z.object({
        last: z.number().int().positive().default(10),
      }),
      execute: async ({ last }: { last: number }) => {
        const output = runForja(["optimize", "history", "--last", String(last)]);
        return { output: output.trim() };
      },
    },
  ],

  // session.compacting hook — called when OpenCode compacts context
  hooks: {
    "session.compacting": async () => {
      const status = parseBuildStatus();
      const summary = [
        `## Forja Build Status`,
        `- Done: ${status.done}/${status.total}`,
        `- Pending: ${status.pending}`,
        `- Blocked: ${status.blocked}`,
        status.nextTask ? `- Next: ${status.nextTask}` : "- All tasks complete!",
      ].join("\n");
      return summary;
    },
  },
};

export default forjaPlugin;
