# Jira: connect work with service context

Open [Jira & delivery](http://localhost:3000/delivery) from Backstage's sidebar. This is a small custom integration for the PoC, using the existing Backstage proxy. It is not an installed marketplace Jira plugin.

## Real connection: Atlassian's public issue tracker

The default **Atlassian public Jira · live read-only** mode requests up to five recently updated JRASERVER issues from `https://jira.atlassian.com/rest/api/2/search`. No account or token is needed for the public records verified during development. The panel shows retrieval time, status, explicitly returned issue links, and links back to Jira. It marks the result as a limited preview when more issues exist.

These are real Atlassian issues, **unrelated to our fictional company, teams, or services**. The live mode proves that the API connection works. Do not present those issues as a dependency or backlog for our PoC. Public access can change or be unavailable at presentation time; rehearse it beforehand.

Atlassian's [Jira demo page](https://www.atlassian.com/software/jira/demo) offers guided demonstrations. It is different from the [public issue tracker](https://jira.atlassian.com/), which supplies this API data.

## Fictional work: a repeatable activation handover

Select **Activation handover · fictional example**. The data comes from `integrations/jira/scenario.json`, not Atlassian. The screen says so, and fictional issue keys are not links to nonexistent Jira records.

Show ACT-101 (policy change), ACT-102 (workspace consumer change), and ACT-103 (journey acceptance). Then filter to Customer Portal to see ACT-104 (customer message) and ACT-106 (support checklist).

Component catalog records hold the example mapping:

```yaml
annotations:
  jira/project-key: ACT
  acmesecure.example/jira-label: policy-service
```

The local adapter reads those mappings from the component records and uses project plus service label to select fictional work. A service's **Jira handover example (fictional)** link opens the filtered view. These annotations illustrate the proposed company mapping; they do not mean that an ACT project exists on Atlassian's public tracker.

## Benefits to explain with the example

| Role | Practical question | How the combined view helps |
| --- | --- | --- |
| Product owner | “Which teams must contribute before we can deliver this outcome?” | Start with the customer journey, follow service owners and declared dependencies, then review recorded work and explicit blockers with those teams. |
| Product owner | “Why is a service ticket done while the feature is not ready?” | Compare individual work status with remaining consumer work and journey acceptance evidence. |
| Business analyst | “Who can clarify this business rule?” | Find the domain owner and API agreement; distinguish customer identity, subscription eligibility, and security requirements. |
| Business analyst | “What should acceptance and handover contain?” | Agree customer examples, expected outcomes, support messages, and evidence with providers, consumers, QA, and support. |
| QA / support | “What context should arrive with this change?” | Open the owning service's acceptance notes and runbook from the same service context. |

Catalog arrows are **software dependencies**. Jira links are **recorded work relationships**. One does not automatically create the other. Status alone does not prove approval, readiness, or a real delivery blocker. Jira remains the source for editing work; the portal does not create or update tickets.

## How the connection runs

```text
Backstage Jira page
  → authenticated Backstage proxy (/api/proxy/jira-poc)
  → loopback Python adapter (8090)
      → Atlassian public search API, or
      → explicitly selected fictional activation dataset
```

The workspace runner starts the adapter. The Backstage proxy permits GET only and requires a Backstage identity. The adapter binds to loopback and holds no private Jira credentials. There is no silent switch from live data to fictional data when a request fails: the page displays an error, and the presenter can select the fictional source explicitly.

## Moving to company Jira

The current adapter connects only to the public tracker and the fictional example. A private company connection remains pilot work:

1. Confirm Jira Cloud or Data Center, its base URL, supported authentication, and the audience allowed to see the returned issues.
2. Agree a stable issue-to-service mapping, then replace the fictional ACT metadata with actual reviewed project and label/component mappings.
3. Add a server-side connector for the instance. Jira Cloud's enhanced search endpoint is `/rest/api/3/search/jql`; Data Center uses `/rest/api/2/search`. Keep credentials server-side and implement the intended access policy.
4. Test denied access, unavailable Jira, missing mappings, and pagination. Decide whether a limited preview is enough or whether all result pages are needed.
5. Keep changes, approvals, and workflow enforcement in the agreed Jira/release process. Add write actions only if a later requirement calls for them.

The [Jira Cloud search reference](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issue-search/), [Data Center search reference](https://developer.atlassian.com/server/jira/platform/rest/v10004/api-group-search/), and [Backstage proxy documentation](https://backstage.io/docs/plugins/proxying/) describe the APIs and proxy behavior used here.
