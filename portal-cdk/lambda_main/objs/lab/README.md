## Lab Access request flow

```mermaid
---
title: Lab Access Request Flow
config:
  theme: default
  flowchart:
    curve: monotoneY
---
flowchart TD
    style A fill:lightgreen,stroke:#333,stroke-width:4px,font-size:16pt
    style B stroke:#333,stroke-width:3px
    style D stroke:#333,stroke-width:3px
    style E fill:pink,stroke:#333,stroke-width:3px
    style H fill:pink,stroke:#333,stroke-width:1px
    style I fill:lightgreen,stroke:#333,stroke-width:1px
    style C fill:lightgreen,stroke:#333,stroke-width:3px
    style F fill:lightyellow,stroke:#333,stroke-width:2px
    style K fill:lightyellow,stroke:#333,stroke-width:2px
    style A1 fill:lightyellow,stroke:#333,stroke-width:2px
    style Z fill:lightgreen,stroke:#333,stroke-width:1px
    style Y fill:lightyellow,stroke:#333,stroke-width:1px
    style X fill:lightblue,stroke:#333,stroke-width:3px
    style W fill:pink,stroke:#333,stroke-width:1px
    Z@{ shape: procs, label: "Google Sheet"}
    Z --> Y@{ shape: cyl, label: "User in<br>Dynamo" }
    Y --Yes--> X(["**-Imported-**"])
    Y --No --> W@{ shape: dbl-circ, label: "Ignored" }
    A -.-> J@{ shape: cloud, label: "Acknowlegement<br>Email"}
    A(("**new**")) --> A1@{ shape: trap-t, label: "OSL Review" }
    A1 --> B("**-pending-**")
    B --> K{"Waiting<br>period"}
    K --> A1
    A1 --> C(["**-approved-**"])
    A1 --> D("**-returned-**")
    D -.-> L@{ shape: cloud, label: "Returned Email"}
    A1 --> E{{"**-rejected-**"}}
    B --> F{Security<br>Review}
    F --> C
    F --> E
    D --> A
    E -.-> H@{ shape: cloud, label: "Rejection<br>Email"}
    C -.-> I@{ shape: cloud, label: "welcome<br>Email"}
```

## Lab Tokens

To allow token processing for a lab, the `allows_tokens` attribute of 
`BaseLabConfig()` configuration must be `True`.

Tokens are currently manually provisioned. To create a token (until this is automated),
open the lab in DynamoDB and modify the `access_tokens` attribute.

Access tokens have 1 required, and 3 optional parameters:

```json
{
  "value": "<some cryptic string>",
  "profiles": ["profile1", "profile2"],
  "start-date": "YYYY-MM-DD HH:MI:SS",
  "end-date": "YYYY-MM-DD HH:MI:SS",
}
```

* **`value`** (_Required_): Something like UUID
* **`profiles`** (_Optional_): List of profiles granted by token. If not provided, the
labs default profiles are used
* **`start-date`** (_Optional_): Date when a token becomes active
* **`end-date`** (_Optional_): Date after which a token cannot be used

### Future:

`Lab()` objects have a function `create_access_token()` that can create tokens. However,
there is no way yet to invoke that function from the portal. Eventually, it should 
probably be integrated into the `Tokens` table on the lab management view.


