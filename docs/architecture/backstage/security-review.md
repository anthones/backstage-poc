# Backstage: OpSec review

[Overview](README.md) · [Terms](../../../CONTEXT.md)

**Status: Proposed. Review date: 2026-11-19. Owner: OpSec; named reviewer pending.**

Backstage will copy service metadata and documentation into a private portal.
Broad internal sharing is an intended benefit, even when source repositories have narrower access.
The main risk is publication outside OpSec boundaries, including sensitive content that does not belong in TechDocs.

## Decisions required

1. Approve the identity authority, user mapping and access-removal target.
2. Decide broad internal readership, content classifications and any exceptions.
3. Approve backend permissions, service credentials, secret storage and rotation.
4. State approval conditions and the evidence InfraOps must supply after provisioning.

Record decisions in [D-04, D-06, D-07, D-10 and D-13](decision-log.md).
Only explicit OpSec approval gates InfraOps allocation. This document starts assessment; it is not the final design.
InfraOps must stay within the approved boundaries; exceeding them requires revised OpSec approval first.
Implementation tests follow allocation and must meet OpSec conditions before user access.

## Controls for the new upstream installation

After OpSec approval, InfraOps selects an upstream release and enables only the required modules.
Configure real user sign-in and explicit read/admin permissions before granting access.
Authentication alone does not establish the required authorization policy. Verify every enabled plugin and backend route.

Proposed Design: private access, trusted users, broad internal reads and explicit admin permissions, subject to OpSec policy.
Exclude privileged automation and write-capable integrations. See [RFC-001](RFC-001-backstage-architecture.md) for scope and the fresh upstream installation basis.

## Assets and access policy

Treat metadata, internal URLs, API descriptions and documentation as internal information until owners classify them.
Search indexes, snippets, caches and backups inherit the source content's classification. Protect identity data, logs and secrets separately.
OpSec must map these categories to company policy.

| Actor                           | Permitted access                                                                                              |
| ------------------------------- | ------------------------------------------------------------------------------------------------------------- |
| Anonymous or unmapped user      | No private catalog, documents or APIs. Review public auth, health and UI assets explicitly.                   |
| Admitted employee               | Read internally published content under OpSec policy. No admin or privileged actions without a separate role. |
| Domain owner                    | Maintain source metadata/docs through reviewed merge requests; catalog administration requires designation.   |
| Catalog admin                   | Authorized InfraOps, NetworkOps and OpSec admins may manage the full catalog.                                 |
| Domain catalog admin            | Designated lead; registration within the lead’s domain only when enforced. Otherwise, use central admins.     |
| Identity administrator/provider | Change trusted User/Group records and membership.                                                             |
| CI publisher                    | Publish only its assigned document prefix. No catalog or infrastructure administration.                       |

Enforce controls in backend APIs. If a feature lacks suitable permission checks, omit it.
Only trusted identity sources may define User/Group entities. A service repository must not grant group membership.
Test registration and management permissions against the selected release. Do not assume it provides a complete domain-admin role.
Only let domain leads register entries when restrictions to their domain are practical and tested. Otherwise, use central catalog admins.
Admins authorize project/entity/team/prefix mappings; publisher credentials must follow that trusted mapping, not editable metadata alone.
Catalog admin rights do not grant control of identities, credentials or infrastructure.

