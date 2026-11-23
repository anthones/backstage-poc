# Backstage: User glossary

[Adoption overview](README.md) · [KiwiTCMS user glossary](../kiwitcms/user-glossary.md)

You are a QA engineer preparing to test a service and report results.
Use Backstage to find the service, its owner and its documentation.
Then use KiwiTCMS to plan tests and record results.

Ask your team lead for the company portal address and access instructions.
Page names and available features depend on the company setup.
The external links below explain upstream terms; they do not open company records.

## 1. Find the service

Search for the service name. Open its catalog entry and check the description.
Use catalog filters to narrow the results when available.

| Term             | Meaning for your task                                                                                   |
| ---------------- | ------------------------------------------------------------------------------------------------------- |
| Software Catalog | The directory of software and its ownership information. Start here to find a service.                  |
| Entity           | One catalog record. It can describe software, a team or another catalog item.                           |
| Component        | A piece of software, such as a service, website or library.                                             |
| Search           | A way to find indexed catalog entries and documentation. Available results depend on the company setup. |

Official guides: [Software Catalog](https://backstage.io/docs/features/software-catalog/) and [Search](https://backstage.io/docs/features/search/).

## 2. Check ownership and purpose

Confirm that you found the right service before you prepare tests.
Ask its owner about unclear scope or missing information.

| Term      | Meaning for your task                                                                                                         |
| --------- | ----------------------------------------------------------------------------------------------------------------------------- |
| Owner     | The team or person responsible for the component. Use this contact for service questions.                                     |
| Group     | A team or other organizational unit listed in the catalog.                                                                    |
| System    | Related components and resources that work together to provide a function.                                                    |
| Domain    | A business area that groups related systems, such as Payments.                                                                |
| Lifecycle | A descriptive stage, such as experimental, production or deprecated. It does not show test results or current service health. |

Official references: [System model](https://backstage.io/docs/features/software-catalog/system-model/) and [Catalog field definitions](https://backstage.io/docs/features/software-catalog/descriptor-format/).

## 3. Understand interfaces and dependencies

Check which interfaces the service offers and which other services it needs.
Use this context to identify related tests and teams.

| Term         | Meaning for your task                                                            |
| ------------ | -------------------------------------------------------------------------------- |
| API          | An application programming interface: a defined way for software to communicate. |
| Provided API | An interface this component offers to other software.                            |
| Consumed API | An interface this component uses from other software.                            |
| Dependency   | Another component or resource that the service needs.                            |
| Resource     | Infrastructure a component needs, such as a database or storage bucket.          |

These relationships describe the catalog model. Check the company's monitoring tools for current health.

Official guide: [Components, APIs and resources](https://backstage.io/docs/features/software-catalog/system-model/).

## 4. Read the service documentation

Open the service's documentation link. Read its purpose, setup steps and known limits before testing.

| Term              | Meaning for your task                                                                                   |
| ----------------- | ------------------------------------------------------------------------------------------------------- |
| TechDocs          | Documentation published inside Backstage, usually linked from a catalog entry.                          |
| Runbook           | Instructions for a specific operational task. Follow the applicable procedure when you need it.         |
| Source repository | The project that stores source code and may store documentation. A source link opens a separate system. |

Access to published documentation and its source repository can differ.
If you find an error, send the page link and a correction to the owner.

Official guide: [TechDocs overview](https://backstage.io/docs/features/techdocs/).

## 5. Share context and start testing

Share the catalog entry and the relevant documentation page with your test plan.
Include the service name, test scope and target version or build.
Use the [KiwiTCMS user glossary](../kiwitcms/user-glossary.md) to select cases, prepare a run and record results.

If a service or document is missing, ask the owner or your team lead to arrange its addition.
