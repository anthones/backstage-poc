# Backstage: Decisions

[Overview](README.md) · [Terms](../../../CONTEXT.md)

**Status: Proposed. Review date: 2026-11-19. OpSec approval and provisioning remain pending.**

Read [RFC-001](RFC-001-backstage-architecture.md) for the proposal.
Review criteria belong to [Network requirements](network-review.md), [OpSec](security-review.md) and [InfraOps](infrastructure-requirements.md).
Each proposed team owner must nominate an accountable person and deputy.

## States

- **Proposed:** awaits review and evidence.
- **Under Review:** the named reviewer has started assessment.
- **Approved:** the authorized owner has recorded evidence, conditions, signature and date.
- **Rejected:** the owner has recorded a reason and alternatives.
- **Deferred:** outside the current scope; reopening requires review.

InfraOps needs explicit OpSec approval before it allocates resources. InfraOps owns and may adapt the final design.
NetworkOps supports InfraOps as needed; it is not a separate proposal approval gate.
A documentation merge is not OpSec approval. InfraOps must stay within the approved security boundaries.
Changes beyond those boundaries require revised OpSec approval before implementation.

## Proposal direction

These directions define the proposal. OpSec and operational approval remain pending:

- This pack starts adoption through a fresh upstream open-source installation after OpSec approval.
- InfraOps selects a supported release at implementation time. No application version or final infrastructure design is prescribed.
- Prefer broad internal catalog/document readership, independently of source-repository access. OpSec decides the permitted audience and exceptions.
- Backstage supports incident work. Separate monitoring, observability and AWX/Ansible handle detection and response.
- Continuous availability is intended. The uptime target and support coverage remain open.
- Authorized InfraOps, NetworkOps and OpSec admins may manage the full catalog.
- Domain leads may add only their own domain entries when restrictions are practical to enforce.
- Otherwise, catalog administration stays with InfraOps and its designated supporting admins.
- TechDocs contains only documentation intended for Backstage. Other material stays outside its sources.
- InfraOps selects content-withdrawal and recovery mechanisms within OpSec policy.
- InfraOps cannot cross approved security boundaries; changes beyond them require revised OpSec approval first.

Use [Terms](../../../CONTEXT.md) for the agreed language.
The [publication-policy ADR](../../adr/0001-backstage-publication-audience.md) records the reason for wider readership; OpSec approval remains pending.

## Outstanding decisions

All rows are **Proposed**, except D-16, which is **Deferred**.
The owner column identifies the accountable team; the other teams must review their affected controls.
Detailed tests and approval conditions remain in the linked reviews.

| ID   | Choice / alternatives                                           | Reason or evidence needed                                                                           | Owner                  | Other affected teams                        |
| ---- | --------------------------------------------------------------- | --------------------------------------------------------------------------------------------------- | ---------------------- | ------------------------------------------- |
| D-01 | Fresh upstream OSS installation after approval                  | InfraOps selects the release and validates it under OpSec conditions                                | InfraOps               | Sponsor, domains, OpSec                     |
| D-02 | Existing Kubernetes / Proxmox VM / VPS / hybrid                 | InfraOps selects/adapts the design within OpSec conditions                                          | InfraOps               | NetworkOps as needed, OpSec, Platform       |
| D-03 | Private access and selected network design                      | InfraOps completes flows and tests; NetworkOps supports as needed                                   | InfraOps               | NetworkOps, OpSec                           |
| D-04 | GitLab OAuth / corporate OIDC / approved proxy                  | Confirm identity authority, scopes, stable mapping and access removal                               | Identity admins        | OpSec, GitLab admins, Platform              |
| D-05 | Existing durable store / S3-compatible / shared filesystem      | Prove compatibility, permissions, durability and restore                                            | InfraOps storage       | NetworkOps, OpSec, Platform                 |
| D-06 | Broad internal TechDocs reads under OpSec boundaries            | Only intended Backstage content enters TechDocs; InfraOps chooses withdrawal controls               | OpSec                  | Domain leads, InfraOps, identity admins     |
| D-07 | Existing secret service / approved encrypted mechanism          | Confirm availability, named credential owners, expiry and rotation tests                            | OpSec/InfraOps         | Platform, integration admins                |
| D-08 | Jira links / reviewed read API later                            | Confirm need, installed server/plugin versions and issue-security behavior                          | Jira owner             | OpSec, Platform, users                      |
| D-09 | Continuous availability; resilience/support tier pending        | InfraOps selects service targets; validate pilot first and 250+ sites before expansion              | InfraOps               | Sponsor, users, Platform                    |
| D-10 | Central admins / restricted registration for designated leads   | Infra/Net/OpSec catalog admins; fallback to InfraOps/supporting admins if delegation is difficult   | InfraOps               | Domain leads, GitLab/identity admins, OpSec |
| D-11 | Nightly backup / point-in-time recovery and added resilience    | Agree RPO/RTO, retention, key custody and measured restore                                          | InfraOps data owner    | Platform, OpSec, sponsor                    |
| D-12 | Protected CI publication / tested filesystem delivery           | Only intended content; tested prefix isolation, failed-publication recovery, withdrawal and restore | InfraOps/docs owner    | Domain CI owners, OpSec                     |
| D-13 | Minimal plugin/image set / justify extras                       | Review routes, patch ownership, scans and compatible rollback                                       | Platform app owner     | OpSec, InfraOps                             |
| D-14 | Plugin schemas / pre-created databases                          | Select supported PostgreSQL; test roles, migrations, TLS and pools                                  | Database operator      | Platform, OpSec                             |
| D-15 | Service monitoring and support; external incident orchestration | Backstage supplements incidents; monitoring/observability and AWX/Ansible handle response           | InfraOps               | Platform, NetworkOps as needed, OpSec       |
| D-16 | Privileged automation deferred / separate future proposal       | New business case, credentials and action-specific security approval required                       | Sponsor/OpSec          | Platform, InfraOps, domains                 |
| D-17 | Confluence/tool links / ingestion later                         | Approve links; review copied-content and credential risks before ingestion                          | Platform catalog owner | Tool owners, OpSec, NetworkOps              |

