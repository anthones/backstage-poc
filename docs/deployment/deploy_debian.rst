Deploying two projects on a Debian VPS
======================================

Run Kiwi TCMS and a second application as separate Docker Compose projects.
Host Nginx owns public ports 80 and 443 and selects an application by its
fully qualified domain name (FQDN). Each project has its own private Docker
network, credentials, and persistent volumes. Kiwi's database has no published
port. Application ports bind only to the VPS loopback address.

This procedure assumes a fresh Debian 13 VPS, SSH access with root or sudo,
and control of DNS for both names. Commands marked **workstation** run on your
computer; all others run on the VPS in Bash. Replace example values before
running commands. Stop at a failed command and resolve it before continuing.
The second project's build, migrations, and storage depend on that project;
the example below specifies the contract it must satisfy.

Architecture and values
-----------------------

The request paths are::

    Internet -> VPS Nginx :443 -> tcms.example.com
                              -> HTTPS 127.0.0.1:18443 -> Kiwi :8443 -> MariaDB
                              -> app.example.com
                              -> HTTP 127.0.0.1:18080 -> second app :3000

Only SSH, HTTP, and HTTPS are public. Port 80 handles certificate validation
and redirects normal requests to HTTPS. The applications do not share a
Docker network or database. A shared VPS still shares a kernel, disk, CPU,
and availability; it is not a strong isolation boundary between untrusted
projects.

Choose these values:

=====================  ====================================================
Value                  Example and purpose
=====================  ====================================================
VPS IPv4               ``203.0.113.10``; replace with the actual public IP
SSH user               ``deploy``; sudo administrator
Kiwi FQDN              ``tcms.example.com``
Second FQDN            ``app.example.com``
Certificate email      ``ops@example.com``; monitored address
Kiwi source and ref    Your repository URL and a reviewed tag or full commit
Second source and ref  Its repository URL and a reviewed tag or full commit
=====================  ====================================================

A starting capacity estimate is 4 vCPUs, 8 GiB RAM, and 60 GiB SSD for modest
usage and an on-server build. Measure both projects and increase this for
larger workloads; it is not a tested capacity guarantee. Source builds use
substantially more RAM and disk than steady operation. If building causes
resource pressure, build on a matching-architecture machine or CI and transfer
the image with ``docker save`` and ``docker load``.

Why use a separate Compose file
-------------------------------

The repository's ``docker-compose.yml`` is an example, not the file used here:

* It publishes Kiwi directly on all interfaces at ports 80 and 443, which
  conflicts with a shared host proxy.
* It uses example passwords, a placeholder secret key, mutable image tags,
  and a ``proxy`` service intended for tests.
* ``Dockerfile`` builds the frontend and Python distribution, collects static
  files, and runs Nginx plus uWSGI as UID 1001. Its current runtime is CentOS
  Stream 10 with Python 3.14; Debian supplies Docker, not these app runtimes.
* ``etc/nginx.conf`` redirects container port 8080 to HTTPS. Proxy to 8443;
  proxying to 8080 produces redirects instead of a working upstream.
* Database setup is explicit. ``initial_setup`` applies migrations, creates a
  superuser, sets the site domain, and refreshes permissions. Later releases
  require ``upgrade`` rather than another ``initial_setup``.

Bootstrap SSH access
--------------------

**Workstation:** use an existing SSH key, or create a dedicated one::

    ssh-keygen -t ed25519 -f ~/.ssh/vps_deploy -C vps-deploy
    ssh -i ~/.ssh/vps_deploy root@203.0.113.10

Verify the first connection's host fingerprint against the provider console.
If the provider gives you another sudo-enabled user, log in as that user and
use ``sudo -i`` for the bootstrap commands. Keep this first session open until
a second session successfully logs in after SSH and firewall changes.

**VPS, root shell:** install utilities and create the administrator::

    apt-get update
    apt-get upgrade -y
    apt-get install -y sudo openssh-server ca-certificates curl git \
      ufw unattended-upgrades nginx certbot python3-certbot-nginx \
      dnsutils openssl gettext-base rsync tmux cron
    adduser deploy
    usermod -aG sudo deploy
    install -d -m 0700 -o deploy -g deploy /home/deploy/.ssh
    cat > /home/deploy/.ssh/authorized_keys <<'EOF'
    PASTE_YOUR_WORKSTATION_PUBLIC_KEY_HERE
    EOF
    chown deploy:deploy /home/deploy/.ssh/authorized_keys
    chmod 0600 /home/deploy/.ssh/authorized_keys
    timedatectl set-timezone Etc/UTC
    timedatectl status
    systemctl enable --now unattended-upgrades
    cat > /etc/apt/apt.conf.d/20auto-upgrades <<'EOF'
    APT::Periodic::Update-Package-Lists "1";
    APT::Periodic::Unattended-Upgrade "1";
    EOF
    systemctl enable --now apt-daily.timer apt-daily-upgrade.timer cron

