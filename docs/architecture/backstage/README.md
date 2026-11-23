# Backstage adoption

**Status: Proposed. Review date: 2026-11-22. Proposed owner: InfraOps.**

This proposal starts Backstage adoption. OpSec will assess a small PoC through self-managed GitLab.
The [RFC](RFC-001-backstage-architecture.md#4-poc-assessment-and-production-basis) holds the PoC link, pending upload.
It does not fix the final infrastructure design.
InfraOps needs explicit OpSec approval before allocating production resources. It selects the production design within those boundaries.
Production approval and provisioning remain pending.

## Read only what your task requires

| Reader       | Start here                                                                                                                            | Required outcome                                                  |
| ------------ | ------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------- |
| OpSec        | [PoC details](RFC-001-backstage-architecture.md#4-poc-assessment-and-production-basis)                                                | Experiment and run checks using the GitLab PoC                    |
| InfraOps     | [Infrastructure plan](infrastructure-requirements.md) and [Network requirements](network-review.md)                                   | Select the design and plan implementation within OpSec boundaries |
| Domain leads | [Architecture proposal](RFC-001-backstage-architecture.md) and [Publication policy](../../adr/0001-backstage-publication-audience.md) | Prepare catalog data and TechDocs content                         |

## Page map

Publish these as separate child pages under this overview. Reference pages support review; they are not additional approval gates.

| Page                                                                   | Purpose                                                                        |
| ---------------------------------------------------------------------- | ------------------------------------------------------------------------------ |
| [Architecture proposal (RFC-001)](RFC-001-backstage-architecture.md)   | Scope, upstream installation basis, options and pilot plan                     |
| [Infrastructure plan](infrastructure-requirements.md)                  | Hosting, sizing, operations and recovery options                               |
| [Network requirements](network-review.md)                              | Proposed flows and tests for InfraOps delivery                                 |
| [Terms](../../../CONTEXT.md)                                           | Shared project language                                                        |
| [Publication policy](../../adr/0001-backstage-publication-audience.md) | Why published documentation can have wider readership than source repositories |
| [Official references](official-source-notes.md)                        | Upstream installation guidance and checks for the release InfraOps selects     |

## Review boundaries

Broad internal readership is the preferred policy; OpSec decides the permitted audience.
Only content intended for Backstage belongs in TechDocs.
Central catalog admins have catalog-wide rights. Domain leads receive restricted rights only when those limits are practical to enforce.
Backstage supports incident work. Separate monitoring, observability and AWX/Ansible handle incident response.
InfraOps chooses hosting and operating methods, and must remain within OpSec boundaries.
