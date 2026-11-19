# Backstage: Infrastructure plan

[Overview](README.md) · [Terms](../../../CONTEXT.md)

**Status: Proposed. Review date: 2026-11-19. Owner: InfraOps with Platform Engineering; named operators pending.**

## Decisions required

1. Identify supported hosting, PostgreSQL, storage, secrets, registry and monitoring services.
2. Compare capacity, cost, private connectivity and support for the hosting options.
3. Agree resource ranges, recovery targets and named operators.
4. Allocate resources after explicit OpSec approval. InfraOps owns the final design and may revise these proposals.

Use [RFC-001](RFC-001-backstage-architecture.md) for scope and [the decision log](decision-log.md) for approval records.

## Fresh upstream installation after approval

After explicit OpSec approval, InfraOps selects a supported upstream open-source Backstage release and creates a new installation.
Select runtime and build-tool versions from that release's documented requirements.
Record the chosen release, dependencies, enabled modules and compatibility results in the implementation record.
This proposal does not select an application version or assert any existing integration capability.

## Hosting and topology

| Option                 | Benefit                                               | Cost/risk                                                                    | Required evidence                                        |
| ---------------------- | ----------------------------------------------------- | ---------------------------------------------------------------------------- | -------------------------------------------------------- |
| Existing Kubernetes    | Reuses Helm/ArgoCD and platform services              | Cluster operations, ingress, storage and policy support must exist           | Capacity, enforceable isolation, service owners and cost |
| Dedicated Proxmox VM   | Simple private pilot; fits Ansible/AWX                | OS/runtime/proxy maintenance; one host can interrupt service                 | VM capacity, firewall, backup and support                |
| VPS                    | Additional capacity if internal hosting is unsuitable | Provider/data-location approval, rental/transfer costs and tunnel dependency | Private routes, latency, bandwidth and recovery support  |
| Hybrid VPS/on-premises | Reuses internal data services                         | More latency, trust boundaries and failure paths                             | Tunnel tests and accepted operating costs                |

Prefer supported internal infrastructure. InfraOps selects and adapts the design; these options do not prescribe a final architecture.
Include runner, registry, storage/backup, TLS, maintenance and on-call effort in the cost comparison.

Candidate pilot topology: one app container serving UI/backend, persistent PostgreSQL and durable private TechDocs storage.
Prefer existing data services. A combined app/database VM is possible if owners accept its common failure risk.

