# KiwiTCMS: Official references

[Overview](README.md)

**Reference review date: 2026-11-19. No application release, image or identity integration is selected.**

These sources support a fresh installation after explicit OpSec approval.
Online documentation and upstream development code change. InfraOps must verify behavior against the release selected for implementation.
The reported development experiment is not production, security or capacity evidence.

## Production, editions and image selection

Upstream requires a containerized production environment. Its Compose example is a starting point, not a complete production design.
The Community example uses MariaDB and separate persistent volumes for database data and uploads.
The guide also covers settings overrides and downstream images. It discourages changing the upstream Dockerfile or deploying development branches.
[Production and customization guide](https://kiwitcms.readthedocs.io/en/latest/installing_docker.html)

The public Community image follows a rolling release. Subscribers can obtain version-tagged images.
InfraOps must preserve an approved image digest or reproducible source build for controlled upgrades and rollback.
Select a released source version, reviewed changes and a supported production container if building internally.
[Container distribution](https://kiwitcms.org/containers/)

The feature matrix lists Community code under GPL-2.0+ and Enterprise under AGPL-3.0+.
Record the licenses and support terms for every selected component; no commercial subscription is selected by this proposal.
[Edition matrix](https://kiwitcms.org/features/)

## Privacy and external dependencies

Upstream documents `ANONYMOUS_ANALYTICS=False` as its analytics opt-out.
Development-server behavior differs from production; absence of requests during development does not establish the production configuration.
[Official analytics guidance](https://kiwitcms.org/blog/kiwi-tcms-team/2024/02/23/anonymous-analytics-via-plausibleio/)

The upstream base template places Plausible and Scarf requests behind that analytics condition.
It separately loads Crowdin translation resources for the Esperanto language code.
Disabling analytics therefore does not prove removal of the translation CDN.
Inspect browser traffic across supported languages and verify operation without external access.
[Base template](https://raw.githubusercontent.com/kiwitcms/Kiwi/master/tcms/templates/base.html)

Advertising uses a separate EthicalAds template include. The reviewed include does not use the analytics flag.
Assess a reviewed template override or an appropriate supported image; hiding ads visually does not prevent network requests.
[Advertising template](https://raw.githubusercontent.com/kiwitcms/Kiwi/master/tcms/templates/include/ads.html), [template override guidance](https://kiwitcms.org/blog/tags/customization/)

Kiwi TCMS also calls its internal test-reporting area “Telemetry.” This includes execution dashboards and test-case health reports.
That application feature is distinct from external usage analytics.
Removing the reporting module can remove the visibility this platform is intended to provide.
[Upstream reporting navigation](https://raw.githubusercontent.com/kiwitcms/Kiwi/master/tcms/settings/common.py)

## Registration, activation and authentication

The configuration reference exposes `REGISTRATION_ENABLED`, `USE_CAPTCHA` and `AUTO_APPROVE_NEW_USERS`.
It documents admin-created accounts when registration is disabled, and manual approval when automatic approval is disabled.
Prefer that controlled account path over an unverified self-registration shortcut.
[Configuration reference](https://kiwitcms.readthedocs.io/en/latest/configuration.html)

The registration view treats email confirmation and administrator activation as different paths.
Disabling email delivery alone does not establish a complete account-provisioning or recovery process.
Test registration GET/POST requests, account activation, password recovery and offboarding using the selected release.
[Registration implementation](https://raw.githubusercontent.com/kiwitcms/Kiwi/master/tcms/kiwi_auth/views.py)

Enterprise bundles OAuth and LDAP add-ons, including GitLab login examples.
Do not assume a Community installation already provides the same identity integration.
Assess approved add-ons, their licenses and maintenance costs before promising SSO.
[Enterprise capabilities](https://kiwitcms.org/blog/kiwi-tcms-team/2025/08/28/enterprise-subscription-explained/)

## Permissions and record integrity

The default Tester group has broad resource permissions; upgrades can reset the built-in groups.
Use reviewed custom groups. Normal staff-panel access does not mean superuser authority.
Object permissions do not protect API operations, and global permissions override object restrictions.
Deactivate departed users; deletion can remove related records.
[Administration and permission limits](https://kiwitcms.readthedocs.io/en/latest/admin.html)

Case history and execution records support traceability. Current upstream code records the case-text history version when creating an execution.
Test that earlier results remain understandable after case edits, cloning and migration.
These features do not establish the company's release-approval process.
[Case history](https://raw.githubusercontent.com/kiwitcms/Kiwi/master/tcms/testcases/models.py), [execution records](https://raw.githubusercontent.com/kiwitcms/Kiwi/master/tcms/testruns/models.py)

## Persistence, recovery and optional connectors

Back up both the database and uploaded evidence. A database-only restore does not restore attachment files.
The upstream backup article illustrates both data sets; validate a consistent backup and restore method for the selected release.
[Database and upload backups](https://kiwitcms.org/blog/atodorov/2018/07/30/how-to-backup-docker-volumes-for-kiwi-tcms/)

The bug-tracker model can store API credentials in the application database as plaintext fields.
If a connector is approved later, treat database access and backups as credential exposure paths.
Use links initially; assess the connector, secret handling and Jira permissions before enabling API access.
[Bug-tracker credential model](https://raw.githubusercontent.com/kiwitcms/Kiwi/master/tcms/testcases/models.py)

Production also needs explicit `DEBUG=False`, a unique secret, permitted hostnames, verified TLS and tested session controls.
None of the proposed configuration changes proves the resulting installation is production-ready.
[Production settings](https://kiwitcms.readthedocs.io/en/latest/configuration.html)
