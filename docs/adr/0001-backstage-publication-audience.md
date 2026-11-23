# Backstage: Publication policy

[Overview](../architecture/backstage/README.md) · [Architecture proposal](../architecture/backstage/RFC-001-backstage-architecture.md)

**Status: Proposed. OpSec approval is pending.**

The requested direction is broad internal access to published service information, including documentation from repositories a reader cannot access.
This favors shared engineering context over mirroring each repository's readership.
OpSec must decide the permitted audience, exclusions and controls before this becomes an approved publication policy.

Source access and publication access are therefore separate decisions.
Repository restrictions alone neither authorize nor prohibit internal publication under OpSec policy.
Authorized InfraOps, NetworkOps and OpSec admins have permission to register entries across the catalog.
Domain leads receive rights within their own domain only when practical to enforce; otherwise, administration stays central.

Only content intended for Backstage belongs in TechDocs. Other repository material stays outside the TechDocs source.
InfraOps chooses withdrawal and recovery methods within OpSec boundaries; it cannot exceed those boundaries without revised approval.

The alternative is to reproduce source-repository permissions for every published copy.
That can narrow disclosure, but limits the intended cross-team discovery benefit and adds permission-synchronization work.

This record captures proposal intent. It does not record OpSec approval or a deployed access policy.
See [TechDocs and data ownership](../architecture/backstage/RFC-001-backstage-architecture.md#8-techdocs-and-data-ownership).
