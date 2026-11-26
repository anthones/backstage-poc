# Deploy this workspace on a Debian VPS over SSH

This runbook deploys **the existing AcmeSecure demonstration workspace** on one
Debian server alongside a second, independent project. It covers bootstrap,
builds, persistence, HTTPS, verification, updates, backups, and recovery.
Commands were reviewed against the repository and official documentation on
**25 November 2026**. They have not been executed on a real VPS.

The architecture/adoption proposal under `docs/architecture/backstage/` concerns
a future company installation. This runbook deploys the checked-in PoC; it does
not turn its seeded business fixtures, shared Guest identity, or allow-all
permissions into a production company platform. For that transition, follow the
[on-premises requirements](../../services/onboarding-service/docs/handbook/on-prem.md)
and the [architecture proposal](../architecture/backstage/README.md).

## 1. Layout and prerequisites

Use a fresh **Debian 13 (trixie), amd64 or arm64** VPS with systemd, a public IP,
and provider console access. Debian 12 can also host these containers, but the
commands below target Debian 13. As an initial estimate, use **4 vCPU, 8 GiB RAM,
and 80 GiB SSD** for this PoC and a small second project. Builds need substantial
memory and disk; measure the second project's requirements before choosing the
final size. The supplied runtime memory limits total about 6 GiB for this project.
Builds compete with both running projects; use a larger machine or a separate
build worker if that causes pressure. This is a single server with a shared
failure domain.

The operator needs an SSH key, sudo access, control of DNS, and read access to
this repository. For a private repository, use a read-only deploy key belonging
to the VPS, or HTTPS credentials through a credential helper. Verify the Git
server's SSH host fingerprint through its official channel; do not disable host
key checking or put an access token into a clone URL.

Replace these examples throughout:

| Name | Example | Purpose |
| --- | --- | --- |
| VPS address | `203.0.113.10` | Replace with the actual public address |
| Administrator | `deploy` | SSH and sudo account |
| Repository | `git@YOUR_GIT_HOST:YOUR_ORG/backstage-poc.git` | Actual repository URL |
| Backstage FQDN | `catalog.example.com` | Catalog, APIs, TechDocs, Jira view |
| Customer portal FQDN | `customers.example.com` | This repository's separate customer UI |
| Second project FQDN | `other.example.com` | Independent application |
| ACME contact | `ops@example.com` | Certificate contact |

The second project is **not** the Customer Portal: this workspace already
contains both Backstage and that portal. Use three hostnames to expose all three
interfaces; omit the customer hostname block if you do not need that interface.

```text
Internet TCP 80/443 -> host Caddy (TLS + hostname routing)
  catalog.example.com   -> 127.0.0.1:7007 -> Backstage app + backend
  customers.example.com -> 127.0.0.1:8080 -> Customer Portal -> six demo services
  other.example.com     -> 127.0.0.1:9000 -> independent project's web container

acmesecure-vps Compose network: Backstage, PostgreSQL, Jira adapter, portal, services
other-project Compose network: independent application's containers and database
```

Only Caddy owns ports 80 and 443. PostgreSQL and Jira have **no host ports**.
The existing service mappings 8081–8086 remain bound to loopback for SSH
diagnostics. There is no production frontend listener on 3000: Backstage's app
backend serves the compiled UI and API together on 7007.

Sections marked **local terminal** run on your laptop. The initial bootstrap
runs as **root on the VPS**. All subsequent commands run in **Bash as `deploy`
on the VPS**, using sudo where shown. Keep each shell's variables in that shell;
after reconnecting, repeat the definitions needed by that section.

## 2. Bootstrap access and operating system

**Local terminal:** use the provider's initial root login, verifying its host
fingerprint. If the image supplies a sudo user instead, use that account and
prefix bootstrap commands with sudo.

```bash
ssh root@203.0.113.10
```

**Root on VPS:**

```bash
apt update
apt full-upgrade -y
apt install -y sudo openssh-server ca-certificates curl gnupg git \
  ufw unattended-upgrades python3 dnsutils jq nano ripgrep
timedatectl set-timezone UTC
adduser deploy
usermod -aG sudo deploy
install -d -m 0700 -o deploy -g deploy /home/deploy/.ssh
```

Install **your public key**, never your private key. Paste one complete public
key line below, replacing the example, then fix ownership and mode:

```bash
cat > /home/deploy/.ssh/authorized_keys <<'KEY'
ssh-ed25519 REPLACE_WITH_YOUR_PUBLIC_KEY operator@laptop
KEY
chown deploy:deploy /home/deploy/.ssh/authorized_keys
chmod 0600 /home/deploy/.ssh/authorized_keys
systemctl enable --now ssh
dpkg-reconfigure -plow unattended-upgrades
```

Keep the original session open. In a **second local terminal**, verify key-only
access and sudo before disabling root/password access:

```bash
ssh -o PasswordAuthentication=no -o KbdInteractiveAuthentication=no deploy@203.0.113.10
sudo -v
```

