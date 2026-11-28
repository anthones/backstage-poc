# Deploy LDAP-only Kiwi TCMS alongside Backstage

This is the Markdown replacement for `deploy_debian.rst`. It assumes the
[Backstage Debian VPS guide](debian-vps.md) has been completed successfully,
**except for every step concerning the unspecified "other project"**. Kiwi
TCMS is that second project. The shared server already has the `deploy` SSH/sudo
account, firewall, Docker Engine/Compose, bounded Docker logs, host Caddy,
working Backstage/customer hostnames, and the configured Restic backup service.

Kiwi uses **LDAP credentials only**, with no local password fallback, SMTP,
email verification, or activation messages. New eligible directory users get
active Kiwi profiles on first successful login; Kiwi roles are assigned
separately. Administrator recovery uses the VPS SSH/sudo control plane.

Keep those services running. Add an independent Kiwi stack and one Caddy
hostname; do not install host Nginx or Certbot, recreate server access, or run
the old second-project example. Any existing Backstage authentication setup
continues to apply to Backstage; it does not automatically sign users into Kiwi.

Commands run in **Bash as `deploy` on the VPS**, using sudo where shown, unless
marked **workstation**. Replace example domains, source URL and reviewed commit
before executing. Stop and investigate a failed command before continuing.
The guide and upstream behavior were reviewed on **28 November 2026**; these
Kiwi deployment commands have not been exercised against your running VPS.

### Exact files and values to change

The worked directory is **Active Directory over LDAPS**. Get the real values
from NetOps before publishing Kiwi. OpenLDAP/StartTLS requires corresponding
username, schema and TLS changes in the settings template; do not copy the AD
formatter unchanged.

| File on the VPS | Required change |
| --- | --- |
| `/srv/kiwitcms/.env` | Set `KIWI_FQDN`, `LDAP_URL`, `LDAP_SEARCH_BASE`, `LDAP_DOMAIN`, and NetOps-approved `LDAP_REQUIRED_FILTER`; select the final LDAP-enabled `KIWI_IMAGE` |
| `/srv/kiwitcms/compose.yaml` | Pass all four `LDAP_*` values to web and mount `ldap-ca.pem`; remove any old `SMTP_PASSWORD`/mail environment entries |
| `/srv/kiwitcms/local_settings.py` | Use the supplied LDAP-only settings: two custom backend paths, no stock `ModelBackend` login, dummy mail backend, blocked local account flows, and custom login template |
| `/srv/kiwitcms/ldap/kiwi_ldap_only.py` | Copy the supplied backend/middleware code into the image; guards synchronous/asynchronous inactive logins and preserves global/Guardian permissions |
| `/srv/kiwitcms/ldap/Dockerfile.ldap` | Build the pinned LDAP packages and custom code on each reviewed Kiwi base image |
| `/srv/kiwitcms/ldap/templates/registration/custom_login.html` | Company-directory login form without registration or password-reset links; copied into the image |
| `/srv/kiwitcms/ldap-ca.pem` | Install the verified directory CA chain; this is separate from Caddy's public/upstream certificates |
| `/usr/local/sbin/kiwi-backup` | Include the LDAP code/templates and CA in its config archive, as shown in section 9 |

The actual source templates are in
[`examples/kiwitcms-ldap/`](examples/kiwitcms-ldap/). `AUTHENTICATION_BACKENDS`
must be exactly `kiwi_ldap_only.LDAPOnlyBackend` and
`kiwi_ldap_only.ObjectPermissionsOnlyBackend`. The LDAP backend inherits model
permission methods, so removing stock `django.contrib.auth.backends.ModelBackend`
from the list disables local password login without removing those permissions.
The second backend supplies Guardian object permissions and never authenticates.

If Kiwi is **already installed**, do not rerun clone/secret initialization or
database migrations from the fresh-install path. Take a backup, pause Kiwi's
backup/cleanup jobs, copy the new LDAP templates, build the derived image, and
merge the listed config changes while Kiwi web is stopped. Preserve the
database password, secret key, uploads, FQDN and TLS material. Review existing
username/privilege collisions before an LDAP account is mapped to an old Kiwi
row. Clear existing Kiwi sessions at cutover with:

```bash
sudo /usr/local/sbin/kiwi-compose run --rm --no-deps web /Kiwi/manage.py shell -c \
  'from django.contrib.sessions.models import Session; Session.objects.all().delete()'
```

That signs out Kiwi users only. Validate the final image/config, run section 5's
LDAP-administrator promotion command, then recreate web and resume the jobs.
An old local administrator password will no longer work, even during an LDAP
outage. Repair directory/configuration access through SSH; do not add a local
authentication backend as an automatic recovery path.

