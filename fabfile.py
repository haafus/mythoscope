"""Deployment tasks for the Mythoscope viewer server.

Usage (`uv tool install fabric` puts `fab` on PATH; the login account is always
explicit, the host is the site's own domain or the box's IP):

    fab -H root@mythoscope.io   bootstrap        # once per server: packages, users, units
    fab -H ubuntu@mythoscope.io deploy           # code — seconds
    fab -H ubuntu@mythoscope.io push-outputs     # data — minutes, ~2s downtime
    fab -H ubuntu@mythoscope.io push-outputs --from-zip=mythoscope-export-20260803.zip

Three rules shape everything here:

1. Code and data move independently. `deploy` never touches ``outputs/``;
   `push-outputs` never touches code. A bad code deploy costs a re-rsync of a
   few MB, not a re-upload of 368MB.

2. ``outputs/`` is swapped, never written in place. ChromaDB keeps its SQLite
   file and HNSW index open while serving; rsyncing over a live store hands the
   running process a half-written index. So we stage beside it and swap under a
   stopped service, keeping the previous copy for rollback.

3. Two accounts, never mixed. `bootstrap` is root and creates everything —
   including the deploy account; every other task is that deploy account, so
   code and data are never root-owned. Fabric falls back to your *local*
   username when the host alias names no User, so each task asserts the account
   it needs rather than trusting whatever the connection turned out to be.
"""

import io
import os
import shutil
import string
import subprocess
import tempfile
import zipfile
from pathlib import Path

from fabric import task
from invoke import Exit

# --- server layout -----------------------------------------------------------
# Code, data and venv are siblings, never nested: `rsync --delete` into APP_DIR
# cannot reach the 368MB store or the installed environment.
ROOT = "/srv/mythoscope"
APP_DIR = f"{ROOT}/app"
VENV_DIR = f"{ROOT}/venv"
OUTPUTS_DIR = f"{ROOT}/outputs"
OUTPUTS_NEXT = f"{ROOT}/outputs.next"
OUTPUTS_PREV = f"{ROOT}/outputs.prev"

SERVICE_USER = "mythoscope"
SERVICE_NAME = "mythoscope"
ENV_FILE = "/etc/mythoscope/env"
UV_BIN = "/usr/local/bin/uv"
SUDOERS_FILE = "/etc/sudoers.d/mythoscope-deploy"

# uv installs managed interpreters under $HOME, and a venv's bin/python is a
# symlink to one — which `ProtectHome=true` hides from the service, so the unit
# would die 203/EXEC. Outside ROOT on purpose: not in ReadWritePaths, so
# ProtectSystem=strict leaves the interpreter read-only for the service.
UV_PYTHON_DIR = "/opt/mythoscope-python"

# The account every task except `bootstrap` connects as; `bootstrap` creates it
# if the image ships root only (Hetzner, DigitalOcean et al.).
DEPLOY_USER = os.environ.get("MYTHO_DEPLOY_USER", "ubuntu")
DOMAIN = os.environ.get("MYTHO_DEPLOY_DOMAIN", "mythoscope.io")

# The loopback port is a contract between two files: the app binds what the
# server's env file says, Caddy proxies what this substitutes into the
# Caddyfile. `_smoke` compares them, because a mismatch leaves the app healthy
# on loopback and the public site returning 502.
APP_PORT = 8000

# Verified empirically against this tree: a venv built with `viewer` alone
# imports every module under src/server/ (including the ones imported lazily
# inside request handlers) and serves every route with a 200. The `corpus` and
# `graphs` extras add requests, beautifulsoup4, trafilatura, fake-useragent,
# PyMuPDF, openai and networkx — none of which the server imports. Add extras
# here if you later enable something that needs them; `search` (text queries)
# also needs MYTHO_SERVER__TEXT_SEARCH=true in the env file, and pulls torch.
EXTRAS = ["viewer"]

LOCAL_ROOT = Path(__file__).parent.resolve()

# Server-local or rebuild-only; never uploaded with the data.
OUTPUT_EXCLUDES = [
    "logs/",              # written by the running service on the server
    "extraction_cache.jsonl",
    "summaries.jsonl",
    "motifs/raw/",        # Berezkin/Trilogy scrape cache — rebuild fuel
]

