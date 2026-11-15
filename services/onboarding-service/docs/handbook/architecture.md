# Six services. Ten dependency links.

![Customer activation architecture](assets/architecture.svg)

## Read the map

Customer Activation calls all five providers. Workspace Provisioning needs both security policy and commercial entitlement. Policy, Subscription, and Notifications each share Tenant Directory. These extra reads deliberately model the coordination cost: a change in Identity can affect every team.

Arrows indicate caller → provider, not ownership transfer or event flow. Each catalog `dependsOn` link corresponds to an actual HTTP call. `providesApis` and `consumesApis` describe the same boundary as a discoverable contract.

There is no runtime cycle. The organizational entanglement comes from shared providers and a journey that crosses four teams. Backstage makes that existing structure visible; it does not simplify it automatically.

## Mermaid source

The SVG above is an offline illustration of this diagram. The Mermaid source is also in `docs/handbook/architecture.mmd` in the onboarding repository.

```mermaid
flowchart LR
  classDef cx fill:#e0e7ff,stroke:#6366f1,color:#172554
  classDef identity fill:#ccfbf1,stroke:#0d9488,color:#134e4a
  classDef commerce fill:#fef3c7,stroke:#d97706,color:#78350f
  classDef security fill:#ffe4e6,stroke:#e11d48,color:#881337

  subgraph CX[Customer Experience]
    O[Customer Activation<br/>Journey coordinator · 8086]
    N[Customer Notifications<br/>Welcome preview · 8085]
  end
  subgraph ID[Identity]
    T[Tenant Directory<br/>Identity and contact · 8081]
  end
  subgraph COM[Commerce]
    S[Subscription Entitlements<br/>Commercial eligibility · 8082]
  end
  subgraph SEC[Cloud Security]
    P[Security Policy<br/>Required controls · 8083]
    W[Workspace Provisioning<br/>Placement and readiness · 8084]
  end

  O -->|identity| T
  O -->|entitlement| S
  O -->|controls| P
  O -->|workspace preview| W
  O -->|notice preview| N
  S -->|tenant exists| T
  P -->|tenant exists| T
  W -->|policy decision| P
  W -->|entitlement| S
  N -->|recipient| T

  class O,N cx
  class T identity
  class S commerce
  class P,W security
```

## Intentional overlap, resolved

- “Active tenant” is split into verified identity, active commercial entitlement, allowed security policy, and workspace readiness.
- Customer Experience owns journey coordination; it cannot change Commerce or Cloud Security decisions.
- Tenant Directory is the authoritative contact source; Notifications does not keep a separate customer spreadsheet.
- Provisioning reads both prerequisite decisions and never guesses that a successful identity lookup implies authorization.

The read-only fixtures make these boundaries explicit. A real activation would also need idempotency, durable state, compensation, and a delivery mechanism for notices.