Paste the contents of ``~/.ssh/vps_deploy.pub``, not your private key. Set a
strong password for ``deploy`` when prompted; sudo uses it. Verify time
synchronization in ``timedatectl status``; enable the provider's time service
or install and enable ``systemd-timesyncd`` if none is running.

**Workstation, second terminal:** verify key login and sudo::

    ssh -i ~/.ssh/vps_deploy deploy@203.0.113.10
    sudo -v

**VPS, verified deploy session:** configure key-only SSH::

    sudo tee /etc/ssh/sshd_config.d/00-vps-access.conf >/dev/null <<'EOF'
    PermitRootLogin no
    PubkeyAuthentication yes
    PasswordAuthentication no
    KbdInteractiveAuthentication no
    EOF
    sudo /usr/sbin/sshd -t
    sudo /usr/sbin/sshd -T | grep -E 'permitrootlogin|passwordauthentication|kbdinteractiveauthentication'

Inspect the effective values, then reload::

    sudo systemctl reload ssh

Test another new deploy login before closing the original root session.
OpenSSH uses the first value it reads for most settings; inspect provider
configuration and any ``Match`` blocks if effective values differ. See the
`Debian sshd configuration manual
<https://manpages.debian.org/trixie/openssh-server/sshd_config.5.en.html>`_.

Configure firewalls and DNS
---------------------------

For this fresh server using SSH port 22::

    sudo ufw default deny incoming
    sudo ufw default allow outgoing
    sudo ufw allow 22/tcp
    sudo ufw allow 80/tcp
    sudo ufw allow 443/tcp
    sudo ufw enable
    sudo ufw status verbose

If SSH uses a different port, allow that actual port before enabling UFW.
In the provider firewall or security group, allow the same TCP ports; restrict
SSH to your administrator IP or VPN where practical. Keep provider console
access available. Apply rules to IPv6 as well if enabled. No inbound rules
are needed for 3306, 8080, 8443, 18443, 18080, or Docker's remote API.

At your DNS provider create an ``A`` record for each FQDN pointing to the same
public IPv4 address. Add ``AAAA`` records only if IPv6 routing, both firewalls,
and Nginx actually work over IPv6. Remove stale AAAA records. During initial
setup use direct DNS records rather than a CDN proxy. Check resolution::

    dig +short A tcms.example.com
    dig +short AAAA tcms.example.com
    dig +short A app.example.com
    dig +short AAAA app.example.com

Docker's published ports can bypass UFW filtering. The loopback-only bindings
below and the absence of database port publishing are intentional; do not
change them to ``18443:8443`` or ``18080:3000``. Keep Docker's normal firewall
management enabled. See `Docker and UFW
<https://docs.docker.com/engine/network/packet-filtering-firewalls/#docker-and-ufw>`_
and `port publishing
<https://docs.docker.com/engine/network/port-publishing/>`_.

Install Docker Engine and Compose
---------------------------------

Use `Docker's Debian apt repository
<https://docs.docker.com/engine/install/debian/#install-using-the-apt-repository>`_
for Engine, Buildx, and the Compose plugin::

    sudo install -m 0755 -d /etc/apt/keyrings
    sudo curl -fsSL https://download.docker.com/linux/debian/gpg \
      -o /etc/apt/keyrings/docker.asc
    sudo chmod a+r /etc/apt/keyrings/docker.asc
    sudo tee /etc/apt/sources.list.d/docker.sources >/dev/null <<EOF
    Types: deb
    URIs: https://download.docker.com/linux/debian
    Suites: $(. /etc/os-release && echo "$VERSION_CODENAME")
    Components: stable
    Architectures: $(dpkg --print-architecture)
    Signed-By: /etc/apt/keyrings/docker.asc
    EOF
    sudo apt-get update
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io \
      docker-buildx-plugin docker-compose-plugin
    sudo systemctl enable --now docker
    sudo docker run --rm hello-world
    sudo docker compose version

These commands assume Docker was not already installed. On an existing host,
follow Docker's conflict-removal instructions after accounting for existing
containers. Continue using ``sudo docker``; membership in the Docker group
grants effectively root-level access. Nothing should listen on TCP 2375/2376.

Create directories and choose a release
---------------------------------------

Keep runtime configuration outside the source checkout::

    sudo install -d -m 0750 -o deploy -g deploy \
      /srv/kiwitcms /srv/other-project
    sudo install -d -m 0700 /var/backups/kiwitcms
    git clone https://github.com/kiwitcms/kiwitcms.git /srv/kiwitcms/source
    cd /srv/kiwitcms/source
    git fetch --tags origin
    KIWI_REF='REPLACE_WITH_REVIEWED_TAG_OR_FULL_COMMIT'
    git checkout --detach "$KIWI_REF"
    git rev-parse HEAD

Use your fork URL if deploying changes from a fork. Do not deploy an
unreviewed moving branch. All subsequent settings paths match the Dockerfile
in this checkout; check the Python version and image layout when selecting
another release.

Build Kiwi from source
----------------------