# One per thing a deploy can break, and every one of them parameter-free.
# outputs/projections and outputs/graphs stay uncovered: their routes need a
# model/document id, so checking them means first fetching a listing.
SMOKE_PATHS = [
    "/",                          # index.html via settings.web_root (code tree)
    "/api/corpus/traditions",     # config/traditions.json — ships with the code
    "/api/corpus/documents",      # outputs/corpus/corpus.json — 500 if unreadable
    "/api/motifs/indexes",        # outputs/motifs
    "/api/similarity/models",     # opens the ChromaDB store — 503 if unreadable
]


# --- helpers -----------------------------------------------------------------

def _require_login(c, expected: str, task: str) -> None:
    """Refuse to run as the wrong account.

    `-H host` with no `User` in the host's ssh_config block silently connects as
    your *local* username, which on the server is usually nobody at all. Every
    task therefore names the account it needs.
    """
    if c.user != expected:
        raise Exit(
            f"`{task}` must connect as {expected}, not {c.user} — try:\n"
            f"  fab -H {expected}@{c.host} {task}"
        )


def _target(c) -> str:
    return f"{c.user}@{c.host}"


def _rsync(c, src: str, dest: str, extra=()) -> None:
    ssh = f"ssh -p {c.port}" if c.port and c.port != 22 else "ssh"
    args = " ".join(extra)
    c.local(
        f'rsync -az --delete --human-readable --info=stats1 '
        f'-e "{ssh}" {args} {src} {_target(c)}:{dest}'
    )


def _put_file(c, content: str, dest: str, mode: str = "0644", owner: str = "root:root") -> None:
    """Upload text to `dest` with an explicit owner and mode (bootstrap only).

    SFTP cannot set ownership, so land it in /tmp and let `install` place it.
    Encode first: paramiko counts a text stream in characters but compares
    against the remote size in bytes, so one em dash in a template is enough for
    `put` to cry "size mismatch" over a file that uploaded perfectly.
    """
    tmp = f"/tmp/.mytho-upload-{os.getpid()}-{Path(dest).name}"
    user, group = owner.split(":")
    c.put(io.BytesIO(content.encode()), tmp)
    c.run(f"install -o {user} -g {group} -m {mode} {tmp} {dest}")
    c.run(f"rm -f {tmp}")


def _regroup(c, path: str) -> None:
    """Hand a freshly-rsynced tree back to the service group.

    `rsync -a` imposes the *source*'s modes and group on the destination: it
    strips the setgid bit off the target directory itself and lands every file in
    the deploy user's own group, which drops the service onto the "other" bits.
    Measured, not assumed — and a delta rsync undoes it again, so this runs after
    every sync rather than once at bootstrap.

    `g+rX` because the source's modes are not ours to trust either: one 0600 file
    in a store built elsewhere (corpus.json arrived that way) is invisible to the
    service and surfaces as a 500 from whichever route happens to read it. `X`
    adds execute only where something already has it, and neither widens
    anything to "other".
    """
    c.run(f"chgrp -Rh {SERVICE_USER} {path}")
    c.run(f"chmod -R g+rX {path}")
    c.run(f"find {path} -type d -exec chmod 2775 {{}} +")


def _svc(c, action: str) -> None:
    c.sudo(f"systemctl {action} {SERVICE_NAME}")