Jump to: [build](#2-obtain-and-build-a-reviewed-release),
[configuration](#3-configure-kiwi-and-its-database),
[initialize](#5-initialize-the-application-before-publishing-it),
[Caddy](#6-add-only-the-kiwi-hostname-to-caddy),
[backups](#9-back-up-kiwi-using-the-existing-off-host-backup-service),
[restore](#10-rehearse-restoration-away-from-the-live-stack),
[updates](#11-upgrade-and-roll-back-kiwi-independently).

## 1. Add Kiwi to the existing layout

```text
Internet TCP 80/443 -> existing host Caddy
  catalog.example.com   -> HTTP 127.0.0.1:7007 -> existing Backstage stack
  customers.example.com -> HTTP 127.0.0.1:8080 -> existing Customer Portal
  tcms.example.com      -> HTTPS 127.0.0.1:18443 -> Kiwi :8443 -> private MariaDB

acmesecure-vps: existing Backstage network, PostgreSQL and release files
kiwitcms:       separate network, database credentials, SQL and uploads volumes
```

| Setting | Value used here |
| --- | --- |
| Kiwi public FQDN | `tcms.example.com` |
| Kiwi source/configuration | `/srv/kiwitcms/source`, `/srv/kiwitcms` |
| Compose project name | `kiwitcms` |
| Host upstream | `127.0.0.1:18443`, HTTPS |
| Internal TLS name | `kiwi-upstream.internal`; no public DNS record needed |
| Named volumes | `kiwitcms_db_data`, `kiwitcms_uploads` |
| Compose wrapper | `/usr/local/sbin/kiwi-compose` |
| Local recovery files | `/var/backups/kiwitcms` |

Add **only** the new Kiwi A record pointing at the existing VPS public IPv4.
Add an AAAA record only if the server's existing IPv6 path works. Leave the
Backstage/customer records and Caddy blocks in place. Do not create the old
`other.example.com` placeholder record or reserve its example port 9000.

```bash
dig +short A tcms.example.com
dig +short AAAA tcms.example.com
sudo ss -lntp
sudo docker stats --no-stream
free -h
df -h / /var/lib/docker /srv
```

Confirm host port 18443 is unused. Reserve runtime capacity for Kiwi in addition
to Backstage: the example limits below allow **1 GiB web + 1 GiB database**, plus
shared OS/proxy headroom. A source build needs extra CPU, memory, and disk.
Resize or build on a matching-architecture worker if the existing VPS cannot
spare that capacity; an on-server build must not exhaust the running Backstage
stack. The two applications still share the VPS's failure domain.

No new inbound firewall ports are needed. Keep the existing SSH/80/443 rules;
do not expose 3306, 8443, or 18443. Docker publishing can bypass UFW, so the
explicit loopback binding below remains essential.
[Docker publication behavior](https://docs.docker.com/engine/network/port-publishing/).

## 2. Obtain and build a reviewed release

The upstream Compose file publishes ports 80/443 itself and contains example
settings. Use a separate production file here. Upstream's final Docker target
is `kiwitcms`; it builds frontend assets, Python packages, static files, and
the Nginx/uWSGI runtime. No host Python environment or Node installation is
needed. Select a reviewed tag or full commit rather than a moving branch.
[Upstream container guidance](https://kiwitcms.readthedocs.io/en/latest/installing_docker.html),
[Dockerfile](https://github.com/kiwitcms/Kiwi/blob/master/Dockerfile).

```bash
sudo apt install -y openssl tmux
sudo install -d -m 0750 -o deploy -g deploy /srv/kiwitcms
sudo install -d -m 0700 /var/backups/kiwitcms /var/backups/kiwitcms/images
git clone https://github.com/kiwitcms/Kiwi.git /srv/kiwitcms/source
cd /srv/kiwitcms/source
git fetch --tags origin
KIWI_REF='REPLACE_WITH_REVIEWED_TAG_OR_FULL_COMMIT'
git checkout --detach "$KIWI_REF"
git status --short
git rev-parse HEAD
```

Use your maintained fork URL if deploying a fork. Build in a persistent SSH
session; `tmux new -s kiwi-build` opens one. Detach with Ctrl-b then d, and
resume with `tmux attach -t kiwi-build`. Inside the build session:

```bash
cd /srv/kiwitcms/source
KIWI_COMMIT="$(git rev-parse HEAD)"
KIWI_RELEASE="$(date -u +%Y%m%dT%H%M%SZ)-$(git rev-parse --short HEAD)"
BASE_IMAGE="local/kiwitcms-base:$KIWI_RELEASE"
KIWI_IMAGE="local/kiwitcms:$KIWI_RELEASE"
sudo docker build --pull --target kiwitcms \
  --label "org.opencontainers.image.revision=$KIWI_COMMIT" \
  -t "$BASE_IMAGE" .
KIWI_GUIDE_FILES=/srv/acmesecure/repo/docs/deployment/examples/kiwitcms-ldap
install -d -m 0755 /srv/kiwitcms/ldap
cp "$KIWI_GUIDE_FILES/Dockerfile.ldap" "$KIWI_GUIDE_FILES/kiwi_ldap_only.py" /srv/kiwitcms/ldap/
cp -R "$KIWI_GUIDE_FILES/templates" /srv/kiwitcms/ldap/
sudo docker build --build-arg "KIWI_BASE=$BASE_IMAGE" \
  -f /srv/kiwitcms/ldap/Dockerfile.ldap -t "$KIWI_IMAGE" /srv/kiwitcms/ldap
sudo docker image inspect "$KIWI_IMAGE" --format '{{.Id}}'
printf '%s\n' "$KIWI_IMAGE" > /srv/kiwitcms/candidate-image.txt
```

Deploy the **final derived image**, not `local/kiwitcms-base`. The LDAP context
contains only its code/templates; no `.env`, private keys or uploads. The
Dockerfile pins `django-python3-ldap==0.16.1`, `ldap3==2.9.1` and
`pyasn1==0.6.5`, installs the guard module under `/Kiwi`, and sets
`PYTHONPATH=/Kiwi` so management commands and uWSGI use the same code. Verify
package compatibility with the selected Kiwi Python/Django versions through
the application checks below. Do not install packages into a running container.

A unique tag preserves earlier builds, but the source commit alone does not
make the image byte-for-byte reproducible: base images and build dependencies
can change. Retain the exact final LDAP-enabled artifact or push it to a retained private
registry. Keep all secrets outside the source checkout and build context.

## 3. Configure Kiwi and its database

### Select images and initialize secrets once

Use a dedicated MariaDB instance; Backstage's PostgreSQL is unrelated. Pull the
MariaDB 11.4 LTS series and record its resolved registry digest. Verify support
against your selected Kiwi release before changing database series.
[MariaDB maintenance policy](https://mariadb.org/about/#maintenance-policy).

The settings override is installed into the selected image's Python package.
Discover that path from the actual image instead of hard-coding its Python
minor version. Production settings import `local_settings.py` there.
[Production settings loader](https://github.com/kiwitcms/Kiwi/blob/master/tcms/settings/product.py).

```bash
cd /srv/kiwitcms
KIWI_IMAGE="$(cat candidate-image.txt)"
sudo docker pull mariadb:11.4
DB_IMAGE="$(sudo docker image inspect mariadb:11.4 --format '{{index .RepoDigests 0}}')"
KIWI_SETTINGS_PATH="$(sudo docker run --rm --entrypoint /venv/bin/python "$KIWI_IMAGE" \
  -c 'from pathlib import Path; import tcms; print(Path(tcms.__file__).parent / "settings" / "local_settings.py")')"
printf 'Image settings override: %s\n' "$KIWI_SETTINGS_PATH"
umask 077
set -o noclobber
cat > .env <<EOF
KIWI_IMAGE=$KIWI_IMAGE
KIWI_SETTINGS_PATH=$KIWI_SETTINGS_PATH
DB_IMAGE=$DB_IMAGE
KIWI_FQDN=tcms.example.com
KIWI_DB_PASSWORD=$(openssl rand -hex 32)
MARIADB_ROOT_PASSWORD=$(openssl rand -hex 32)
KIWI_SECRET_KEY=$(openssl rand -hex 48)
LDAP_URL=ldaps://dc.company.example:636
LDAP_SEARCH_BASE=OU=People,DC=company,DC=example
LDAP_DOMAIN=company.example
LDAP_REQUIRED_FILTER='(&(memberOf=CN=KiwiUsers,OU=Groups,DC=company,DC=example)(!(userAccountControl:1.2.840.113556.1.4.803:=2)))'
EOF
set +o noclobber
chmod 0600 .env
```

Do not rerun that initialization over an existing `.env`. The `noclobber`
option rejects overwriting it. Keep `KIWI_SECRET_KEY` stable and recoverable.
Changing an env-file password does not rotate credentials in an initialized
MariaDB volume. Resolved Compose configuration can expose secrets; use
`config --quiet` and keep `.env` out of Git and issue reports.

Replace **all four LDAP values** with NetOps' actual settings using `nano .env`.
The example filter restricts direct AD group membership and excludes disabled
accounts; nested groups or a different schema need NetOps' corresponding
predicate. An eligible user binds with their directory password and must be
able to read their own profile. End-user passwords do not belong in `.env`.
Allow container/VPN egress to the approved LDAPS endpoint; public inbound rules
are unchanged. `mail` is profile metadata, not an activation requirement.

Install the verified directory CA chain and the complete LDAP-only settings.
The settings are a Python module, so they import Kiwi defaults explicitly; they
do not rely on variables leaking from the parent settings module:

```bash
cd /srv/kiwitcms
sudo install -m 0644 /PATH/TO/NETOPS-LDAP-CA.pem /srv/kiwitcms/ldap-ca.pem
cp /srv/acmesecure/repo/docs/deployment/examples/kiwitcms-ldap/local_settings.py ./local_settings.py
cat > uwsgi.override <<'UWSGI'
[uwsgi]
processes = 2
UWSGI
chmod 0644 local_settings.py uwsgi.override
```

Review `local_settings.py` before starting. Its effective policy includes:

```python
REGISTRATION_ENABLED = False
AUTO_APPROVE_NEW_USERS = False
AUTHENTICATION_BACKENDS = [
    "kiwi_ldap_only.LDAPOnlyBackend",
    "kiwi_ldap_only.ObjectPermissionsOnlyBackend",
]
EMAIL_BACKEND = "django.core.mail.backends.dummy.EmailBackend"
EMAIL_HOST = EMAIL_HOST_USER = EMAIL_HOST_PASSWORD = ""
SERVER_EMAIL = DEFAULT_FROM_EMAIL = ""
```

The full file also configures strict LDAPS certificate validation, AD username
mapping, the required eligibility filter, middleware blocking local account
flows, a company-login template, and console logging instead of mail-to-admin
handlers. **Do not append the stock `ModelBackend`**: doing so restores local
password sign-in. `AUTO_APPROVE_NEW_USERS` does not govern LDAP provisioning;
the backend creates active users after directory authentication, without mail.
An existing Kiwi account explicitly marked inactive stays blocked in both sync
and async login paths. Do not blanket-activate old inactive users.

Local health-check hostnames remain included without allowing arbitrary public
hosts. The image already enables secure cookies and HTTPS enforcement. The worker
override prevents Kiwi from allocating a worker for every host CPU; tune the
limits and worker count from measurements.
[Kiwi settings](https://kiwitcms.readthedocs.io/en/latest/configuration.html),
[uWSGI override](https://github.com/kiwitcms/Kiwi/blob/master/etc/uwsgi.conf).

### Configure a separate Compose project

```bash
cat > compose.yaml <<'COMPOSE'
name: kiwitcms
services:
  db:
    image: ${DB_IMAGE:?Set DB_IMAGE}
    command:
      - --character-set-server=utf8mb4
      - --collation-server=utf8mb4_unicode_ci
    environment:
      MARIADB_DATABASE: kiwi
      MARIADB_USER: kiwi
      MARIADB_PASSWORD: ${KIWI_DB_PASSWORD:?Set KIWI_DB_PASSWORD}
      MARIADB_ROOT_PASSWORD: ${MARIADB_ROOT_PASSWORD:?Set MARIADB_ROOT_PASSWORD}
    volumes:
      - db_data:/var/lib/mysql
    healthcheck:
      test: ['CMD', 'healthcheck.sh', '--connect', '--innodb_initialized']
      interval: 10s
      timeout: 5s
      retries: 30
      start_period: 30s
    mem_limit: 1g
    restart: unless-stopped
  web:
    image: ${KIWI_IMAGE:?Set KIWI_IMAGE}
    pull_policy: never
    depends_on:
      db:
        condition: service_healthy
    ports:
      - 127.0.0.1:18443:8443
    volumes:
      - uploads:/Kiwi/uploads
      - ./local_settings.py:${KIWI_SETTINGS_PATH:?Set KIWI_SETTINGS_PATH}:ro
      - ./uwsgi.override:/Kiwi/etc/uwsgi.override:ro
      - ./ssl:/Kiwi/ssl:ro
      - ./ldap-ca.pem:/Kiwi/ldap-ca.pem:ro
    environment:
      KIWI_DB_HOST: db
      KIWI_DB_PORT: '3306'
      KIWI_DB_NAME: kiwi
      KIWI_DB_USER: kiwi
      KIWI_DB_PASSWORD: ${KIWI_DB_PASSWORD:?Set KIWI_DB_PASSWORD}
      KIWI_SECRET_KEY: ${KIWI_SECRET_KEY:?Set KIWI_SECRET_KEY}
      KIWI_FQDN: ${KIWI_FQDN:?Set KIWI_FQDN}
      LDAP_URL: ${LDAP_URL:?Set LDAP_URL}
      LDAP_SEARCH_BASE: ${LDAP_SEARCH_BASE:?Set LDAP_SEARCH_BASE}
      LDAP_DOMAIN: ${LDAP_DOMAIN:?Set LDAP_DOMAIN}
      LDAP_REQUIRED_FILTER: ${LDAP_REQUIRED_FILTER:?Set LDAP_REQUIRED_FILTER}
    cap_drop: [ALL]
    mem_limit: 1g
    restart: unless-stopped
volumes:
  db_data:
  uploads:
COMPOSE
chmod 0644 compose.yaml
sudo tee /usr/local/sbin/kiwi-compose >/dev/null <<'WRAPPER'
#!/bin/sh
set -eu
exec docker compose --project-directory /srv/kiwitcms \
  --project-name kiwitcms --env-file /srv/kiwitcms/.env \
  -f /srv/kiwitcms/compose.yaml "$@"
WRAPPER
sudo chmod 0755 /usr/local/sbin/kiwi-compose
sudo /usr/local/sbin/kiwi-compose config --quiet
```

Use this wrapper for Kiwi and `acme-compose` for Backstage. There are no shared
networks, database credentials, fixed container names, or volumes. The host's
existing bounded Docker log configuration applies to the new containers.
The database has no host port. Do not use `down -v` on either live project.

## 4. Establish TLS trust between Caddy and Kiwi

Kiwi's container has its own Nginx. Container port 8080 redirects to HTTPS;
connect Caddy to **8443 through host 18443**. Its inner server also handles
static files and protected attachments, so proxy all paths through it rather
than serving `/Kiwi/uploads` as a public host directory.
[Container TLS and proxy guidance](https://kiwitcms.readthedocs.io/en/latest/installing_docker.html#ssl-configuration).

The default image certificate has a build-specific name. Install an explicit
private upstream certificate with a known SAN, then trust that certificate only
for Caddy's Kiwi upstream. This is separate from the automatically managed
public certificate for `tcms.example.com`.

```bash
sudo install -d -m 0755 /srv/kiwitcms/ssl
sudo openssl req -x509 -newkey rsa:3072 -noenc -days 825 \
  -keyout /srv/kiwitcms/ssl/localhost.key \
  -out /srv/kiwitcms/ssl/localhost.crt \
  -subj '/CN=kiwi-upstream.internal' \
  -addext 'subjectAltName=DNS:kiwi-upstream.internal' \
  -addext 'basicConstraints=critical,CA:FALSE' \
  -addext 'extendedKeyUsage=serverAuth'
sudo chown 1001:1001 /srv/kiwitcms/ssl/localhost.key
sudo chmod 0600 /srv/kiwitcms/ssl/localhost.key
sudo chmod 0644 /srv/kiwitcms/ssl/localhost.crt
sudo install -m 0644 /srv/kiwitcms/ssl/localhost.crt /etc/caddy/kiwitcms-upstream.crt
openssl verify -CAfile /srv/kiwitcms/ssl/localhost.crt \
  -verify_hostname kiwi-upstream.internal /srv/kiwitcms/ssl/localhost.crt
```

The upstream runtime uses UID 1001 in the reviewed Dockerfile, which must be
able to read the mounted private key. Check that UID when choosing a different
image. Keep the directory mount read-only and never put the key in the source
checkout. The public trust copy is readable by the existing Caddy service.
Monitor this upstream certificate's expiry; Caddy renews public ACME
certificates, **not** this private mounted certificate.

## 5. Initialize the application before publishing it

Start the dedicated database and wait for readiness. The one-off initialization
container does not publish Kiwi's web ports:

```bash
sudo /usr/local/sbin/kiwi-compose up -d --wait --wait-timeout 360 db
sudo /usr/local/sbin/kiwi-compose run --rm --no-deps web /Kiwi/manage.py migrate --noinput
sudo /usr/local/sbin/kiwi-compose run --rm --no-deps web /Kiwi/manage.py set_domain tcms.example.com
sudo /usr/local/sbin/kiwi-compose run --rm --no-deps web /Kiwi/manage.py refresh_permissions --noinput
```

Use the real public hostname in `set_domain`, without a scheme or path. These
are the schema/site/permission steps from Kiwi's initialization command, with
its **local `createsuperuser` step omitted**. Do not run `initial_setup` in this
LDAP-only flow. For an existing database, skip these initialization commands;
later software releases use the normal `upgrade` procedure.
[Initialization implementation](https://github.com/kiwitcms/Kiwi/blob/master/tcms/core/management/commands/initial_setup.py).

Provision the first administrator by authenticating a real, eligible directory
user through the configured LDAP backend, then granting that Kiwi profile the
initial admin flags. The password is prompted, not embedded in shell history
or the command line. Choose an authorized administrator, not an arbitrary pilot:

```bash
sudo /usr/local/sbin/kiwi-compose run --rm --no-deps web /Kiwi/manage.py shell -c '
from getpass import getpass
from django.contrib.auth import authenticate
username = input("Approved LDAP administrator username: ")
user = authenticate(username=username, password=getpass("Directory password: "))
if user is None:
    raise SystemExit("LDAP sign-in failed or the Kiwi profile is inactive; no promotion performed")
user.is_staff = True
user.is_superuser = True
user.set_unusable_password()
user.save(update_fields=["is_staff", "is_superuser", "password"])
print("Promoted LDAP user:", user.get_username())
'
```

No verification message or activation link is sent. A missing LDAP `mail` value
is not a reason to invent a local email/password registration. Keep an SSH/sudo
session and NetOps recovery contact: new web logins require directory access.
Repeat this controlled promotion for a second LDAP administrator if appropriate.

```bash
sudo /usr/local/sbin/kiwi-compose run --rm --no-deps web /Kiwi/manage.py check --deploy
sudo /usr/local/sbin/kiwi-compose run --rm --no-deps web /Kiwi/manage.py migrate --check
sudo /usr/local/sbin/kiwi-compose up -d --wait --wait-timeout 180 web
sudo /usr/local/sbin/kiwi-compose exec web /Kiwi/manage.py set_domain
curl --noproxy '*' --fail --show-error --head \
  --cacert /srv/kiwitcms/ssl/localhost.crt \
  --resolve kiwi-upstream.internal:18443:127.0.0.1 \
  -H 'Host: tcms.example.com' \
  https://kiwi-upstream.internal:18443/accounts/login/
sudo /usr/local/sbin/kiwi-compose ps
```

Expect HTTP 200 from the local login endpoint with certificate verification.
`set_domain` without an argument prints the current domain; to correct it use
`set_domain tcms.example.com`. Review `check --deploy` warnings. HSTS needs an
explicit policy after HTTPS is proven; debug mode, weak keys, and insecure
cookies are configuration errors. A healthy process does not prove user login.

## 6. Add only the Kiwi hostname to Caddy

Preserve the current global options, `demo_access` snippet and all Backstage,
customer, or identity-provider blocks. Append this block with your actual Kiwi
FQDN. Importing the existing `demo_access` keeps Kiwi behind the same
operator/VPN IP gate during the pilot; Kiwi still uses its own account login.
When expanding the pilot, update its allowed networks deliberately.

```caddyfile
tcms.example.com {
    import demo_access
    request_body {
        max_size 10MB
    }
    reverse_proxy https://127.0.0.1:18443 {
        header_up Host {hostport}
        transport http {
            tls_server_name kiwi-upstream.internal
            tls_trust_pool file /etc/caddy/kiwitcms-upstream.crt
            response_header_timeout 60s
        }
    }
    log
}
```

The public Host must reach Django unchanged. Caddy 2.11+ rewrites Host for
HTTPS upstreams by default; `header_up Host {hostport}` explicitly preserves
the original hostname. `tls_server_name` verifies the independent private
upstream name, and `tls_trust_pool` trusts its certificate. Do not add
`tls_insecure_skip_verify` to work around a wrong name, expired certificate,
or unreadable trust file.
[Caddy HTTPS proxy behavior](https://caddyserver.com/docs/caddyfile/directives/reverse_proxy#https),
[TLS transport](https://caddyserver.com/docs/caddyfile/directives/reverse_proxy#the-http-transport).

```bash
sudo cp -p /etc/caddy/Caddyfile "/etc/caddy/Caddyfile.before-kiwi-$(date -u +%Y%m%dT%H%M%SZ)"
sudo nano /etc/caddy/Caddyfile
sudo caddy fmt --overwrite /etc/caddy/Caddyfile
sudo caddy validate --config /etc/caddy/Caddyfile --adapter caddyfile
sudo systemctl reload caddy
sudo journalctl -u caddy -n 100 --no-pager
```

Caddy obtains the public certificate and handles renewal and HTTP-to-HTTPS
redirects using the existing inbound ports and ACME configuration. There is
no host Nginx site, Certbot invocation, or new certificate-renewal hook to add.
The Nginx process **inside Kiwi's container** remains part of its upstream
runtime and does not compete for the host's public ports.

## 7. Verify Kiwi and the existing applications

**Workstation, from an already allowlisted address:**

```bash
curl -I http://tcms.example.com/accounts/login/
curl --fail --show-error -I https://tcms.example.com/accounts/login/
curl --fail --show-error -I https://catalog.example.com/
curl --fail --show-error -I https://customers.example.com/
nc -vz -w 3 YOUR_VPS_PUBLIC_IP 18443
nc -vz -w 3 YOUR_VPS_PUBLIC_IP 3306
```

HTTP should redirect to the same Kiwi hostname over HTTPS; public TLS must
validate normally. The direct-port checks should time out or be refused.
Repeat for IPv6 if you publish an AAAA record. From an unapproved client,
the Kiwi Caddy block should return 403. Backstage and Customer Portal must
continue to serve their own applications and existing access policy.

On the **VPS**:

```bash
sudo /usr/local/sbin/kiwi-compose ps
sudo /usr/local/sbin/kiwi-compose exec web /Kiwi/manage.py migrate --check
sudo /usr/local/sbin/acme-compose ps
sudo ss -lntp
sudo docker stats --no-stream
```

In a browser, sign in as an eligible normal LDAP user and assign/verify that
profile's Kiwi permissions through the LDAP administrator. Exercise a test plan, case, run and result; upload and download an
attachment, including a permission-denied download case. Check static assets,
links, and site domain. The browser should use only `https://tcms.example.com`,
without `:18443` or the private upstream name.

Kiwi's inner Nginx sees the Docker-side peer for some client-IP behavior,
including its login rate limit. Do not assume its default limit distinguishes
all real users behind Caddy. Caddy's access journal retains the external client
address. Review real-IP trust separately before changing those controls.

## 8. Complete application settings and scheduled cleanup

### LDAP accounts, permissions and disabled email flows

Users sign in with their directory username and password. The LDAP backend
creates their local Kiwi profile on first successful sign-in and updates mapped
profile fields on later logins. It does not use email activation and does not
wait for `AUTO_APPROVE_NEW_USERS`. Eligibility is enforced by the directory base
and `LDAP_REQUIRED_FILTER`; use NetOps' approved group/disabled-account filter.

Assign Kiwi roles to those existing LDAP-created profiles. `Tester` membership,
admin-site staff access, and superuser status are separate permission choices;
do not grant them to every LDAP user automatically. Never create a local web
password as a recovery workaround. The configured LDAP backend checks local
`is_active` too, so a deliberately deactivated Kiwi profile stays blocked.

The final settings discard outgoing email through
`django.core.mail.backends.dummy.EmailBackend`, remove SMTP credentials and use
console error logging. There is **no SMTP setup, sendtestemail command, mailbox
verification, or activation step**. LDAP email is optional profile metadata.
Directory password recovery belongs to NetOps, not Kiwi's password-reset form.

The supplied middleware returns 404 for these account-changing routes before
upstream views execute:

- `/accounts/register/`, `/accounts/confirm/...`, and `/accounts/passwordreset/...`;
- `/accounts/<id>/reset-user-email/`, which otherwise deactivates a profile and sends an activation email;
- Django admin password-change routes and the local-user creation form.

The custom login form omits registration/reset links. Some upstream signed-in
user-menu links may still reference directory-managed account actions; their
routes return the explicit directory-management response instead of changing a
password/email or sending mail. Do not remove the server-side guard merely to
make those links work.

Verify the effective configuration inside the serving container:

```bash
sudo /usr/local/sbin/kiwi-compose exec web /Kiwi/manage.py shell -c '
from django.conf import settings
from django.contrib.auth import get_backends
expected = ["kiwi_ldap_only.LDAPOnlyBackend", "kiwi_ldap_only.ObjectPermissionsOnlyBackend"]
assert list(settings.AUTHENTICATION_BACKENDS) == expected
assert settings.EMAIL_BACKEND == "django.core.mail.backends.dummy.EmailBackend"
assert settings.REGISTRATION_ENABLED is False
assert settings.AUTO_APPROVE_NEW_USERS is False
assert len(get_backends()) == 2
print("LDAP-only policy loaded; mail delivery and local password fallback disabled")
'
```

From an **allowlisted workstation**, confirm the login page offers company
credentials without a local-reset link, and check that disabled routes return
404 (a Caddy 403 is an IP-gate result, not proof of the application policy):

```bash
for path in accounts/register/ accounts/passwordreset/ accounts/confirm/legacy-key/ accounts/1/reset-user-email/ admin/password_change/; do
  curl --silent --show-error -o /dev/null -w '%{http_code}\n' "https://tcms.example.com/$path"
done
```

Test a correct LDAP login, wrong/empty passwords, an ineligible directory user,
a disabled directory user, a locally inactive Kiwi profile, and a local-only
account with a previously valid local password. Only active eligible LDAP
identities may obtain a new session. Exercise browser and enabled RPC/API login
paths, plus global/object permissions and attachments. An LDAP outage must
reject new logins rather than falling back to local credentials.

Existing authenticated sessions have their own lifecycle. For offboarding,
disable the directory account and local Kiwi profile and revoke the relevant
sessions through the agreed operator process. Changing the LDAP filter alone
is not an immediate revocation mechanism for every existing session.

### Session cleanup through the existing systemd host

Kiwi's startup process does not run cron. Use systemd rather than installing a
second scheduler. The lock below coordinates with the existing Backstage
backup and the Kiwi backup in the next section, avoiding cleanup during dumps.

```bash
sudo tee /etc/systemd/system/kiwitcms-sessions.service >/dev/null <<'SERVICE'
[Unit]
Description=Clean expired Kiwi TCMS sessions
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
ExecStart=/usr/bin/flock -n /run/lock/acmesecure-backup.lock /usr/local/sbin/kiwi-compose exec -T web /Kiwi/manage.py clearsessions
SERVICE
sudo tee /etc/systemd/system/kiwitcms-sessions.timer >/dev/null <<'TIMER'
[Unit]
Description=Daily Kiwi TCMS session cleanup

[Timer]
OnCalendar=*-*-* 03:17:00 UTC
Persistent=true

[Install]
WantedBy=timers.target
TIMER
sudo systemctl daemon-reload
sudo systemctl start kiwitcms-sessions.service
sudo systemctl enable --now kiwitcms-sessions.timer
sudo systemctl list-timers kiwitcms-sessions.timer
```

## 9. Back up Kiwi using the existing off-host backup service

The completed Backstage backup does **not** automatically include Kiwi's
MariaDB and attachment volume. Reuse the already configured encrypted Restic
repository and credentials in `/etc/acmesecure/backup.env`, with a separate
`kiwitcms` snapshot tag and job. Do not reinitialize the repository, regenerate
its password, or change Backstage's backup service.

### Retain each application image once

Before the first backup, archive the exact locally built Kiwi image. Repeat for
every new image **before** upgrading. The database image is recorded by its
registry digest and must remain available from the registry or a retained
internal mirror. Source files alone do not recover the exact built image.

```bash
cd /srv/kiwitcms
KIWI_IMAGE="$(sed -n 's/^KIWI_IMAGE=//p' .env)"
set -o pipefail
sudo docker image save "$KIWI_IMAGE" | gzip \
  | sudo tee "/var/backups/kiwitcms/images/${KIWI_IMAGE##*:}.tar.gz" >/dev/null
sudo gzip -t "/var/backups/kiwitcms/images/${KIWI_IMAGE##*:}.tar.gz"
```

A private registry with retained image digests can replace these application
archives; make that recovery dependency explicit before omitting them.

### Install the coordinated database/attachment backup

This job briefly stops **Kiwi web only**, dumps SQL and attachments as one
recovery set, restarts Kiwi, and uploads the set/configuration/images. It does
not stop Backstage, its services, PostgreSQL, or Caddy. Close any other Kiwi
writers or one-off management jobs for the capture. The shared backup lock
prevents overlap with Backstage's existing job. A lock conflict fails this run
and needs an alert/retry; it must not be silently treated as a successful backup.

```bash
sudo tee /usr/local/sbin/kiwi-backup >/dev/null <<'BACKUP'
#!/usr/bin/env bash
set -euo pipefail
umask 077
set -a
source /etc/acmesecure/backup.env
set +a
: "${RESTIC_REPOSITORY:?Use the existing off-host repository}"
: "${RESTIC_PASSWORD_FILE:?Use the existing repository password file}"
exec 9>/run/lock/acmesecure-backup.lock
flock -n 9
COMPOSE=/usr/local/sbin/kiwi-compose
"$COMPOSE" ps --status running --services | grep -qx web
cd /srv/kiwitcms
BACKUP_DIR=/var/backups/kiwitcms/latest
mkdir -p "$BACKUP_DIR"
printf 'in-progress %s\n' "$(date -u +%Y%m%dT%H%M%SZ)" > "$BACKUP_DIR/status.txt"
stopped=no
resume_web() {
  local status=$?
  if [[ "$stopped" == yes ]]; then
    "$COMPOSE" start web || status=1
  fi
  exit "$status"
}
trap resume_web EXIT
stopped=yes
"$COMPOSE" stop web
"$COMPOSE" exec -T db sh -c \
  'exec mariadb-dump -uroot -p"$MARIADB_ROOT_PASSWORD" --single-transaction --routines --events --triggers --databases kiwi' \
  | gzip > "$BACKUP_DIR/database.sql.gz"
"$COMPOSE" run --rm --no-deps -T --entrypoint tar web \
  -C /Kiwi/uploads -czf - . > "$BACKUP_DIR/uploads.tar.gz"
tar -czf "$BACKUP_DIR/config.tar.gz" .env compose.yaml local_settings.py uwsgi.override ssl ldap ldap-ca.pem
KIWI_IMAGE=$(sed -n 's/^KIWI_IMAGE=//p' .env)
DB_IMAGE=$(sed -n 's/^DB_IMAGE=//p' .env)
docker image inspect "$KIWI_IMAGE" "$DB_IMAGE" > "$BACKUP_DIR/images.json"
docker image inspect "$KIWI_IMAGE" --format '{{index .Config.Labels "org.opencontainers.image.revision"}}' \
  > "$BACKUP_DIR/source-commit.txt"
gzip -t "$BACKUP_DIR/database.sql.gz"
tar -tzf "$BACKUP_DIR/uploads.tar.gz" >/dev/null
tar -tzf "$BACKUP_DIR/config.tar.gz" >/dev/null
(cd "$BACKUP_DIR" && sha256sum database.sql.gz uploads.tar.gz config.tar.gz images.json source-commit.txt > SHA256SUMS)
printf 'complete %s\n' "$(date -u +%Y%m%dT%H%M%SZ)" > "$BACKUP_DIR/status.txt"
"$COMPOSE" up -d --wait --wait-timeout 180 web
stopped=no
restic backup --tag kiwitcms \
  "$BACKUP_DIR" /var/backups/kiwitcms/images \
  /usr/local/sbin/kiwi-compose /usr/local/sbin/kiwi-backup \
  /etc/systemd/system/kiwitcms-backup.service /etc/systemd/system/kiwitcms-backup.timer \
  /etc/systemd/system/kiwitcms-sessions.service /etc/systemd/system/kiwitcms-sessions.timer \
  /etc/caddy
restic forget --tag kiwitcms --keep-daily 7 --keep-weekly 4 --prune
restic check
BACKUP
sudo chmod 0750 /usr/local/sbin/kiwi-backup
sudo tee /etc/systemd/system/kiwitcms-backup.service >/dev/null <<'SERVICE'
[Unit]
Description=Back up Kiwi TCMS SQL, attachments and deployment state
Requires=docker.service
After=docker.service network-online.target
Wants=network-online.target

[Service]
Type=oneshot
ExecStart=/usr/local/sbin/kiwi-backup
UMask=0077
SERVICE
sudo tee /etc/systemd/system/kiwitcms-backup.timer >/dev/null <<'TIMER'
[Unit]
Description=Nightly Kiwi TCMS backup

[Timer]
OnCalendar=*-*-* 03:45:00 UTC
RandomizedDelaySec=15m
Persistent=true

[Install]
WantedBy=timers.target
TIMER
sudo systemctl daemon-reload
sudo systemctl start kiwitcms-backup.service
sudo systemctl status kiwitcms-backup.service --no-pager
sudo journalctl -u kiwitcms-backup.service -n 100 --no-pager
sudo systemctl enable --now kiwitcms-backup.timer
sudo systemctl list-timers kiwitcms-backup.timer
```

The example runs after the original Backstage backup schedule. Adjust if its
normal duration overlaps. Monitor both jobs independently, newest off-host
snapshot age, repository integrity, and restore results. Retention affects
snapshots tagged `kiwitcms`; the Backstage snapshot tag stays separate.

`latest` is a working recovery set, not a local backup history. A failed capture
can leave it incomplete: require `status.txt` to say `complete` and all checksums
to pass. No upload/retention runs after a failed capture. Previous successful
off-host snapshots remain the recovery source. The exit trap attempts to
restart Kiwi after a capture failure; verify its state and investigate alerts.
Image archives accumulate until deliberately retired after their matching
recovery snapshots are no longer required.

Record successful snapshot IDs:

```bash
sudo bash -euc 'set -a; source /etc/acmesecure/backup.env; set +a; restic snapshots --tag kiwitcms'
```

Keep the existing Restic password and repository credentials recoverable
outside this VPS. The database, config archive, SSL key and uploads are
confidential and must remain encrypted off-host. The archive now also includes
`ldap/` (Dockerfile, guard module and login template) and `ldap-ca.pem`; LDAP
connection/eligibility values remain in `.env`. Retain the final derived image.

## 10. Rehearse restoration away from the live stack

Use a separate VPS or isolated VM of the same architecture. The following
assumes no existing Kiwi volumes there. Do not point these commands at the
working server as a rehearsal. Restore the chosen Restic snapshot into a
staging directory first, using the existing recovery credentials:

```bash
sudo install -d -m 0700 /root/kiwi-restore
sudo bash -euc 'set -a; source /etc/acmesecure/backup.env; set +a; restic restore YOUR_SNAPSHOT_ID --target /root/kiwi-restore'
```

The snapshot restores original paths under that target. Its SQL/config set is
`/root/kiwi-restore/var/backups/kiwitcms/latest`; its image archives are under
`/root/kiwi-restore/var/backups/kiwitcms/images`. In a **root Bash shell** on the
recovery machine:

```bash
sudo bash
set -euo pipefail
umask 077
RECOVERY=/root/kiwi-restore/var/backups/kiwitcms/latest
cd "$RECOVERY"
grep -q '^complete ' status.txt
sha256sum -c SHA256SUMS
install -d -m 0750 /srv/kiwitcms
tar -xzf config.tar.gz -C /srv/kiwitcms
cd /srv/kiwitcms
KIWI_IMAGE=$(sed -n 's/^KIWI_IMAGE=//p' .env)
gzip -dc "/root/kiwi-restore/var/backups/kiwitcms/images/${KIWI_IMAGE##*:}.tar.gz" | docker image load
install -m 0755 /root/kiwi-restore/usr/local/sbin/kiwi-compose /usr/local/sbin/kiwi-compose
chown 1001:1001 ssl/localhost.key
chmod 0600 ssl/localhost.key .env
/usr/local/sbin/kiwi-compose pull db
/usr/local/sbin/kiwi-compose up -d --wait --wait-timeout 360 db
gzip -dc "$RECOVERY/database.sql.gz" \
  | /usr/local/sbin/kiwi-compose exec -T db sh -c 'exec mariadb -uroot -p"$MARIADB_ROOT_PASSWORD"'
/usr/local/sbin/kiwi-compose run --rm --no-deps -T --entrypoint tar web \
  -C /Kiwi/uploads -xzf - < "$RECOVERY/uploads.tar.gz"
/usr/local/sbin/kiwi-compose run --rm --no-deps -T web /Kiwi/manage.py migrate --check
```

Before starting recovery web, verify the dummy email backend remains selected,
block external write integrations, and arrange approved LDAP access/test users
with NetOps. Keep the LDAP-only policy during recovery; do not add local login.
Start the matching application, using a temporary rehearsal FQDN and Caddy
configuration when testing full browser behavior:

```bash
/usr/local/sbin/kiwi-compose up -d --wait --wait-timeout 180 web
/usr/local/sbin/kiwi-compose ps
exit
```

For the rehearsal FQDN, change `KIWI_FQDN`, recreate web, then run
`kiwi-compose exec web /Kiwi/manage.py set_domain YOUR_REHEARSAL_FQDN`.
Install its copied upstream trust certificate in the recovery proxy and use
the same private TLS server name. Verify real records, user permissions and
attachment downloads. Do not run `initial_setup` on restored data.

For disaster recovery, restore the matching image, database digest, SQL,
uploads, settings, secret key and SSL material together. Recover only Kiwi's
hostname block/trust file into the current shared Caddy configuration; do not
overwrite a working Backstage Caddyfile with an older full copy. Restore jobs
and configuration ownership (`deploy` for maintainable files, UID 1001 for
the private upstream key) before resuming service. Change public DNS only after
recovery checks pass.

## 11. Upgrade and roll back Kiwi independently

Build a new reviewed image while Kiwi and Backstage remain running. Review
release notes, configuration and database changes, and test migrations on a
restored rehearsal first. In the persistent build session:

```bash
cd /srv/kiwitcms/source
git status --short
git fetch --tags origin
NEW_REF='REPLACE_WITH_REVIEWED_TAG_OR_FULL_COMMIT'
git checkout --detach "$NEW_REF"
NEW_COMMIT="$(git rev-parse HEAD)"
NEW_RELEASE="$(date -u +%Y%m%dT%H%M%SZ)-$(git rev-parse --short HEAD)"
NEW_BASE_IMAGE="local/kiwitcms-base:$NEW_RELEASE"
NEW_IMAGE="local/kiwitcms:$NEW_RELEASE"
sudo docker build --pull --target kiwitcms \
  --label "org.opencontainers.image.revision=$NEW_COMMIT" -t "$NEW_BASE_IMAGE" .
sudo docker build --build-arg "KIWI_BASE=$NEW_BASE_IMAGE" \
  -f /srv/kiwitcms/ldap/Dockerfile.ldap -t "$NEW_IMAGE" /srv/kiwitcms/ldap
printf '%s\n' "$NEW_IMAGE" > /srv/kiwitcms/candidate-image.txt
set -o pipefail
sudo docker image save "$NEW_IMAGE" | gzip \
  | sudo tee "/var/backups/kiwitcms/images/${NEW_IMAGE##*:}.tar.gz" >/dev/null
sudo gzip -t "/var/backups/kiwitcms/images/${NEW_IMAGE##*:}.tar.gz"
```

Run a successful pre-upgrade backup and record its snapshot ID.
The backup script records the **deployed image's source label**, rather than
mistaking the newly checked-out candidate source for the running release.
The candidate must include the LDAP layer and current guard/template files.
Review those files when upgrading; deploying only the upstream base image
would omit the required auth module. Keep the LDAP-only settings and dummy
email backend through upgrades and recovery.

```bash
sudo systemctl start kiwitcms-backup.service
sudo systemctl status kiwitcms-backup.service --no-pager
sudo systemctl stop kiwitcms-backup.timer kiwitcms-sessions.timer
sudo systemctl show -p ActiveState -p Result kiwitcms-backup.service kiwitcms-sessions.service
```

Ensure neither job is still running before proceeding; wait for a running job
to finish. Coordinate operator-run backups/management commands too. Keep the
Backstage backup timer enabled.

```bash
cd /srv/kiwitcms
NEW_IMAGE="$(cat candidate-image.txt)"
NEW_SETTINGS_PATH="$(sudo docker run --rm --entrypoint /venv/bin/python "$NEW_IMAGE" \
  -c 'from pathlib import Path; import tcms; print(Path(tcms.__file__).parent / "settings" / "local_settings.py")')"
cp -p .env ".env.before-upgrade-$(date -u +%Y%m%dT%H%M%SZ)"
sudo /usr/local/sbin/kiwi-compose stop web
sed -i -e "s|^KIWI_IMAGE=.*|KIWI_IMAGE=$NEW_IMAGE|" \
  -e "s|^KIWI_SETTINGS_PATH=.*|KIWI_SETTINGS_PATH=$NEW_SETTINGS_PATH|" .env
sudo /usr/local/sbin/kiwi-compose config --quiet
sudo /usr/local/sbin/kiwi-compose run --rm --no-deps -T web /Kiwi/manage.py upgrade --noinput
sudo /usr/local/sbin/kiwi-compose run --rm --no-deps -T web /Kiwi/manage.py migrate --check
sudo /usr/local/sbin/kiwi-compose up -d --wait --wait-timeout 180 web
sudo /usr/local/sbin/kiwi-compose logs --tail=100 web
sudo systemctl start kiwitcms-backup.timer kiwitcms-sessions.timer
```

Execute the cutover steps individually. If migration fails, leave Kiwi web
stopped and investigate instead of proceeding to startup. Recheck login,
workflow, attachments and Backstage availability after every release.

`upgrade` also refreshes permissions and removes stale attachments/comments.
If schema or attachment cleanup occurred, rollback requires the **complete**
pre-upgrade database/uploads/configuration/image set on fresh recovery volumes.
Do not run old code against the new schema or downgrade MariaDB in place.
An image-only rollback is appropriate only when the data/schema remain
compatible. Keep failed-release data for diagnosis, and handle database-series
updates as a separate tested operation.
Do not roll back to a local-password-enabled configuration under this policy;
recover a known-good LDAP-only image/settings pair through SSH instead.
[Upgrade implementation](https://github.com/kiwitcms/Kiwi/blob/master/tcms/core/management/commands/upgrade.py).

## 12. Operations and troubleshooting

```bash
sudo /usr/local/sbin/kiwi-compose ps
sudo /usr/local/sbin/kiwi-compose logs --tail=200 web db
sudo /usr/local/sbin/acme-compose ps
sudo journalctl -u caddy -u kiwitcms-backup.service -u kiwitcms-sessions.service --since '1 hour ago'
sudo docker stats --no-stream
df -h
free -h
openssl x509 -in /srv/kiwitcms/ssl/localhost.crt -noout -dates
openssl x509 -in /srv/kiwitcms/ssl/localhost.crt -checkend 2592000 -noout
```

The final command fails when the private upstream certificate has less than
30 days remaining. Add that expiry to monitoring alongside public TLS, backup
age, disk/memory, restart counts and application login/workflow checks.

For upstream certificate renewal, prepare a new SAN-matching key/cert pair in
a staging directory. First load a Caddy trust bundle containing **old and new**
certificates and reload Caddy, then install the new pair and recreate Kiwi web.
Verify upstream/public TLS, remove the old trust entry, and reload Caddy again.
Preserve UID 1001 key access and update the encrypted backup. Do not overwrite
the live key/cert with an untested pair or assume ACME renews them.

| Symptom | Check |
| --- | --- |
| Caddy 502 / TLS verification failure | Kiwi health, loopback 18443, private certificate expiry/SAN, Caddy trust file and `tls_server_name` |
| Redirect loop | HTTPS 8443 upstream, not the redirect-only 8080; preserved public Host |
| HTTP 400 or CSRF 403 | Public hostname, `ALLOWED_HOSTS`, HTTPS trusted origin and original Host forwarding |
| Caddy 403 | Client IPv4/IPv6/VPN address versus the existing `demo_access` allowlist |
| Wrong application or certificate | New A/AAAA record and Kiwi site block; preserve existing Backstage/customer blocks |
| HTTP 413 | Kiwi upload limit plus both inner Nginx and Caddy body limits |
| DB authentication fails after env edit | Credentials already stored in MariaDB; env editing does not rotate them |
| Build/web killed or restarted | Host RAM/disk, configured limits, kernel OOM events and competing Backstage workload |
| Backup/cleanup timer fails | Journal, running containers, shared lock conflict, repository access and latest successful snapshot |
| All new logins fail | NetOps LDAPS routing/DNS/CA, AD UPN domain, eligible-user filter and the user's local `is_active`; there is intentionally no local password fallback |
| User is asked to activate by email | Wrong image/settings or legacy account flow: verify the dummy email backend and account-flow middleware; do not configure SMTP to work around it |

Docker health status alone does not restart an unhealthy but running process.
Both stacks already use restart policies, and the host already starts Docker
and Caddy at boot. A full VPS reboot affects Backstage too, so schedule one
shared maintenance window only when appropriate; do not reboot as a Kiwi-only
deployment step. After that planned reboot, check both Compose projects,
timers, hostnames, login and attachment workflows.

Keep the original server patching and Caddy certificate procedures. Rebuild
Kiwi images deliberately for application/base-image updates, retain known-good
images, and avoid global volume pruning. Kiwi can now be deployed, stopped,
backed up and upgraded through its own wrapper without operating the Backstage
Compose project.
