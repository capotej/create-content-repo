// scaffold.ts — writes the content-repo template tree into ./<name>.
// All file bodies come from templates.ts (inlined strings).

import {
  agentsMd,
  buildPy,
  buildSkill,
  exampleAbout,
  exampleLink,
  examplePaper,
  examplePost,
  gitignore,
  miseToml,
  netlifyToml,
  newContentSkill,
  publishSkill,
  readmeMd,
} from "./templates.js";
import { existsSync, mkdirSync, writeFileSync } from "node:fs";
import { join, resolve } from "node:path";

export interface ScaffoldOptions {
  typstVersion: string;
  force: boolean;
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

  const files = new Map<string, string>();
  const t = today();

  files.set("mise.toml", miseToml(opts.typstVersion));
  files.set("netlify.toml", netlifyToml);
  files.set(".gitignore", gitignore);
  files.set("README.md", readmeMd(name));
  files.set("AGENTS.md", agentsMd(name, opts.typstVersion));

  files.set("content/posts/" + t + "-hello-world.typ", examplePost(t));
  files.set("content/links/" + t + "-typst.typ", exampleLink(t));
  files.set("content/papers/" + t + "-typst-paper.typ", examplePaper(t));
  files.set("content/pages/about.typ", exampleAbout);
  files.set("assets/.gitkeep", "");

  files.set(".agents/skills/build/SKILL.md", buildSkill);
  files.set(
    ".agents/skills/build/scripts/build.py",
    "#!/usr/bin/env python3\n" + buildPy.replace(/^#!.*\n/, ""),
  );
  files.set(".agents/skills/new-content/SKILL.md", newContentSkill);
  files.set(".agents/skills/publish/SKILL.md", publishSkill);

  for (const [rel, body] of files) {
    const dest = join(root, rel);
    mkdirSync(join(dest, ".."), { recursive: true });
    writeFileSync(dest, body, "utf8");
  }

  console.log(`scaffolded ${root} (${files.size} files)`);
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