Run the build in ``tmux`` so an SSH disconnect does not interrupt it::

    tmux new -s kiwi-build
    cd /srv/kiwitcms/source
    KIWI_COMMIT=$(git rev-parse HEAD)
    KIWI_IMAGE="local/kiwitcms:$KIWI_COMMIT"
    sudo docker build --pull --target kiwitcms \
      --label "org.opencontainers.image.revision=$KIWI_COMMIT" \
      -t "$KIWI_IMAGE" .
    sudo docker image inspect "$KIWI_IMAGE" --format '{{.Id}}'

Detach with Ctrl-b then d; reconnect using ``tmux attach -t kiwi-build``.
The Dockerfile handles Node, Python, translation compilation, static files,
and package checks; no host pip/npm install is needed. Its build fetches
dependencies and uses a mutable CentOS base. A commit tag identifies the
source, but rebuilding that commit is not a byte-for-byte reproducible image.
Retain the built image or push it to your own registry by digest for recovery.
Do not put secrets in the source directory or Docker build context.

Configure the production Kiwi stack
-----------------------------------

The following commands run as ``deploy``. They create secrets once; do not
rerun the environment-file creation over an existing installation. Changing
the password in an environment file does not change users in an existing
MariaDB data volume.

Pull the MariaDB 11.4 series and record its resolved digest. This keeps a
repeat deployment on the same database image until you deliberately update it.
The 11.4 series is covered by MariaDB's `maintenance policy
<https://mariadb.org/about/#maintenance-policy>`_.

::

    cd /srv/kiwitcms
    sudo docker pull mariadb:11.4
    DB_IMAGE=$(sudo docker image inspect mariadb:11.4 \
      --format '{{index .RepoDigests 0}}')
    KIWI_COMMIT=$(git -C source rev-parse HEAD)
    umask 077
    set -o noclobber
    cat > .env <<EOF
    KIWI_IMAGE=local/kiwitcms:$KIWI_COMMIT
    DB_IMAGE=$DB_IMAGE
    KIWI_FQDN=tcms.example.com
    KIWI_DB_PASSWORD=$(openssl rand -hex 32)
    MARIADB_ROOT_PASSWORD=$(openssl rand -hex 32)
    KIWI_SECRET_KEY=$(openssl rand -hex 48)
    EOF
    set +o noclobber
    chmod 0600 .env

``noclobber`` prevents replacing an existing ``.env``. Keep an encrypted copy of
these secrets off the VPS, especially ``KIWI_SECRET_KEY``. Compose environment
values are visible to root and Docker administrators; do not commit ``.env``
or paste resolved ``docker compose config`` output into issue reports.

Create a production settings override::

    cat > local_settings.py <<'EOF'
    import os

    DEBUG = False
    ALLOWED_HOSTS = [os.environ["KIWI_FQDN"], "127.0.0.1", "localhost"]
    CSRF_TRUSTED_ORIGINS = ["https://" + os.environ["KIWI_FQDN"]]
    REGISTRATION_ENABLED = False
    AUTO_APPROVE_NEW_USERS = False
    EOF
    chmod 0644 local_settings.py

Loopback hostnames allow the image's built-in health check. There is no
wildcard public hostname. Registration starts disabled; administrators create
accounts. Secure cookies and HTTPS enforcement already come from Kiwi.

Create an independent Compose file, not an override of the repository file::

    cat > compose.yaml <<'EOF'
    name: kiwitcms
    services:
      db:
        image: ${DB_IMAGE:?Set DB_IMAGE in .env}
        command:
          - --character-set-server=utf8mb4
          - --collation-server=utf8mb4_unicode_ci
        environment:
          MARIADB_DATABASE: kiwi
          MARIADB_USER: kiwi
          MARIADB_PASSWORD: ${KIWI_DB_PASSWORD:?Set KIWI_DB_PASSWORD}
          MARIADB_ROOT_PASSWORD: ${MARIADB_ROOT_PASSWORD:?Set root password}
        volumes:
          - db_data:/var/lib/mysql
        healthcheck:
          test: ["CMD", "healthcheck.sh", "--connect", "--innodb_initialized"]
          interval: 10s
          timeout: 5s
          retries: 30
          start_period: 30s
        restart: unless-stopped
        logging:
          driver: local
          options:
            max-size: "10m"
            max-file: "5"
      web:
        image: ${KIWI_IMAGE:?Set KIWI_IMAGE in .env}
        pull_policy: never
        depends_on:
          db:
            condition: service_healthy
        ports:
          - "127.0.0.1:18443:8443"
        volumes:
          - uploads:/Kiwi/uploads
          - ./local_settings.py:/venv/lib64/python3.14/site-packages/tcms/settings/local_settings.py:ro
          - ./uwsgi.override:/Kiwi/etc/uwsgi.override:ro
        environment:
          KIWI_DB_HOST: db
          KIWI_DB_PORT: "3306"
          KIWI_DB_NAME: kiwi
          KIWI_DB_USER: kiwi
          KIWI_DB_PASSWORD: ${KIWI_DB_PASSWORD:?Set KIWI_DB_PASSWORD}
          KIWI_SECRET_KEY: ${KIWI_SECRET_KEY:?Set KIWI_SECRET_KEY}
          KIWI_FQDN: ${KIWI_FQDN:?Set KIWI_FQDN}
        cap_drop:
          - ALL
        restart: unless-stopped
        logging:
          driver: local
          options:
            max-size: "10m"
            max-file: "5"
    volumes:
      db_data:
      uploads:
    EOF
    cat > uwsgi.override <<'EOF'
    [uwsgi]
    processes = 2
    EOF
    chmod 0644 compose.yaml uwsgi.override
    sudo docker compose config --quiet

