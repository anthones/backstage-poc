"""Mounted production settings for the LDAP-only Kiwi deployment guide."""
import os
import ssl
from copy import deepcopy

from ldap3 import Tls
from tcms.settings import common as kiwi_defaults

DEBUG = False
ALLOWED_HOSTS = [os.environ["KIWI_FQDN"], "127.0.0.1", "localhost"]
CSRF_TRUSTED_ORIGINS = ["https://" + os.environ["KIWI_FQDN"]]
REGISTRATION_ENABLED = False
AUTO_APPROVE_NEW_USERS = False

# All mail is intentionally discarded. No SMTP or activation email is used.
EMAIL_BACKEND = "django.core.mail.backends.dummy.EmailBackend"
EMAIL_HOST = EMAIL_HOST_USER = EMAIL_HOST_PASSWORD = ""
EMAIL_USE_TLS = EMAIL_USE_SSL = False
SERVER_EMAIL = DEFAULT_FROM_EMAIL = ""
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "INFO"},
    "loggers": {
        "django": {"handlers": ["console"], "level": "INFO", "propagate": False},
    },
}

INSTALLED_APPS = [*kiwi_defaults.INSTALLED_APPS, "django_python3_ldap"]
AUTHENTICATION_BACKENDS = [
    "kiwi_ldap_only.LDAPOnlyBackend",
    "kiwi_ldap_only.ObjectPermissionsOnlyBackend",
]
MIDDLEWARE = [
    "kiwi_ldap_only.BlockLocalAccountFlowsMiddleware",
    *kiwi_defaults.MIDDLEWARE,
]
TEMPLATES = deepcopy(kiwi_defaults.TEMPLATES)
TEMPLATES[0]["DIRS"] = ["/Kiwi/ldap-templates", *TEMPLATES[0].get("DIRS", [])]

LDAP_AUTH_URL = [os.environ["LDAP_URL"]]
LDAP_AUTH_CONNECT_USE_SSL = True
LDAP_AUTH_USE_TLS = False  # StartTLS is a different mode; this example uses LDAPS.
LDAP_AUTH_CONNECT_ARGS = {
    "tls": Tls(validate=ssl.CERT_REQUIRED, ca_certs_file="/Kiwi/ldap-ca.pem"),
}
LDAP_AUTH_CONNECT_TIMEOUT = 5
LDAP_AUTH_RECEIVE_TIMEOUT = 10
LDAP_AUTH_SEARCH_BASE = os.environ["LDAP_SEARCH_BASE"]
LDAP_AUTH_OBJECT_CLASS = "user"
LDAP_AUTH_FORMAT_USERNAME = "django_python3_ldap.utils.format_username_active_directory_principal"
LDAP_AUTH_ACTIVE_DIRECTORY_DOMAIN = os.environ["LDAP_DOMAIN"]
LDAP_AUTH_FORMAT_SEARCH_FILTERS = "kiwi_ldap_only.eligible_filters"
LDAP_AUTH_USER_FIELDS = {
    "username": "sAMAccountName",
    "first_name": "givenName",
    "last_name": "sn",
    "email": "mail",  # Profile metadata only; never an activation prerequisite.
}
LDAP_AUTH_USER_LOOKUP_FIELDS = ("username",)
