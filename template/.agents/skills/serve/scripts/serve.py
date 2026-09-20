#!/usr/bin/env python3
"""Dev server for the content-repo: serves build/ on :3000 and rebuilds
when content/, assets/, or the build script change.

Stdlib only; Linux + mise assumed (typst is routed through mise by the
build script itself). Rebuilds always run the ordinary build script in a
fresh process, so the dev loop exercises the exact pipeline Netlify runs.

Usage: python3 .agents/skills/serve/scripts/serve.py [--port N] [--host H]
"""

import os
import subprocess
import sys
import threading
import time
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
BUILD = REPO / "build"
BUILD_SCRIPT = REPO / ".agents" / "skills" / "build" / "scripts" / "build.py"
WATCH_DIRS = (REPO / "content", REPO / "assets")
WATCH_FILES = (BUILD_SCRIPT,)
DEFAULT_PORT = 3000
DEFAULT_HOST = "127.0.0.1"
POLL_SECONDS = 0.5
DEBOUNCE_SECONDS = 0.4


def die(msg):
    print("serve: ERROR: " + msg, file=sys.stderr)
    sys.exit(1)


def run_build():
    """Run the ordinary build in a fresh process; report but survive failure."""
    print("serve: build start", flush=True)
    p = subprocess.run([sys.executable, str(BUILD_SCRIPT)], cwd=str(REPO))
    if p.returncode == 0:
        print("serve: build ok — reload the page", flush=True)
    else:
        print(
            "serve: build FAILED (exit "
            + str(p.returncode)
            + ") — fix the error and save to retry",
            flush=True,
        )


def snapshot():
    """mtime fingerprint of everything watched. A dict compare detects
    creates, edits, and deletions without inotify watch bookkeeping."""
    state = {}
    for d in WATCH_DIRS:
        if not d.is_dir():
            continue
        for root, _dirs, names in os.walk(d):
            for name in names:
                p = Path(root) / name
                try:
                    state[str(p)] = p.stat().st_mtime_ns
                except OSError:
                    pass  # vanished mid-scan; the next poll sees the deletion
    for f in WATCH_FILES:
        if f.is_file():
            try:
                state[str(f)] = f.stat().st_mtime_ns
            except OSError:
                pass
    return state


def watch_loop(stop):
    prev = snapshot()
    while not stop.is_set():
        time.sleep(POLL_SECONDS)
        cur = snapshot()
        if cur == prev:
            continue
        while not stop.is_set():  # debounce: wait for edit bursts to settle
            time.sleep(DEBOUNCE_SECONDS)
            settled = snapshot()
            if settled == cur:
                break
            cur = settled
        if stop.is_set():
            break
        changed = [p for p in set(prev) | set(cur) if prev.get(p) != cur.get(p)]
        for p in sorted(changed):
            try:
                rel = str(Path(p).relative_to(REPO))
            except ValueError:
                rel = p
            print("serve: changed: " + rel, flush=True)
        prev = cur
        run_build()
        # Edits landing during the rebuild still differ from prev, so the
        # next poll schedules one more build — never a missed change.


def main():
    port, host = DEFAULT_PORT, DEFAULT_HOST
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        a = args[i]
        if a in ("--port", "--host"):
            if i + 1 >= len(args):
                die(a + " requires a value")
            val = args[i + 1]
            if a == "--port":
                try:
                    port = int(val)
                except ValueError:
                    die("--port needs an integer, got: " + val)
            else:
                host = val
            i += 2
        elif a in ("-h", "--help"):
            print(__doc__)
            return
        else:
            die("unknown argument: " + a)

    if not (REPO / "content").is_dir():
        die("no content/ dir at " + str(REPO) + " — run from the repo root")
    if not BUILD_SCRIPT.is_file():
        die("missing build script: " + str(BUILD_SCRIPT))

    run_build()  # initial build; on failure keep serving — watch retries on fix

    handler = partial(SimpleHTTPRequestHandler, directory=str(BUILD))
    httpd = ThreadingHTTPServer((host, port), handler)
    httpd.daemon_threads = True

    stop = threading.Event()
    threading.Thread(target=watch_loop, args=(stop,), daemon=True).start()

    print("serve: http://{}:{}/ -> {}".format(host, port, BUILD), flush=True)
    print("serve: watching content/, assets/, build.py — Ctrl+C stops", flush=True)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        stop.set()
        httpd.server_close()
        print("serve: stopped", flush=True)


if __name__ == "__main__":
    main()
