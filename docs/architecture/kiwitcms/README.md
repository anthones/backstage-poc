# KiwiTCMS adoption

**Status: Proposed. Review date: 2026-11-19. Proposed delivery owner: InfraOps.**

This proposal starts adoption of a shared test management platform for approximately 50 daily users, mostly QA engineers.
InfraOps needs explicit OpSec approval before allocating resources or installing the service.
InfraOps selects the final design within OpSec boundaries. No approval, installation or deployment has occurred.

## Reading order

| Reader                   | Start here                                                                                           | Required outcome                                            |
| ------------------------ | ---------------------------------------------------------------------------------------------------- | ----------------------------------------------------------- |
| Engineering and QA leads | [RFC-002: KiwiTCMS adoption](RFC-002-kiwitcms-adoption.md)                                           | Agree scope, ownership, pilot workflow and success measures |
| OpSec                    | [Privacy, identity and permissions](RFC-002-kiwitcms-adoption.md#6-privacy-identity-and-permissions) | Set security boundaries and conditions for installation     |
| InfraOps                 | [Deployment and operations](RFC-002-kiwitcms-adoption.md#7-deployment-and-operations)                | Select hosting, build method, capacity and recovery design  |
| All reviewers            | [Decision record](RFC-002-kiwitcms-adoption.md#10-decisions-and-next-steps)                          | Record choices, owners and approval state                   |
| Technical reviewers      | [Official references](official-references.md)                                                        | Verify upstream behavior against the selected release       |

## Shared organizational context

The proposal carries forward the [Backstage governance and infrastructure assumptions](../backstage/README.md).
NetworkOps supports InfraOps as needed. It is not a separate approval gate.
Existing monitoring, observability and AWX/Ansible remain responsible for infrastructure incident response.

KiwiTCMS is a separate application. Its identity model, permissions, data and installation need their own assessment.
The [RFC terms](RFC-002-kiwitcms-adoption.md#3-workflow-and-source-of-truth) define the test management language used here.
