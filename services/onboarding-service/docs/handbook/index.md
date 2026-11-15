# Customer activation integration handbook

Customer Experience owns this handbook as part of the onboarding-service repository. It covers the multi-repository workspace and cross-domain procedures. Each service repository owns its implementation, catalog metadata, API contract, support runbook, and QA handover.

[Software catalog](http://localhost:3000/) · [Dependency graph](http://localhost:3000/catalog-graph)

| Procedure | Location |
| --- | --- |
| Repository boundaries, catalog polling, and CI drift checks | [Repositories](repositories.md) |
| System-level dependency overview and Mermaid source | [Architecture](architecture.md) |
| Authoritative service documentation and escalation | [Ownership directory](ownership.md) |
| Local cross-service failure and recovery | [Integration exercise](incident.md) |
| Changes involving several teams | [QA coordination](handover.md) |
| Meeting sequence | [Walkthrough](presentation.md) |
| Internal SCM and on-premises deployment | [Configuration path](on-prem.md) |

The local POC runs seeded business previews and uses separate file catalog locations as stand-ins for independently checked-out SCM repositories. Backstage periodically reads each service's YAML. Documentation is built by the repository's own CI script and published locally for this exercise. No remote repositories are created.

The `/demo` route in Backstage opens this TechDocs handbook. The frontend does not keep a separate authored copy. Each service builds documentation into its own `site/` directory; `backstage/.techdocs/` stores only published copies.
