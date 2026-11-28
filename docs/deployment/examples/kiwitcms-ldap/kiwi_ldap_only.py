"""LDAP-only authentication and directory-managed account flows for Kiwi TCMS.

Referenced by dotted paths in local_settings.py; do not import this module
while Django settings are still loading.
"""
import os
import re

from django.http import HttpResponseNotFound
from django_python3_ldap.auth import LDAPBackend
from django_python3_ldap.utils import format_search_filters
from guardian.backends import ObjectPermissionBackend


class LDAPOnlyBackend(LDAPBackend):
    """Keep inherited model permissions, but require an active LDAP login."""

    def authenticate(self, request=None, **credentials):
        user = super().authenticate(request, **credentials)
        return user if user is not None and self.user_can_authenticate(user) else None

    async def aauthenticate(self, request=None, **credentials):
        user = await super().aauthenticate(request, **credentials)
        return user if user is not None and self.user_can_authenticate(user) else None


class ObjectPermissionsOnlyBackend(ObjectPermissionBackend):
    """Guardian permissions without a password authentication fallback."""

    def authenticate(self, request=None, **credentials):
        return None

    async def aauthenticate(self, request=None, **credentials):
        return None


def eligible_filters(ldap_fields):
    """AND the normal escaped username filter with NetOps' approved filter."""
    return [*format_search_filters(ldap_fields), os.environ["LDAP_REQUIRED_FILTER"]]


_LOCAL_ACCOUNT_PATHS = (
    re.compile(r"^/accounts/(?:register|confirm|passwordreset)(?:/|$)"),
    re.compile(r"^/accounts/\d+/reset-user-email(?:/|$)"),
    re.compile(r"^/admin/password_change(?:/|$)"),
    re.compile(r"^/admin/auth/user/(?:add(?:/|$)|[^/]+/password(?:/|$))"),
)


class BlockLocalAccountFlowsMiddleware:
    """Reject local creation, password-reset and email-activation endpoints."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if any(pattern.match(request.path_info) for pattern in _LOCAL_ACCOUNT_PATHS):
            return HttpResponseNotFound(
                "Account credentials and email changes are managed by your directory.",
                content_type="text/plain",
            )
        return self.get_response(request)
