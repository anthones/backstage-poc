# Backstage: finding our way across teams

A live Community of Practice session for colleagues who have never used Backstage. Allow **50 minutes for the presentation, then 10 minutes for Q&A (60 minutes total)**. Timings include navigation, demonstrations, and pauses; rehearse them with the local environment.

Read the blockquotes aloud. **Show**, **Do**, and **Pause** are presenter instructions. Keep one page still while explaining it, and point to the field you are discussing. Let people read before moving on.

| Time | Audience question | What to show |
| --- | --- | --- |
| 0:00–15:00 | What is Backstage, and where does its information come from? | Catalog, one service, API, documentation, ingestion |
| 15:00–30:00 | How does the customer UI connect to work across teams? | Customer website, journey, ownership, dependencies |
| 30:00–35:00 | How does Jira help product owners and business analysts use this context? | Live public connection, then fictional linked work |
| 35:00–48:00 | How do support and QA receive a useful handover? | Customer-visible failure, L1/L2 instructions, recovery, QA |
| 48:00–50:00 | What should we try in our company? | Small pilot and discussion prompt |
| 50:00–60:00 | What concerns would affect adoption? | Prepared Q&A and audience questions |

Use **Customer Activation** as the example throughout. It means getting a customer's workspace ready to use. **Security Policy** is one of the services it needs; it supplies required security controls. Explain the other services only when they become relevant.

## Before people join

From the workspace root, prepare dependencies if needed with `./scripts/setup.sh`. Then build the documentation and start the PoC:

```sh
./scripts/build-docs.sh
./scripts/start.sh
```

Keep the runner open. In a second terminal, confirm the starting state:

```sh
./scripts/demo.sh recover
```

Expect `result.activation` to be `ready`. Rehearse `happy`, `outage`, and `recover` before the meeting, and finish with `recover`. Save the outage response for the fallback below.

Keep the customer website, Backstage, terminal, and editor available. Use the links below as a navigation reference; they do not all need separate tabs. Choose Guest if prompted:

