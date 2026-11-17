"""Own only the child processes created by this foreground demo session."""
import os
from pathlib import Path
import signal
import socket
import subprocess
import sys
import time
import urllib.request
from load_model import load_model

ROOT = Path(__file__).resolve().parent.parent
MODEL = load_model()
SERVICES_ONLY = "--services-only" in sys.argv
children = []
logs = []


def wait_for(url, proc, timeout=120):
    until = time.monotonic() + timeout
    while time.monotonic() < until:
        if proc.poll() is not None:
            raise RuntimeError(f"Process exited while waiting for {url}; inspect .run/*.log")
        try:
            with urllib.request.urlopen(url, timeout=1) as response:
                if response.status == 200:
                    return
        except (OSError, ValueError):
            pass
        time.sleep(0.5)
    raise RuntimeError(f"Timed out waiting for {url}; inspect .run/*.log")


def launch(name, command, cwd, env=None):
    log = (ROOT / ".run" / f"{name}.log").open("w")
    logs.append(log)
    proc = subprocess.Popen(command, cwd=cwd, env=env, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    children.append(proc)
    return proc


def interrupted(_signum, _frame):
    raise KeyboardInterrupt


def main():
    ports = [s["port"] for s in MODEL] + [8080, 8090] + ([] if SERVICES_ONLY else [3000, 7007])
    for port in ports:
        with socket.socket() as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                sock.bind(("127.0.0.1", port))
            except OSError as error:
                raise RuntimeError(f"Cannot bind local port {port}: {error}. Check port availability and permission to listen.") from error
    (ROOT / ".run").mkdir(exist_ok=True)
    if not SERVICES_ONLY:
        print("Building local TechDocs before the presentation...", flush=True)
        subprocess.run([str(ROOT / "scripts/build-docs.sh")], cwd=ROOT, check=True)
    for service in MODEL:
        name, port = service["name"], service["port"]
        service_env = dict(os.environ, PORT=str(port), LISTEN_ADDR="127.0.0.1", ENABLE_DEMO_CONTROLS="true" if name == "policy-service" else "false", PYTHONUNBUFFERED="1")
        # The local runner uses loopback URLs even if the shell has Compose overrides.
        for dep in MODEL:
            service_env[dep["name"].upper().replace("-", "_") + "_URL"] = f"http://127.0.0.1:{dep['port']}"
        proc = launch(name, [sys.executable, "main.py"], ROOT / "services" / name, service_env)
        wait_for(f"http://127.0.0.1:{port}/healthz", proc, 10)
    portal_env = dict(os.environ, LISTEN_ADDR="127.0.0.1", PORT="8080", PYTHONUNBUFFERED="1",
                      ONBOARDING_SERVICE_URL="http://127.0.0.1:8086", SUBSCRIPTION_SERVICE_URL="http://127.0.0.1:8082")
    portal = launch("customer-portal", [sys.executable, "main.py"], ROOT / "frontend/customer-portal", portal_env)
    wait_for("http://127.0.0.1:8080/healthz", portal, 10)
    jira = launch("jira-adapter", [sys.executable, "main.py"], ROOT / "integrations/jira", dict(os.environ, JIRA_ADAPTER_PORT="8090"))
    wait_for("http://127.0.0.1:8090/healthz", jira, 10)
    if not SERVICES_ONLY:
        print("Starting the existing Backstage app (first compile can take a minute)...", flush=True)
        backend = launch("backstage-backend", ["node", ".yarn/releases/yarn-4.13.0.cjs", "start", "backend"], ROOT / "backstage")
        frontend = launch("backstage-frontend", ["node", ".yarn/releases/yarn-4.13.0.cjs", "start", "app"], ROOT / "backstage")
        wait_for("http://localhost:7007/.backstage/health/v1/readiness", backend, 180)
        wait_for("http://localhost:3000", frontend, 180)
    print("\nDemo ready: http://localhost:3000/demo" if not SERVICES_ONLY else "\nSix services ready on ports 8081–8086.", flush=True)
    print("Customer UI: http://localhost:8080 · Jira adapter: http://localhost:8090 · Backstage delivery view: /delivery", flush=True)
    print("Run ./scripts/demo.sh happy or .venv/bin/python scripts/verify.py in another terminal.\nLogs: .run/*.log · Ctrl-C stops only this session's processes.", flush=True)
    while True:
        if any(proc.poll() is not None for proc in children):
            raise RuntimeError("A demo process exited; inspect .run/*.log")
        time.sleep(1)


if __name__ == "__main__":
    signal.signal(signal.SIGTERM, interrupted)
    exit_code = 0
    try:
        main()
    except KeyboardInterrupt:
        print("\nStopping demo processes...", flush=True)
    except Exception as error:
        print(str(error), file=sys.stderr)
        exit_code = 1
    finally:
        for proc in reversed(children):
            if proc.poll() is None:
                os.killpg(proc.pid, signal.SIGTERM)
        for proc in children:
            try:
                proc.wait(timeout=8)
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid, signal.SIGKILL)
        for log in logs:
            log.close()
    sys.exit(exit_code)
