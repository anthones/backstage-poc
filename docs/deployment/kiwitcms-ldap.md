# Kiwi TCMS: LDAP-only configuration reference

The [deployment guide](deploy_debian.md) now includes LDAP-only authentication
from the first build. Use its complete commands for a fresh install or its
existing-installation cutover note. This replaces the earlier optional LDAP
configuration that kept a local password recovery account.

| VPS file | Change |
| --- | --- |
| `/srv/kiwitcms/ldap/Dockerfile.ldap` | Install the pinned LDAP packages on the reviewed Kiwi base; copy the guard module and company-login template |
| `/srv/kiwitcms/ldap/kiwi_ldap_only.py` | LDAP-only sync/async authentication, inactive-user guard, Guardian permission wrapper and local-account-flow blocking |
| `/srv/kiwitcms/ldap/templates/registration/custom_login.html` | Directory credentials form with CSRF protection, without registration/reset links |
| `/srv/kiwitcms/local_settings.py` | Load the two custom backends; configure LDAPS and the required eligibility filter; disable mail and local account flows |
| `/srv/kiwitcms/.env` | Set `LDAP_URL`, `LDAP_SEARCH_BASE`, `LDAP_DOMAIN`, `LDAP_REQUIRED_FILTER` and the final derived `KIWI_IMAGE`; preserve DB credentials and `KIWI_SECRET_KEY` |
| `/srv/kiwitcms/compose.yaml` | Pass all four LDAP values and mount `ldap-ca.pem` read-only; remove old SMTP variables |
| `/srv/kiwitcms/ldap-ca.pem` | NetOps' verified directory CA chain |
| `/usr/local/sbin/kiwi-backup` | Add `ldap/` and `ldap-ca.pem` to the configuration archive; retain the derived image |

Copy the actual files from [the supplied templates](examples/kiwitcms-ldap/).
The worked example is **AD over LDAPS**: users enter a short name, the backend
binds with the configured UPN domain, and the directory must permit own-profile
lookup. NetOps must confirm the eligible-user/group filter and disabled-account
rules. OpenLDAP and StartTLS need corresponding schema, formatter and TLS edits.
Do not put end-user directory passwords in the environment file.

The required authentication list is exactly:

```python
AUTHENTICATION_BACKENDS = [
    "kiwi_ldap_only.LDAPOnlyBackend",
    "kiwi_ldap_only.ObjectPermissionsOnlyBackend",
]
EMAIL_BACKEND = "django.core.mail.backends.dummy.EmailBackend"
REGISTRATION_ENABLED = False
AUTO_APPROVE_NEW_USERS = False
```

Do **not** add `django.contrib.auth.backends.ModelBackend` as another backend:
that would accept local passwords. The LDAP class already inherits its global
permission methods; the second class supplies Guardian object permissions.
Both synchronous and asynchronous authentication reject locally inactive users.

Eligible LDAP users get active Kiwi profiles on first successful login without
email activation. Those registration flags do not restrict LDAP admission;
`LDAP_REQUIRED_FILTER` and the directory search base do. Assign Kiwi roles
explicitly. LDAP email is profile metadata, not a verification prerequisite.

There is no SMTP configuration or email-based password recovery. The middleware
blocks registration, confirmation, password-reset, email-reset, admin password
change and local-user creation routes. This also prevents the email-change view
from deactivating a user while waiting for an activation message that cannot be
sent. Directory credentials are managed by NetOps.

For initial administration, use the main guide's prompted LDAP sign-in and
promotion command over SSH. Skip `initial_setup`/`createsuperuser`; use the
schema/site/permission initialization steps listed there. A local administrator
password cannot sign in during a directory outage. Recovery is through SSH/sudo
and restoration of directory access or a known-good LDAP-only configuration.

Before cutover on an existing deployment: take a verified backup, stop Kiwi web,
review username/privilege collisions and old inactive profiles, preserve secrets,
clear old Kiwi sessions, and install the complete image/configuration pair.
Do not blanket-activate existing inactive accounts or restore local login as a
fallback. Recreate web after environment/image/mount changes.

Validate effective backends and dummy mail settings, then test browser and RPC
logins: eligible LDAP succeeds; wrong/empty passwords, local-only credentials,
ineligible/disabled directory users and locally inactive profiles fail. Verify
permissions, attachments, 404 responses for blocked account routes, and the
absence of activation/reset links on the login page. No live directory login is
verified by these repository changes.

[LDAP backend documentation](https://github.com/etianen/django-python3-ldap),
[Kiwi account routes](https://github.com/kiwitcms/Kiwi/blob/master/tcms/kiwi_auth/urls.py),
[Kiwi initialization](https://github.com/kiwitcms/Kiwi/blob/master/tcms/core/management/commands/initial_setup.py).
