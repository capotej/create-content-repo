#!/usr/bin/env node
// @capotej/create-content-repo — zero-dependency scaffolder.
// Usage: npx @capotej/create-content-repo <name> [--typst-version <ver>]
// No subcommands, no runtime deps: parse argv, scaffold, print next steps.

import { scaffold } from "./scaffold.js";
import { fileURLToPath } from "node:url";

interface Args {
  name: string | undefined;
  typstVersion: string;
  force: boolean;
}

function parseArgs(argv: string[]): Args {
  const args: Args = { name: undefined, typstVersion: "0.15.1", force: false };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--typst-version") {
      const v = argv[++i];
      if (v === undefined) {
        fail(`--typst-version requires a value (e.g. 0.15.1)`);
      }
      args.typstVersion = v;
    } else if (a === "--force") {
      args.force = true;
    } else if (a === "--help" || a === "-h") {
      usage();
      process.exit(0);
    } else if (a === "--version" || a === "-v") {
      console.log(resolveVersion());
      process.exit(0);
    } else if (a.startsWith("--")) {
      fail(`unknown flag: ${a}`);
    } else if (args.name === undefined) {
      args.name = a;
    } else {
      fail(`unexpected extra argument: ${a}`);
    }
  }
  return args;
}

function resolveVersion(): string {
  // ESM: read package.json next to the compiled dist/cli.js
  const { readFileSync } = require_fs();
  const path = fileURLToPath(new URL("../package.json", import.meta.url));
  const pkg = JSON.parse(readFileSync(path, "utf8")) as { version: string };
  return pkg.version;
}

function require_fs(): typeof import("node:fs") {
  // Node >=22 ships process.getBuiltinModule; tsc rejects a bare require() in ESM.
  const fs = (
    process as unknown as {
      getBuiltinModule?: (id: string) => typeof import("node:fs");
    }
  ).getBuiltinModule?.("node:fs");
  if (fs) return fs;
  throw new Error("process.getBuiltinModule unavailable (need Node >= 22)");
}

function usage(): void {
  console.log(`Usage: npx @capotej/create-content-repo <name> [options]

Scaffolds ./<name> as a content-repo: Typst (.typ) content, agent skills with
a stdlib-Python build orchestrator, mise-pinned toolchain, Netlify deploy.

Options:
  --typst-version <ver>  typst version to pin in mise.toml (default 0.15.1)
  --force                scaffold into a non-empty directory
  -h, --help             show this help
  -v, --version          print the generator version`);
}

function fail(msg: string): never {
  console.error(`create-content-repo: ${msg}`);
  console.error(`Run with --help for usage.`);
  process.exit(1);
}

function main(): void {
  const args = parseArgs(process.argv.slice(2));
  if (args.name === undefined) {
    usage();
    process.exit(1);
  }
  scaffold(args.name, { typstVersion: args.typstVersion, force: args.force });
}

main();