def _smoke(c, retries: int = 15) -> None:
    """Hit the app through loopback (not through Caddy) so a failure points at
    the service, not at TLS or DNS."""
    port = c.run(
        f"grep -E '^MYTHO_SERVER__PORT=' {ENV_FILE} | cut -d= -f2", warn=True, hide=True
    ).stdout.strip() or str(APP_PORT)
    if port != str(APP_PORT):
        raise Exit(
            f"{ENV_FILE} sets MYTHO_SERVER__PORT={port}, but Caddy proxies {APP_PORT} — "
            f"the site would 502 while the app answers fine on loopback.\n"
            f"Either put the env file back to {APP_PORT}, or set APP_PORT in fabfile.py "
            f"and re-run `bootstrap` to re-render the Caddyfile."
        )

    ready = c.run(
        f"for i in $(seq 1 {retries}); do "
        f"curl -sf -o /dev/null http://127.0.0.1:{port}/ && exit 0; sleep 1; done; exit 1",
        warn=True, hide=True,
    )
    if not ready.ok:
        c.sudo(f"journalctl -u {SERVICE_NAME} -n 40 --no-pager", warn=True)
        raise Exit(f"Service did not answer on 127.0.0.1:{port} — see the log above.")

    failed = []
    for path in SMOKE_PATHS:
        # Keep the body: these handlers put the real cause in `detail`, and a bare
        # status code sends you to the journal for something already in the reply.
        out = c.run(
            f"curl -s -w '\\n%{{http_code}}' http://127.0.0.1:{port}{path}", hide=True
        ).stdout
        body, _, code = out.rpartition("\n")
        code = code.strip()
        print(f"  {code}  {path}")
        if code != "200":
            print(f"        {body.strip()[:300]}")
            failed.append(f"{path} -> {code}")
    if failed:
        raise Exit("Smoke check failed: " + "; ".join(failed))


def _local_sha() -> str:
    try:
        sha = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"], cwd=LOCAL_ROOT,
            capture_output=True, text=True, check=True,
        ).stdout.strip()
        dirty = subprocess.run(
            ["git", "status", "--porcelain"], cwd=LOCAL_ROOT,
            capture_output=True, text=True, check=True,
        ).stdout.strip()
        return f"{sha}{'-dirty' if dirty else ''}"
    except subprocess.CalledProcessError:
        return "unknown"


def _du(path: Path) -> str:
    total = sum(f.stat().st_size for f in path.rglob("*") if f.is_file())
    return f"{total / 1e6:.0f}MB"


# --- tasks -------------------------------------------------------------------