The explicit worker count avoids Kiwi allocating one worker for every host
CPU while sharing the VPS. Tune workers, database memory, and both apps'
resource limits from measurements. No shared network or global container
names are required. Named volumes are ``kiwitcms_db_data`` and
``kiwitcms_uploads``; do not use ``docker compose down -v`` or volume pruning
against a live deployment.

Initialize Kiwi before publishing it
------------------------------------

Start only the database, wait for readiness, then run setup in a one-off
container. It does not publish web ports::

    cd /srv/kiwitcms
    sudo docker compose up -d --wait --wait-timeout 360 db
    sudo docker compose run --rm --no-deps web /Kiwi/manage.py initial_setup

The image normally starts through ``CMD``; the command above replaces it
with the setup command. Answer the prompts for administrator credentials and
enter ``tcms.example.com`` as the domain, without a scheme, port, or path.
If setup fails midway, inspect the failure rather than blindly creating
another superuser. Then verify and start the web process::

    sudo docker compose run --rm --no-deps web /Kiwi/manage.py check --deploy
    sudo docker compose run --rm --no-deps web /Kiwi/manage.py migrate --check
    sudo docker compose up -d --wait --wait-timeout 180 web
    sudo docker compose exec web /Kiwi/manage.py set_domain
    curl -fkI -H 'Host: tcms.example.com' \
      https://127.0.0.1:18443/accounts/login/
    sudo docker compose ps

The login URL should return 200. ``-k`` is used only for this local upstream's
image-generated self-signed certificate. Do not use it for public HTTPS
checks. Review ``check --deploy`` warnings: HSTS is a deliberate policy choice
you may enable later after HTTPS works; debug mode, weak secrets, or insecure
cookies need correction. A passing health check alone does not verify setup
or browser login.

Deploy the second project independently
---------------------------------------

This template assumes its repository has a production Dockerfile that starts
an HTTP application on ``0.0.0.0:3000``. Replace the source URL, ref, container
port, runtime environment, storage, and initialization with that project's
requirements. An application bound to ``127.0.0.1`` inside its container is
not reachable through Docker's port mapping.

::

    git clone https://YOUR_GIT_HOST/YOUR_ORG/YOUR_SECOND_REPO.git \
      /srv/other-project/source
    cd /srv/other-project/source
    git fetch --tags origin
    OTHER_REF='REPLACE_WITH_REVIEWED_TAG_OR_FULL_COMMIT'
    git checkout --detach "$OTHER_REF"
    OTHER_COMMIT=$(git rev-parse HEAD)
    sudo docker build --pull -t "local/other-project:$OTHER_COMMIT" .
    cd /srv/other-project
    umask 077
    cat > .env <<EOF
    OTHER_IMAGE=local/other-project:$OTHER_COMMIT
    OTHER_CONTAINER_PORT=3000
    EOF
    touch runtime.env
    chmod 0600 .env runtime.env
    cat > compose.yaml <<'EOF'
    name: other-project
    services:
      web:
        image: ${OTHER_IMAGE:?Set OTHER_IMAGE}
        pull_policy: never
        env_file:
          - runtime.env
        ports:
          - "127.0.0.1:18080:${OTHER_CONTAINER_PORT:?Set container port}"
        restart: unless-stopped
        logging:
          driver: local
          options:
            max-size: "10m"
            max-file: "5"
    EOF
    chmod 0644 compose.yaml

Fill ``runtime.env`` with that application's production variables. Configure
its external URL as ``https://app.example.com`` and trust forwarding headers
only through the intended proxy path. Add its own database and named volumes
if required, with no database ``ports`` and no shared Kiwi credentials.
Run its documented migrations or setup, then start it::

    cd /srv/other-project
    sudo docker compose config --quiet
    sudo docker compose up -d
    sudo docker compose ps
    sudo docker compose logs --tail 100 web
    curl -fI http://127.0.0.1:18080/

Use the project's real health endpoint if ``/`` does not support HEAD or
does not return a successful status. Add its real health check to Compose.
This template intentionally cannot specify an unknown app's database,
migrations, workers, WebSocket needs, or backups. Those must be completed
before treating the second project as ready. Keep host port 18080 unique;
both containers may use the same internal port without conflict.

Obtain separate public certificates
-----------------------------------

