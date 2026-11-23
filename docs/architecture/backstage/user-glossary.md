# Backstage: User glossary

[Adoption overview](README.md) · [KiwiTCMS user glossary](../kiwitcms/user-glossary.md)

You need to understand, use, change or support company software.
Backstage brings software ownership, dependencies, documentation and tool links into one place.
It serves developers, QA, InfraOps, NetworkOps, OpSec, team leads and new colleagues.

| Your task                                    | Start with                                |
| -------------------------------------------- | ----------------------------------------- |
| Join a team or take over a service           | Its owner, purpose and documentation      |
| Develop or test a change                     | Its APIs, dependencies and related teams  |
| Support a service or investigate an incident | Its runbook, owner and monitoring links   |
| Review or coordinate work across teams       | Its system, domain and source information |

Ask your team lead for the company portal address and access instructions.
Page names and available features depend on the company setup.
The external links below explain upstream terms; they do not open company records.

## 1. Find the software or team

Search for a service, application, library or team. Open its catalog entry and check the description.
Use catalog filters to narrow the results when available.

| Term             | Meaning for your task                                                                                   |
| ---------------- | ------------------------------------------------------------------------------------------------------- |
| Software Catalog | The directory of company software and its ownership information. Start here to find what exists.        |
| Entity           | One catalog record. It can describe software, a team or another catalog item.                           |
| Component        | A piece of software, such as a service, website or library.                                             |
| Search           | A way to find indexed catalog entries and documentation. Available results depend on the company setup. |

Official guides: [Software Catalog](https://backstage.io/docs/features/software-catalog/) and [Search](https://backstage.io/docs/features/search/).

## 2. Check ownership and purpose

Confirm what the software does, which team owns it and how it fits into the company.
Use this context for onboarding, handovers and work across team boundaries.

| Term      | Meaning for your task                                                                                                   |
| --------- | ----------------------------------------------------------------------------------------------------------------------- |
| Owner     | The team or person responsible for the component. Use this contact for service questions.                               |
| Group     | A team or other organizational unit listed in the catalog.                                                              |
| System    | Related components and resources that work together to provide a function.                                              |
| Domain    | A business area that groups related systems, such as Payments.                                                          |
| Lifecycle | A descriptive stage, such as experimental, production or deprecated. Check monitoring tools for current service health. |

Official references: [System model](https://backstage.io/docs/features/software-catalog/system-model/) and [Catalog field definitions](https://backstage.io/docs/features/software-catalog/descriptor-format/).

## 3. Understand interfaces and dependencies

Check which interfaces the software offers and which services or resources it needs.
Use these relationships to find reusable interfaces, assess a change's impact and identify teams to involve.

| Term         | Meaning for your task                                                            |
| ------------ | -------------------------------------------------------------------------------- |
| API          | An application programming interface: a defined way for software to communicate. |
| Provided API | An interface this component offers to other software.                            |
| Consumed API | An interface this component uses from other software.                            |
| Dependency   | Another component or resource that the service needs.                            |
| Resource     | Infrastructure a component needs, such as a database or storage bucket.          |

These relationships describe the catalog model. Check the company's monitoring tools for current health.

Official guide: [Components, APIs and resources](https://backstage.io/docs/features/software-catalog/system-model/).

## 4. Read the documentation

Open the documentation for your task: an introduction, usage guide, interface description or runbook.
Use it to learn the system, prepare a change or support operations.

| Term              | Meaning for your task                                                                                   |
| ----------------- | ------------------------------------------------------------------------------------------------------- |
| TechDocs          | Documentation published inside Backstage, usually linked from a catalog entry.                          |
| Runbook           | Instructions for a specific operational task. Follow the applicable procedure when you need it.         |
| Source repository | The project that stores source code and may store documentation. A source link opens a separate system. |

Access to published documentation and its source repository can differ.
If you find an error, send the page link and a correction to the owner.

Official guide: [TechDocs overview](https://backstage.io/docs/features/techdocs/).

## 5. Open the right tool

Follow the entry's links to continue your work in the relevant system.

| Term             | Meaning for your task                                                                                                                      |
| ---------------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| Tool link        | A route to a related system, such as GitLab, Jira, Confluence or a monitoring dashboard.                                                   |
| Merge request    | A proposed source change for review in GitLab. Teams use these to update catalog information and documentation.                            |
| Incident context | Ownership, dependencies and runbooks that help responders understand a service. Monitoring and response tools handle detection and action. |

Each linked tool has its own access controls. A link does not grant access.
For test planning and results, see the [KiwiTCMS user glossary](../kiwitcms/user-glossary.md).

## 6. Share and maintain the information

Share the catalog entry and the exact documentation page in a handover, issue or review.
Include the question or change so the next person has context.
Send stale ownership, broken links or unclear instructions to the responsible team.
Team contributors use the normal GitLab review process for corrections.

For a missing entry, ask the owner or your team lead to contact an authorized catalog admin.

Official guide: [GitLab merge requests](https://docs.gitlab.com/user/project/merge_requests/).
