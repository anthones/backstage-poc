# Backstage: Official references

[Overview](README.md) · [Terms](../../../CONTEXT.md)

**Reference review date: 2026-11-19. Status: planning guidance for a new open-source installation after OpSec approval.**

This proposal selects no Backstage release or dependency version.
InfraOps will select a supported upstream release and compatible components after explicit OpSec approval.
The sources below describe upstream capabilities and configuration options. They do not establish an approved or working installation.

## Fresh installation and version selection

The upstream installation guide describes how to create a new Backstage application with the official app generator.
The generated application is a starting point. Production use requires security configuration, persistent services, integrations and tests.
Follow the guide for the release selected after approval. [Upstream installation](https://backstage.io/docs/getting-started/)

Before rollout, InfraOps should record the selected release, runtime, package manager, plugins, build tools and container-image digests.
Select compatible database and documentation tools too. Pin versions and repeat relevant tests after changes.
The upgrade guide covers coordinated package updates and app-template changes. [Upgrade guidance](https://backstage.io/docs/getting-started/keeping-backstage-updated/)

## Authentication, permissions and plugin trust

The upstream threat model expects a protected deployment. Signed-in access can remain broad unless operators configure restrictions.
Plugins and their credentials form part of the application's trusted environment.
Operators must assess plugins, configuration, outbound reads and copied content. [Threat model](https://backstage.io/docs/overview/threat-model/)

Modern backend authentication and user authorization are separate controls.
The permission framework requires a policy; enabling it alone does not define the intended access rules.
Verify behavior for every selected plugin and route. [Backend authentication](https://backstage.io/docs/auth/service-to-service-auth/), [permission policy](https://backstage.io/docs/permissions/getting-started/)

## GitLab identity and catalog data

The GitLab provider documents OAuth sign-in, self-managed hosts and identity resolvers.
InfraOps must test the selected provider's scopes, stable user mapping and account-removal behavior.
Human sign-in and service credentials for repository reads require separate review. [GitLab sign-in](https://backstage.io/docs/auth/gitlab/provider/)

GitLab discovery can find entities within configured paths. Its provider requires deliberate installation and configuration.
Organizational data has separate configuration; verify the selected release's membership behavior.
[Discovery](https://backstage.io/docs/integrations/gitlab/discovery/), [organization data](https://backstage.io/docs/integrations/gitlab/org/)

GitLab documents group and project access tokens with different resource boundaries.
Check account roles, required read scopes, expiry and rotation on the company instance.
[Group tokens](https://docs.gitlab.com/user/group/settings/group_access_tokens/), [project tokens](https://docs.gitlab.com/user/project/settings/project_access_tokens/)

## TechDocs publication and storage

Upstream guidance describes CI generation and publication to durable storage, with Backstage serving generated files.
Use separate publisher and runtime identities. Select and pin compatible generation and publication tools after approval.
[Architecture](https://backstage.io/docs/features/techdocs/architecture/), [CI publication](https://backstage.io/docs/features/techdocs/configuring-ci-cd/)

Storage documentation lists supported publisher configurations.
InfraOps must test any self-managed S3-compatible service with the selected Backstage release, publisher, certificates and permissions.
No storage product or compatibility result is selected here. [Storage guidance](https://backstage.io/docs/features/techdocs/using-cloud-storage/)

## Deployment and persistent data

Upstream guidance supports different infrastructure choices and favors existing organizational deployment practices.
The container guide includes a combined frontend/backend approach; separate frontend deployment is optional.
These are design options for InfraOps, not prescribed topology or ports.
[Deployment](https://backstage.io/docs/deployment/), [container build](https://backstage.io/docs/deployment/docker/)

The database guide describes PostgreSQL for Backstage data.
InfraOps must validate plugin migrations, database rights, connection limits, persistence and recovery for the selected release.
[PostgreSQL guidance](https://backstage.io/docs/getting-started/config/database/)

## Optional Jira access and remaining checks

Before adding Jira API data, match the connector to the company's Jira Data Center version.
A PAT inherits its account's permissions; it is not inherently read-only.
Test issue security, pagination, expiry and the permitted audience.
[Atlassian PAT guidance](https://confluence.atlassian.com/enterprise/using-personal-access-tokens-1026032365.html), [Jira REST reference](https://developer.atlassian.com/server/jira/platform/rest-apis/)

Online documentation changes. InfraOps must confirm each applicable instruction against the versions chosen after OpSec approval.
Complete integration, access-control, load and recovery tests before user access.
