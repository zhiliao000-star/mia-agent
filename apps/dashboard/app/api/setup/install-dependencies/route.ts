import { spawn } from "node:child_process";
import { NextResponse } from "next/server";

export const runtime = "nodejs";

function run(command: string, args: string[]) {
  return new Promise<{ code: number | null; output: string }>((resolve) => {
    const child = spawn(command, args, { cwd: process.cwd(), shell: false });
    let output = "";
    child.stdout.on("data", (chunk) => {
      output += chunk.toString();
    });
    child.stderr.on("data", (chunk) => {
      output += chunk.toString();
    });
    child.once("exit", (code) => resolve({ code, output: output.slice(-8000) }));
  });
}

export async function POST() {
  const result = await run("npm", ["install"]);
  return NextResponse.json({ ok: result.code === 0, ...result });
}
