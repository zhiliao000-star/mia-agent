#!/usr/bin/env node

import { createWriteStream, existsSync, mkdirSync } from "node:fs";
import net from "node:net";
import path from "node:path";
import { spawn } from "node:child_process";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(__dirname, "..");
const logsDir = path.join(root, ".mia", "logs");
mkdirSync(logsDir, { recursive: true });

const args = new Set(process.argv.slice(2));
const getArgValue = (name, fallback = "") => {
  const raw = process.argv.find((arg) => arg.startsWith(`${name}=`));
  return raw ? raw.slice(name.length + 1) : fallback;
};

if (args.has("--help") || args.has("-h")) {
  console.log(`Mia Gateway

Usage:
  npm run mia:gateway
  npm run mia:gateway:ngrok
  node scripts/mia-gateway.mjs [options]

Options:
  --no-convex              Do not start Convex dev
  --no-dashboard           Do not start Next.js dashboard
  --no-agent               Do not start FastAPI agent service
  --tunnel=ngrok           Start ngrok for the agent service
  --dashboard-port=3000    Dashboard port
  --agent-port=8000        Agent service port
  --verbose                Stream child process output in this terminal
`);
  process.exit(0);
}

const dashboardPort = Number(getArgValue("--dashboard-port", "3000"));
const agentPort = Number(getArgValue("--agent-port", "8000"));
const tunnel = getArgValue("--tunnel", args.has("--ngrok") ? "ngrok" : "");
const verbose = args.has("--verbose");

const basePath = [
  path.join(root, ".venv", "bin"),
  "/opt/homebrew/bin",
  "/usr/local/bin",
  "/usr/bin",
  "/bin",
  "/usr/sbin",
  "/sbin",
  process.env.PATH ?? "",
].join(":");

const children = new Map();

function logLine(service, line) {
  process.stdout.write(`[${service}] ${line}`);
}

function makeLog(service) {
  return createWriteStream(path.join(logsDir, `${service}.log`), { flags: "a" });
}

function isPortOpen(port) {
  return new Promise((resolve) => {
    const socket = net.createConnection({ port, host: "127.0.0.1" });
    socket.setTimeout(500);
    socket.once("connect", () => {
      socket.destroy();
      resolve(true);
    });
    socket.once("timeout", () => {
      socket.destroy();
      resolve(false);
    });
    socket.once("error", () => resolve(false));
  });
}

function commandExists(command) {
  return new Promise((resolve) => {
    const child = spawn("sh", ["-lc", `command -v ${command}`], {
      cwd: root,
      env: { ...process.env, PATH: basePath },
      stdio: "ignore",
    });
    child.once("exit", (code) => resolve(code === 0));
  });
}

function spawnService({ name, command, args: serviceArgs, cwd = root, env = {} }) {
  const log = makeLog(name);
  log.write(`\n\n=== ${new Date().toISOString()} starting ${name} ===\n`);
  const child = spawn(command, serviceArgs, {
    cwd,
    env: { ...process.env, PATH: basePath, ...env },
    stdio: ["ignore", "pipe", "pipe"],
  });
  children.set(name, child);

  child.stdout.on("data", (chunk) => {
    const text = chunk.toString();
    log.write(text);
    if (verbose) {
      for (const line of text.split(/(?<=\n)/)) {
        if (line) logLine(name, line);
      }
    }
  });

  child.stderr.on("data", (chunk) => {
    const text = chunk.toString();
    log.write(text);
    if (verbose) {
      for (const line of text.split(/(?<=\n)/)) {
        if (line) logLine(name, line);
      }
    }
  });

  child.once("exit", (code, signal) => {
    children.delete(name);
    const line = `exited code=${code ?? "null"} signal=${signal ?? "none"}\n`;
    log.write(line);
    log.end();
    logLine("gateway", `${name} ${line}`);
  });
}

function printBanner() {
  process.stdout.write(`
███╗   ███╗██╗ █████╗      █████╗  ██████╗ ███████╗███╗   ██╗████████╗
████╗ ████║██║██╔══██╗    ██╔══██╗██╔════╝ ██╔════╝████╗  ██║╚══██╔══╝
██╔████╔██║██║███████║    ███████║██║  ███╗█████╗  ██╔██╗ ██║   ██║
██║╚██╔╝██║██║██╔══██║    ██╔══██║██║   ██║██╔══╝  ██║╚██╗██║   ██║
██║ ╚═╝ ██║██║██║  ██║    ██║  ██║╚██████╔╝███████╗██║ ╚████║   ██║
╚═╝     ╚═╝╚═╝╚═╝  ╚═╝    ╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═══╝   ╚═╝

`);
}

async function start() {
  printBanner();
  logLine("gateway", `root ${root}\n`);
  logLine("gateway", `logs ${logsDir}\n`);

  if (!args.has("--no-convex")) {
    spawnService({
      name: "convex",
      command: "npx",
      args: ["convex", "dev"],
    });
  }

  if (!args.has("--no-dashboard")) {
    if (await isPortOpen(dashboardPort)) {
      logLine("dashboard", `port ${dashboardPort} already listening; not starting duplicate\n`);
    } else {
      spawnService({
        name: "dashboard",
        command: "npx",
        args: ["next", "dev", "apps/dashboard", "-p", String(dashboardPort)],
      });
    }
  }

  if (!args.has("--no-agent")) {
    if (await isPortOpen(agentPort)) {
      logLine("agent", `port ${agentPort} already listening; not starting duplicate\n`);
    } else {
      const uvicorn = path.join(root, ".venv", "bin", "uvicorn");
      spawnService({
        name: "agent",
        command: existsSync(uvicorn) ? uvicorn : "uvicorn",
        args: ["mia.main:app", "--reload", "--port", String(agentPort)],
        cwd: path.join(root, "apps", "agent-service"),
      });
    }
  }

  if (tunnel === "ngrok") {
    if (await commandExists("ngrok")) {
      spawnService({
        name: "ngrok",
        command: "ngrok",
        args: ["http", String(agentPort)],
      });
    } else {
      logLine("ngrok", "ngrok is not installed or not on PATH; tunnel skipped\n");
    }
  }

  logLine("gateway", `dashboard http://localhost:${dashboardPort}\n`);
  logLine("gateway", `agent http://localhost:${agentPort}/health\n`);
  logLine("gateway", "child output is in .mia/logs; use --verbose to stream it here\n");
}

function shutdown(signal) {
  logLine("gateway", `received ${signal}; stopping ${children.size} child service(s)\n`);
  for (const [name, child] of children) {
    logLine("gateway", `stopping ${name}\n`);
    child.kill("SIGTERM");
  }
  setTimeout(() => process.exit(0), 1200).unref();
}

process.on("SIGINT", () => shutdown("SIGINT"));
process.on("SIGTERM", () => shutdown("SIGTERM"));

start().catch((error) => {
  logLine("gateway", `${error instanceof Error ? error.stack : String(error)}\n`);
  process.exit(1);
});