| Page | Use |
| --- | --- |
| [Customer website](http://localhost:8080/) | Customer-facing subscription and activation previews |
| [Jira & delivery](http://localhost:3000/delivery) | Real public connection and fictional handover example |
| [Catalog](http://localhost:3000/) | Opening and service discovery |
| [Security Policy component](http://localhost:3000/catalog/default/component/policy-service) | Owner, API, documentation links, ingestion result |
| [Security Policy API](http://localhost:3000/catalog/default/api/policy-service-api) | Interface description |
| [Customer Activation component](http://localhost:3000/catalog/default/component/onboarding-service) | Customer journey entry point |
| [Dependency graph](http://localhost:3000/catalog-graph) | Relationships between services |
| [Architecture illustration](http://localhost:3000/docs/default/component/onboarding-service/handbook/architecture) | Backup if the graph is hard to read |
| [Activation runbook](http://localhost:3000/docs/default/component/onboarding-service/runbook) | L1 starts with the reported symptom |
| [Policy runbook](http://localhost:3000/docs/default/component/policy-service/runbook) | L2 diagnosis and recovery |
| [Policy QA and release](http://localhost:3000/docs/default/component/policy-service/qa) | Test expectations and release handover |
| [QA coordination](http://localhost:3000/docs/default/component/onboarding-service/handbook/handover) | Cross-team release record |

In the editor, open `services/policy-service/catalog-info.yaml`, its `docs/runbook.md`, and the `catalog.locations` section near the bottom of `backstage/app-config.yaml`. Rehearse the small title edit in section 4 and restore it before the meeting. Increase browser, editor, and terminal text sizes.

Customer and company examples and contacts are fictional. The Jira public mode displays real Atlassian issues, explicitly unrelated to these services. The services make test requests; they do not create real customer workspaces or send email. The outage control is specific to this local PoC.

## Part 1 — Meet Backstage and understand the information

### 1. 0:00–3:00 — Give people a reason to look

**Show:** Catalog. Do not start a command or open the graph yet.

> Think about the last time you needed help from another team. You may have known the product, but not which service was involved, who owned it, or where the useful documentation lived.
>
> Today we will explore whether Backstage could make those questions easier to answer.
>
> We will start with a short tour and see where the information comes from. Then we will look at work that crosses several teams. Finally, we will follow a support issue and a QA handover.
>
> You do not need to know the code to follow this session.

**Pause:** Ask, “Who has had to ask around just to find the right team?” Allow a show of hands; save incident stories for discussion.

> Backstage is an open source framework for building an internal developer portal. A portal is a shared website that brings useful information and tools together.
>
> This is our small example of that website. Its catalog is a directory of our software. We can use it to find a service, the team responsible for it, the services it depends on, and its instructions.

### 2. 3:00–8:00 — Read one service page together

**Do:** In the catalog, select **All** if the view is restricted to owned items. Choose kind **Component** if needed. Find **Security Policy** using the catalog's text filter and open it. It may also appear under its identifier, `policy-service`.

> Each entry describes a piece of software. Backstage calls this kind of entry a component. In our example, the components are services: small applications with particular jobs.
>
> Let us open just one: Security Policy. It tells other services which security controls a customer workspace requires, such as encryption.

**Show:** The service description, then its owner. Point to each before speaking.

> The description tells us what it does. The owner tells us which team is responsible for it: Cloud Security.
>
> If I need clarification about a security requirement, I now know where to start.

**Do:** Follow the owner link. Briefly show the Cloud Security group page, then return to Policy.

> The owner is a team record that we can open. These are example team details; a company pilot would need our actual contacts and escalation routes.

**Show:** Policy's API entry, using the prepared API tab if needed. Point to the documented operation without expanding every schema.

> An API is the agreed way one application asks another for something. This page describes the request and the response. Developers and testers can inspect that agreement here.

**Show:** Follow Policy's **L1 / L2 runbook** link. Let the page settle.

> Here are the operating instructions attached to the same service. Backstage's documentation feature is called TechDocs.
>
> We have moved from “What is this?” to “Who owns it?” to “How do I use or support it?” We will use these instructions later.

### 3. 8:00–11:00 — Show where the information lives

**Show:** Policy's `catalog-info.yaml` in the editor. Show only the first Component record. Point to `metadata.name`, `metadata.title`, `spec.owner`, and `spec.dependsOn`; do not scroll into the long API definition.

> Where did the service page get those facts?
>
> This small text record lives beside the service's code. The team writes its name, description, owner, and dependencies here. YAML is simply the file format used for that record.
>
> Backstage reads the record and uses it to build the page we just visited. Reading and processing that information is called ingestion.
>
> The name is the service's identifier. The title is the name people see. The owner points to the responsible team. “Depends on” lists other services this one needs.

**Show:** `docs/runbook.md` beside the browser's runbook page.

> The instructions also come from the team's repository: the place where it keeps and reviews its code and related files. This text becomes the documentation page.
>
> Teams can review a service change together with its operating instructions. Other teams can find the published result through the same portal.

### 4. 11:00–15:00 — Make ingestion visible

**Show:** `catalog.locations` in `backstage/app-config.yaml`. Point to the Policy file location.

> Backstage needs to know where to look. In this PoC, we have registered a separate catalog file for each of the six backend service folders and one frontend folder on this computer.
>
> In a company setup, we could connect it to our internal Git repositories. Teams would update their records through their usual review process, and Backstage would read the configured sources.

**Do:** Return to Policy's `catalog-info.yaml`. Change only the first `metadata.title` from `Security Policy` to `Security Policy (demo)`. Save it. Return to the Policy component page and reload after processing has had time to run.

**Presenter note:** The configured catalog processing interval has a suggested minimum of 15 seconds; it is asynchronous. Allow up to 90 seconds in rehearsal. While waiting, explain the two paths below. If the title has not appeared by the end of this section, use the fallback and continue.

> I have changed the display title in the source file. Watch the heading in Backstage. We are making the change at its source, and the catalog will read it again.

**Show or point through this explanation:**

```text
Service record → Backstage reads it → Catalog page
Documentation text → Build and publish → TechDocs page
```

> There are two update paths here. The catalog rereads service records. Documentation is built into web pages and published separately. In this PoC, a script does that publishing; in a company setup, it can be part of the team's automated pipeline.
>
> Changing a document does not update the published page until that build and publication happen.

**When the title appears, say:**

> There is our changed title. The source file supplied the information; Backstage made it visible.

**Do:** Restore `Security Policy`, save, and allow it to be ingested. Continue without waiting on screen for the second refresh. Leave the API record unchanged throughout.

> That is the basic model: teams maintain the information, and colleagues use a shared place to find it. If a team declares the wrong owner or misses a dependency, that record needs correcting.

## Part 2 — Use the shared view to work across teams

### 5. 15:00–20:00 — Begin with what the customer actually uses

**Show:** The customer website at **http://localhost:8080/**. Leave **Acme · active subscription** selected. Click **Check subscription**, then **Preview activation**. Pause after each result.

> Here is the customer's application. It runs separately from Backstage. The customer uses this website; our colleagues use Backstage to understand and support it.
>
> The subscription check asks Commerce whether this customer has access. The activation preview asks Customer Activation to check the full journey. Both are real requests to our running demo services, using fictional customer data.
>
> We have two successful results. Keep that distinction in mind: being allowed to use a workspace and getting the whole workspace ready are different checks.

**Do:** Select **Example · suspended subscription**, then click **Preview activation** and show the blocked result. Return to **Acme · active subscription** and repeat the preview before continuing.

> This is an expected business decision: a suspended subscription should be blocked. It is different from a technical outage. Both may stop a customer, but the explanation and responsible team differ.

**Show:** Expand **Support evidence** on the successful activation. Point to the request ID and `simulation: true`, then collapse it.

> The demo keeps the service response available as support evidence. Nothing has been provisioned: this is a preview. A production customer interface would show only the appropriate message and support reference.

**Do:** Open **Find this application in Backstage**. Point to Customer Portal's type **website**, its owner, its two consumed APIs, and its dependency relationships.

> The catalog can describe the frontend as well as its backend services. This website belongs to Customer Experience. It calls Subscription and Activation through its own small API bridge.
>
> It does not call Policy directly. But when Activation needs Policy, the customer website is indirectly affected. Let us follow that relationship.

**Pause:** Ask, “If the website displays an activation error, would that alone tell us that the frontend code is broken?” Take one answer, then trace the relationship on screen.


### 6. 20:00–24:00 — Introduce one customer journey

**Show:** Follow Customer Portal to Customer Activation, then open the dependency graph. If the graph is crowded, use the prepared architecture illustration. Point to one service at a time.

> Now let us connect this to how we work.
>
> A customer wants to activate a workspace. That sounds like one task. In this example, it needs work owned by four teams.

**Point:** Customer Activation, Tenant Directory, Subscription Entitlements, Security Policy, Workspace Provisioning, then Customer Notifications.

> Customer Experience coordinates the activation. Identity supplies the customer record. Commerce checks whether the subscription allows access. Cloud Security supplies the security requirements and workspace preparation. Customer Experience also owns the customer notification.
>
> Each team has a reasonable responsibility. The difficulty is making the whole journey work across those responsibilities.

**Show:** One arrow from Activation to Policy. Then Policy to Tenant Directory.

> An arrow means “this service depends on that service.” Activation needs Policy. Policy, in turn, needs the customer record from Identity.
>
> The graph comes from the declared relationships. It helps us see who relies on whom. It describes the structure; we will use a running request later to see an actual failure.

**Audience exercise (90 seconds):** Keep the graph visible. Ask people to identify one service that needs Identity and name its owner. Take two answers, then open one record to check. Explain that a dependency shows whom to involve; it does not prove that every change breaks that consumer.

### 7. 24:00–28:00 — Show how a silo becomes a delay

**Show:** Keep the graph still. Focus on Policy and its two direct consumers: Activation and Workspace Provisioning.

> Imagine Cloud Security needs to add a required security control. This is a change scenario for discussion; we are not changing the policy code today.
>
> A ticket inside that team might say, “Update the policy service.” But who else needs to know? Who must adapt their work? Who will check the customer outcome?

**Pause:** Let people look at the two incoming dependency arrows.

> Here we can identify two direct users of Policy: Workspace Provisioning and Customer Activation. We can open their records and find their owners before we commit to a release date.
>
> Without that shared view, we may discover the missing coordination during testing or after release. Someone then has to reconstruct the dependency chain through messages and meetings.
>
> With this view, we have a concrete starting point for the conversation: here is the service being changed, here are the services that use it, and here are the responsible teams. We call those users its consumers.
>
> Those teams still need to agree on what the change means, whether it is compatible, and when to release it. Backstage helps us find the participants and the information they need for that agreement.

**Do:** Open Customer Activation's owner, then return to Policy's owner. Avoid following further links.

> There are two responsibilities to keep clear. Cloud Security owns the policy service and its repair or change. Customer Experience owns coordination of the full activation journey.
>
> When another team takes on a repair, the customer journey still needs someone coordinating it. That is an agreement we must make explicit and record.

### 8. 28:00–30:00 — Connect the screen to the company problem

**Show:** Return to the Customer Activation overview.

> Think of three recurring delays: finding the right team, discovering a dependency late, and receiving work without enough context.
>
> The catalog helps with the first by giving us an owner to contact. The relationships help with the second by showing declared consumers. The attached documentation gives us a place for the context needed in a handover.
>
> That could mean less time searching, fewer tickets passed between teams, and fewer surprises late in delivery. We should test those outcomes in our own work.
>
> To make this useful, teams need to agree what ownership means and keep their records current. The platform team can run the portal and its connections; service teams maintain their service information. Support and QA should help define the instructions they need.

**Pause:** Ask, “Where do we usually lose the most time: finding an owner, finding a dependency, or getting a complete handover?” Take one or two short answers. Connect them to the fields already shown.

> We have found the software and the teams. Next, let us connect that context to planned work in Jira, before following a support issue and a QA handover.

### 9. 30:00–35:00 — Jira: connect a feature to the work and agreements it needs

**Show:** **Jira & delivery** in Backstage's sidebar, or `http://localhost:3000/delivery`. Start with **Atlassian public Jira · live read-only**. Let it load. Point to the source notice, retrieved time, issue status, and one link back to Jira.

> This is a real, read-only connection to Atlassian's public Jira tracker. These are Atlassian's issues, unrelated to our fictional services. It shows that we can bring work records into the portal and link back to their source.
>
> For our company story, I will now choose a separate, explicitly fictional example. We have not created or changed anything in Atlassian's Jira.

**Do:** Select **Activation handover · fictional example**, with **Whole activation journey** selected. Point to ACT-101, ACT-102, and ACT-103. Read the summaries, not all the notes.

> Here is the policy change, the work in its workspace consumer, and acceptance of the full activation journey. The example records work dependencies between them.
>
> A product owner can ask which teams must contribute to the promised customer outcome, and which agreements or evidence are still missing. Finishing the policy ticket alone does not complete the feature.
>
> A business analyst can find the owner of the business rule, compare the API agreement with the desired customer behavior, and agree concrete acceptance examples with the affected teams.

**Do:** Filter to **Customer Portal**. Point to ACT-104, the customer message, and ACT-106, the support checklist. Follow **Open Customer Portal in the catalog**.

> The frontend needs a useful customer message, and support needs enough evidence to act. Those requirements can be part of the planned work instead of being discovered at the end.
>
> In this example, the service record identifies the Jira project and a service label. That mapping connects the fictional work to its service. Connecting our private Jira would also require its credentials, access rules, and real mappings.
>
> The two kinds of relationship answer different questions. Catalog dependencies tell us which software uses which software. Jira links tell us which work items have a recorded relationship. Teams must still confirm the actual delivery constraints and release readiness.

**Pause:** Ask a product owner or BA, “What information is usually missing when you try to agree the scope or acceptance of a change like this?” Allow one short response. Keep changes and approvals in Jira and the agreed release process.

## Part 3 — Give support and QA enough information to act

### 10. 35:00–39:00 — L1: start from the customer's symptom

**Show:** Terminal. Run one command at a time from the workspace root.

```sh
./scripts/demo.sh happy
```

**Point:** `result.activation: ready`. Do not explain every field. This repeats the successful baseline already seen in the customer UI.

> This happy command repeats the successful activation using a terminal instead of the customer website. It confirms our starting point; it does not reset a fault.
>
> I will now use the demo's fault control to make Security Policy unavailable, and repeat the same journey.

```sh
./scripts/demo.sh outage
```

**Expected:** The fault-control response appears first, then the failed activation response. The command exits nonzero by design. Point to `request_id: demo-outage` and the `root_cause` fields naming `policy-service` and `cloud-security`.

> The customer sees “activation failed.” The response gives us more detail: the policy service is unavailable, and its owner is Cloud Security.
>
> Our demo service code produces this error information. Backstage gives us the service record and the instructions to use with it.

**Do:** Return to the customer website. Click **Check subscription**, then **Preview activation**, keeping Acme selected. The subscription check still succeeds; activation now shows **We could not prepare your workspace**. Expand **Support evidence**. The browser request has its own request ID; do not claim it is `demo-outage`.

> This is the same customer-facing journey we saw earlier. The subscription check still works, while activation fails. Support can start with that symptom and reference, then use the service record to find the next action.

**Show:** Activation runbook, **L1: first five minutes**.

> L1 means first-line support: the people receiving and assessing the report.
>
> They start with the service the customer was using. This page tells them what evidence to collect and how to route the issue: customer ID, time, request ID, and the error response.
>
> A request ID is a reference we can use to find the same request in different services' logs. It gives the next team a specific event to investigate.

**Point:** Step 5, routing to `root_cause.owner` and keeping Customer Experience as coordinator.

> The useful handover is: “Activation failed for this customer, at this time, with this request ID. The response points to Policy. Here is the evidence.”
>
> Cloud Security receives something it can investigate. Customer Experience continues to coordinate the customer issue. If there is no response at all, support starts with the affected service's catalog owner.

### 11. 39:00–42:00 — L2: investigate, recover, and confirm the journey

**Show:** Policy runbook, **L2: isolate the failing boundary**.

> L2 means the specialists who investigate further. In this example, Cloud Security has the knowledge and responsibility to investigate Policy.
>
> Their instructions describe the service's dependencies, where to find its logs, and how to check recovery. They can use the same request ID collected by L1.
>
> Both groups use the same service documentation, with steps suited to their work. The next team can continue from the evidence already collected.

**Show:** The runbook's recovery section. Then run:

```sh
./scripts/demo.sh recover
```

**Expected:** The demo fault is cleared and activation returns `result.activation: ready`. Return to the customer website and click **Preview activation** again to show the successful customer result. The previous on-screen result does not refresh itself.

> Recover clears our deliberately injected fault and repeats activation. It gives us a known reset for this exercise. Backstage did not detect or fix the service; we used its information to support the investigation. In a real incident, the service owner would use that system's recovery procedure.
>
> We check the original customer journey before closing the issue. A service process being up is only one part of recovery.
>
> The value for support is having a clear next action, a responsible team, and evidence that carries through the handover. That depends on teams writing usable instructions and checking them when services change.

### 12. 42:00–46:00 — QA: turn “ready for testing” into a useful handover

**Show:** Policy's **QA and release** page. Point to the acceptance table.

> Now we move from an incident to a planned change. Return to our earlier example: Cloud Security wants to add a required security control.
>
> QA means quality assurance: checking that a change works as expected and that existing behavior still works. QA needs more than a message saying, “The development is done.” They need to know what changed, how to exercise it, what result to expect, and what else might be affected.
>
> This page already gives us repeatable examples for the current PoC. These are named test customers with known conditions.

**Point:** Three rows only: `tenant-acme`, `tenant-suspended`, and Policy outage/recovery. Translate the results rather than reading status codes aloud.

> The normal customer should activate successfully. A customer with a suspended subscription should remain blocked. If Policy is unavailable, activation should fail with a useful explanation and succeed again after recovery.
>
> Those are baseline checks we can repeat. For the proposed new control, the provider must also document its meaning and add specific acceptance criteria and tests. The existing table does not prove a future change is correct.

**Show:** Dependency graph briefly, then return to QA notes.

> QA can use the dependencies to choose coverage beyond the changed service. Policy's own check may pass while Workspace Provisioning interprets its answer incorrectly. We also need to check the full activation journey.
>
> This gives QA a reason for each test, rather than asking them to guess which other teams' work might break.

**Audience exercise (60 seconds):** Ask, “What result should we expect when the customer exists but the subscription is suspended?” Invite QA or a BA to state the customer outcome and the responsible decision owner. Confirm that identity can succeed while Commerce blocks access; use this as an example of an acceptance rule spanning teams.

### 13. 46:00–48:00 — Show what must accompany the handover

**Show:** QA coordination page, **Release record template**. Present it as a template to complete for a change, not an already approved release.

> This is the information we want to arrive with a change: the exact version being tested; what changed and why; the affected consumers; test instructions and expected results; release order; and how to roll back.
>
> For our proposed policy change, Cloud Security supplies the changed requirements and provider evidence. The consumer teams confirm how they will handle it. QA records what passed and what remains unresolved. Customer Experience coordinates acceptance of the full journey.
>
> Backstage makes the service documents and relationships easy to reach. The teams still need to complete the release record and agree the handover. The graph itself does not send approvals or confirm that a release is safe.

**Show:** Policy repository's code, catalog file, API definition, and `docs/` folder in the editor. Do not run the repository verification suite during this introduction.

> We can review the relevant code, interface, catalog information, and instructions together. This PoC also has automated checks for some mismatches between them, such as an API route changing while its recorded definition stays unchanged.
>
> Those are checks added to this project. People still need to review whether the instructions are understandable and correct. Support and QA should help shape those instructions and have a practical way to contribute corrections.

## 48:00–50:00 — Invite a practical next step

**Show:** Customer Activation overview. Stop switching pages.

> We started by finding one service and seeing where its information comes from. We then used its relationships to find the teams involved in a change. Finally, we used the attached instructions to carry evidence into support and expectations into QA.
>
> A useful next step would be one real customer journey involving several teams. Record its owners and dependencies, and give support and QA the information they need to use it.
>
> Before and during that pilot, measure the time to find the responsible team, the number of ticket transfers, and the number of handovers returned for missing information. Also record the effort needed to maintain the information.
>
> Which recent incident or delayed release would be a useful case to try?

**Pause:** Leave the service page visible. Invite questions for the next ten minutes.

## 50:00–60:00 — Q&A

Use the [Q&A preparation](qa-questions.md) for short answers and suggested screens. Prioritize concerns about added maintenance, existing Jira/documentation tools, accountability, and what happens when teams disagree. Take three or four questions; record unresolved decisions with an owner.

> What would this change in your team's daily work, and what would make it unhelpful?

If nobody starts, invite: “We already have Jira and documentation. What would have to improve for this to earn its place?” Answer with one concrete journey and the pilot measurements, then invite a different perspective.

## Presenter fallback notes

| If this happens | Continue this way |
| --- | --- |
| Only some services appear in the catalog | Select **All** and kind **Component**; clear remaining filters. Use a prepared service link if needed. |
| The ingestion title change takes too long | Say, “Catalog processing has not caught up yet. This is the source record and the page it feeds.” Restore the original title in the file. Do not claim to have shown a completed update. |
| The graph is crowded or fails to load | Use the architecture illustration. Explain that it is a prepared diagram of this PoC, not a live status display. |
| Public Jira is unavailable | Say the live connection is unavailable. Explicitly select the fictional source to explain the handover; do not present it as fetched Jira data. |
| The customer website fails to load | Use the API commands, label them as requests behind the customer UI, and show its catalog record and dependencies. |
| The outage command prints a curl error and exits nonzero | Continue if the expected failure JSON is present. That exit is deliberate. |
| A service fails unexpectedly | Use the saved rehearsal response or the [incident exercise](incident.md). Say it is recorded example evidence. Follow the same support steps. |
| A documentation page fails to load | Open the corresponding Markdown source in that service's `docs/` folder. |
| Time is running short | Omit the live title edit and show its source-to-page mapping. Keep the three-part order and the L1, L2, and QA examples. |

After the meeting, restore Policy's original title if necessary and run `./scripts/demo.sh recover` if an outage was injected. Ctrl-C in the runner stops its processes.

## Background for presenter questions

These are follow-up references, not extra sections to read aloud.

- Backstage can be extended with plugins and software templates; this session demonstrates the catalog, relationships, APIs, and TechDocs. See the official [Backstage overview](https://backstage.io/docs/overview/what-is-backstage/).
- Catalog metadata can be maintained in repositories and updated through a normal Git workflow. See the official [Software Catalog documentation](https://backstage.io/docs/features/software-catalog/). This PoC's registrations, polling, and custom checks are described in [Repositories and CI](repositories.md).
- This PoC builds and publishes documentation separately from catalog processing. The official [TechDocs architecture](https://backstage.io/docs/features/techdocs/architecture/) explains the build-and-publish approach.
- Company sign-in, authorization, persistent storage, and operations belong in a real deployment plan. See the local [on-premises pilot notes](on-prem.md).
- The [Jira guide](jira.md) explains the live/public versus fictional sources and benefits for product owners and BAs. [Q&A preparation](qa-questions.md) covers likely adoption concerns.
- The [ownership directory](ownership.md), [incident exercise](incident.md), and [QA coordination guide](handover.md) explain the agreements used in this example.
