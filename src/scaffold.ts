// scaffold.ts — writes the content-repo template tree into ./<name>.
// The template lives as real files under template/ (shipped in the npm
// package); this module copies it, substituting {{PLACEHOLDER}} values.

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
    const dest = join(root, outRel);
    mkdirSync(dirname(dest), { recursive: true });
    writeFileSync(dest, body, "utf8");
    count++;
  });

  console.log(`scaffolded ${root} (${count} files)`);
  console.log("");
  console.log("next steps:");
  console.log(`  cd ${name}`);
  console.log(`  git init && git add -A && git commit -m "init content-repo"`);
  console.log(`  mise install`);
  console.log(`  python3 .agents/skills/build/scripts/build.py`);
  console.log(`  python3 -m http.server -d build 8001`);
  console.log("");
  console.log("deploy: push to Netlify (netlify.toml is ready)");
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