@task
def bootstrap(c):
    """Install packages, create both accounts, install units. Idempotent.

    Connects as root, so nothing here needs sudo. It grants the deploy account
    passwordless sudo on the way out, which is what makes every later task
    non-interactive.
    """
    _require_login(c, "root", "bootstrap")

    print("== packages ==")
    c.run("apt-get update -qq")
    c.run(
        "DEBIAN_FRONTEND=noninteractive apt-get install -y -qq "
        "rsync curl sudo ca-certificates debian-keyring debian-archive-keyring apt-transport-https"
    )

    print("== deploy account ==")
    if c.run(f"id -u {DEPLOY_USER}", warn=True, hide=True).ok:
        print(f"  {DEPLOY_USER} exists — account left alone")
    else:
        # Key-only, exactly like a provider-supplied `ubuntu`: no password is
        # set, so console and `su` are locked and sudo below is NOPASSWD.
        # Copying root's authorized_keys is what lets the key you are connected
        # with right now also drive `deploy`.
        if not c.run("test -s /root/.ssh/authorized_keys", warn=True, hide=True).ok:
            raise Exit(
                "/root/.ssh/authorized_keys is missing or empty — there is no key to "
                f"copy, and {DEPLOY_USER} would be created with no way to log in."
            )
        home = f"/home/{DEPLOY_USER}"
        c.run(f"useradd --create-home --shell /bin/bash {DEPLOY_USER}")
        c.run(f"install -d -m 700 -o {DEPLOY_USER} -g {DEPLOY_USER} {home}/.ssh")
        c.run(
            f"install -m 600 -o {DEPLOY_USER} -g {DEPLOY_USER} "
            f"/root/.ssh/authorized_keys {home}/.ssh/authorized_keys"
        )
        print(f"  created {DEPLOY_USER}; authorized_keys copied from root")

    # Applied whether or not we created the account, so a provider image's
    # `ubuntu` and a bootstrap-created one end up identical. cloud-init's shape:
    # the drop-in alone is what grants sudo, the group is convention.
    c.run(f"usermod -aG sudo {DEPLOY_USER}")
    sudoers = f"{DEPLOY_USER} ALL=(ALL) NOPASSWD:ALL\n"
    tmp = "/tmp/.mytho-sudoers"
    c.put(io.BytesIO(sudoers.encode()), tmp)
    if not c.run(f"visudo -c -f {tmp}", warn=True, hide=True).ok:
        c.run(f"rm -f {tmp}")
        raise Exit("Generated sudoers drop-in failed validation — not installing it.")
    c.run(f"install -o root -g root -m 0440 {tmp} {SUDOERS_FILE}")
    c.run(f"rm -f {tmp}")

    print("== caddy ==")
    if not c.run("command -v caddy", warn=True, hide=True).ok:
        c.run(
            "curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' "
            "| gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg"
        )
        c.run(
            "curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' "
            "> /etc/apt/sources.list.d/caddy-stable.list"
        )
        c.run("apt-get update -qq")
        c.run("DEBIAN_FRONTEND=noninteractive apt-get install -y -qq caddy")
    else:
        print("  already installed")

    print("== uv ==")
    if not c.run(f"test -x {UV_BIN}", warn=True, hide=True).ok:
        # System-wide so the deploy user and any future operator share one uv.
        c.run(f"sh -c 'curl -LsSf https://astral.sh/uv/install.sh | UV_INSTALL_DIR={Path(UV_BIN).parent} sh'")
    else:
        print(f"  {c.run(f'{UV_BIN} --version', hide=True).stdout.strip()}")

    print("== service account and directories ==")
    # System account: no login, no home of its own — it only reads the tree.
    c.run(
        f"id -u {SERVICE_USER} >/dev/null 2>&1 || "
        f"useradd --system --no-create-home --shell /usr/sbin/nologin {SERVICE_USER}"
    )
    c.run(f"usermod -aG {SERVICE_USER} {DEPLOY_USER}")
    # Owned by the deploy user so rsync and `uv sync` need no sudo; group-readable
    # so the service can read it. setgid keeps new files in the group, which is
    # what lets the service write outputs/logs after we rsync the store in.
    c.run(f"mkdir -p {APP_DIR} {OUTPUTS_DIR} {OUTPUTS_DIR}/logs /etc/mythoscope /var/log/caddy")
    c.run(f"chown -R {DEPLOY_USER}:{SERVICE_USER} {ROOT}")
    # Written by `deploy` as the deploy user, read and executed by the service.
    c.run(f"install -d -m 2775 -o {DEPLOY_USER} -g {SERVICE_USER} {UV_PYTHON_DIR}")
    # Only on directories — `chmod -R 2775` would set the setgid bit on regular
    # files too, which means something else entirely there.
    c.run(f"find {ROOT} -type d -exec chmod 2775 {{}} +")

    print("== env file ==")
    if c.run(f"test -f {ENV_FILE}", warn=True, hide=True).ok:
        print(f"  {ENV_FILE} exists — left alone")
    else:
        _put_file(
            c, (LOCAL_ROOT / "etc/mythoscope.env.example").read_text(),
            ENV_FILE, mode="0640", owner=f"root:{SERVICE_USER}",
        )

    print("== systemd unit ==")
    _put_file(c, (LOCAL_ROOT / "etc/mythoscope.service").read_text(),
              f"/etc/systemd/system/{SERVICE_NAME}.service")
    c.run("systemctl daemon-reload")
    c.run(f"systemctl enable {SERVICE_NAME}")

    print("== caddy site ==")
    caddyfile = string.Template((LOCAL_ROOT / "etc/Caddyfile").read_text()).safe_substitute(
        DOMAIN=DOMAIN, PORT=APP_PORT
    )
    _put_file(c, caddyfile, "/etc/caddy/Caddyfile", owner="root:caddy", mode="0644")
    if not c.run("caddy validate --config /etc/caddy/Caddyfile", warn=True).ok:
        raise Exit("Caddyfile failed validation — not reloading Caddy.")
    # `validate` provisions the config, which opens the log writer — as root,
    # leaving a root-owned mythoscope.log that the `caddy` user then cannot open
    # ("setting up custom log 'log0'"). Fix ownership after validating, never
    # before, or the next validate re-creates the problem.
    c.run("install -d -m 0755 -o caddy -g caddy /var/log/caddy")
    c.run("chown -R caddy:caddy /var/log/caddy")
    c.run("systemctl reload caddy || systemctl restart caddy")

    print(
        f"\nBootstrap done for {DOMAIN}.\n"
        f"  1. Point {DOMAIN}'s A record at this host (Caddy gets certs on first request).\n"
        f"  2. Review {ENV_FILE}.\n"
        f"  3. fab -H {DEPLOY_USER}@{c.host} deploy && "
        f"fab -H {DEPLOY_USER}@{c.host} push-outputs\n"
        f"  Everything from here on connects as {DEPLOY_USER}, not root.\n"
        f"  The service is enabled but not started — it has no code yet."
    )


