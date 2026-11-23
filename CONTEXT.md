# Backstage adoption

[Overview](docs/architecture/backstage/README.md)

This glossary defines terms for the Backstage adoption proposal.

## Language

**Adoption proposal**:
A starting point for assessment and planning. It does not prescribe InfraOps' final design.
_Avoid_: Definitive design, deployment authorization

**Upstream OSS installation**:
A new Backstage installation from a supported official open-source release selected after OpSec approval.
_Avoid_: Existing application deployment

**OpSec approval**:
The explicit security approval required before InfraOps allocates production resources for Backstage.
_Avoid_: Documentation approval, NetworkOps approval gate

**Catalog admin**:
A central catalog admin or a designated domain lead with enforced rights within their own domain.
_Avoid_: Every service owner, every employee

**Central catalog admin**:
An authorized InfraOps, NetworkOps or OpSec administrator with catalog-wide rights.
_Avoid_: Every member of those teams

**Domain catalog admin**:
A designated domain lead with permission to register entries within their own domain. This role requires practical, enforced restrictions.
_Avoid_: Global administrator, any repository contributor

**Domain team lead**:
A designated lead for a domain team. Catalog administration requires explicit designation and an assigned permission scope.
_Avoid_: Any repository contributor

**TechDocs content**:
Documentation intended for publication in Backstage. Material outside that audience is not part of the TechDocs content.
_Avoid_: All repository documentation

**Published documentation**:
Documentation made available through Backstage under OpSec's reader access policy. Its audience can differ from the source repository's audience.
_Avoid_: Source repository, source-access mirror

**OpSec boundaries**:
The approved security limits for Backstage's exposure, readership, credentials and privileges.
_Avoid_: Suggested infrastructure layout

**Incident context**:
Service ownership, dependencies and documentation that support incident work. This information is separate from incident detection and response controls.
_Avoid_: Incident orchestrator, monitoring service