Private repository permissions do not protect published copies automatically.
Validate how the selected release enforces the intended read policy across catalog, TechDocs and search.
Test metadata, assets, shared-document references, search snippets and caches with allowed and denied users.
Keep document storage private. TechDocs includes only material intended for Backstage; other material stays outside its sources.
Domain teams verify generated sites against this publication boundary. OpSec sets security exclusions and the permitted audience. [Permission setup](https://backstage.io/docs/permissions/getting-started/), [upstream references](official-source-notes.md)

## Content withdrawal

InfraOps chooses how to withdraw published content when it no longer meets OpSec policy.
The method must stop access and republication. It must cover search/caches and prevent restored copies from exposing withdrawn content.
OpSec sets security and retention boundaries. InfraOps selects the mechanism, response target and recovery checks.

## Human sign-in and access removal

GitLab OAuth is the candidate. Confirm employee lifecycle, MFA, contractors and group ownership before choosing it as the identity authority.
An existing corporate OIDC provider or approved authenticating proxy is an alternative.
OAuth support alone does not establish OIDC claim handling.

Use one reviewed resolver to map the GitLab host and stable user ID to one catalog User.
Reject unknown or duplicate mappings. Test renamed/recreated accounts, group changes and unverified email addresses.
Define nested/shared group rules and synchronization frequency. [GitLab provider and resolvers](https://backstage.io/docs/auth/gitlab/provider/)

Proposed access-removal target: 30 minutes after account suspension or approved group removal.
Test existing Backstage tokens, provider sessions, cached membership and GitLab outages.
GitLab logout alone does not prove immediate portal revocation. Approve a workable mechanism or revise the target before granting user access.

## Credentials and secrets

Use an existing approved secret service or encrypted deployment mechanism; availability remains unconfirmed.
Keep secrets out of Git, images, frontend configuration, artifacts and logs.
Assign a named owner and deputy for each credential. Prefer short-lived credentials where supported.

The table lists scope, storage, replacement rules, owner and the effect of credential theft. Runtime secrets use the selected secret service; CI secrets use protected jobs.
Infrastructure keys use the approved infrastructure/backup secret store.
Proposed service-secret rotation: at most 90 days, before expiry and immediately after suspected exposure.
Owners must test replacement, old-key denial and emergency revocation. OpSec must approve exceptions.

| Credential                   | Scope                                | Storage / lifecycle                                                  | Owner                     | Compromise impact                       |
| ---------------------------- | ------------------------------------ | -------------------------------------------------------------------- | ------------------------- | --------------------------------------- |
| GitLab OAuth secret          | Sign-in app and exact callback       | Runtime secret store; coordinated client replacement                 | InfraOps/identity admin   | Authentication-flow abuse               |
| User/provider tokens         | Minimum identity scopes              | Session/browser/backend state: verify storage, expiry and revocation | Identity/app owner        | User impersonation                      |
| Backend signing/session keys | Token/session protection             | Selected keystore: pending; supported rotation and recovery          | InfraOps/app owner        | Multiple-user impersonation             |
| GitLab repository reader     | Approved groups/projects; read only  | Runtime secret store; expire/replace and test discovery              | InfraOps/GitLab admin     | Readable source disclosure              |
| GitLab organization reader   | Required users/groups only           | Runtime secret store; replace and test membership sync               | Identity/GitLab admin     | Identity disclosure or false membership |
| Jira PAT, if approved        | Approved issue reads; no write/admin | Runtime secret store; expire/replace, test denied access             | Jira owner                | Issue disclosure/misuse                 |
| Runtime storage key          | Required read/list only              | Runtime secret store; replace and test denied writes                 | InfraOps/storage owner    | Published-content disclosure            |
| CI publisher key             | Assigned entity prefix               | Protected CI secret or short-lived identity; expire/replace          | Domain CI/storage owner   | Document replacement/deletion           |
| Database credential          | App state/migrations; no superuser   | Runtime secret store; coordinate database/pool replacement           | Database operator         | App-state/identity compromise           |
| Registry push identity       | CI image namespace                   | Protected CI secret; expire/replace and test push                    | Build owner               | Malicious image publication             |
| Registry pull identity       | Runtime image reads                  | Runtime-host secret store; expire/replace and test pull              | InfraOps                  | Image disclosure                        |
| Tunnel key, if needed        | Approved peers/routes                | Infrastructure secret store; network key lifecycle                   | InfraOps/network operator | Routed-network access                   |
| Backup service credential    | Required backup/restore              | Isolated backup secret store; replace and test restore               | InfraOps                  | Backup disclosure/destruction           |
| Backup encryption key        | Approved backup set                  | Separate key custody; rotation must retain required restore keys     | InfraOps                  | Backup disclosure or unrecoverable data |
| Deployment/admin identity    | Required operational access          | Approved admin system; review/expire/revoke access                   | InfraOps                  | Runtime compromise                      |
| Log/metrics agent identity   | Required collection only             | Agent secret store; expire/replace and verify collection             | InfraOps                  | Sensitive-log disclosure                |

Compare group/project tokens with a dedicated GitLab service account. Confirm GitLab version, licensing, token selection and effective permissions.
Do not use an employee's long-lived PAT or grant repository writes to simplify discovery.

Jira links suffice initially. Before API use, select a compatible plugin/connector and test the installed Data Center version.
Jira PATs inherit account permissions; they are not inherently read-only.
Test issue security, pagination and the readership of returned summaries. [Atlassian PAT guidance](https://confluence.atlassian.com/enterprise/using-personal-access-tokens-1026032365.html)

## Required technical controls

- Review each plugin's maintainer, version, routes, permissions and credentials. Plugins in one backend share its trust boundary.
- Lock dependencies and image digests. Scan dependencies, secrets and images; record the software bill of materials.
- Rebuild and test the selected application after dependency or base-image changes.
- Isolate untrusted merge-request builds from protected publication jobs. Scope each publisher to its assigned prefix.
- Use non-root containers, resource limits and limited temporary storage. Exclude privileged containers, host sockets and unused cluster credentials.
- Restrict URL readers, catalog substitutions and redirects. Test metadata addresses, loopback, encoded URLs and DNS changes.
- Apply fixed proxy targets, permitted methods, timeouts and request limits. A shared credential must not expose arbitrary upstream requests.

Use the [network connection table](network-review.md) for permitted traffic. Confluence ingestion and privileged automation remain outside scope.

## Threat and risk table

Severity is an estimate. Residual risk means the risk after controls pass. OpSec has accepted none.
All rows are Proposed. Owners are teams until named reviewers accept responsibility.

| ID   | Threat                                       | Severity | Required control                                          | Owner               | Residual risk                           |
| ---- | -------------------------------------------- | -------- | --------------------------------------------------------- | ------------------- | --------------------------------------- |
| S-01 | Guest/allow-all access                       | Critical | Remove defaults; test backend denials                     | Platform            | Medium: policy defects                  |
| S-02 | Publication outside permitted readership     | High     | OpSec audience/exceptions; docs/search/cache access tests | Domain/InfraOps     | Medium: classification errors/downloads |
| S-03 | Forged user or group                         | Critical | Trusted identity source; stable mapping                   | Identity/Platform   | Low–Medium: source compromise           |
| S-04 | Access remains after suspension              | High     | Prove agreed removal window                               | Identity/Platform   | Medium until proven                     |
| S-05 | Source/API token theft                       | High     | Narrow rights; secret rotation                            | Integration owners  | Medium: readable data exposed           |
| S-06 | SSRF/placeholder source reads                | High     | URL restrictions and network egress controls              | Platform/NetworkOps | Medium: permitted endpoints             |
| S-07 | Malicious dependency/plugin                  | Critical | Small plugin set; controlled builds/patches               | Platform/OpSec      | Medium: trusted runtime code            |
| S-08 | CI overwrites documents                      | High     | Protected jobs; prefix permissions; restore               | Domain/InfraOps     | Medium: own-site modification           |
| S-09 | Data/backup loss or exposure                 | High     | Private access; encrypted independent backup              | InfraOps            | Low–Medium after restore test           |
| S-10 | Ingress/TLS/proxy bypass                     | High     | Private ingress; trusted headers; CA tests                | NetworkOps/Platform | Low–Medium: device compromise           |
| S-11 | Jira issue disclosure                        | High     | Links first; access/compatibility tests before API        | Jira owner          | Low for links; Medium for API           |
| S-12 | Unapproved privileged action                 | Critical | Omit deferred modules/routes/credentials                  | Platform            | Low if absent                           |
| S-13 | Exhaustion or dependency outage              | Medium   | Limits, timeouts and failure tests                        | Platform/InfraOps   | Medium: pilot single-instance outage    |
| S-14 | Secret/content disclosure in retained copies | High     | Redaction, retention, deletion controls                   | Platform/InfraOps   | Medium: historical copies               |
| S-15 | Compromised backend reaches other systems    | Critical | Narrow credentials/egress; isolated management            | InfraOps/NetworkOps | Medium–High: centralized readable data  |

## Audit, patching and incident response

Record sign-in outcomes, permission denials, catalog/identity changes, publications, releases, secret changes and administrative access.
Include actor, resource, result, timestamp and request ID. Exclude tokens and content bodies.
Verify audit support; ordinary application logs may not cover these events.

Proposed log retention: 30 days searchable, 90 days restricted archive, subject to company policy.
Alert on access failures, unexpected traffic, expired credentials, stale discovery, publication errors and backup failures.

Platform handles application incidents. NetworkOps isolates traffic. InfraOps preserves/rebuilds systems. OpSec directs evidence and breach assessment.
Revoke exposed credentials, assess all readable content, restore trusted state and repeat access tests before reopening.

Proposed patch targets: assess exploited/critical flaws within one business day; fix or isolate within 72 hours.
Address high-severity flaws within 14 days. Review routine dependencies monthly. OpSec must approve targets and staffing.

**Before allocation:** OpSec records approval or requested changes, audience rules, credential constraints and implementation conditions.
**After provisioning:** InfraOps supplies identity/access tests, rotation tests and evidence for accepted risks before user access.
Confirm secret-service availability and support coverage. Record signatories, conditions and review dates in the decision log.
