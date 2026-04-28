#!/usr/bin/env node

import { existsSync, mkdirSync, writeFileSync } from "node:fs";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(__dirname, "..");
const logsDir = path.join(root, ".mia", "logs");
mkdirSync(logsDir, { recursive: true });

const nodePath = process.execPath;
const gatewayPath = path.join(root, "scripts", "mia-gateway.mjs");
const launchAgentsDir = path.join(os.homedir(), "Library", "LaunchAgents");
const plistPath = path.join(launchAgentsDir, "com.mia.gateway.plist");

if (!existsSync(gatewayPath)) {
  throw new Error(`Missing gateway script: ${gatewayPath}`);
}

mkdirSync(launchAgentsDir, { recursive: true });

const plist = `<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>com.mia.gateway</string>
  <key>ProgramArguments</key>
  <array>
    <string>${nodePath}</string>
    <string>${gatewayPath}</string>
  </array>
  <key>WorkingDirectory</key>
  <string>${root}</string>
  <key>RunAtLoad</key>
  <true/>
  <key>KeepAlive</key>
  <true/>
  <key>StandardOutPath</key>
  <string>${path.join(logsDir, "launchd.out.log")}</string>
  <key>StandardErrorPath</key>
  <string>${path.join(logsDir, "launchd.err.log")}</string>
  <key>EnvironmentVariables</key>
  <dict>
    <key>PATH</key>
    <string>${[
      path.join(root, ".venv", "bin"),
      "/opt/homebrew/bin",
      "/usr/local/bin",
      "/usr/bin",
      "/bin",
      "/usr/sbin",
      "/sbin",
    ].join(":")}</string>
  </dict>
</dict>
</plist>
`;

writeFileSync(plistPath, plist);

console.log(`Wrote ${plistPath}`);
console.log("");
console.log("Load it with:");
console.log(`launchctl bootstrap gui/$(id -u) ${plistPath}`);
console.log("");
console.log("Stop it with:");
console.log("launchctl bootout gui/$(id -u)/com.mia.gateway");
console.log("");
console.log("Logs:");
console.log(logsDir);