A more resilient option uses two app replicas across separate hosts and resilient ingress/data services.
This supports app maintenance and single-app failure, at additional resource and support cost.
Two replicas do not remove a single database, storage or tunnel failure.
[Backstage scaling](https://backstage.io/docs/deployment/scaling/)

## Provisional sizing

Assume approximately 200 registered users, periodic daily access, over 200 services with TechDocs, and few plugins.
Use 5–10 active pilot users, 10–20 active users normally, and 40–50 for a short burst.
These are planning assumptions, not measured capacity.

Ranges exclude existing platform services, backups and replication unless stated. GiB denotes binary storage/memory capacity.

| Resource                         | Minimal pilot: 10–20 sites                         | Broader deployment test: 250+ sites                                            |
| -------------------------------- | -------------------------------------------------- | ------------------------------------------------------------------------------ |
| Application                      | 1 replica; 1–2 vCPU, 2–4 GiB RAM                   | 1 replica, or 2 for approved resilience; same range per replica initially      |
| App limits                       | Candidate request 1 vCPU/2 GiB; limit 2 vCPU/4 GiB | Tune from tests; assess 2–4 vCPU/4–6 GiB ceiling only if needed                |
| App temporary space              | 2–5 GiB; no persistent docs                        | 5–10 GiB per replica                                                           |
| App-only VM                      | 2–4 vCPU, 4–8 GiB including OS/proxy               | Same starting range per app VM                                                 |
| PostgreSQL                       | 1–2 vCPU, 2–4 GiB; 20–40 GiB persistent SSD        | 2–4 vCPU, 4–8 GiB; 50–100 GiB SSD                                              |
| Combined pilot app/database VM   | 6–8 vCPU, 12–16 GiB; separate OS/data budgets      | Not the resilient topology                                                     |
| TechDocs live-storage allocation | 2–10 GiB                                           | 25–100 GiB; revise for images, versions and growth                             |
| Separate object store, if needed | Candidate 1–2 vCPU/2–4 GiB plus durable disks      | Candidate 2–4 vCPU/4–8 GiB; operator must confirm server/topology requirements |
| Docs CI worker                   | 2–4 vCPU/4–8 GiB; 5–10 GiB workspace               | Start with two concurrent builds; measure before increasing                    |
| App-image build worker           | Measure build peak                                 | Candidate 4–8 vCPU/8–16 GiB                                                    |
| Network test envelope            | 10–50 Mbit/s bursts                                | Test with 100 Mbit/s available; test constrained tunnels separately            |

Keep OS/service headroom. Replica and storage-redundancy costs are additional.
Do not procure storage from service count alone. Measure generated site sizes and object counts.

Estimate storage as site count × mean size × retained versions, plus replication, growth and backup overhead.
For example, 250 sites at 20–100 MiB need approximately 5–25 GiB for one version before overhead.
Three versions and image-heavy sites can exceed the proposed range.
Database growth also includes APIs, users, groups, search indexes and transaction logs.

## PostgreSQL and persistence

Select an operator-supported PostgreSQL major and test the chosen Backstage release and plugin migrations against it.
Use private access, verified TLS, persistent disks and an app role without superuser rights.

InfraOps selects a database isolation model supported by the chosen release. Test required database objects and migration rights.
Test ownership/migration rights; avoid global database-creation privileges. Back up every plugin's state and required roles.
[Database guidance](https://backstage.io/docs/getting-started/config/database/)

Count connection pools across plugins and replicas. Reserve admin/migration capacity below the database connection limit.
Candidate small pools: 2–5 connections per active plugin, adjusted by tests.
Verify PostgreSQL-backed search and access filtering. Monitor locks, latency, connections, disk, vacuum and transaction-log growth.

App local files remain disposable. Preserve database identity/session state where used, published docs, release configuration and audit records.
Catalog reconstruction alone is not full database recovery.

## TechDocs build and publication

After approval, define a shared GitLab CI workflow for approved service repositories.
TechDocs sources and generated output must contain only material intended for Backstage.
Generate documentation in CI. Serve published output from durable storage, without runtime build credentials or a Docker socket.

1. Validate metadata, ownership and classification. Build merge requests without publication secrets.
2. Build protected-branch docs with pinned MkDocs/TechDocs tools and reviewed plugins.
3. Validate metadata/assets. Publish only the assigned entity prefix with a protected job identity.
4. Serialize publication per entity. Prevent an older pipeline from replacing a newer result.
5. Record entity, commit, pipeline and tool versions. Retain the last successful artifact for recovery.
6. Test interrupted uploads, rollback, deletion, renamed entities and search refresh.

Do not assume multi-file publication is atomic.
Prefer an existing supported store; use separate backend read and CI write credentials.
Keep objects private and serve them through Backstage access controls.
InfraOps selects withdrawal, republication suppression, search/cache cleanup and restore checks under OpSec boundaries.
Verify the withdrawal outcome; successful publication alone does not prove content removal.

S3-compatible storage, including MinIO, requires server/publisher version, endpoint, CA, signing, path-style and permission tests.
Confirm endpoint and request-style support in the selected publisher. Test the actual server and CI tools together.
A backed-up shared filesystem is an alternative; review its protocol, mounts, publication permissions and replica consistency.
[CI guidance](https://backstage.io/docs/features/techdocs/configuring-ci-cd/), [storage guidance](https://backstage.io/docs/features/techdocs/using-cloud-storage/)

## Build, registry and deployment

Build a new application from the selected upstream release after approval.
Use its supported runtime/toolchain, fixed dependencies and matching build/runtime versions. Follow the official container guidance.
Create an image from reviewed source, fixed dependencies, required tests, scans and a software bill of materials.
Use a non-root runtime and immutable image digest. Pin the base image and retain previous approved releases.
[Docker guidance](https://backstage.io/docs/deployment/docker/)

Create deployment configuration for the selected environment. Review merged settings and enabled routes.
Keep credentials and published documentation out of the application image.

On Kubernetes, follow existing Helm/ArgoCD practices after confirming cluster support.
Configure private ingress, secret references, resource limits, probes and enforced network policies.
Keep database/storage lifecycle separate from app rollout and chart deletion.

On Proxmox/VPS, use Ansible/AWX for OS, runtime, proxy, certificates, firewall, secrets and supervised container operation.
Record image/config history and a controlled restart/rollback process.

## Monitoring and health

Use existing collectors where available. Monitor HTTP latency/errors, memory/CPU, restarts, discovery age, docs freshness and search age.
Also monitor sign-in failures, storage/database errors, credential/certificate expiry, backup age and tunnel state.
Assign an alert owner and runbook for each component.

Choose health routes supported by the selected release. Test their behavior before configuring startup, readiness and liveness probes.
Built-in readiness may not cover all integrations.

Use startup allowance for migrations. Liveness must avoid repeated restarts during dependency outages.
Add private synthetic catalog/docs/search/sign-in tests. Keep health/metrics endpoints private.

Candidate alerts: 5xx above 2% for five minutes, p95 above two seconds, memory above 80%, or free disk below 20%.
Alert on discovery/index age above two cycles, failed backups and credentials/certificates expiring within 14 days.
Tune thresholds from pilot measurements. See [OpSec](security-review.md) for audit coverage, retention and patch targets.

## Recovery targets and backups

Backstage should remain available at all times. It supplements incident work; separate monitoring, observability and AWX/Ansible handle response.
InfraOps must select an uptime target and support coverage. Continuous service does not by itself imply continuous staffing.
The ranges below are discussion inputs, not agreed commitments.
RPO means maximum data loss; RTO means maximum recovery time after incident declaration.

| Target               | Pilot                                                                                 | More resilient option, if funded                                               |
| -------------------- | ------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------ |
| Support/availability | Continuous availability intended; uptime target and support coverage pending InfraOps | InfraOps selects resilience and staffing needed for the agreed target          |
| RPO                  | Up to 24 hours; provisional                                                           | Database ≤1 hour; docs ≤24 hours. Retained artifacts must meet that same limit |
| RTO                  | Pending InfraOps service tier; previous one-business-day example needs review         | Four elapsed hours, with matching support coverage                             |
| Performance example  | p95 API/search <1 second; complete document navigation <2 seconds                     | Same under representative load and one app loss                                |
| Content freshness    | InfraOps defines separate catalog, document and search clocks/targets                 | Validate the selected targets at broader scale                                 |

Pilot backup proposal: nightly consistent database backup; seven daily and four weekly copies.
Include all plugin state, roles, published docs, release/config records and recovery-key custody.
The more resilient option needs transaction-log archiving for its database RPO.

Keep encrypted backups outside the runtime's failure/credential domain.
Storage versioning and VM snapshots supplement independent backups; they do not replace database-consistent recovery.
Agree retention, off-site location and replacement capacity. No automatic site failover is assumed.

Restore procedure:

1. Restrict access. Select the recovery point and restore network, DNS, CA and secret access.
2. Restore database roles/plugin state and document storage into an isolated recovery environment.
3. Deploy a compatible approved image/configuration. Rotate secrets if compromise is suspected.
4. Test sign-in, identity mapping, catalog, documents, search and denied access.
5. Reconcile later GitLab changes and republish missing approved docs. Record actual time and data loss before reopening.

Complete a restore drill before pilot access; repeat quarterly and after major changes as a proposed cadence.
Name disaster recovery owners and a rebuild location for host, site or provider loss.

## Upgrades, rollback and capacity tests

Platform owns monthly routine release review and emergency patches under OpSec targets.
Test the selected release, dependency updates, identity/permissions, storage and migrations before rollout.
Back up before migration. Confirm mixed-version compatibility before rolling across replicas.

An old image may not support a migrated database.
If downgrade compatibility fails, restore the matching database, docs and configuration, with an accepted data-loss window.

Perform capacity and recovery tests on the new installation after approval. Validate the pilot at its selected size.
Use the following broader test before expansion. It is not required before allocation:

1. Load at least 250 representative sites plus realistic API/User/Group records. Include large, image-heavy documents.
2. Run 10–20 active sessions for 30–60 minutes. Add a 15-minute burst of 40–50 users.
3. Use realistic pauses and catalog/docs/search requests. Measure requests per second rather than infer them from user count.
4. Overlap discovery, indexing and two publications. Measure latency, errors, memory, CPU, database pools/I/O and network use.
5. Test dependency/tunnel failure and recovery. For two replicas, remove one and repeat normal load.
6. Record versions, data sizes and results. Adjust resources for 25–30% headroom; review usage after two and four weeks.

## Provisioning and acceptance checklist

| Owner                  | Evidence required                                                           | Decisions              |
| ---------------------- | --------------------------------------------------------------------------- | ---------------------- |
| Sponsor/Platform       | Named owner, staffing, scope and service targets                            | D-01, D-09             |
| NetworkOps             | Network design and tests coordinated by InfraOps; no separate approval gate | D-03                   |
| OpSec/identity admins  | Approved identity, audience, permissions and secrets                        | D-04, D-06, D-07       |
| InfraOps               | Costed hosting/capacity and named service operators                         | D-02                   |
| Database operator      | Supported version, roles, pools, persistence and migration tests            | D-14                   |
| Storage/CI owners      | Durable storage, publisher compatibility and permissions                    | D-05, D-12             |
| Platform/GitLab admins | Scoped discovery, trusted identities and real owner validation              | D-10                   |
| Platform/InfraOps      | Approved image/plugins, alerts, restore/load results                        | D-09, D-11, D-13, D-15 |

Which services and capacity exist today? Who supports them, at what cost and hours?
Can operators meet the intended continuous availability? InfraOps resolves operational choices within OpSec conditions.
Allocation requires explicit OpSec approval; implementation evidence follows provisioning and precedes user access.
InfraOps cannot cross approved boundaries. Obtain revised OpSec approval before implementing a change beyond them.
