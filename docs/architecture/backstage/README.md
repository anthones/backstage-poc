# Backstage adoption

**Status: Proposed. Review date: 2026-11-19. Proposed owner: InfraOps.**

This proposal starts Backstage adoption through a fresh upstream open-source installation after OpSec approval.
It does not fix the final infrastructure design.
InfraOps needs explicit OpSec approval before it allocates resources. It can then select a design within the approved boundaries.
No security approval, allocation or deployment has occurred.

## Read only what your task requires

| Reader        | Start here                                                                                                                            | Required outcome                                                  |
| ------------- | ------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------- |
| OpSec         | [Architecture summary](RFC-001-backstage-architecture.md), then [OpSec review](security-review.md)                                    | Record approval, boundaries or required changes                   |
| InfraOps      | [Infrastructure plan](infrastructure-requirements.md) and [Network requirements](network-review.md)                                   | Select the design and plan implementation within OpSec boundaries |
| Domain leads  | [Architecture proposal](RFC-001-backstage-architecture.md) and [Publication policy](../../adr/0001-backstage-publication-audience.md) | Prepare catalog data and TechDocs content                         |
| All reviewers | [Decisions](decision-log.md)                                                                                                          | Record choices, owners, conditions and approval state             |

## Page map

Publish these as separate child pages under this overview. Reference pages support review; they are not additional approval gates.

| Page                                                                   | Purpose                                                                        |
| ---------------------------------------------------------------------- | ------------------------------------------------------------------------------ |
| [Architecture proposal (RFC-001)](RFC-001-backstage-architecture.md)   | Scope, upstream installation basis, options and pilot plan                     |
| [OpSec review](security-review.md)                                     | Security decisions and required controls                                       |
| [Infrastructure plan](infrastructure-requirements.md)                  | Hosting, sizing, operations and recovery options                               |
| [Network requirements](network-review.md)                              | Proposed flows and tests for InfraOps delivery                                 |
| [Decisions](decision-log.md)                                           | Authoritative record of choices and approval state                             |
| [Terms](../../../CONTEXT.md)                                           | Shared project language                                                        |
| [Publication policy](../../adr/0001-backstage-publication-audience.md) | Why published documentation can have wider readership than source repositories |
| [Official references](official-source-notes.md)                        | Upstream installation guidance and checks for the release InfraOps selects     |

## Review boundaries

Broad internal readership is the preferred policy; OpSec decides the permitted audience.
Only content intended for Backstage belongs in TechDocs.
Central catalog admins have catalog-wide rights. Domain leads receive restricted rights only when those limits are practical to enforce.
Backstage supports incident work. Separate monitoring, observability and AWX/Ansible handle incident response.
InfraOps chooses hosting and operating methods, and must remain within OpSec boundaries.