@task
def deploy(c):
    """Sync code, install dependencies, restart, smoke check."""
    _require_login(c, DEPLOY_USER, "deploy")

    lock = LOCAL_ROOT / "uv.lock"
    if not lock.exists():
        raise Exit("No uv.lock — run `uv lock` first. --frozen will not resolve without it.")
    if subprocess.run(["git", "ls-files", "--error-unmatch", "uv.lock"], cwd=LOCAL_ROOT,
                      capture_output=True).returncode != 0:
        print("  [warn] uv.lock is untracked — commit it so the server installs what you tested")

    sha = _local_sha()
    if sha.endswith("-dirty"):
        print("  [warn] working tree is dirty — deploying uncommitted changes")

    print(f"== rsync code ({sha}) ==")
    # `:- .gitignore` reuses the repo's own ignore rules, so there is no second
    # list to drift. That already excludes outputs/, .venv/, .env and *.pkl.
    _rsync(c, "./", APP_DIR, extra=[
        "--filter=':- .gitignore'",
        "--exclude=.git/",
        "--exclude=mockups/",
        "--exclude=docs/",
        "--exclude=tests/",
    ])

    print("== link data ==")
    # settings.py reads outputs/ relative to WorkingDirectory; the real store
    # lives outside the rsync target, so bridge them with a symlink.
    c.run(f"test -L {APP_DIR}/outputs || ln -sfn {OUTPUTS_DIR} {APP_DIR}/outputs")

    print("== uv sync ==")
    extras = " ".join(f"--extra {e}" for e in EXTRAS)
    c.run(
        f"cd {APP_DIR} && UV_PROJECT_ENVIRONMENT={VENV_DIR} "
        f"UV_PYTHON_INSTALL_DIR={UV_PYTHON_DIR} "
        f"{UV_BIN} sync --frozen --no-dev {extras}"
    )
    c.run(f"printf '%s\\n' '{sha}' > {APP_DIR}/DEPLOYED")

    print("== permissions ==")
    # Last, so it covers what `uv sync` and the stamp just wrote too.
    _regroup(c, APP_DIR)

    print("== restart ==")
    _svc(c, "restart")
    _smoke(c)
    print(f"\nDeployed {sha} to https://{DOMAIN}")


