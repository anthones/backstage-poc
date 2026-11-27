# KiwiTCMS adoption

**Status: Proposed. Review date: 2026-11-23. Delivery owner: InfraOps; workflow owner: a nominated QA lead.**

KiwiTCMS would replace scattered test-plan/result records for approximately 50 daily users, mostly QA engineers.
A working GitLab repository will be provided for OpSec experiments. Production deployment requires explicit OpSec approval.
InfraOps selects the final production design within approved boundaries.

## Reading order

| Reader               | Start here                                                                            | Outcome                                       |
| -------------------- | ------------------------------------------------------------------------------------- | --------------------------------------------- |
| End users            | [User glossary](user-glossary.md)                                                     | Plan tests, record results and share progress |
| Engineering/QA leads | [RFC-002](RFC-002-kiwitcms-adoption.md)                                               | Agree scope, workflow and pilot measures      |
| OpSec                | [Working repository](RFC-002-kiwitcms-adoption.md#6-working-repository)               | Experiment and run checks                     |
| InfraOps             | [Deployment and operations](RFC-002-kiwitcms-adoption.md#7-deployment-and-operations) | Select hosting, build, capacity and recovery  |
| VPS operator         | [Deployment after Backstage](../../deployment/deploy_debian.md)                     | Add Kiwi TCMS to the existing Debian VPS      |
| Technical reviewers  | [Official references](official-references.md)                                         | Verify selected-release behavior              |

The [Backstage context](../backstage/README.md) supplies shared governance and infrastructure assumptions.
NetworkOps supports InfraOps as needed; it is not another approval gate.
Use the [RFC terms](RFC-002-kiwitcms-adoption.md#3-workflow-and-source-of-truth) for the test workflow.