Nginx can validate both names even if the second app is not ready. Define the
actual values in the current deploy shell; repeat these exports after
reconnecting if needed::

    export KIWI_FQDN=tcms.example.com
    export OTHER_FQDN=app.example.com
    export CERT_EMAIL=ops@example.com
    sudo install -d -m 0755 /var/www/letsencrypt/.well-known/acme-challenge

Create an initial HTTP-only configuration for ACME validation::

    cat > /tmp/two-projects-bootstrap.conf <<'EOF'
    server {
        listen 80 default_server;
        listen [::]:80 default_server;
        server_name _;
        return 444;
    }
    server {
        listen 80;
        listen [::]:80;
        server_name ${KIWI_FQDN} ${OTHER_FQDN};
        location /.well-known/acme-challenge/ {
            root /var/www/letsencrypt;
        }
        location / {
            return 503;
        }
    }
    EOF
    envsubst '${KIWI_FQDN} ${OTHER_FQDN}' \
      < /tmp/two-projects-bootstrap.conf \
      | sudo tee /etc/nginx/sites-available/two-projects >/dev/null
    sudo unlink /etc/nginx/sites-enabled/default
    sudo ln -s /etc/nginx/sites-available/two-projects \
      /etc/nginx/sites-enabled/two-projects
    sudo nginx -t
    sudo systemctl enable --now nginx
    sudo systemctl reload nginx

On a fresh Debian Nginx installation the default symlink exists. If adapting
an already configured host, inspect enabled sites before changing them.
Prove HTTP reachability from the **workstation**, not just the VPS::

    curl -I http://tcms.example.com/
    curl -I http://app.example.com/

Expect 503 at this stage. If requests time out, resolve DNS, provider firewall,
UFW, and IPv6 problems before requesting certificates. If the names have CAA
records, they must permit Let's Encrypt. Back on the **VPS**::

    sudo certbot certonly --webroot -w /var/www/letsencrypt \
      --cert-name "$KIWI_FQDN" -d "$KIWI_FQDN" \
      --email "$CERT_EMAIL" --agree-tos --non-interactive
    sudo certbot certonly --webroot -w /var/www/letsencrypt \
      --cert-name "$OTHER_FQDN" -d "$OTHER_FQDN" \
      --email "$CERT_EMAIL" --agree-tos --non-interactive
    sudo certbot certificates

Each FQDN gets a separate certificate and renewal configuration. The
`Certbot webroot authenticator
<https://eff-certbot.readthedocs.io/en/stable/using.html#webroot>`_ uses public
HTTP port 80. Leave the challenge path available after enabling redirects.

Configure the shared reverse proxy
----------------------------------

Replace the bootstrap site only after both certificates exist::

    cat > /tmp/two-projects-production.conf <<'EOF'
    map $http_upgrade $connection_upgrade {
        default upgrade;
        '' close;
    }
    server {
        listen 80 default_server;
        listen [::]:80 default_server;
        server_name _;
        return 444;
    }
    server {
        listen 443 ssl default_server;
        listen [::]:443 ssl default_server;
        ssl_reject_handshake on;
    }
    server {
        listen 80;
        listen [::]:80;
        server_name ${KIWI_FQDN} ${OTHER_FQDN};
        location /.well-known/acme-challenge/ {
            root /var/www/letsencrypt;
        }
        location / {
            return 301 https://$host$request_uri;
        }
    }
    server {
        listen 443 ssl;
        listen [::]:443 ssl;
        server_name ${KIWI_FQDN};
        ssl_certificate /etc/letsencrypt/live/${KIWI_FQDN}/fullchain.pem;
        ssl_certificate_key /etc/letsencrypt/live/${KIWI_FQDN}/privkey.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        client_max_body_size 10m;
        large_client_header_buffers 4 12k;
        access_log /var/log/nginx/kiwitcms-access.log;
        error_log /var/log/nginx/kiwitcms-error.log;
        location / {
            proxy_pass https://127.0.0.1:18443;
            proxy_ssl_verify off;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $remote_addr;
            proxy_set_header X-Forwarded-Proto https;
            proxy_read_timeout 60s;
        }
    }
    server {
        listen 443 ssl;
        listen [::]:443 ssl;
        server_name ${OTHER_FQDN};
        ssl_certificate /etc/letsencrypt/live/${OTHER_FQDN}/fullchain.pem;
        ssl_certificate_key /etc/letsencrypt/live/${OTHER_FQDN}/privkey.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        client_max_body_size 10m;
        access_log /var/log/nginx/other-project-access.log;
        error_log /var/log/nginx/other-project-error.log;
        location / {
            proxy_pass http://127.0.0.1:18080;
            proxy_http_version 1.1;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $remote_addr;
            proxy_set_header X-Forwarded-Proto https;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection $connection_upgrade;
            proxy_read_timeout 60s;
        }
    }
    EOF
    envsubst '${KIWI_FQDN} ${OTHER_FQDN}' \
      < /tmp/two-projects-production.conf \
      | sudo tee /etc/nginx/sites-available/two-projects >/dev/null
    sudo nginx -t
    sudo systemctl reload nginx

