import { existsSync } from "node:fs";
import path from "node:path";
import { NextResponse } from "next/server";

export const runtime = "nodejs";

const root = process.cwd();

export async function GET() {
  return NextResponse.json({
    ok: true,
    root,
    envLocalExists: existsSync(path.join(root, ".env.local")),
    agentEnvExists: existsSync(path.join(root, "apps", "agent-service", ".env")),
    convexInstalled: existsSync(path.join(root, "node_modules", "convex")),
    gatewayInstalled: existsSync(path.join(root, "scripts", "mia-gateway.mjs")),
    dashboardEnvExists: existsSync(path.join(root, "apps", "dashboard", ".env.local")),
  });
}
