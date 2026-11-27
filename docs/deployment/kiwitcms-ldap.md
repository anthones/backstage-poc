# Add LDAP authentication to the deployed Kiwi TCMS instance

This short follow-up assumes the [Kiwi deployment guide](deploy_debian.md) is
complete. Keep its Caddy/DNS/TLS, database, uploads, `/srv/kiwitcms` paths and
`kiwi-compose` wrapper. The example extends the **source-built Community image**
with `django-python3-ldap`; the Enterprise edition has its own bundled identity
options. Backstage's identity configuration is independent.
[Kiwi editions](https://kiwitcms.org/features/),
[LDAP backend documentation](https://github.com/etianen/django-python3-ldap).

## 1. Get the directory details

Ask NetOps for the LDAPS hostname/port, trusted CA chain, eligible-user search
base/filter, username attributes, and a pilot account. The example below is
**Active Directory**, with users entering `alice` and binding as
`alice@company.example`. The user must be allowed to read their own profile;
if a search account is required, configure the backend's reader-account settings
with NetOps. Permit container/VPN egress to LDAP; no new inbound VPS port is needed.

Use a dedicated eligible-user subtree, or the backend's documented custom
search-filter hook for group restrictions. LDAP authentication can create users
outside Kiwi's registration form: `REGISTRATION_ENABLED=False` and
`AUTO_APPROVE_NEW_USERS=False` do **not** provide an LDAP admission policy.
Keep a tested, distinctly named local recovery administrator, and resolve
collisions between existing local usernames and directory usernames first.

## 2. Build an LDAP-enabled image

Run in **Bash as `deploy` on the VPS**. Extend the currently deployed image;
installing a package inside a running container would be lost on recreation.
The pinned backend is a Community-image customization: test it with the Python
and Django versions in your selected Kiwi image before rollout.

```bash
cd /srv/kiwitcms
BASE_IMAGE="$(sed -n 's/^KIWI_IMAGE=//p' .env)"
LDAP_IMAGE="local/kiwitcms:ldap-$(date -u +%Y%m%dT%H%M%SZ)"
cat > Dockerfile.ldap <<'DOCKERFILE'
ARG KIWI_BASE
FROM ${KIWI_BASE}
USER 0
RUN /venv/bin/pip install --no-cache-dir \
    django-python3-ldap==0.16.1 ldap3==2.9.1 pyasn1==0.6.5 \
    && /venv/bin/pip check
USER 1001
DOCKERFILE
sudo docker build --build-arg "KIWI_BASE=$BASE_IMAGE" \
  -t "$LDAP_IMAGE" - < Dockerfile.ldap
sudo docker run --rm --entrypoint /venv/bin/python "$LDAP_IMAGE" \
  -c 'import django, ldap3, django_python3_ldap; print("LDAP imports OK; Django", django.get_version())'
```

The stdin-only build context keeps `.env`, uploads and private keys out of the
build. The image retains Kiwi's existing settings path and runtime UID. Retain
the exact new image with the deployment guide's image-archive procedure.

## 3. Add CA trust and settings

Take a successful Kiwi backup. Pause its backup/cleanup timers and let any
active jobs finish before editing the configuration. Save copies for rollback:

```bash
sudo systemctl start kiwitcms-backup.service
sudo systemctl stop kiwitcms-backup.timer kiwitcms-sessions.timer
sudo systemctl show -p ActiveState kiwitcms-backup.service kiwitcms-sessions.service
cp -p .env .env.before-ldap
cp -p local_settings.py local_settings.py.before-ldap
cp -p compose.yaml compose.yaml.before-ldap
sudo install -m 0644 /PATH/TO/NETOPS-LDAP-CA.pem /srv/kiwitcms/ldap-ca.pem
nano .env
```

Add these non-secret values to `.env`, replacing the examples:

```dotenv
LDAP_URL=ldaps://dc.company.example:636
LDAP_SEARCH_BASE=OU=KiwiUsers,DC=company,DC=example
LDAP_DOMAIN=company.example
```

In `compose.yaml`, append these entries to the **existing `web.environment`**:

```yaml
      LDAP_URL: ${LDAP_URL:?Set LDAP_URL}
      LDAP_SEARCH_BASE: ${LDAP_SEARCH_BASE:?Set LDAP_SEARCH_BASE}
      LDAP_DOMAIN: ${LDAP_DOMAIN:?Set LDAP_DOMAIN}
```

Append this entry to **`web.volumes`**, preserving all current mounts:

```yaml
      - ./ldap-ca.pem:/Kiwi/ldap-ca.pem:ro
```

Append the following to the existing `local_settings.py`:

```python
import ssl
from ldap3 import Tls
from tcms.settings import common as kiwi_defaults

INSTALLED_APPS = [*kiwi_defaults.INSTALLED_APPS, "django_python3_ldap"]
AUTHENTICATION_BACKENDS = [
    "django_python3_ldap.auth.LDAPBackend",
    *kiwi_defaults.AUTHENTICATION_BACKENDS,
]
LDAP_AUTH_URL = [os.environ["LDAP_URL"]]
LDAP_AUTH_CONNECT_USE_SSL = True
LDAP_AUTH_USE_TLS = False  # This option means StartTLS; this example uses LDAPS.
LDAP_AUTH_CONNECT_ARGS = {
    "tls": Tls(validate=ssl.CERT_REQUIRED, ca_certs_file="/Kiwi/ldap-ca.pem"),
}
LDAP_AUTH_CONNECT_TIMEOUT = 5
LDAP_AUTH_RECEIVE_TIMEOUT = 10
LDAP_AUTH_SEARCH_BASE = os.environ["LDAP_SEARCH_BASE"]
LDAP_AUTH_OBJECT_CLASS = "user"
LDAP_AUTH_FORMAT_USERNAME = "django_python3_ldap.utils.format_username_active_directory_principal"
LDAP_AUTH_ACTIVE_DIRECTORY_DOMAIN = os.environ["LDAP_DOMAIN"]
LDAP_AUTH_USER_FIELDS = {
    "username": "sAMAccountName",
    "first_name": "givenName",
    "last_name": "sn",
    "email": "mail",
}
LDAP_AUTH_USER_LOOKUP_FIELDS = ("username",)
```

This retains Kiwi's local `ModelBackend` and Guardian permission backend. Do
not replace them with LDAP alone. Certificate verification remains enabled.
For mandatory StartTLS or OpenLDAP, adapt the URL/TLS settings and username/DN
formatter to NetOps' schema; this AD example is not a generic search-then-bind
configuration. [Backend settings and filters](https://pypi.org/project/django-python3-ldap/).

## 4. Cut over, test and retain the recovery path

In the same shell, select the newly built image and check the full application
configuration before recreating web:

```bash
sed -i "s|^KIWI_IMAGE=.*|KIWI_IMAGE=$LDAP_IMAGE|" .env
sudo /usr/local/sbin/kiwi-compose config --quiet
sudo /usr/local/sbin/kiwi-compose run --rm --no-deps web /Kiwi/manage.py check --deploy
sudo /usr/local/sbin/kiwi-compose run --rm --no-deps web /Kiwi/manage.py migrate --check
sudo /usr/local/sbin/kiwi-compose up -d --wait --wait-timeout 180 web
sudo /usr/local/sbin/kiwi-compose logs --tail=100 web
```

Do not run `initial_setup` again. In a fresh browser session, test the pilot's
LDAP password, a wrong password, an ineligible account, and the local recovery
administrator. Check disabled accounts through both browser and any enabled
RPC/API login path; their active-user checks can differ. Assign the pilot's
Kiwi groups/permissions explicitly; LDAP
sign-in does not automatically grant Tester, staff or superuser rights. Test
test-case/run actions and attachment access after assigning those permissions.

Keep LDAP-managed local passwords **unusable**, including for migrated existing
accounts. Otherwise the retained local backend can accept a local password
after LDAP access is revoked. Newly created LDAP accounts use unusable passwords;
do not set local passwords for them. Existing sessions are a separate revocation
concern: test offboarding and agree the session-expiry/revocation procedure.

For backups, add `Dockerfile.ldap` and `ldap-ca.pem` to the config archive's
`tar` input list in `/usr/local/sbin/kiwi-backup`, and archive the new application
image as in the deployment guide. Then run a successful backup and resume jobs:

```bash
sudo systemctl start kiwitcms-backup.service
sudo systemctl start kiwitcms-backup.timer kiwitcms-sessions.timer
```

For a configuration rollback, restore the three `*.before-ldap` files and
recreate Kiwi web using `kiwi-compose up -d --wait web`. This extension does not
require reverting SQL or uploads; keep any newly created users and review their
access. Rebuild the LDAP layer whenever upgrading the underlying Kiwi image.
No live directory login has been verified by this documentation change.