The restricted ``envsubst`` argument replaces domain placeholders while
preserving Nginx variables such as ``$host`` and ``$remote_addr``. Do not use
bare ``envsubst`` here. With a failed config test, fix the file before reload;
the currently running Nginx workers continue with the previous configuration.

Only the Kiwi upstream disables `upstream certificate verification
<https://nginx.org/en/docs/http/ngx_http_proxy_module.html#proxy_ssl_verify>`_
because that connection is local and uses the image's self-signed certificate.
Public clients still receive a trusted Let's Encrypt certificate. Do not
extend this setting to a remote upstream without configuring certificate
trust. Kiwi's inner Nginx serves its static files and protected attachments;
the host proxies all paths and does not expose the uploads volume directly.
Its current inner proxy sets the uWSGI client address from the Docker-side
peer, so Kiwi's internal logs and rate limiting may group external clients
together. Host Nginx's access logs retain the real public client address.

Configure automatic certificate renewal and Nginx reload::

    sudo install -d -m 0755 /etc/letsencrypt/renewal-hooks/deploy
    sudo tee /etc/letsencrypt/renewal-hooks/deploy/reload-nginx >/dev/null <<'EOF'
    #!/bin/sh
    set -eu
    /usr/sbin/nginx -t
    /bin/systemctl reload nginx
    EOF
    sudo chmod 0755 /etc/letsencrypt/renewal-hooks/deploy/reload-nginx
    sudo systemctl enable --now certbot.timer
    sudo certbot renew --dry-run
    sudo /etc/letsencrypt/renewal-hooks/deploy/reload-nginx
    systemctl list-timers certbot.timer

Certbot's dry run checks renewal, while the final explicit hook invocation
checks the reload command. See `Certbot renewal hooks
<https://eff-certbot.readthedocs.io/en/stable/using.html#renewing-certificates>`_.

Post deployment checks and application configuration
----------------------------------------------------

**Workstation:** verify public certificates without ``-k``, redirects, and
the intended application at each name::

    curl -I http://tcms.example.com/accounts/login/
    curl -fI https://tcms.example.com/accounts/login/
    curl -I http://app.example.com/
    curl -fI https://app.example.com/
    curl --connect-timeout 5 http://203.0.113.10:18080/
    curl -k --connect-timeout 5 https://203.0.113.10:18443/

HTTP should redirect to the same name over HTTPS; the two direct application
port checks should fail. Test IPv6 too if you published AAAA records. On the
**VPS**, inspect published bindings and listening sockets::

    sudo ss -lntp
    sudo docker ps --format 'table {{.Names}}\t{{.Ports}}\t{{.Status}}'
    sudo ufw status verbose
    cd /srv/kiwitcms
    sudo docker compose exec web /Kiwi/manage.py migrate --check

Log into Kiwi in a browser. Verify the site domain, create a normal user,
confirm permissions, create a test plan and test case, and upload/download an
attachment. Open the second FQDN and verify its own login and core workflow.
No application should require a host port in browser URLs. Confirm that an
unrecognized hostname does not serve either application.

Configure SMTP before relying on password resets or email notifications.
Kiwi's SMTP settings are Python overrides, not automatically recognized
``KIWI_EMAIL_*`` environment variables. For example, append this to
``/srv/kiwitcms/local_settings.py`` using ``nano`` or your preferred editor::

    EMAIL_HOST = "smtp.example.com"
    EMAIL_PORT = 587
    EMAIL_USE_TLS = True
    EMAIL_USE_SSL = False
    EMAIL_HOST_USER = "smtp-user"
    EMAIL_HOST_PASSWORD = os.environ["SMTP_PASSWORD"]
    SERVER_EMAIL = DEFAULT_FROM_EMAIL = "kiwi@example.com"

Add ``SMTP_PASSWORD`` to the protected ``.env`` file and pass it explicitly in
the web service's ``environment`` mapping::

    SMTP_PASSWORD: ${SMTP_PASSWORD:?Set SMTP_PASSWORD}

Recreate the web container and test delivery::

    cd /srv/kiwitcms
    sudo docker compose config --quiet
    sudo docker compose up -d --wait web
    sudo docker compose exec web /Kiwi/manage.py sendtestemail ops@example.com

Use your SMTP provider's required sender verification and DNS records. Permit
outbound SMTP at the VPS provider if it is blocked. For Python-only settings
changes, ``docker compose restart web`` is sufficient; changed Compose
environment variables require recreation with ``up -d``.

Kiwi has no cron daemon in its startup script. Schedule session cleanup on
the host::

    sudo tee /etc/cron.d/kiwitcms-sessions >/dev/null <<'EOF'
    17 3 * * * root cd /srv/kiwitcms && /usr/bin/docker compose exec -T web /Kiwi/manage.py clearsessions >> /var/log/kiwitcms-sessions.log 2>&1
    EOF

