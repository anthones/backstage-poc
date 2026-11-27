# LDAP-backed sign-in for the deployed Backstage instance

This guide extends the **working [Debian VPS deployment](debian-vps.md)**. Keep
its containers, PostgreSQL, public Backstage origin, Caddy routing, IP allowlist,
release directories, and backup process. The examples use
`https://catalog.example.com`, `/srv/acmesecure/repo`, and the `acme-compose`
wrapper from that guide. Substitute the names already deployed on your VPS.

There are two paths while NetOps' identity setup is still unknown:

| What NetOps provides | Path |
| --- | --- |
| An existing identity provider connected to LDAP/AD, with OIDC available | **A:** register Backstage there; reuse its directory connection |
| An LDAP/AD directory without an OIDC identity provider | **B:** deploy Keycloak, federate it with LDAP, then register Backstage |
| SAML-only identity service or details still missing | Ask NetOps for an OIDC client or an agreed broker; do the source preparation while waiting |

Both paths finish with the same Backstage changes in sections 5–9. The worked
fallback is Keycloak; an existing Authentik, Keycloak, AD FS, or another provider
can be used when it offers the required OIDC authorization-code integration.

Jump to: [NetOps handoff](#1-details-to-obtain-from-netops),
[existing IdP](#2-path-a--use-the-existing-identity-provider),
[new Keycloak](#3-path-b--add-keycloak-to-the-vps),
[LDAP federation](#4-connect-keycloak-to-ldapad-and-register-backstage),
[Backstage changes](#5-prepare-the-backstage-source-revision),
[runtime configuration](#6-install-the-final-oidc-runtime-layer),
[cutover](#8-build-a-candidate-release-and-cut-over),
[acceptance](#9-acceptance-checks),
[optional directory sync](#10-optional--synchronize-ldap-users-and-groups-into-backstage),
[operations](#11-operations-backups-offboarding-and-recovery).

```text
Browser -> Backstage "Company account" button -> HTTPS identity provider
                                                   |
                                      LDAP/AD validates the user's password
                                                   |
Browser <- Backstage callback <- OIDC authorization code
             |
Backstage exchanges code server-side, checks identity, resolves a catalog User
             |
Backstage issues its own user token for its APIs
```

Backstage's upstream LDAP integration imports organizational entities. It does
not add a password sign-in screen. OIDC supplies sign-in; optional LDAP ingestion
supplies catalog Users and Groups. End-user LDAP passwords go to the identity
provider, and are not stored in Backstage configuration. See the official
[LDAP integration](https://backstage.io/docs/integrations/ldap/org/) and
[OIDC provider](https://backstage.io/docs/auth/oidc/).

The checked-in application uses Backstage **1.56.0**, the new backend system,
and the new frontend system (`createApp` from `@backstage/frontend-defaults`).
The package pins below match that release: OIDC module **0.4.22**, optional LDAP
module **0.12.10**, and core app API **1.20.6**. Recheck the release manifest if
your deployed source has since been upgraded.
[Release manifest](https://backstage.io/docs/releases/v1.56.0-changelog/).

The companion files under [`examples/ldap/`](examples/ldap/) are templates.
Writing this guide does not enable authentication, change the running VPS, or
install an identity server. Commands below run in **Bash as `deploy` on the VPS**
unless a browser or another machine is explicitly identified.

## 1. Details to obtain from NetOps

This is the handoff checklist for NetOps' forthcoming guide. Keep passwords and
client secrets in the agreed secret channel, outside tickets and Git.

| For either path | Required answer |
| --- | --- |
| Identity service | Existing product/URL/owner, or agreement to operate Keycloak |
| Eligible people | Pilot users, access group, disabled-user treatment, contractors |
| Identity mapping | Stable username and authoritative, unique email; whether users can change either |
| Account verification | How the IdP establishes `email_verified: true` for the controlled directory email |
| Network | VPS/container routes, DNS, VPN/private network, egress allowlists, TLS CA chain |
| Lifecycle | Password/MFA policy, lockout, session lifetime, offboarding and recovery owner |

| Path A: existing IdP | Path B: direct directory connection |
| --- | --- |
| Issuer and full OIDC discovery URL | LDAP vendor: AD, OpenLDAP, FreeIPA, etc. |
| Confidential client ID and secret | LDAPS hostname/port, or StartTLS requirement |
| Exact redirect URI approval | Read-only bind DN and its password |
| Authorization code flow and client authentication method | User/group search base DNs and allowed search filters |
| `openid`, `profile`, `email` claims, verified email and stable `sub` | Username, UUID, email, group and disabled-account attributes |
| Application assignment/access policy | CA certificates and tested nested-group semantics |

Do not guess DNs or reuse the fictional people in `catalog/org.yaml` as real
identities. The pilot needs one genuine directory user and that person's exact
verified email. Keep a tested SSH/sudo session available during cutover.

## 2. Path A — use the existing identity provider

NetOps registers a **confidential OIDC client** for Backstage:

| Setting | Example |
| --- | --- |
| Client/application ID | `backstage` |
| Flow | Authorization code / Standard flow |
| Client authentication | Enabled; server-side secret |
| Redirect URI | `https://catalog.example.com/api/auth/oidc/handler/frame` |
| Web origin, if the IdP requests one | `https://catalog.example.com` |
| Claims/scopes | `openid profile email`; verified directory email |
| Assignment | Approved Backstage pilot group/users |

Use the **exact** callback URL, without a wildcard. Disable unused direct
password grants, implicit flow, and service-account grants for this client.
Confirm any mandatory PKCE or client-authentication requirements against the
selected Backstage provider before enforcing them; do not weaken a company-wide
IdP policy just to make a sample client work.

Get the discovery URL from NetOps, rather than constructing it from the product
name. A Keycloak example is:

```text
https://sso.example.com/realms/acmesecure/.well-known/openid-configuration
```

From the VPS, inspect only public metadata:

```bash
curl --fail --show-error --silent \
  'https://sso.example.com/realms/acmesecure/.well-known/openid-configuration' \
  | jq '{issuer, authorization_endpoint, token_endpoint, userinfo_endpoint, jwks_uri}'
```

The browser must reach the authorization endpoint and Backstage callback. The
Backstage **container** must reach discovery, token, user-info, and JWKS
endpoints. A host-only successful curl is insufficient. Check that path too:

```bash
sudo /usr/local/sbin/acme-compose exec -T backstage node -e '
  fetch(process.argv[1]).then(async response => {
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const metadata = await response.json();
    console.log({ issuer: metadata.issuer, jwks_uri: metadata.jwks_uri });
  }).catch(error => { console.error(error.message); process.exit(1); });
' 'https://sso.example.com/realms/acmesecure/.well-known/openid-configuration'
```

If the IdP is on this VPS behind Caddy, its incoming source can be the VPS public
egress or a Docker gateway address. The old operator-IP allowlist may reject it.
Permit the required backend access at the **IdP**, while retaining the existing
Backstage allowlist. The callback is a browser request; allow the user's network
there. Use the public HTTPS issuer consistently, rather than replacing it with
`http://keycloak:8080` to bypass routing problems.

For an IdP signed by a private CA, follow section 7's Node CA mount. Trust the
actual CA chain; keep TLS hostname verification enabled. Once the IdP can sign
in the pilot user and supplies the claims above, continue at **section 5**.

## 3. Path B — add Keycloak to the VPS

Skip sections 3–4 when NetOps already operates an appropriate IdP. This adds a
**separate identity stack**, not another container inside the second project's
network. Reserve approximately **2.5 GiB additional runtime memory** for the
sample limits, plus OS/build headroom; resize the VPS or host identity elsewhere
if the existing two projects cannot spare it. Both Backstage and its identity
service would share this VPS's outage/recovery boundary.

The template uses Keycloak **26.8.2**, a PostgreSQL database, production `start`,
HTTP only on a host-loopback upstream, and HTTPS at Caddy. Pick a reviewed patch
release/digest and maintain it; do not use `start-dev` for this installation.
[Keycloak release](https://www.keycloak.org/2026/11/keycloak-2682-released),
[container guidance](https://www.keycloak.org/server/containers).

### Install the independent identity stack

Add an A/AAAA record for `sso.example.com`, using the same DNS/TLS procedure as
the first guide. Port **8180** is a new loopback port; public ports stay 80/443.

```bash
sudo install -d -m 0755 /srv/acme-identity
sudo install -d -m 0700 /etc/acme-identity
sudo install -d -m 0755 /etc/acme-identity/truststores
sudo install -m 0644 /srv/acmesecure/repo/docs/deployment/examples/ldap/compose.keycloak.yaml \
  /srv/acme-identity/compose.yaml
sudo install -m 0600 /dev/null /etc/acme-identity/runtime.env
printf 'KEYCLOAK_ORIGIN=https://sso.example.com\nKEYCLOAK_DB_PASSWORD=%s\nKEYCLOAK_BOOTSTRAP_PASSWORD=%s\n' \
  "$(python3 -c 'import secrets; print(secrets.token_hex(32))')" \
  "$(python3 -c 'import secrets; print(secrets.token_hex(32))')" \
  | sudo tee /etc/acme-identity/runtime.env >/dev/null
sudo tee /usr/local/sbin/identity-compose >/dev/null <<'WRAPPER'
#!/bin/sh
set -eu
exec docker compose --project-name acme-identity \
  --env-file /etc/acme-identity/runtime.env \
  -f /srv/acme-identity/compose.yaml "$@"
WRAPPER
sudo chmod 0755 /usr/local/sbin/identity-compose
```

Before starting, edit the env file if your SSO hostname differs. For a private
LDAP CA, install the verified PEM CA chain now. It is a public certificate file,
not an LDAP server's private key:

```bash
sudo install -m 0644 /PATH/TO/NETOPS-LDAP-CA.pem \
  /etc/acme-identity/truststores/ldap-ca.pem
```

Skip that copy if the directory uses a CA already trusted by Java. Keycloak
loads additional trusted certificates from its mounted `conf/truststores`
directory. Copying a CA to the VPS OS alone does not configure the container's
Java trust. [Keycloak truststore](https://www.keycloak.org/server/keycloak-truststore).

```bash
sudo /usr/local/sbin/identity-compose config --quiet
sudo /usr/local/sbin/identity-compose pull
sudo /usr/local/sbin/identity-compose up -d
sudo /usr/local/sbin/identity-compose ps
sudo /usr/local/sbin/identity-compose logs --tail=100 keycloak
```

The first production start performs image configuration and can take time.
Only 127.0.0.1:8180 is published. PostgreSQL and Keycloak's management port 9000
remain unexposed. The image's internal 9000 does not conflict with the second
project's host 9000.

### Add the SSO hostname to Caddy

Preserve existing hostname blocks. Append this one, replacing the hostname.
The `demo_access` snippet already defined in the first guide restricts only
administration here; realm endpoints need browser and Backstage backend access.

```caddyfile
sso.example.com {
    @administration path /admin /admin/* /realms/master /realms/master/*
    handle @administration {
        import demo_access
        reverse_proxy 127.0.0.1:8180
    }
    handle {
        reverse_proxy 127.0.0.1:8180
    }
    log
}
```

```bash
sudo nano /etc/caddy/Caddyfile
sudo caddy fmt --overwrite /etc/caddy/Caddyfile
sudo caddy validate --config /etc/caddy/Caddyfile --adapter caddyfile
sudo systemctl reload caddy
curl --fail --show-error --silent \
  https://sso.example.com/realms/master/.well-known/openid-configuration | jq .issuer
```

The last curl must run from an approved administration address, because this
example protects the master realm too. An unapproved VPS egress can correctly
receive 403; the application realm created next must be reachable from Backstage.
Keycloak's HTTPS hostname, `KC_HTTP_ENABLED=true`, and
`KC_PROXY_HEADERS=xforwarded` account for Caddy's TLS termination. Only Caddy can
reach the published loopback upstream. Do not publish the upstream on all
interfaces. [Keycloak hostname settings](https://www.keycloak.org/server/hostname),
[proxy configuration](https://www.keycloak.org/server/reverseproxy).

In a browser from an approved address, open `https://sso.example.com/admin/`.
Retrieve the bootstrap password through your protected administrator channel
(for example, inspect the root-only env file in the VPS editor); do not paste it
into a ticket or command argument. Create a named administrator, test its login,
and remove the temporary `bootstrap-admin` account. Keep recovery credentials
outside the VPS. The bootstrap env values only initialize a new installation;
changing them does not reset existing administrators.

Create an application realm named **acmesecure**. Keep `master` for administration.
Turn public user registration off, enable brute-force protection, and agree MFA
and session settings with NetOps. Configure these before inviting users.

## 4. Connect Keycloak to LDAP/AD and register Backstage

### Test directory access from the container network

Obtain approved routing/VPN, directory firewall rules, and DNS from NetOps. For
LDAPS, permit outbound TCP 636 to the specific directory host; for mandatory
StartTLS use the directory's approved port, commonly 389. Neither port needs
inbound exposure on the VPS. Check the Docker network path, not only the host.

This disposable diagnostic container shares Keycloak's Compose network and
prompts for the bind password. Substitute the **actual** host, DN, base and
pilot filter. The CA mount can be empty when the issuer is publicly trusted.

```bash
sudo docker run --rm -it --network acme-identity_default \
  --mount type=bind,src=/etc/acme-identity/truststores,dst=/trust,readonly \
  debian:trixie-slim bash -euc '
    apt-get update
    apt-get install -y --no-install-recommends ldap-utils ca-certificates
    if [ -f /trust/ldap-ca.pem ]; then export LDAPTLS_CACERT=/trust/ldap-ca.pem; fi
    ldapsearch -LLL -x -H ldaps://ldap.company.example:636 \
      -D "CN=backstage-reader,OU=Service Accounts,DC=company,DC=example" -W \
      -b "OU=People,DC=company,DC=example" \
      "(sAMAccountName=alice)" dn mail sAMAccountName memberOf
  '
```

For StartTLS, use `ldap://...:389` **and `-ZZ`** so a failed TLS upgrade fails
the test. Use `uid` instead of `sAMAccountName` for an appropriate OpenLDAP
schema. A successful query must return the intended user and canonical email,
with validated TLS. NetOps must confirm the actual account/group filter; the
sample pilot query is not an application access policy.

### Configure User Federation

In the **acmesecure** realm, choose **User federation → Add LDAP provider**.
Use the tested values. The following are starting mappings to confirm with
NetOps, not interchangeable schema defaults:

| Setting | Active Directory example | OpenLDAP example |
| --- | --- | --- |
| Vendor | Active Directory | Other / appropriate LDAP vendor |
| Connection URL | `ldaps://dc.company.example:636` | `ldaps://ldap.company.example:636` |
| Bind type | simple, over TLS | simple, over TLS |
| Bind DN/credential | Dedicated read-only account | Dedicated read-only account |
| Users DN | `OU=People,DC=company,DC=example` | `ou=people,dc=company,dc=example` |
| Edit mode | `READ_ONLY` | `READ_ONLY` |
| Import users | On | On |
| Sync registrations | Off | Off |
| Username LDAP attribute | `sAMAccountName` | `uid` |
| RDN LDAP attribute | `cn` | Directory's actual naming attribute, often `uid` |
| UUID LDAP attribute | `objectGUID` | `entryUUID` |
| User object classes | AD user classes confirmed by NetOps | e.g. `inetOrgPerson` |
| Email mapper | LDAP `mail` → Keycloak email | LDAP `mail` → Keycloak email |
| Search scope/filter | Approved subtree, access group, disabled-account exclusion | Equivalent approved scope and eligibility filter |

Use **Test connection** and **Test authentication**, save, then sync the eligible
pilot users. For StartTLS, enable it explicitly in the provider instead of
combining StartTLS with an `ldaps://` URL. Keep certificate verification on.
Read-only mode must cover the identity attributes as well as credentials;
verify the email mapper reads the authoritative LDAP value and users cannot
replace it through the account console.

User and group schemas differ, and nested group membership may need a mapper
or a different filter. AD membership filters do not automatically work against
an OpenLDAP server without a `memberOf` overlay. Have NetOps test the actual
eligible-user and disabled-user rules. Existing imported users, caches, and
active sessions also need an offboarding procedure.
[Keycloak LDAP federation](https://www.keycloak.org/docs/latest/server_admin/index.html#_ldap).

### Establish verified email and test directory sign-in

The OIDC module's default profile mapping exposes email only when the IdP's
user-info result has **`email_verified: true`**. That matters for the email-based
catalog resolver used below. Confirm the claim through the IdP's mapper/token
inspection tools without copying tokens to public JWT-decoding sites.
[OIDC profile mapping source](https://github.com/backstage/backstage/blob/v1.56.0/plugins/auth-backend-module-oidc-provider/src/authenticator.ts).

For the pilot, an administrator may mark that user's email verified **after**
confirming the directory value through the agreed identity-verification process.
For rollout, agree an actual verification process: Keycloak email verification
with configured SMTP, or a controlled authoritative directory/mapping policy.
Do not mark arbitrary user-editable emails verified to clear a login error.

In a private browser window, open
`https://sso.example.com/realms/acmesecure/account/` and sign in using the pilot's
**directory** password. Check a wrong password is rejected. Complete required
MFA/verification actions before adding Backstage to the flow.

### Create the Backstage OIDC client

In **Clients → Create client**, choose OIDC and client ID `backstage`.
Enable **Client authentication** and **Standard flow**. Disable implicit flow,
direct access grants, and service-account roles. Set the exact redirect URI to
`https://catalog.example.com/api/auth/oidc/handler/frame`, and web origin to
`https://catalog.example.com`. Ensure the profile/email client scopes expose the
approved claims in user-info. Copy the generated client secret from the
Credentials tab through the protected administrator channel.

The discovery URL is now:

```text
https://sso.example.com/realms/acmesecure/.well-known/openid-configuration
```

Run section 2's discovery checks from the host and existing Backstage container.
Both must succeed before continuing. Keep any client eligibility restriction
consistent with the directory filter and the catalog user policy.

## 5. Prepare the Backstage source revision

These changes are to the source checkout; review and commit them before the
release build. No application authentication code is changed just by installing
the runtime YAML. Start from the currently deployed revision and a clean tree:

```bash
cd /srv/acmesecure/repo
git status --short
git switch -c ldap-authentication
```

Define a helper that uses the existing Node 24 build image. This keeps native
dependencies on the correct VPS platform and preserves the checked-in Yarn:

```bash
build_shell() {
  sudo docker run --rm --init --user "$(id -u):$(id -g)" \
    --env HOME=/tmp --env NODE_OPTIONS=--max-old-space-size=4096 \
    --mount type=bind,src=/srv/acmesecure/repo,dst=/workspace \
    --workdir /workspace acmesecure-vps/build:node24 bash -euc "$1"
}
build_shell '
  cd backstage
  node .yarn/releases/yarn-4.13.0.cjs workspace backend add --exact @backstage/plugin-auth-backend-module-oidc-provider@0.4.22
  node .yarn/releases/yarn-4.13.0.cjs workspace app add --exact @backstage/core-app-api@1.20.6
'
```

In `backstage/packages/backend/src/index.ts`, retain the auth backend, replace
the Guest module registration with OIDC, and remove the stale Guest comment:

```ts
backend.add(import('@backstage/plugin-auth-backend'));
backend.add(import('@backstage/plugin-auth-backend-module-oidc-provider'));
```

Do not register a second OIDC implementation under the same provider ID. The
Guest package can remain in the lockfile, but the serving backend must no longer
register its provider. The final runtime config below also nulls the Guest
settings inherited from the base and VPS YAML files.

Install the new frontend-system module:

```bash
cp docs/deployment/examples/ldap/corporateSignIn.tsx.example \
  backstage/packages/app/src/modules/corporateSignIn.tsx
nano backstage/packages/app/src/App.tsx
```

Add this import and add `corporateSignIn` to the existing `features` array,
preserving the catalog, navigation, home, demo, and delivery modules:

```tsx
import { corporateSignIn } from './modules/corporateSignIn';

// Existing imports stay in place.
export default createApp({
  features: [
    catalogPlugin, navModule, homeModule, demoPlugin, deliveryPlugin,
    corporateSignIn,
  ],
});
```

The example module uses a custom auth API and `SignInPageBlueprint` for this
repository's **new frontend system**. It exposes only "Company account", with
no Guest fallback. Its backend provider ID is deliberately `oidc`, independent
of the button's branding. Legacy `createApp({ components: ... })` examples do
not match this application.

### Register the pilot User in the catalog

Start with one controlled catalog User; LDAP catalog synchronization is optional
and comes later. Replace this example with the pilot's **real** unique email:

```bash
cat > catalog/corporate-users.yaml <<'USERS'
apiVersion: backstage.io/v1alpha1
kind: User
metadata:
  namespace: corporate
  name: alice
spec:
  profile:
    displayName: Alice Example
    email: alice@company.example
  memberOf: []
USERS
nano catalog/all.yaml
```

Add `- ./corporate-users.yaml` to its existing `spec.targets`, retaining
`./org.yaml` and `./platform.yaml`. The deployment staging script already copies
the whole catalog directory, and the existing `/published/catalog/all.yaml`
location discovers the new file. Do not register a container path pointing back
to the host checkout.

The configured resolver looks up the verified IdP email in
`User.spec.profile.email`. It returns the full catalog identity, e.g.
`user:corporate/alice`; the username and email local part need not match.
Email must be unique across **all namespaces**, including fixture users. This
built-in resolver also retries a plus-address without its tag; use canonical
addresses and test aliases deliberately. It has no namespace-filter option.
If mail is mutable, reassignable, or ambiguous, agree an immutable issuer/subject
mapping and custom resolver before rollout. Keep User entity writes trusted;
the current allow-all permission policy is not a workforce authorization policy.
[Resolver behavior and identity model](https://backstage.io/docs/auth/identity-resolver/).

Do not enable `dangerouslyAllowSignInWithoutUserInCatalog` or add a fallback
resolver to get around a missing pilot User. A directory user without an
approved catalog mapping should fail sign-in in this design.

## 6. Install the final OIDC runtime layer

Keep secrets separate from the committed templates and the release's published
files. Create a root-only environment file:

```bash
sudo install -m 0600 /dev/null /etc/acmesecure/oidc.env
printf 'AUTH_SESSION_SECRET=%s\n' "$(python3 -c 'import secrets; print(secrets.token_hex(32))')" \
  | sudo tee /etc/acmesecure/oidc.env >/dev/null
sudo nano /etc/acmesecure/oidc.env
```

Retain the generated session secret and append these values in the editor,
substituting the exact discovery URL, client ID and secret supplied by the IdP:

```dotenv
AUTH_OIDC_METADATA_URL=https://sso.example.com/realms/acmesecure/.well-known/openid-configuration
AUTH_OIDC_CLIENT_ID=backstage
AUTH_OIDC_CLIENT_SECRET='REPLACE_WITH_THE_IDP_CLIENT_SECRET'
```

Single-quote literal values containing `$` or other Compose interpolation
characters. This is a Compose service `env_file`, not a shell script to source.
Do not overwrite this file on every release; keep the session secret stable
across normal restarts. Coordinate client-secret rotation with the IdP.

Copy the non-secret configuration templates:

```bash
sudo install -m 0644 docs/deployment/examples/ldap/app-config.oidc.yaml \
  /etc/acmesecure/app-config.oidc.yaml
sudo install -m 0600 docs/deployment/examples/ldap/compose.oidc.yaml \
  /etc/acmesecure/compose.oidc.yaml
```

The auth YAML sets `auth.environment: production`, a stable session secret,
`guest: null`, and `auth.providers.oidc.production` with one email resolver. It
loads **after** both existing Backstage config files. The third Compose file
loads the secret env file into the backend container and overrides its command
to load this final config. Supplying a host `--env-file` alone would not pass
those values into the container.

The generic OIDC provider already requests `openid profile email`. Do not add
the `scope` configuration key to it; use `additionalScopes` only for additional
provider-specific requirements. Both `app.baseUrl` and `backend.baseUrl` remain
the existing HTTPS Backstage origin.

## 7. Private CA trust, if needed

For a public-CA IdP such as the Caddy-hosted example, skip this section. For an
internal IdP, install its approved CA chain, readable by the non-root Node user:

```bash
sudo install -d -m 0755 /etc/acmesecure/pki
sudo install -m 0644 /PATH/TO/NETOPS-IDP-CA.pem /etc/acmesecure/pki/idp-ca.pem
sudo nano /etc/acmesecure/compose.oidc.yaml
```

Append the following **under the existing `services.backstage.volumes` list**:

```yaml
      - /etc/acmesecure/pki:/etc/ssl/corporate:ro
```

Append this line to `/etc/acmesecure/oidc.env` in the editor:

```dotenv
NODE_EXTRA_CA_CERTS=/etc/ssl/corporate/idp-ca.pem
```

Node reads the extra CA file at process startup, so recreate the container after
changing it. Keycloak's LDAP truststore and Node's IdP trust are separate. If
you later enable direct LDAP ingestion from Backstage, include that directory's
CA in the Node bundle too. Never use `NODE_TLS_REJECT_UNAUTHORIZED=0` or
`rejectUnauthorized: false` to bypass a trust failure.
[Node CA configuration](https://nodejs.org/api/cli.html#node_extra_ca_certsfile).

## 8. Build a candidate release and cut over

Take a verified backup using the first guide's process. Keep the Caddy allowlist
in place throughout. Save the old wrapper and environment before changing the
selected release:

```bash
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
sudo cp -p /usr/local/sbin/acme-compose "/etc/acmesecure/acme-compose.before-oidc-$STAMP"
sudo cp -p /etc/acmesecure/runtime.env "/etc/acmesecure/runtime.env.before-oidc-$STAMP"
git diff --check
git diff --stat
```

Review the source and lockfile changes, then commit the reviewed revision using
your normal Git workflow. Record that commit for the release. The identity
templates alone do not replace the source edits in section 5.

```bash
build_shell '
  ./scripts/setup.sh
  ./scripts/check-services.sh
  cd backstage
  node .yarn/releases/yarn-4.13.0.cjs tsc
  node .yarn/releases/yarn-4.13.0.cjs build:backend
'
export RELEASE_ID="$(date -u +%Y%m%dT%H%M%SZ)-$(git rev-parse --short HEAD)"
export RELEASE_DIR="/srv/acmesecure/releases/$RELEASE_ID"
export BACKSTAGE_ORIGIN='https://catalog.example.com'
umask 022
python3 deploy/vps/prepare-public-files.py "$RELEASE_DIR" "$BACKSTAGE_ORIGIN"
git rev-parse HEAD > "$RELEASE_DIR/source-commit.txt"
```

Preserve the database password while preparing a candidate runtime file:

```bash
set -o pipefail
sudo sed -e "s|^RELEASE_ID=.*|RELEASE_ID=$RELEASE_ID|" \
  -e "s|^RELEASE_DIR=.*|RELEASE_DIR=$RELEASE_DIR|" \
  /etc/acmesecure/runtime.env \
  | sudo tee /etc/acmesecure/candidate.env >/dev/null
sudo chmod 0600 /etc/acmesecure/candidate.env
sudo docker compose -p acmesecure-vps --env-file /etc/acmesecure/candidate.env \
  -f compose.yaml -f deploy/vps/compose.vps.yaml \
  -f /etc/acmesecure/compose.oidc.yaml config --quiet
sudo docker compose -p acmesecure-vps --env-file /etc/acmesecure/candidate.env \
  -f compose.yaml -f deploy/vps/compose.vps.yaml \
  -f /etc/acmesecure/compose.oidc.yaml build
```

Validate the **merged Backstage configuration inside the build helper**, where
the new provider's config schema is installed. Use dummy secrets and no sign-in
traffic; validation does not contact the identity provider:

```bash
build_shell '
  cd backstage
  AUTH_SESSION_SECRET=validation-only \
  AUTH_OIDC_METADATA_URL=https://sso.example.com/realms/acmesecure/.well-known/openid-configuration \
  AUTH_OIDC_CLIENT_ID=backstage AUTH_OIDC_CLIENT_SECRET=validation-only \
  BACKSTAGE_ORIGIN=https://catalog.example.com POSTGRES_PASSWORD=validation-only \
  node .yarn/releases/yarn-4.13.0.cjs backstage-cli config:check \
    --config app-config.yaml \
    --config ../deploy/vps/app-config.vps.yaml \
    --config ../docs/deployment/examples/ldap/app-config.oidc.yaml
'
```

Once builds/configuration checks pass, make the wrapper always include the new
third Compose layer. Future releases and backup commands must use this wrapper:

```bash
sudo tee /usr/local/sbin/acme-compose >/dev/null <<'WRAPPER'
#!/bin/sh
set -eu
exec docker compose \
  --project-directory /srv/acmesecure/repo \
  --project-name acmesecure-vps \
  --env-file /etc/acmesecure/runtime.env \
  -f /srv/acmesecure/repo/compose.yaml \
  -f /srv/acmesecure/repo/deploy/vps/compose.vps.yaml \
  -f /etc/acmesecure/compose.oidc.yaml "$@"
WRAPPER
sudo chmod 0755 /usr/local/sbin/acme-compose
sudo cp -p /etc/acmesecure/candidate.env /etc/acmesecure/runtime.env
sudo /usr/local/sbin/acme-compose up -d --no-build --pull never
sudo /usr/local/sbin/acme-compose logs --tail=150 backstage
curl --fail --show-error http://127.0.0.1:7007/.backstage/health/v1/readiness
```

This recreates containers as required and can briefly interrupt this project.
Do not use only `restart` after changing Compose environment or mount settings.
For subsequent releases, add `-f /etc/acmesecure/compose.oidc.yaml` to the first
guide's candidate validation/build commands, and preserve the updated wrapper.
The staged base VPS file may still contain its old Guest settings; the final
OIDC config overrides them, and the new backend no longer registers Guest.

## 9. Acceptance checks

Open a **new private browser window** from an allowlisted address. Clear old
Guest state by using this new session rather than relying on a previously open
tab. Test the complete flow:

1. Backstage offers "Company account" and no Guest button.
2. Sign-in redirects/popups go to the expected IdP hostname and realm.
3. The pilot's real LDAP credentials work, and a wrong password fails at the IdP.
4. Backstage returns to its exact HTTPS origin without redirect loops.
5. User settings show the intended identity, such as `user:corporate/alice`,
   rather than `user:default/guest`.
6. Catalog, TechDocs, search, `/demo`, and `/delivery` work with the new identity.
7. A second approved user resolves to a distinct catalog User.
8. A valid directory user missing from the approved catalog registry fails
   Backstage resolution. An ineligible user fails the IdP's application policy.
9. A disabled pilot account cannot obtain a **new** IdP login; test existing
   session behavior separately as described in section 11.

Check API access directly on the VPS without an existing browser cookie/token:

```bash
curl -sS -o /dev/null -w '%{http_code}\n' http://127.0.0.1:7007/api/catalog/entities
curl -sS -o /dev/null -w '%{http_code}\n' \
  -H 'X-Requested-With: XMLHttpRequest' http://127.0.0.1:7007/api/auth/guest/refresh
```

The catalog request should be **401**, and Guest refresh must not mint a token
(normally 404 after removing the provider). A 200 Guest refresh is a failed
cutover even if the Guest button disappeared. Test from an unallowlisted network
that the existing Caddy gate still returns 403.

The Customer Portal is a separate FastAPI application: it **does not acquire
LDAP sign-in** through these Backstage changes. Keep its current access policy.
The second hosted project likewise keeps its own authentication and routing.
Do not add basic auth on Backstage's API routes, because its bearer tokens also
use the Authorization header.

## 10. Optional — synchronize LDAP Users and Groups into Backstage

A controlled file registry is sufficient for the pilot. For larger directories,
use either your existing org-data integration or the upstream LDAP catalog
provider. This requires Backstage itself to reach LDAP and to possess a separate
read-only bind credential; Keycloak federation does not create catalog entities.

Install the release-compatible module through `build_shell`:

```bash
build_shell '
  cd backstage
  node .yarn/releases/yarn-4.13.0.cjs workspace backend add --exact @backstage/plugin-catalog-backend-module-ldap@0.12.10
'
```

Add next to the existing catalog backend registration:

```ts
backend.add(import('@backstage/plugin-catalog-backend-module-ldap'));
```

Merge a provider block into the final auth/config layer or another explicitly
loaded final config. This example is for a directory with `uid` users and
`groupOfNames` groups; it is **not an AD filter**:

```yaml
catalog:
  providers:
    ldapOrg:
      corporate:
        target: ${LDAP_URL}
        bind:
          dn: ${LDAP_BIND_DN}
          secret: ${LDAP_BIND_PASSWORD}
        users:
          - dn: ${LDAP_USERS_DN}
            options:
              scope: sub
              filter: '(&(objectClass=inetOrgPerson)(mail=*))'
              paged: { pageSize: 500, pagePause: true }
            map:
              rdn: uid
              name: uid
              displayName: cn
              email: mail
              memberOf: memberOf
            set:
              metadata.namespace: corporate
        groups:
          - dn: ${LDAP_GROUPS_DN}
            options:
              scope: sub
              filter: '(objectClass=groupOfNames)'
              paged: { pageSize: 500, pagePause: true }
            map:
              rdn: cn
              name: cn
              displayName: cn
              members: member
            set:
              metadata.namespace: corporate
        schedule:
          frequency: { minutes: 15 }
          timeout: { minutes: 10 }
```

Put all of the `LDAP_*` connection/search values in the
root-only `/etc/acmesecure/oidc.env`, which already feeds the backend container.
Use `ldaps://...` here and configure the Node CA bundle as in section 7. This
sample does not implement StartTLS client options; if NetOps mandates StartTLS,
verify support/configuration against the selected LDAP provider instead of
silently using a plaintext bind. Ask NetOps for scoped, enabled/eligible-user
filters rather than importing an entire company directory by default.

For AD, confirm `sAMAccountName`, the correct RDN/UUID behavior, eligible-user
and disabled-account filters, `member`/`memberOf`, and nested groups against the
actual schema. Do not assume changing only the connection URL is sufficient.
Keep the provider ID `corporate` stable once it owns entities. Users and groups
in the same provider can be related through their directory DNs; inspect the
resulting `memberOf` relations, especially across namespaces and nested groups.

Before switching ownership from files to LDAP, back up and remove
`corporate-users.yaml` from `catalog/all.yaml` and the staged catalog, and let
the old file-owned entities be removed/orphan-cleaned. Coordinate the pilot's
brief mapping gap. Do not let both providers claim the same full entity ref or
create duplicate emails. Preserve the pilot's agreed entity ref where possible.
Repeat the build, staged release, schema validation and acceptance checks.
Wait for ingestion before retrying sign-in. LDAP import is asynchronous, so
fresh accounts may not resolve immediately.

Corporate groups live in a different namespace from the default demo teams.
Directory membership does not automatically make a person the owner of a demo
service or grant an administrator role. Reconcile ownership deliberately and
implement a permission policy before relying on groups for authorization.

## 11. Operations, backups, offboarding and recovery

### Ownership of the running integration

Record who operates the IdP/LDAP connection, who can change User mappings, and
who rotates the OIDC client and directory-reader credentials. Monitor discovery,
token exchange failures, directory sync age, certificate expiry, and failed
logins without logging passwords or tokens. The existing Backstage allow-all
policy still allows broad actions by authenticated users; replacing Guest
establishes identity, but does not implement roles or catalog-write restrictions.

The source change also replaces the local frontend's sign-in screen. If you
need native local development, configure a separate development OIDC client,
callback and `auth.environment`; do not add the live client secret to Git or
re-enable Guest in the deployed final config.

### Sessions and offboarding

Disabling an LDAP account, removing a catalog User, or disabling Guest does not
retroactively invalidate every token already issued. Backstage tokens, provider
refresh cookies, IdP sessions, caches, and LDAP sync have different lifetimes.
Set and test the permitted revocation delay with NetOps. For an offboarding
exercise, revoke IdP sessions, remove application eligibility/catalog mapping,
and check both a fresh login and an existing Backstage session over the agreed
expiry window. A container restart or rotating `AUTH_SESSION_SECRET` alone is
not a universal user-token revocation mechanism. Keep the network gate during
cutover and until old Guest tokens can no longer be used.

### Back up identity state

`/etc/acmesecure/oidc.env`, the final config, and the updated wrapper are already
inside the first guide's backup paths. Verify their inclusion and keep the
required decryption/recovery credentials outside the VPS. If Path A uses an
existing IdP, confirm NetOps backs up its application/client/federation state.

For Path B, the original backup does **not** include Keycloak's separate
database or `/etc/acme-identity`. Add a consistent dump of its single database
to the root backup script **before `restic backup`**:

```bash
sudo install -d -m 0700 /var/backups/acme-identity
sudo nano /usr/local/sbin/acme-backup
```

Insert these commands in that root script (its existing `set -euo pipefail` and
`umask 077` apply):

```bash
/usr/local/sbin/identity-compose exec -T database \
  pg_dump -U keycloak -d keycloak -Fc > /var/backups/acme-identity/latest.dump.tmp
test -s /var/backups/acme-identity/latest.dump.tmp
mv /var/backups/acme-identity/latest.dump.tmp /var/backups/acme-identity/latest.dump
```

Extend the same Restic invocation to include
`/var/backups/acme-identity/latest.dump`, `/etc/acme-identity`,
`/srv/acme-identity`, and `/usr/local/sbin/identity-compose`. A PostgreSQL dump
of this one database is consistent while Keycloak runs. Retain the pinned image,
custom themes/providers if added, CA material, client secrets, database password,
realm keys, and administrator recovery information. A realm export alone is not
a replacement for database backup. Reapply this backup extension if you replace
the original backup script during a future deployment.

Run the updated backup, inspect its status/snapshot, and rehearse restoration
to an isolated identity stack. Restore the custom-format dump to a fresh matching
PostgreSQL database with `pg_restore --exit-on-error --no-owner`, using the
Keycloak database role as owner, **before** starting the test Keycloak instance.
Use an isolated test hostname/client/callback to exercise restored sign-in;
never restore over the running identity database as a test.

### Rollback and lockout recovery

Keep SSH/sudo and the previous source revision, tagged images, env file and
wrapper backup. For an IdP problem, leave Backstage unavailable to new sign-ins
while correcting the IdP, secret, CA, mapping or network configuration. Do not
quietly enable Guest as a fallback to a failed corporate login.

If reverting the source release, also restore its matching runtime selection,
wrapper and auth layer as a coordinated change. An old Guest-enabled release
reopens token issuance to anyone allowed through Caddy; use it only as an
explicit, temporary protected maintenance decision. Image rollback must respect
any database migrations as in the original guide. Do not delete Backstage or
Keycloak database volumes to fix a configuration error, and do not change the
other hosted project's Compose project or proxy routes.

## 12. Troubleshooting and completion criteria

| Symptom | Likely checks |
| --- | --- |
| No company sign-in button | Frontend module imported and added to features; new image built/served; fresh browser session |
| "Unknown auth provider" / OIDC 404 | Correct backend module included and registered; ID `oidc` on frontend and backend |
| LDAP login works but Backstage says email missing | User-info `email_verified` is true, `email` exists, correct email/client-scope mappers |
| Cannot resolve user identity | User ingested, exact canonical mail, no duplicate emails, correct entity namespace and mapping |
| Redirect URI rejected | Exact HTTPS callback, correct client/realm, matching `BACKSTAGE_ORIGIN` |
| Invalid client / token endpoint 401 | Client authentication enabled, correct secret, client-auth method supported |
| Discovery works on host but fails in Backstage | Container DNS/VPN/routing, Caddy's seen source IP, private CA mount and Node trust |
| Callback returns Caddy 403 | Browser's IPv4/IPv6/VPN egress still matches the catalog allowlist |
| LDAPS trust or hostname error | CA chain mounted into Keycloak/Node as appropriate, certificate SAN matches directory hostname |
| Keycloak can't bind, or syncs zero users | Bind account rights/password, exact bases/filter, schema/attributes, test from its container network |
| Logged-in user still has broad powers | Existing allow-all policy; authentication and permission policy are separate work |
| Guest still signs in | Guest backend registration removed, final YAML loaded last with `guest: null`, correct new image recreated |

Complete the integration only after both positive and negative login cases pass,
the full catalog/docs/Jira flow works under a real user identity, and identity
state can be restored. Until NetOps supplies the actual directory/IdP values,
these templates and checks are the implementation plan; no live directory
connection or end-to-end LDAP login has been verified by this repository change.