## Approval sequence and record

1. Use the proposal to request OpSec assessment. InfraOps supplies implementation options and coordinates supporting teams.
2. OpSec records explicit approval, conditions or required changes. InfraOps can then allocate resources, select the upstream release and finalize the design.
3. InfraOps implements and validates the service against OpSec conditions before granting user access or publishing internal content.
4. Validate the pilot at its actual size. Complete 250-site capacity tests before expansion.
5. Record design changes and operational results. Obtain revised OpSec approval before crossing existing boundaries.

For each state change, record the decision ID, old/new state, selected option, alternatives, reason and evidence.
Add named signatories, date, conditions, residual risks, next review date and implementation reference.
Keep sensitive endpoints and credentials in restricted operational records.

| Date       | Decisions       | State/change                                      | Authority                                               |
| ---------- | --------------- | ------------------------------------------------- | ------------------------------------------------------- |
| 2026-11-19 | D-01–D-15, D-17 | Initial Proposed records                          | Document preparation; no team approval                  |
| 2026-11-19 | D-16            | Initial Deferred scope                            | Follows requested pilot scope; future approval required |
| 2026-11-19 | All             | Editorial reduction; choices and states unchanged | Documentation update only                               |

## Proposal history

| Date       | Decisions  | Clarification                                                                          | Authority/state                                    |
| ---------- | ---------- | -------------------------------------------------------------------------------------- | -------------------------------------------------- |
| 2026-11-19 | D-01–D-03  | Starting proposal; InfraOps owns design; explicit OpSec approval gates allocation      | Proposal direction; actual OpSec approval pending  |
| 2026-11-19 | D-06       | Broad internal sharing preferred despite narrower source access                        | Preferred policy; OpSec policy pending             |
| 2026-11-19 | D-09, D-15 | Continuous availability intended; incident response stays with separate tools          | Proposal direction; operating tier pending         |
| 2026-11-19 | D-10       | InfraOps and designated domain leads are intended admins                               | Proposal direction; role scope/enforcement pending |
| 2026-11-19 | D-10       | Central Infra/Net/OpSec admins; domain lead rights only if practical; central fallback | Proposal direction; enforcement pending            |
| 2026-11-19 | D-06, D-12 | TechDocs content is intended for Backstage; InfraOps chooses withdrawal mechanisms     | Proposal direction; security policy pending        |
| 2026-11-19 | D-02, D-03 | InfraOps cannot cross OpSec boundaries without revised approval                        | Proposal direction; actual OpSec approval pending  |
| 2026-11-19 | D-01       | Fresh upstream installation after OpSec approval; InfraOps selects the release         | Proposal direction; release selection pending      |