Verify the cron service is active with ``systemctl is-active cron``. Include
this job in host configuration backups and rotate its log if it grows.

Backups and recovery
--------------------

Back up the database and uploaded attachments as one recovery set, along
with the Compose file, settings, secret key, database image digest, source
commit, and exact application image. Copy the set encrypted to another
machine or object storage; a snapshot or archive on this VPS is not an
off-server backup. Give the second project its own equivalent backup job.

This manual Kiwi backup briefly stops its web container to prevent writes
while the SQL dump and uploads archive are taken. The second project and
host Nginx continue running. Run in a maintenance window and close any other
Kiwi writers or one-off administration jobs first. ``sudo bash`` starts a
temporary root shell; run this block inside it::

    sudo bash
    set -euo pipefail
    cd /srv/kiwitcms
    umask 077
    BACKUP_DIR="/var/backups/kiwitcms/$(date -u +%Y%m%dT%H%M%SZ)"
    mkdir -p "$BACKUP_DIR"
    trap 'docker compose up -d web' EXIT
    docker compose stop web
    docker compose exec -T db sh -c \
      'exec mariadb-dump -uroot -p"$MARIADB_ROOT_PASSWORD" --single-transaction --routines --events --triggers --databases kiwi' \
      | gzip > "$BACKUP_DIR/database.sql.gz"
    docker compose run --rm --no-deps -T --entrypoint tar web \
      -C /Kiwi/uploads -czf - . > "$BACKUP_DIR/uploads.tar.gz"
    tar -czf "$BACKUP_DIR/config.tar.gz" .env compose.yaml \
      local_settings.py uwsgi.override
    git -C source rev-parse HEAD > "$BACKUP_DIR/source-commit.txt"
    KIWI_IMAGE=$(sed -n 's/^KIWI_IMAGE=//p' .env)
    DB_IMAGE=$(sed -n 's/^DB_IMAGE=//p' .env)
    docker image inspect "$KIWI_IMAGE" "$DB_IMAGE" \
      > "$BACKUP_DIR/images.json"
    docker image save "$KIWI_IMAGE" \
      | gzip > "$BACKUP_DIR/images.tar.gz"
    gzip -t "$BACKUP_DIR/database.sql.gz" "$BACKUP_DIR/images.tar.gz"
    tar -tzf "$BACKUP_DIR/uploads.tar.gz" >/dev/null
    tar -tzf "$BACKUP_DIR/config.tar.gz" >/dev/null
    (cd "$BACKUP_DIR" && sha256sum *.gz > SHA256SUMS)
    docker compose up -d --wait --wait-timeout 180 web
    trap - EXIT
    exit

If any backup command fails, discard that incomplete set. The exit trap
attempts to restart the web container; verify ``docker compose ps`` after a
failure. Image archives can be large; a private registry with retained image
digests can replace daily image exports. Keep configuration and image
archives confidential because they can contain secrets. The database image
is recorded by registry digest rather than included in the application image
archive; recovery requires access to that registry or a retained mirror.

For recurring backups, put the root-shell body in a root-owned script and
schedule it with a systemd timer or cron plus ``flock`` to prevent overlapping
runs. Include failure alerting, an encrypted off-server transfer, and a
retention policy (for example 7 daily and 4 weekly successful sets). Choose
the destination and recovery objectives before automating deletion. Also
back up ``/etc/nginx``, ``/etc/letsencrypt``, SSH/firewall configuration, and
host jobs through the same protected off-server process.

Restore rehearsal
~~~~~~~~~~~~~~~~~

Rehearse on a separate VPS or isolated VM with the same CPU architecture.
These commands assume a fresh ``/srv/kiwitcms`` with **no existing Kiwi data
volumes** and an unpacked backup set at ``/root/kiwi-restore``. Never import
over a live database or extract attachments into an active deployment.
In a root Bash shell::

    set -euo pipefail
    cd /root/kiwi-restore
    sha256sum -c SHA256SUMS
    install -d -m 0750 /srv/kiwitcms
    tar -xzf config.tar.gz -C /srv/kiwitcms
    gzip -dc images.tar.gz | docker image load
    cd /srv/kiwitcms
    docker compose pull db
    docker compose up -d --wait --wait-timeout 360 db
    gzip -dc /root/kiwi-restore/database.sql.gz \
      | docker compose exec -T db sh -c \
          'exec mariadb -uroot -p"$MARIADB_ROOT_PASSWORD"'
    docker compose run --rm --no-deps -T --entrypoint tar web \
      -C /Kiwi/uploads -xzf - < /root/kiwi-restore/uploads.tar.gz
    docker compose run --rm --no-deps -T web /Kiwi/manage.py migrate --check
    docker compose up -d --wait --wait-timeout 180 web

Restore the matching application image and DB version first. Do not run
``initial_setup`` against restored data. On a rehearsal machine, prevent SMTP
and integrations from making external changes before starting web. Use an
SSH tunnel from the **workstation** to inspect the restored app locally::

    ssh -i ~/.ssh/vps_deploy -L 18443:127.0.0.1:18443 deploy@RESTORE_VPS_IP

