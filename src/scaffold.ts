// scaffold.ts — writes the content-repo template tree into ./<name>.
// The template lives as real files under template/ (shipped in the npm
// package); this module copies it, substituting {{PLACEHOLDER}} values.

import { spawnSync } from "node:child_process";
import { existsSync, mkdirSync, readdirSync, readFileSync, writeFileSync } from "node:fs";
import { createRequire } from "node:module";
import { dirname, join, resolve } from "node:path";

const require = createRequire(import.meta.url);

export interface ScaffoldOptions {
  typstVersion: string;
  force: boolean;
}

function templateRoot(): string {
  // template/ ships as a sibling of dist/ in the published package.
  const marker = require.resolve("../template/mise.toml");
  return dirname(marker);
}

function today(): string {
  // Local date, YYYY-MM-DD — filenames and meta dates must agree.
  const d = new Date();
  const mm = String(d.getMonth() + 1).padStart(2, "0");
  const dd = String(d.getDate()).padStart(2, "0");
  return `${d.getFullYear()}-${mm}-${dd}`;
}

export function scaffold(name: string, opts: ScaffoldOptions): void {
  if (!/^[a-z0-9][a-z0-9._-]*$/i.test(name)) {
    throw new Error(`invalid repo name: ${name} (use letters, digits, ., _, -)`);
  }

  const root = resolve(name);
  if (existsSync(root)) {
    const nonEmpty = existsSync(join(root, "mise.toml")) || existsSync(join(root, "content"));
    if (nonEmpty && !opts.force) {
      throw new Error(
        `${root} already exists and looks scaffolded (mise.toml or content/ present); use --force to overwrite files`,
      );
    }
  }

  const subs: Record<string, string> = {
    NAME: name,
    TYPST_VERSION: opts.typstVersion,
    DATE: today(),
  };
  const renames: [RegExp, string][] = [[/(^|\/)DATE-(.+\.typ)$/, `$1${subs.DATE}-$2`]];

  const tpl = templateRoot();
  let count = 0;
  walk(tpl, (rel) => {
    let body = readFileSync(join(tpl, rel), "utf8");
    for (const [key, value] of Object.entries(subs)) {
      body = body.split(`{{${key}}}`).join(value);
    }
    const outRel = renames.reduce((acc, [re, to]) => acc.replace(re, to), rel);
    // npm strips a root .gitignore from the package; ship it as `gitignore`
    // and write it under its real name at scaffold time.
    const destRel = outRel === "gitignore" ? ".gitignore" : outRel;
    const dest = join(root, destRel);
    mkdirSync(dirname(dest), { recursive: true });
    writeFileSync(dest, body, "utf8");
    count++;
  });

  console.log(`scaffolded ${root} (${count} files)`);
  console.log("");

  const git = initGit(root);
  console.log("next steps:");
  console.log(`  cd ${name}`);
  if (!git) {
    console.log(`  git init && git add -A && git commit -m "init content-repo"`);
  }
  console.log(`  mise install`);
  console.log(`  prek install`);
  console.log(`  python3 .agents/skills/build/scripts/build.py`);
  console.log(`  python3 -m http.server -d build 8001`);
  console.log("");
  console.log("deploy: push to Netlify (netlify.toml is ready)");
}

function initGit(root: string): boolean {
  // prek's hooks only run inside a git repo, and a content-repo's audit log
  // starts at the first commit — so wire both at scaffold time when git is
  // available. Missing git is not an error; the next-steps hint covers it.
  if (spawnSync("git", ["--version"], { stdio: "ignore" }).status !== 0) {
    return false;
  }
  const run = (args: string[]): boolean =>
    spawnSync("git", args, { cwd: root, stdio: "ignore" }).status === 0;
  if (!run(["init", "-b", "main"]) || !run(["add", "-A"])) {
    return false;
  }
  // Containers/CI often have no user.name/user.email; give the fresh repo a
  // local identity so the initial commit always lands (amendable later).
  const hasIdentity = (key: string): boolean =>
    spawnSync("git", ["config", key], { cwd: root, encoding: "utf8" }).stdout.trim() !== "";
  if (!hasIdentity("user.email")) {
    run(["config", "user.email", "content-repo@localhost"]);
  }
  if (!hasIdentity("user.name")) {
    run(["config", "user.name", "content-repo"]);
  }
  return run(["commit", "-m", "init content-repo"]);
}

function walk(root: string, fn: (rel: string) => void): void {
  // readdirSync with recursive:true returns both files and directories; this
  // wrapper recurses explicitly so separators stay "/" on every platform.
  for (const entry of readdirSync(root, { withFileTypes: true })) {
    const abs = join(root, entry.name);
    if (entry.isDirectory()) {
      walk(abs, (rel) => fn(`${entry.name}/${rel}`));
    } else if (entry.isFile()) {
      fn(entry.name);
    }
  }
}
