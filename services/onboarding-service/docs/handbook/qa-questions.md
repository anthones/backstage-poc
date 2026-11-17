# Q&A: questions we should expect

Reserve **10 minutes after the 50-minute presentation**. These are likely questions to prepare for, not assumptions about colleagues' motives. People protecting their team's time may have valid concerns about maintenance, accountability, access, and another initiative that adds work.

Start with: **“What would this change in your team's daily work, and what would make it unhelpful?”** Hear the whole concern, give a short answer, and show one concrete example if useful. Aim for three or four questions. Capture unresolved decisions with an owner; do not invent a company policy during Q&A.

## Most likely questions

### “We already have Jira and Confluence. Why another tool?”

> Jira records planned work, and our documentation tools hold knowledge. Backstage connects software to the teams, interfaces, dependencies, and instructions needed to work on it. We should test whether that connection saves time finding context. If it only duplicates pages and boards, we have not designed a useful pilot.

**Show:** A service's owner, API, runbook, and linked Jira example. Explain which information stays in each source.

### “Who will keep this up to date? My team has no spare capacity.”

> That effort belongs in the pilot's cost. Teams maintain the small set of facts and instructions about their own services; the platform team maintains the portal. We should begin with one journey and a small useful record, review it when that service changes, and measure maintenance effort as well as time saved.

**Follow-up to invite:** Which current document or repeated request could this replace? Do not promise that software removes maintenance.

### “Isn't this an organizational problem that software cannot fix?”

> Yes, we still need agreements about responsibilities, communication, and handover. The shared view helps us make those agreements concrete and accessible. We should use it to support a working agreement, then measure whether that agreement improves actual work.

**Show:** Cloud Security owns the provider; Customer Experience coordinates the customer journey.

### “If my team is listed as owner, will every ticket get dumped on us?”

> The owner record gives people a starting point. We still need a routing agreement and enough evidence to justify an escalation. In this example, the journey coordinator stays involved while the provider investigates its part. We should agree the meaning of ownership and escalation with teams before publishing their records.

**Show:** Activation runbook, step 5, and its evidence packet.

### “Our service passed its tests. Why are we responsible for someone else's failure?”

> Your team remains responsible for its own service and agreed interface. The journey owner coordinates checks across the participating services. Shared acceptance examples make the boundary visible: what your service promises, what its caller expects, and who checks their combination.

**Show:** Policy's API and the journey regression matrix. Avoid assigning a root cause solely from a graph.

### “We already know who to contact. What does this add?”

> That knowledge is useful. The test is whether a new colleague, a different shift, or another team can find the same answer without needing you to be available. We can use one real support case to compare how long that takes.

### “Can it tell us which team is blocking delivery?”

> It can show declared software dependencies and explicitly recorded Jira work links. We still need to confirm whether one item really prevents another from progressing and what agreement is missing. Use the view to arrange the right conversation, rather than treating a dependency arrow as a performance judgment.

**Show:** Catalog dependency versus the fictional ACT-101 → ACT-102 work link. They describe different things.

### “Jira says Done. Does that mean the feature is ready to release?”

> A workflow status tells us what that team has recorded. Release readiness also needs compatible versions, acceptance evidence, support instructions, and any required agreements. We should define those requirements for the journey and attach their evidence to the release record.

**Show:** QA coordination's release record template.

## Questions about trust and adoption

### “What if the owner or dependency is wrong?”

> It can mislead people, so records need named maintainers and a practical correction process. This PoC checks some facts against code; it cannot prove every dependency or sentence is correct. During a pilot, validate the records with the teams and deployed system, and record corrections when an incident exposes a gap.

### “What happens when teams disagree about ownership?”

> Backstage cannot decide that. The affected leads need to resolve the responsibility and escalation agreement, then update the records. Publishing a disputed name does not create a working agreement.

### “Can we adopt this without reorganizing the company?”

> We can try one journey using today's teams and repositories. First agree who coordinates the outcome and what each participant provides. That lets us test a better handover before considering broader changes.

### “Can another team browse our confidential work?”

> Access must be designed for our deployment and the connected tools. This local demo uses Guest access and public or fictional Jira data. A private Jira connection needs an explicit permission model; a broad integration account could expose work to portal users who could not otherwise see it.

**Presenter note:** Do not claim Jira's end-user permissions automatically carry through a service-account integration. No private Jira credentials are used in this PoC.

### “Will this become a tool for ranking or blaming teams?”

> For this pilot, I propose measuring the journey: search time, transfers, returned handovers, and maintenance effort. A dependency count does not measure a team's performance. We should agree how pilot data will be used with the teams involved.

### “Do L1 support, product owners, and BAs have to learn YAML?”

> They can browse the portal and use the instructions without editing YAML. We do need a contribution workflow they can use to correct documents and improve acceptance examples. The pilot should test that workflow with them, rather than assuming that a repository is convenient for everyone.

### “Who runs and funds the portal, and what if it is unavailable?”

> A pilot needs a named platform owner, a maintenance budget, and an operating plan. The source files remain in repositories, and published records should link to the owning sources. Support also needs a fallback for essential instructions and escalation routes when the portal is unavailable.

## Questions about this demonstration

### “Is the customer website Backstage?”

> They are separate applications. The customer uses the website on port 8080. Colleagues use Backstage on port 3000 to find its owners and supporting information. The website calls Subscription and Activation; it does not call Backstage to complete those previews.

### “Why does the website call Subscription if Activation checks it too?”

> The separate check lets a customer see subscription eligibility before trying the full journey. Activation still checks the prerequisites itself. A successful preliminary screen must not allow a caller to bypass the backend's decisions. It also lets us show that subscription can succeed while a later activation step fails.

### “Did Backstage detect and repair that outage?”

> No. The demo service code produced the error evidence. We used Backstage to find the owner and instructions. The presenter cleared a deliberately injected fault, then checked the customer journey again. Detection, paging, and automated repair would require further integrations and operating procedures.

### “What exactly do happy, outage, and recover prove?”

> Happy gives us a successful baseline. Outage makes one known dependency fail so we can practice interpreting the symptom, evidence, and handover. Recover resets that demo fault and checks that the journey succeeds again. They illustrate how we use service evidence and Backstage together; they do not prove that Backstage fixed an incident or improved productivity.

**Show:** The [command explanation](incident.md#what-the-three-commands-demonstrate).

### “Is this a real Jira integration or just sample data?”

> The public mode makes a read-only API request to Atlassian's real public issue tracker. Those tickets are unrelated to our services. The activation mode is explicitly fictional and illustrates how our own work could be mapped to service records. It does not create tickets, change statuses, or collect approvals.

**Show:** The source selector and notice on the [Jira view](http://localhost:3000/delivery).

### “Can we connect our own Jira and automatically find all affected work?”

> That would need our instance connection, credentials, access rules, and an agreed mapping between issues and catalog services. A project alone may cover many services, so we may need labels, Jira components, or another maintained field. Finding relevant records is possible; complete impact analysis still depends on the quality of those mappings and dependency records.

**Show:** Policy's `jira/project-key` and `acmesecure.example/jira-label` annotations. The ACT mapping in this PoC is fictional; private Jira is not connected.

### “What is the success criterion, and when would we stop?”

> Before starting, agree a short pilot, baseline measurements, and a review date. Look for less time finding owners and fewer transfers or returned handovers, while counting upkeep. If those outcomes do not improve enough to justify the effort, change the approach or stop extending it.

## Close the discussion

Ask for **one real journey, participating teams, and someone willing to help define a complete handover**. Record open decisions about ownership, access, publishing, and operating cost. Keep a longer platform rollout decision separate from this small experiment.
