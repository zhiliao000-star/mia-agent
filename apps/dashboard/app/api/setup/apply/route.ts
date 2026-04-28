import { mkdirSync, writeFileSync } from "node:fs";
import path from "node:path";
import { NextResponse } from "next/server";

export const runtime = "nodejs";

const root = process.cwd();

type SetupPayload = {
  envText?: string;
  convexUrl?: string;
};

export async function POST(request: Request) {
  const body = (await request.json()) as SetupPayload;
  const envText = body.envText?.trim();
  if (!envText) {
    return NextResponse.json({ ok: false, error: "Missing envText" }, { status: 400 });
  }

  const rootEnv = path.join(root, ".env.local");
  const dashboardEnv = path.join(root, "apps", "dashboard", ".env.local");
  const agentEnv = path.join(root, "apps", "agent-service", ".env");
  mkdirSync(path.dirname(dashboardEnv), { recursive: true });
  mkdirSync(path.dirname(agentEnv), { recursive: true });

  writeFileSync(rootEnv, `${envText}\n`);
  writeFileSync(agentEnv, `${envText}\n`);
  if (body.convexUrl) {
    writeFileSync(dashboardEnv, `NEXT_PUBLIC_CONVEX_URL=${body.convexUrl}\n`);
  }

  return NextResponse.json({
    ok: true,
    written: [rootEnv, agentEnv, body.convexUrl ? dashboardEnv : null].filter(Boolean),
  });
}