From another workstation terminal, verify the login endpoint::

    curl -fkI -H 'Host: tcms.example.com' \
      https://127.0.0.1:18443/accounts/login/

For full browser validation, give the rehearsal host a temporary FQDN, update
``KIWI_FQDN`` and ``set_domain``, and configure HTTPS there. Verify real
records, permissions, and attachment downloads. For actual disaster recovery,
restore Nginx/certificates or reissue certificates, then change DNS only after
checks pass. Restore source and configuration ownership to ``deploy`` before
resuming routine maintenance.

Upgrade and rollback
--------------------

Keep the previous image and complete a backup before every release. Build
the new image while the old app continues running::

    cd /srv/kiwitcms/source
    git status --short
    git fetch --tags origin
    NEW_REF='REPLACE_WITH_REVIEWED_TAG_OR_FULL_COMMIT'
    git checkout --detach "$NEW_REF"
    NEW_COMMIT=$(git rev-parse HEAD)
    sudo docker build --pull --target kiwitcms \
      -t "local/kiwitcms:$NEW_COMMIT" .

Review release notes for database, Python path, and configuration changes;
test migration on a restored staging copy. Take the backup described above
before this cutover. A Kiwi-only maintenance window does not require stopping
the other project. In the deploy shell::

    cd /srv/kiwitcms
    cp .env .env.before-upgrade
    sudo docker compose stop web
    sed -i "s|^KIWI_IMAGE=.*|KIWI_IMAGE=local/kiwitcms:$NEW_COMMIT|" .env
    sudo docker compose config --quiet
    sudo docker compose run --rm --no-deps -T web /Kiwi/manage.py upgrade --noinput
    sudo docker compose run --rm --no-deps -T web /Kiwi/manage.py migrate --check
    sudo docker compose up -d --wait --wait-timeout 180 web
    sudo docker compose logs --tail 100 web

Execute these commands individually. If migration fails, leave web stopped
and investigate; do not proceed to startup. ``upgrade`` also refreshes
permissions and removes stale attachments/comments, so a database-only
rollback is insufficient. A plain ``docker compose pull`` does not upgrade
this locally built image.

If no database or attachment changes occurred, restoring the previous
``KIWI_IMAGE`` and recreating web may suffice. After migrations or cleanup,
restore the complete pre-upgrade SQL, uploads, configuration, and image on
fresh volumes using the recovery procedure. Do not point old code at a new
schema or downgrade MariaDB in place. Preserve the failed deployment's data
for diagnosis. Treat MariaDB version updates as a separate, tested change;
do not replace the recorded digest with ``latest``.

Operations and troubleshooting
------------------------------

Useful VPS commands::

    cd /srv/kiwitcms
    sudo docker compose ps
    sudo docker compose logs --tail 200 web db
    sudo docker stats --no-stream
    df -h
    free -h
    sudo journalctl -u nginx -u docker --since '1 hour ago'
    sudo tail -n 100 /var/log/nginx/kiwitcms-error.log
    sudo journalctl -u certbot.service --since '7 days ago'

Common symptoms:

* **502:** confirm the corresponding loopback endpoint responds and the
  container is running. Kiwi uses HTTPS 18443; the second app uses HTTP
  18080. Inspect app and Nginx error logs.
* **Redirect loop:** ensure the Kiwi upstream is port 8443 through host
  18443, with the original ``Host`` preserved. Do not disable HTTPS or
  secure cookies to work around proxy errors.
* **400 or CSRF 403:** compare FQDN, ``ALLOWED_HOSTS``, trusted origin,
  ``Host`` forwarding, and the browser's HTTPS URL.
* **Wrong project or certificate:** check A/AAAA records, enabled Nginx
  sites, ``server_name``, and SNI using the actual FQDN. Different app ports
  do not replace separate virtual hosts.
* **413:** Kiwi defaults to 5 MiB attachments, and both proxy layers allow
  10 MiB request bodies. Raising the application limit also requires
  reviewing both Nginx limits and Django's request size limit.
* **Database not ready or authentication failure:** inspect ``db`` health
  and logs; check stored-volume credentials. Environment edits do not
  rotate an existing database user's password.
* **Restart loops or killed build:** inspect RAM, disk space, Docker logs,
  and ``sudo journalctl -k`` for out-of-memory events.

Monitor both FQDNs from outside the VPS, certificate expiration, backup age
and restore success, disk usage, memory, and container restarts. Docker's
health status does not itself restart an unhealthy but still running process.
Install OS security updates routinely and schedule reboots when required.
Rebuild app images deliberately to receive base-image security updates.
Avoid unattended application or database major-version updates.

Finally, schedule a reboot test after saving work::

    sudo reboot

Reconnect, verify Nginx/Docker/cron and the Certbot timer, check both Compose
projects, and repeat public login and attachment checks. ``unless-stopped``
restarts running services after reboot, but containers you deliberately
stopped remain stopped until explicitly started.