@task(help={"from_zip": "A `mytho export` bundle to unpack and push instead of the local outputs/."})
def push_outputs(c, from_zip=None):
    """Upload outputs/ and swap it in under a stopped service (~2s downtime)."""
    _require_login(c, DEPLOY_USER, "push-outputs")

    staging = None
    try:
        if from_zip:
            zip_path = Path(from_zip).expanduser().resolve()
            if not zip_path.exists():
                raise Exit(f"No such bundle: {zip_path}")
            staging = Path(tempfile.mkdtemp(prefix="mytho-bundle-"))
            print(f"== unpack {zip_path.name} ==")
            # Unpack locally rather than shipping the zip: rsync then does a
            # delta transfer, and re-pushes after a partial rebuild stay cheap.
            with zipfile.ZipFile(zip_path) as zf:
                zf.extractall(staging)
            src = staging / "outputs"
            if not src.is_dir():
                raise Exit(f"{zip_path.name} has no outputs/ at its root — not a `mytho export` bundle.")
        else:
            src = LOCAL_ROOT / "outputs"
            if not src.is_dir():
                raise Exit(f"No {src} — build the pipeline or pass --from-zip.")

        print(f"== staging {_du(src)} to {OUTPUTS_NEXT} ==")
        # Seed the staging dir from the live store first, so rsync only sends
        # the delta rather than the whole 368MB on every push.
        c.run(f"test -d {OUTPUTS_NEXT} || cp -a {OUTPUTS_DIR} {OUTPUTS_NEXT}")
        _rsync(c, f"{src}/", OUTPUTS_NEXT,
               extra=[f"--exclude={p}" for p in OUTPUT_EXCLUDES])

        print("== permissions ==")
        _regroup(c, OUTPUTS_NEXT)
        # Chroma opens its SQLite store read-write even to serve reads (§5 of
        # docs/deployment.md), so group-read is not enough for this one subtree:
        # /api/similarity/models 503s with "attempt to write a readonly database"
        # while every other route is fine. The rest of outputs/ stays 0644.
        store = f"{OUTPUTS_NEXT}/embeddings"
        if c.run(f"test -d {store}", warn=True, hide=True).ok:
            c.run(f"find {store} -type f -exec chmod 0664 {{}} +")

        print("== swap ==")
        # The only window where the store is inconsistent — the service is down
        # for it. Two renames on the same filesystem, so it is fast.
        _svc(c, "stop")
        try:
            # `mytho server` calls setup_logging() on every start (cli.py), which
            # mkdirs outputs/logs and opens a FileHandler — the service needs group
            # write there, and rsync -a would have carried the local mode over.
            # The rm is sudo'd because the previous store contains whatever the
            # service wrote as `mythoscope`, and unlinking those needs write on
            # the directory holding them — which the service may own outright.
            c.sudo(f"rm -rf {OUTPUTS_PREV}")
            c.run(
                f"mv {OUTPUTS_DIR} {OUTPUTS_PREV} && "
                f"mv {OUTPUTS_NEXT} {OUTPUTS_DIR} && mkdir -p {OUTPUTS_DIR}/logs && "
                f"chmod 2775 {OUTPUTS_DIR} {OUTPUTS_DIR}/logs"
            )
        except Exception:
            # A swap that dies half-way should not also be an outage: bring the
            # service back on whatever store is in place, then surface the error.
            c.sudo(f"systemctl start {SERVICE_NAME}", warn=True)
            raise
        _svc(c, "start")
        _smoke(c)
        print(f"\nOutputs live. Previous store kept at {OUTPUTS_PREV} (`fab rollback-outputs`).")
    finally:
        if staging and staging.exists():
            shutil.rmtree(staging, ignore_errors=True)


@task
def rollback_outputs(c):
    """Swap outputs.prev back in."""
    _require_login(c, DEPLOY_USER, "rollback-outputs")
    if not c.run(f"test -d {OUTPUTS_PREV}", warn=True, hide=True).ok:
        raise Exit(f"No {OUTPUTS_PREV} to roll back to.")
    _svc(c, "stop")
    try:
        c.sudo(f"rm -rf {OUTPUTS_NEXT}")  # service-written files: see push-outputs
        c.run(f"mv {OUTPUTS_DIR} {OUTPUTS_NEXT} && mv {OUTPUTS_PREV} {OUTPUTS_DIR}")
    except Exception:
        c.sudo(f"systemctl start {SERVICE_NAME}", warn=True)
        raise
    _svc(c, "start")
    _smoke(c)
    print(f"\nRolled back. The store you replaced is at {OUTPUTS_NEXT}.")


@task
def status(c):
    """Deployed revision, service state, disk."""
    _require_login(c, DEPLOY_USER, "status")
    c.run(f"cat {APP_DIR}/DEPLOYED 2>/dev/null || echo 'no DEPLOYED stamp'")
    c.sudo(f"systemctl status {SERVICE_NAME} --no-pager -n 5", warn=True)
    c.run(f"du -sh {OUTPUTS_DIR} {OUTPUTS_PREV} 2>/dev/null", warn=True)
    c.run(f"df -h {ROOT} | tail -1")


@task(help={"n": "Number of lines (default 100)."})
def logs(c, n=100):
    """Tail the service journal."""
    _require_login(c, DEPLOY_USER, "logs")
    c.sudo(f"journalctl -u {SERVICE_NAME} -n {n} --no-pager")


@task
def restart(c):
    """Restart the service and smoke check it."""
    _require_login(c, DEPLOY_USER, "restart")
    _svc(c, "restart")
    _smoke(c)


@task
def smoke(c):
    """Run the smoke check without touching anything."""
    _require_login(c, DEPLOY_USER, "smoke")
    _smoke(c)
