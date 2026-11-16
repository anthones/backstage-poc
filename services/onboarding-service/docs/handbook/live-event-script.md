# Live presentation: one activation, four teams

Allow **9–10 minutes**, plus questions. Speak the quoted text. Follow the **Show** and **Run** cues silently.

Remember five steps: **Find → Trace → Act → Check → Measure**.

## Before the meeting

Start the POC with `./scripts/start.sh` from the workspace root. Keep that terminal open. Use a second terminal for the commands below.

1. Run `./scripts/demo.sh recover` to clear any previous fault and confirm successful activation.
2. Run `.venv/bin/python scripts/verify-repositories.py`. Keep its output in a spare terminal tab.
3. Open the pages in the table below. Sign in as Guest if needed.
4. Open `services/policy-service/` in the editor. Keep `routes.py`, `catalog-info.yaml`, and `docs/` visible.
5. Increase the browser and terminal font sizes. Share the application window. Keep these notes on a separate screen if available.

| Tab | Page |
| --- | --- |
| 1 | [Default catalog](http://localhost:3000/) |
| 2 | [Architecture and Mermaid diagram](http://localhost:3000/docs/default/component/onboarding-service/handbook/architecture) |
| 3 | [Customer Activation](http://localhost:3000/catalog/default/component/onboarding-service) |
| 4 | [Security Policy](http://localhost:3000/catalog/default/component/policy-service) |
| 5 | [Policy runbook](http://localhost:3000/docs/default/component/policy-service/runbook) |
| 6 | [Policy QA and release](http://localhost:3000/docs/default/component/policy-service/qa) |
| 7 | [On-premises pilot](http://localhost:3000/docs/default/component/onboarding-service/handbook/on-prem) |

## 0:00–0:45 — Start with the work

**Show:** Default catalog. Pause before opening a service.

> A customer cannot activate a workspace. Four teams take part in that request. Who should support contact first?
>
> Today, we will follow that problem from the first report to recovery. Then we will check a service change.
>
> Backstage gives us a shared place to find services, owners, interfaces, and instructions. Each team keeps those records in its repository.
>
> This example uses six small services. They make test requests; they do not create real workspaces or send email.

**Delivery cue:** Let the opening question stand for two seconds. Do not collect answers yet.

## 0:45–1:45 — Find: developers and team leads

**Show:** Architecture diagram. Point to Activation, then Tenant, Subscription, and Policy. Keep the diagram still while speaking.

> These six services have ten dependency links. Customer Activation calls all five providers.
>
> Consider the phrase “active customer.” Identity confirms that the tenant exists. Commerce decides whether the subscription permits use. Cloud Security defines the required controls.
>
> Those decisions belong to different teams. The documentation gives each decision a clear meaning.

**Show:** Customer Activation overview. Point to its owner and dependencies.

> A developer can find the provider and its API before changing a caller. A new colleague can use the same path.
>
> A team lead can see where responsibilities meet. If two teams dispute a boundary, they still need to agree and update their records.

## 1:45–3:00 — Trace: first-line support

**Run:**

```sh
./scripts/demo.sh happy
./scripts/demo.sh outage
```

**Expected:** The first request returns `activation: ready`. The second returns HTTP 502 and exits nonzero. This failure is deliberate. Point to `request_id`, `root_cause.service`, and `root_cause.owner`.

> The first request succeeds. Now I have made Policy unavailable.
>
> The customer sees an activation failure. The response identifies Policy as the cause and Cloud Security as its owner.
>
> Our service code supplies that evidence. Backstage supplies the owner record and the team's instructions.

**Show:** Policy runbook, “L1: first five minutes.”

> First-line support can record the tenant, request ID, time, and error. The runbook tells them what to check and where to send the result.
>
> The receiving team gets enough evidence to start. Customer Experience keeps responsibility for customer updates and the full activation journey.

## 3:00–4:00 — Act: second-line support and service owners

**Show:** Policy component relationships, or the architecture diagram. Point to Policy's two direct consumers: Provisioning and Activation. Then show the runbook's L2 instructions.

> Second-line support can see which callers may be affected. They can use the request ID to find the related logs.
>
> The graph shows declared dependencies. It does not show live service health. We get the failure evidence from the running services.
>
> Cloud Security owns the repair. The runbook also tells support how to check recovery.

**Run:**

```sh
./scripts/demo.sh recover
```

**Expected:** HTTP 200 and `activation: ready`.

> Activation succeeds again. We checked the original customer journey before closing the incident.
>
> For support, the benefit is a clear next action. For the service owner, it is fewer repeated requests for basic information.

## 4:00–5:15 — Check: QA and release owners

**Show:** Policy QA page. Point to the acceptance table, then the release requirements.

> Now suppose Cloud Security changes a required control. Provisioning and Activation both use that decision.
>
> QA can find the affected services and the expected results here. The checks cover success, blocked subscriptions, missing tenants, an outage, and recovery.
>
> The owner supplies the changed contract, test results, release version, and rollback instructions. QA can start from a written handover.
>
> Release owners can plan a compatible order. A breaking change still needs agreement from its consumers. The graph helps identify them; it does not collect their approval.

**Delivery cue:** Point to two test rows. Do not read the whole table.

## 5:15–6:45 — Keep the records useful: developers and domain owners

**Show:** Policy repository in the editor. Point to `routes.py`, `catalog-info.yaml`, `openapi.yaml`, and `docs/`.

> The team keeps its code, catalog record, API definition, and support documents together. Backstage reads the catalog record and serves the published documentation.
>
> This POC reads six local repository folders. An internal Git connection would replace those file locations in a pilot.
>
> We also added checks to each service's CI pipeline. These checks compare the code with the committed metadata, API definition, and interface table.

**Run:** From the workspace root:

```sh
.venv/bin/python scripts/verify-repositories.py
```

**Expected:** Six standalone checks pass. Six stale-change cases are rejected. The script changes temporary copies only. `PASS rejected stale route` means the check caught the deliberate error.

> This check changes a route in a temporary copy and leaves the metadata unchanged. The service's checks reject that mismatch.
>
> These are checks we wrote for this POC. Backstage does not provide them automatically. Reviewers must still check the meaning of the instructions.
>
> Domain teams keep control of their records. Other teams can find the reviewed result without asking for another copy.

## 6:45–7:45 — Operate: platform and security teams

**Show:** On-premises pilot page. Point to identity, authorization, storage, and operations.

> The platform team runs the shared portal and its connections. Domain teams maintain their service records and documents.
>
> An on-premises pilot needs company sign-in, access rules, persistent storage, backups, and an upgrade process. This local demo uses Guest access.
>
> Security teams can use the catalog to find owners and review declared dependencies. They must verify those records against the deployed system.
>
> Keeping the portal inside the company gives us control over its hosting. We still have to operate and secure it.

## 7:45–9:00 — Measure: product, delivery, and engineering leaders

**Show:** Return to the architecture diagram.

> Product and delivery leads can see which teams a change involves before setting a release date. Support can give customers updates based on evidence.
>
> We should test the benefit in one real customer journey. Measure how long support takes to find the owner. Count ticket transfers and handovers returned for missing information.
>
> Compare those results before and during the pilot. Also record the time teams spend maintaining the catalog and documents.
>
> We found the owner, traced the failure, used the runbook, and checked recovery. We also saw how CI catches some stale records.
>
> Which recent incident or delayed release should we use to test this with our teams?

**Delivery cue:** Stop sharing the terminal. Leave the diagram visible for discussion.

## If the live demo stops

- If the outage command exits nonzero with the expected JSON, continue. That is the intended result.
- If a service is unreachable, use the [incident exercise](incident.md) and label its JSON as an expected example.
- If a page does not load, open its Markdown source from the owning service's `docs/` folder.
- If the repository check takes too long, show the output saved before the meeting. Say when you ran it.
- Always run `./scripts/demo.sh recover` after an interrupted outage exercise.
- If time is short, use the saved CI output and reduce the platform section to its first two paragraphs.

## Presenter reference

The script applies short sentences, active verbs, consistent terms, and one main point per sentence from [ASD-STE100, Issue 9](https://www.asd-ste100.org/assets/files/ASD-STE100_ISSUE9.pdf). It uses those writing principles; it does not claim full controlled-vocabulary compliance.

The prose also follows [Orwell's six rules](https://www.orwellfoundation.com/the-orwell-foundation/orwell/essays-and-other-works/politics-and-the-english-language/): avoid worn-out figures of speech, prefer short words, cut needless words, use active voice, replace needless jargon, and put clear meaning above rigid rules.

The talk's technical claims come from this POC's [architecture](architecture.md), [incident exercise](incident.md), [repository checks](repositories.md), [QA procedure](handover.md), and [pilot requirements](on-prem.md).