**As `deploy` on VPS:** inspect provider snippets, then validate effective SSH
settings. OpenSSH normally uses the first setting encountered; earlier provider
configuration or `Match` blocks may override your intentions. See the
[Debian SSH configuration manual](https://manpages.debian.org/trixie/openssh-server/sshd_config.5.en.html).

```bash
sudo ls -la /etc/ssh/sshd_config.d
sudo tee /etc/ssh/sshd_config.d/00-vps.conf >/dev/null <<'SSH_CONFIG'
PermitRootLogin no
PubkeyAuthentication yes
PasswordAuthentication no
KbdInteractiveAuthentication no
SSH_CONFIG
sudo /usr/sbin/sshd -t
sudo /usr/sbin/sshd -T | rg 'permitrootlogin|pubkeyauthentication|passwordauthentication|kbdinteractiveauthentication'
```

Expected values are `no`, `yes`, `no`, `no`. Resolve unexpected values before proceeding.
For configurations with `Match`, also inspect `sshd -T -C
user=deploy,addr=YOUR_CLIENT_IP,host=YOUR_CLIENT_HOSTNAME`.

```bash
sudo systemctl reload ssh
```

Test a **third new SSH connection** before closing the original root session.
Retain provider console access for recovery. If the OS upgrade installed a new
kernel, reboot now and verify you can reconnect:

```bash
sudo reboot
```

## 3. Firewall and external network

On the **VPS**, allow SSH before enabling the firewall. These commands assume
SSH remains on port 22; adjust the rule first if your provider uses another port.

```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
sudo ufw status verbose
```

Apply the same policy in the **provider's firewall/security group**: allow
TCP 22, 80, and 443, deny other unsolicited inbound traffic. Restrict SSH to
your management IP/CIDR if it is stable, keeping a recovery path. Apply rules
to IPv4 and IPv6 if both are enabled; confirm `IPV6=yes` in `/etc/default/ufw`.
Permit outbound DNS, NTP, HTTPS, and established traffic. OS repositories may
also require HTTP. Live public Jira needs outbound HTTPS to `jira.atlassian.com`.

Docker-published ports can bypass UFW. Every application mapping must explicitly
use `127.0.0.1:HOST_PORT:CONTAINER_PORT`; never assume UFW protects an unrestricted
Docker mapping. Use a current Docker Engine (at least 28) and retain its default
bridge isolation/routing settings.
[Docker firewall limitations](https://docs.docker.com/engine/install/debian/),
[port publication](https://docs.docker.com/engine/network/port-publishing/).

At your DNS provider, create three **A records** pointing to the VPS IPv4:

```text
catalog.example.com    A    YOUR_PUBLIC_IPV4
customers.example.com  A    YOUR_PUBLIC_IPV4
other.example.com      A    YOUR_PUBLIC_IPV4
```

Add AAAA records only if IPv6 routes to this VPS and both firewalls allow it.
Remove stale AAAA records. Initially use direct DNS without a CDN/proxy so that
certificate and routing failures are easier to diagnose. Any restrictive CAA
policy must permit the certificate issuer used by your Caddy configuration.

Check from both the VPS and your laptop:

```bash
dig +short A catalog.example.com
dig +short AAAA catalog.example.com
dig +short A customers.example.com
dig +short A other.example.com
```

## 4. Install Docker Engine and Compose

These use [Docker's official Debian APT repository](https://docs.docker.com/engine/install/debian/).
On an existing host, first review conflicting packages using that documentation.

```bash
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/debian/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc
sudo tee /etc/apt/sources.list.d/docker.sources >/dev/null <<DOCKER_APT
Types: deb
URIs: https://download.docker.com/linux/debian
Suites: $(. /etc/os-release && echo "$VERSION_CODENAME")
Components: stable
Architectures: $(dpkg --print-architecture)
Signed-By: /etc/apt/keyrings/docker.asc
DOCKER_APT
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

On this fresh VPS, configure bounded container logs **before** creating containers.
If `/etc/docker/daemon.json` already exists, merge these keys with its contents
instead of replacing it. This daemon-wide change affects both projects.

```bash
sudo install -d -m 0755 /etc/docker
sudo tee /etc/docker/daemon.json >/dev/null <<'DOCKER_CONFIG'
{
  "log-driver": "local",
  "log-opts": { "max-size": "10m", "max-file": "5" }
}
DOCKER_CONFIG
sudo systemctl enable --now docker
sudo systemctl restart docker
sudo docker run --rm hello-world
sudo docker compose version
```

Use `sudo docker` in this guide. Membership in the `docker` group grants
root-equivalent access; there is no need to add the administrator to that group.
Do not expose the Docker daemon over an unauthenticated TCP socket.

## 5. Obtain source and define a release

```bash
sudo install -d -m 0755 -o deploy -g deploy /srv/acmesecure /srv/acmesecure/releases
sudo install -d -m 0700 /etc/acmesecure /var/backups/acmesecure
git clone git@YOUR_GIT_HOST:YOUR_ORG/backstage-poc.git /srv/acmesecure/repo
cd /srv/acmesecure/repo
git fetch --tags origin
git checkout --detach YOUR_REVIEWED_COMMIT_OR_TAG
git status --short
```

Select a revision that includes `deploy/vps/` and this guide. Require a clean
checkout before building. Use a new release identifier even for a rebuild of
the same commit:

```bash
export RELEASE_ID="$(date -u +%Y%m%dT%H%M%SZ)-$(git rev-parse --short HEAD)"
export RELEASE_DIR="/srv/acmesecure/releases/$RELEASE_ID"
export BACKSTAGE_ORIGIN='https://catalog.example.com'
```

## 6. Build and verify the application

The original root Compose file builds only the six services and customer portal.
The supplied [VPS overlay](../../deploy/vps/compose.vps.yaml) adds PostgreSQL,
Backstage, and the Jira adapter. It disables the Policy fault-control route and
sets initial per-container memory limits. The root file's loopback bindings are
retained. Always use the two files together and the project name shown below.

Backstage's existing Dockerfile expects a compiled bundle. Build with the same
Node/OS family as its runtime (`node:24-trixie-slim`), using the checked-in Yarn
release. The VPS runtime Dockerfile explicitly invokes that Yarn release and
installs native-module build tools in a separate dependency stage, avoiding the
scaffold's reliance on global Yarn and prebuilt native binaries. The build helper
keeps Node, Python, compilers, and development
dependencies out of the host OS. The build happens **on the VPS architecture**;
do not copy macOS `node_modules` or native modules to the VPS.
[Backstage container build requirements](https://backstage.io/docs/deployment/docker/).

```bash
cd /srv/acmesecure/repo
sudo docker build -t acmesecure-vps/build:node24 -f deploy/vps/Dockerfile.build deploy/vps
sudo docker run --rm --init \
  --user "$(id -u):$(id -g)" \
  --env HOME=/tmp \
  --env NODE_OPTIONS=--max-old-space-size=4096 \
  --mount type=bind,src="$PWD",dst=/workspace \
  --workdir /workspace \
  acmesecure-vps/build:node24 bash -euc '
    ./scripts/setup.sh
    ./scripts/check-services.sh
    cd backstage
    node .yarn/releases/yarn-4.13.0.cjs tsc
    node .yarn/releases/yarn-4.13.0.cjs build:backend
  '
```

`setup.sh` creates the Python environment, installs pinned requirements and Yarn
dependencies, builds seven TechDocs sites, and publishes them to
`backstage/.techdocs/`. The checks validate service behavior/contracts, catalog
metadata, TechDocs visibility, and the portal/Jira integration. The final steps
type-check and bundle Backstage, including its frontend. Do not run the local
development runner (`scripts/start.sh`) as the server deployment.

Stage a separate copy of published files, translating hard-coded Backstage
navigation links to the real HTTPS origin. The script leaves authored metadata,
source documentation, and contract snapshots unchanged. Service API/health
links on localhost:8081–8086 remain private and require SSH tunnels.

```bash
umask 022
python3 deploy/vps/prepare-public-files.py "$RELEASE_DIR" "$BACKSTAGE_ORIGIN"
git rev-parse HEAD > "$RELEASE_DIR/source-commit.txt"
```

Create the protected Compose environment file. Password generation avoids
putting a secret directly into shell history. On **updates**, follow section 12
to retain the existing database password; do not rerun this initialization block.

```bash
sudo install -m 0600 /dev/null /etc/acmesecure/runtime.env
printf 'RELEASE_ID=%s\nRELEASE_DIR=%s\nBACKSTAGE_ORIGIN=%s\n' \
  "$RELEASE_ID" "$RELEASE_DIR" "$BACKSTAGE_ORIGIN" \
  | sudo tee /etc/acmesecure/runtime.env >/dev/null
printf 'POSTGRES_PASSWORD=%s\n' "$(python3 -c 'import secrets; print(secrets.token_hex(32))')" \
  | sudo tee -a /etc/acmesecure/runtime.env >/dev/null
```

Create a stable wrapper so future commands always use the same Compose project,
paths, and environment. Relative build paths resolve against the root Compose
file; keep it first. Commands run through sudo can read the protected env file.
[Compose file merging](https://docs.docker.com/compose/how-tos/multiple-compose-files/merge/).

```bash
sudo tee /usr/local/sbin/acme-compose >/dev/null <<'WRAPPER'
#!/bin/sh
set -eu
exec docker compose \
  --project-directory /srv/acmesecure/repo \
  --project-name acmesecure-vps \
  --env-file /etc/acmesecure/runtime.env \
  -f /srv/acmesecure/repo/compose.yaml \
  -f /srv/acmesecure/repo/deploy/vps/compose.vps.yaml "$@"
WRAPPER
sudo chmod 0755 /usr/local/sbin/acme-compose
sudo /usr/local/sbin/acme-compose config --quiet
sudo /usr/local/sbin/acme-compose build
```

Do not share unredacted `compose config` or container inspection output: those
can contain the database password. `config --quiet` validates without printing it.

## 7. Start the stack and check it locally

```bash
sudo /usr/local/sbin/acme-compose pull postgres
sudo /usr/local/sbin/acme-compose up -d --no-build --pull never
sudo /usr/local/sbin/acme-compose ps
sudo /usr/local/sbin/acme-compose logs --tail=100 postgres backstage jira-adapter
```

PostgreSQL has a named persistent volume and no public listener. Backstage waits
for it to accept connections, then creates/migrates its plugin databases. Initial
startup and indexing take time; inspect logs if readiness does not become 200.
The fixture services do not persist business data. TechDocs and catalog files
are mounted read-only from the release directory, outside the container.

```bash
curl --fail --show-error http://127.0.0.1:7007/.backstage/health/v1/readiness
curl --fail --show-error http://127.0.0.1:8080/healthz
for port in 8081 8082 8083 8084 8085 8086; do
  curl --fail --show-error "http://127.0.0.1:$port/healthz" || break
  curl --fail --show-error "http://127.0.0.1:$port/readyz" || break
done
curl --fail --show-error 'http://127.0.0.1:8080/api/subscription?tenant=tenant-acme'
curl --fail --show-error -X POST http://127.0.0.1:8080/api/activation \
  -H 'Content-Type: application/json' -d '{"tenant_id":"tenant-acme"}'
sudo /usr/local/sbin/acme-compose exec -T jira-adapter python -c \
  'import urllib.request; print(urllib.request.urlopen("http://127.0.0.1:8090/healthz").read().decode())'
```

Do not use `verify.py`, `verify-extensions.py`, `demo.sh outage`, or the catalog
refresh mutation check as unattended VPS smoke tests: some intentionally change
the policy fault state or catalog files. Several local verification scripts also
assume a frontend on port 3000. Use the checks here and the browser checks below.

The dedicated PostgreSQL container uses the image's bootstrap account as
Backstage's database account. It has superuser rights **inside this dedicated
database instance**. Do not share that database instance or credentials with the
second project. For a company installation, provision a separate least-privilege
role and precreated plugin databases/schemas according to the chosen Backstage
database strategy. Changing `POSTGRES_PASSWORD` in the env file does not rotate
an existing initialized database's password.
[Backstage database configuration](https://backstage.io/docs/getting-started/config/database/),
[PostgreSQL image initialization](https://hub.docker.com/_/postgres).

## 8. Deploy the second project separately

The other project's implementation is unspecified. This template assumes it
provides one HTTP container image; replace the image, internal HTTP port, and
add its required environment, volumes, private database, and startup checks
according to its own deployment instructions. A host systemd application can
also serve `127.0.0.1:9000`; Caddy needs only that upstream.

Use a different directory, project name, loopback port, volumes, network, and
credentials. Avoid fixed `container_name` values. Both projects can use the same
**container** port; their **host** ports must be different.

```bash
sudo install -d -m 0755 -o deploy -g deploy /srv/other-project
sudo install -d -m 0700 /etc/other-project
cat > /srv/other-project/compose.yaml <<'OTHER_COMPOSE'
services:
  web:
    image: ${OTHER_IMAGE:?Set the other project's reviewed image tag or digest}
    ports:
      - '127.0.0.1:9000:${OTHER_CONTAINER_PORT:?Set its HTTP listen port}'
    restart: unless-stopped
    init: true
    mem_limit: 1g
OTHER_COMPOSE
sudo install -m 0600 /dev/null /etc/other-project/runtime.env
sudo nano /etc/other-project/runtime.env
```

Enter the actual values in the editor, for example:

```dotenv
OTHER_IMAGE=YOUR_REGISTRY/YOUR_PROJECT:YOUR_RELEASE
OTHER_CONTAINER_PORT=3000
```

The application must listen on `0.0.0.0` **inside its container**, and use
`https://other.example.com` as its external origin where required. Configure its
proxy trust, callback URLs, persistent data, migrations, and WebSocket settings
as that project requires. Do not use a development server as its production
entry point. Then run:

```bash
sudo docker compose -p other-project --env-file /etc/other-project/runtime.env \
  -f /srv/other-project/compose.yaml config --quiet
sudo docker compose -p other-project --env-file /etc/other-project/runtime.env \
  -f /srv/other-project/compose.yaml pull
sudo docker compose -p other-project --env-file /etc/other-project/runtime.env \
  -f /srv/other-project/compose.yaml up -d
curl --fail --show-error http://127.0.0.1:9000/
```

If the real application has not been installed, omit its Caddy block for now;
adding it before its upstream starts produces HTTP 502. No real second project
is deployed merely by filling in its hostname.

## 9. Install the shared Caddy reverse proxy

Install from the [official Caddy Debian repository](https://caddyserver.com/docs/install#debian-ubuntu-raspbian).
The package supplies a systemd service and persistent certificate storage.

```bash
sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https curl gnupg
curl -1sLf https://dl.cloudsmith.io/public/caddy/stable/gpg.key \
  | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt \
  | sudo tee /etc/apt/sources.list.d/caddy-stable.list >/dev/null
sudo chmod o+r /usr/share/keyrings/caddy-stable-archive-keyring.gpg /etc/apt/sources.list.d/caddy-stable.list
sudo apt update
sudo apt install -y caddy
sudo systemctl enable --now caddy
```

This PoC exposes a Guest token issuer and uses allow-all authorization. Restrict
**every request** to the Backstage and customer hostnames to explicit operator
or VPN egress IPs. Caddy's matcher below checks the directly connected client IP;
this guide assumes clients connect directly to Caddy, without a CDN or another
proxy. All approved visitors still share one Guest identity inside Backstage.
IP filtering does not provide per-user Backstage authorization. The Guest
production override in the supplied config is intentional for this protected
demo only. Before offering it as a company service, replace Guest, configure a
real sign-in resolver and permission policy, and test them.
[Guest provider behavior](https://backstage.io/docs/auth/guest/provider/).

Determine the public client IPs that should have access, including IPv6 if your
browser uses it. The first address in `$SSH_CONNECTION` shows the peer of this
SSH session; verify it also represents the browser's egress. Use your VPN's
stable egress ranges if operator addresses change frequently:

```bash
printf '%s\n' "$SSH_CONNECTION"
```

Edit `/etc/caddy/Caddyfile`, replacing the **complete contents** of the package's
default file with the following. Replace the hostnames, contact, and
`198.51.100.25/32` with the actual approved client address/range. Add additional
approved IPv4/IPv6 CIDRs on that same `remote_ip` line, separated by spaces.
The second project's block leaves authentication to that application; import
`demo_access` there too if it also needs an IP gate.

```bash
sudo nano /etc/caddy/Caddyfile
```

```caddyfile
{
    email ops@example.com
}

(demo_access) {
    @blocked not remote_ip 198.51.100.25/32
    respond @blocked "Access restricted" 403
}

catalog.example.com {
    import demo_access
    @health path /.backstage/health/*
    respond @health 404
    reverse_proxy 127.0.0.1:7007
    log
}

customers.example.com {
    import demo_access
    @health path /healthz
    respond @health 404
    reverse_proxy 127.0.0.1:8080
    log
}

other.example.com {
    reverse_proxy 127.0.0.1:9000
    log
}
```

Caddy uses the hostname and TLS SNI to select an upstream, so all names can share
one IP and the same HTTPS port. No separate public application ports or path
prefixes are needed. It forwards host/proxy headers and handles WebSocket
upgrades automatically. IP filtering also works with Backstage's bearer-token
API calls; do not add HTTP basic auth on these routes, since both mechanisms use
the Authorization header. Keep Backstage `app.baseUrl`, `backend.baseUrl`, and CORS
origin on the **same HTTPS origin**; the supplied config does that.
[Caddy reverse proxy](https://caddyserver.com/docs/caddyfile/directives/reverse_proxy),
[client IP matchers](https://caddyserver.com/docs/caddyfile/matchers#remote-ip).

```bash
sudo chmod 0644 /etc/caddy/Caddyfile
sudo caddy fmt --overwrite /etc/caddy/Caddyfile
sudo caddy validate --config /etc/caddy/Caddyfile --adapter caddyfile
sudo systemctl reload caddy
sudo systemctl status caddy --no-pager
sudo journalctl -u caddy -n 100 --no-pager
```

Caddy obtains/renews certificates and redirects HTTP to HTTPS once DNS is
correct and inbound TCP 80/443 reaches it. Keep these ports open for normal
operation and renewal. UDP 443 is optional for HTTP/3; omit it if unnecessary.
If certificates fail, check A/AAAA, provider firewall/NAT, port conflicts, CAA,
and the Caddy journal. Do not work around failures with self-signed public TLS
or `curl -k`.
[Automatic HTTPS requirements](https://caddyserver.com/docs/automatic-https).

## 10. Verify from outside the VPS

**Local terminal from an approved IP:** these must use normal TLS certificate
verification. The HTTP request should redirect to HTTPS; the HTTPS catalog
request should return **200**. From an unapproved address, catalog and customer
requests should return **403**. Verify that denial using another network too.

```bash
curl -I http://catalog.example.com/
curl -I https://catalog.example.com/
curl --fail --show-error -o /dev/null -w '%{http_code}\n' https://catalog.example.com/
curl --fail --show-error 'https://customers.example.com/api/subscription?tenant=tenant-acme'
curl --fail --show-error -o /dev/null -w '%{http_code}\n' https://other.example.com/
```

For the second application, expect its own sign-in
redirect or authenticated response if it protects `/`.

In a browser, verify all of the following:

- The approved client reaches Backstage and can choose Guest; an unapproved client receives 403.
- The catalog contains seven components and six APIs without processing errors.
- `/demo`, `/catalog-graph`, `/delivery`, and component TechDocs pages load.
- TechDocs search eventually returns results after indexing.
- Catalog, documentation, and customer-portal navigation uses the public catalog
  FQDN. Local service health/API links remain diagnostic links through SSH.
- The Customer Portal checks a subscription and previews a successful activation.
- The Jira fictional scenario loads. The explicitly live public source either
  shows real public Jira records or an explicit unavailability response.
- The second hostname shows the second application, including its own sign-in,
  callbacks, and static assets. It never shows Backstage or the customer portal.

**On VPS:** inspect listener addresses and restart state:

```bash
sudo ss -lntp
sudo /usr/local/sbin/acme-compose ps
sudo docker stats --no-stream
df -h / /var/lib/docker /srv
free -h
```

Only SSH and Caddy should be publicly listening. Test from your laptop that
ports 3000, 5432, 7007, 8080–8086, 8090, and 9000 are unreachable on the public
IP (repeat for IPv6 when configured). For example:

```bash
nc -vz -w 3 203.0.113.10 7007
nc -vz -w 3 203.0.113.10 9000
```

A timeout/refused connection is expected. Confirm 22/80/443 are reachable.

For private diagnostics from your laptop:

```bash
ssh -N -L 8083:127.0.0.1:8083 deploy@203.0.113.10
```

Then inspect `http://127.0.0.1:8083/healthz` locally. Do not open that service's
port to the Internet to make its catalog link work.

## 11. Reboot behavior and ongoing operations

Docker and Caddy are enabled at boot. All application containers have
`restart: unless-stopped`; they survive SSH disconnects and restart after a host
reboot unless deliberately stopped. A dependency health condition orders the
initial Compose startup; Docker restart policies do not continuously enforce
dependency readiness. Inspect logs after a reboot and restart Backstage if its
database startup failed. There is no need for `nohup`, tmux, or the dev runner.

Schedule a maintenance reboot after initial verification, then repeat the local
readiness, external routing, access-filter, and browser checks from sections 7 and 10:

```bash
sudo reboot
```

Routine commands on the VPS:

```bash
sudo /usr/local/sbin/acme-compose logs --tail=100 backstage
sudo /usr/local/sbin/acme-compose restart backstage
sudo journalctl -u caddy --since '1 hour ago' --no-pager
sudo /usr/local/sbin/acme-compose stop
sudo /usr/local/sbin/acme-compose start
```

The last two intentionally stop/start **this project's whole stack**, without
touching the other Compose project. To operate the other project, use its
`-p other-project --env-file ... -f ...` command prefix from section 8.

Monitor free disk, memory, swap/OOM kills, restart count, local readiness, public
HTTPS availability, certificate expiry, and backup age. Send alerts somewhere an
operator will see them. The Docker log driver is bounded; set appropriate
journald retention as well. Check `journalctl --disk-usage` periodically.
Uptime checks must use suitable application routes or deliberate public endpoints,
since Backstage's built-in health route is blocked at Caddy. Run external demo
checks from an allowlisted monitoring address.

Review/install OS, Docker, Caddy, base-image and application dependency updates
regularly. Unattended upgrades do not rebuild images or update app dependencies.
Plan host/Docker restarts for both projects. Keep reviewed previous image tags;
avoid `docker system prune -a --volumes`, which can destroy rollback artifacts
and data. Base image tags here intentionally select a major/OS family; for
reproducible releases, record and pin reviewed image digests for the build and
runtime together. PostgreSQL major upgrades need a separate migration plan;
never switch its major tag and reuse the data volume without one.

## 12. Backups, releases, and rollback

### Back up before the first update, then automate it

Backstage creates multiple plugin databases. A backup of only the default
`postgres` database is insufficient. The example uses `pg_dumpall` to include
every database and roles. Stop Backstage while creating a deployment recovery
point to avoid application changes spanning independent database snapshots.
For routine online backups, choose a consistency policy suitable for your RPO;
per-database dumps are not one atomic snapshot across all plugin databases.

**On VPS:**

```bash
set -o pipefail
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
sudo /usr/local/sbin/acme-compose stop backstage
sudo /usr/local/sbin/acme-compose exec -T postgres pg_dumpall -U backstage \
  | sudo tee "/var/backups/acmesecure/$STAMP.sql" >/dev/null
sudo test -s "/var/backups/acmesecure/$STAMP.sql"
sudo chmod 0600 "/var/backups/acmesecure/$STAMP.sql"
sudo tar -czf "/var/backups/acmesecure/$STAMP-files.tgz" \
  /etc/acmesecure /etc/caddy /usr/local/sbin/acme-compose /srv/acmesecure/releases
sudo chmod 0600 "/var/backups/acmesecure/$STAMP-files.tgz"
sudo /usr/local/sbin/acme-compose start backstage
```

The Bash `pipefail` option ensures a failed database dump
cannot be hidden by `tee` succeeding. Check the command's exit status before
continuing. If a backup fails, investigate and restart the stopped application
when appropriate. Do not treat a nonempty file alone as a successful backup.
The archive includes secrets; encrypt it before copying it off-host. Retain the
source revision and images, too: local image tags are lost with the VPS unless
you push to a private registry or export the selected image set with
`docker image save`. Record `acme-compose config --images` and image IDs for each
release. Back up the second project according to its own data consistency rules.

### Schedule encrypted off-host backups

The supplied backup script creates the multi-database dump, restarts Backstage,
then uploads it and the release/config files with Restic. It uses an exclusive
lock, preserves failure status, and tries to restart Backstage if a dump fails.
It briefly stops **Backstage only** each night; schedule around your viewers.
The service fails if Backstage was already stopped. Coordinate releases and
backups so they do not overlap.

The example backend is an **off-host S3-compatible bucket**, which you must
provision. Supply its endpoint, bucket, and scoped access credentials; these are
operator-specific inputs, not services included in this VPS. Restic encrypts
backup contents. Keep the repository password and storage recovery credentials
in a password manager outside the VPS as well.
[Restic repository configuration](https://restic.readthedocs.io/en/stable/030_preparing_a_new_repo.html),
[retention](https://restic.readthedocs.io/en/stable/060_forget.html).

```bash
sudo apt install -y restic
sudo install -m 0600 /dev/null /etc/acmesecure/restic-password
printf '%s\n' "$(python3 -c 'import secrets; print(secrets.token_hex(32))')" \
  | sudo tee /etc/acmesecure/restic-password >/dev/null
sudo install -m 0600 /dev/null /etc/acmesecure/backup.env
sudo nano /etc/acmesecure/backup.env
```

Fill in the actual values (this is sourced as a root-owned shell file, so quote
values and do not insert executable shell expressions):

```bash
RESTIC_REPOSITORY='s3:https://YOUR_S3_ENDPOINT/YOUR_BUCKET/acmesecure'
RESTIC_PASSWORD_FILE='/etc/acmesecure/restic-password'
AWS_ACCESS_KEY_ID='YOUR_BACKUP_ACCESS_KEY'
AWS_SECRET_ACCESS_KEY='YOUR_BACKUP_SECRET_KEY'
```

Initialize a **new** repository once. For an existing repository, recover its
original password file and use `restic snapshots` instead of generating a new
password and initializing again.

```bash
sudo bash -euc 'set -a; source /etc/acmesecure/backup.env; set +a; restic init'
cd /srv/acmesecure/repo
sudo install -m 0750 -o root -g root deploy/vps/backup.sh /usr/local/sbin/acme-backup
sudo install -m 0644 deploy/vps/acmesecure-backup.service /etc/systemd/system/
sudo install -m 0644 deploy/vps/acmesecure-backup.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl start acmesecure-backup.service
sudo systemctl status acmesecure-backup.service --no-pager
sudo journalctl -u acmesecure-backup.service -n 100 --no-pager
sudo systemctl enable --now acmesecure-backup.timer
sudo systemctl list-timers acmesecure-backup.timer
```

The schedule is 02:30 UTC plus up to 15 minutes of jitter; missed runs are caught
up after boot. It keeps seven daily and four weekly snapshots. Monitor the
service's exit status and newest off-host snapshot, and connect failure alerts
to your monitoring system. Review retention and storage deletion permissions
before enabling it. The script does not export Docker images; retain those in a
private registry or an encrypted image archive. Test recovering files with:

```bash
sudo bash -euc 'set -a; source /etc/acmesecure/backup.env; set +a; restic snapshots'
sudo install -d -m 0700 /var/backups/acmesecure/restore-files
sudo bash -euc 'set -a; source /etc/acmesecure/backup.env; set +a; restic restore latest --tag acmesecure-vps --target /var/backups/acmesecure/restore-files'
```

The restored SQL is under `restore-files/var/backups/acmesecure/latest.sql`.
Use it in the isolated database restoration below. Never restore files directly
over the running application as a test. Keep the second project's backup policy
separate. A local archive alone is not disaster recovery.

### Update this project

Run a verified backup first. Record the old release and preserve its protected
environment file. The source checkout supplies build/Compose definitions; the
release directory supplies immutable catalog/docs/config copies.

```bash
cd /srv/acmesecure/repo
git status --short
OLD_COMMIT="$(git rev-parse HEAD)"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
sudo cp -p /etc/acmesecure/runtime.env "/etc/acmesecure/runtime.env.before-$STAMP"
git fetch --tags origin
git checkout --detach YOUR_NEXT_REVIEWED_COMMIT_OR_TAG
export RELEASE_ID="$(date -u +%Y%m%dT%H%M%SZ)-$(git rev-parse --short HEAD)"
export RELEASE_DIR="/srv/acmesecure/releases/$RELEASE_ID"
export BACKSTAGE_ORIGIN='https://catalog.example.com'
```

Repeat section 6's **build helper command** (rebuild the helper image if its
Dockerfile changed), then stage the new files:

```bash
umask 022
python3 deploy/vps/prepare-public-files.py "$RELEASE_DIR" "$BACKSTAGE_ORIGIN"
git rev-parse HEAD > "$RELEASE_DIR/source-commit.txt"
```

Build using a separate candidate env file so the active release selection does
not change until the build succeeds. Preserve `POSTGRES_PASSWORD`:

```bash
set -o pipefail
sudo sed -e "s|^RELEASE_ID=.*|RELEASE_ID=$RELEASE_ID|" \
  -e "s|^RELEASE_DIR=.*|RELEASE_DIR=$RELEASE_DIR|" \
  /etc/acmesecure/runtime.env \
  | sudo tee /etc/acmesecure/candidate.env >/dev/null
sudo chmod 0600 /etc/acmesecure/candidate.env
sudo docker compose -p acmesecure-vps --env-file /etc/acmesecure/candidate.env \
  -f compose.yaml -f deploy/vps/compose.vps.yaml config --quiet
sudo docker compose -p acmesecure-vps --env-file /etc/acmesecure/candidate.env \
  -f compose.yaml -f deploy/vps/compose.vps.yaml build
sudo cp -p /etc/acmesecure/candidate.env /etc/acmesecure/runtime.env
sudo /usr/local/sbin/acme-compose up -d --no-build --pull never
```

Use `set -o pipefail` for the candidate-file pipeline too. Do not reuse an image
tag for different build contents. This rollout can briefly interrupt this
application; it does not promise zero downtime. Recheck section 7/10 after every
release. If the hostname changes, also update `BACKSTAGE_ORIGIN` in the candidate
env file, regenerate staged files, and update DNS/Caddy together.

### Roll back

If the release made **no incompatible database migrations**, select the previous
source/config and previous tagged images, keeping its release directory:

```bash
cd /srv/acmesecure/repo
git checkout --detach YOUR_PREVIOUS_COMMIT
sudo cp -p /etc/acmesecure/runtime.env.before-YOUR_TIMESTAMP /etc/acmesecure/runtime.env
sudo /usr/local/sbin/acme-compose config --quiet
sudo /usr/local/sbin/acme-compose up -d --no-build --pull never
```

The previous source may contain different Compose definitions, so restore it as
well as the env file. If migrations are incompatible, image rollback alone is
unsafe: restore the pre-upgrade databases and release/config artifacts as a
coordinated recovery. Keep the second project running while recovering this
project. Never use `down -v` on the live stack as a shortcut.

### Rehearse database restoration in isolation

This creates a **new isolated Compose project/volume**, without published ports,
so it cannot overwrite the live database. Choose an unused restore-test name.
The plain SQL dump can contain role definitions with credentials; protect it.

```bash
sudo tee /etc/acmesecure/restore-test.yaml >/dev/null <<'RESTORE_COMPOSE'
services:
  postgres:
    image: postgres:17-trixie
    environment:
      POSTGRES_USER: restore_admin
      POSTGRES_HOST_AUTH_METHOD: trust
    volumes:
      - restore-data:/var/lib/postgresql/data
volumes:
  restore-data:
RESTORE_COMPOSE
sudo docker compose -p acme-restore-test -f /etc/acmesecure/restore-test.yaml up -d
sudo docker compose -p acme-restore-test -f /etc/acmesecure/restore-test.yaml \
  exec -T postgres pg_isready -U restore_admin -d postgres
```

Wait for readiness to return success, then restore your selected dump. This
isolated, temporary database trusts its private container network; never publish
its port or use these authentication settings for the live database.

```bash
sudo cat /var/backups/acmesecure/YOUR_TIMESTAMP.sql \
  | sudo docker compose -p acme-restore-test -f /etc/acmesecure/restore-test.yaml \
      exec -T postgres psql -U restore_admin -d postgres --set ON_ERROR_STOP=on
sudo docker compose -p acme-restore-test -f /etc/acmesecure/restore-test.yaml \
  exec -T postgres psql -U restore_admin -d postgres -c '\l'
```

Verify expected plugin databases, roles, representative rows, and application
behavior in an isolated recovery deployment before treating the backup as
proven. The original dump's `backstage` role is distinct from `restore_admin`,
avoiding a bootstrap-role collision. Retain recovery evidence. Remove only this
temporary test project's containers and volume when finished:

```bash
sudo docker compose -p acme-restore-test -f /etc/acmesecure/restore-test.yaml down -v
```

For actual VPS loss: rebuild the host, recover the repository revision and image
artifacts, restore the matching release/config/env files and databases into new
volumes, start this project privately, run the checks, and finally enable its
Caddy routes. Recovery from a migration rollback must restore the matched
pre-upgrade state; expect loss of writes since that backup.

## 13. Troubleshooting

| Symptom | Check/action |
| --- | --- |
| Cannot reconnect over SSH | Provider console, ssh service/config, authorized key ownership, both firewalls, effective sshd settings |
| Caddy certificate error | A/AAAA/CAA, reachable TCP 80/443, no other listener on those ports, `journalctl -u caddy` |
| HTTP 403 before Backstage | Check the actual browser/monitor IPv4 or IPv6 egress against the Caddy allowlist |
| HTTP 502 | Curl the matching loopback upstream, inspect Compose state/logs; verify FQDN-to-port mapping |
| Login redirects to localhost | Confirm `BACKSTAGE_ORIGIN`, selected runtime env/config, both base URLs, and CORS; recreate Backstage |
| Guest provider refuses startup | Ensure the VPS config is loaded after base config; override is for this proxy-protected demo only |
| No catalog entities / missing docs | Check `/published` bind mount, seven published sites, absolute catalog locations, readable permissions, ingestion errors |
| Links open localhost:3000 | Rebuild/stage with the intended origin; restart/recreate affected container and allow catalog refresh |
| Jira scenario fails | Adapter startup, internal DNS `jira-adapter:8090`, container listener 0.0.0.0, Backstage proxy credentials |
| Public Jira fails only | Outbound HTTPS, DNS/CA validation, remote availability; fictional scenario remains distinct |
| Activation returns 502/503 | Check all six services' health/readiness and service URL envs; inspect correlation ID/root cause |
| Database password failed after editing env | Initialized volume retains old password; use a coordinated SQL password rotation and recreate app containers |
| Build exits 137 / server freezes | Memory/OOM and disk usage; reduce concurrent work or move builds off-server |
| Second project breaks after deploying this one | Port ownership, project names, shared proxy syntax, resource exhaustion; projects must retain independent networks/volumes |

## Deployment files and verification limits

The companion files are under [`deploy/vps/`](../../deploy/vps/): the Compose
overlay, Backstage runtime configuration, Backstage/build-helper Dockerfiles, Jira adapter
Dockerfile/context filter, public-file staging script, and backup script/timer.
The default local
development flow is unchanged. VPS configuration deliberately ignores the
existing `backstage/app-config.production.yaml`, whose example catalog locations
and assumptions do not describe this sibling workspace.

Repository-side validation can check Compose merging, shell syntax, staging,
and configuration structure. A deployment is complete only after actual VPS
build/startup, public TLS/access/domain routing, reboot, monitoring, and off-host
backup/restore checks succeed. Provider firewall, DNS, second-project image and
its data requirements remain operator-specific inputs.
