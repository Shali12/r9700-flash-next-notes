# Hermes Agent side

How the agent uses the rig: a cloud model plans and reviews, and delegates implementation to two local workers through
Hermes's `delegate_task` tool ([docs](https://hermes-agent.nousresearch.com/docs/user-guide/features/delegation)).
Hermes runs on a separate machine; only model inference happens on the rig.

| File | What it is |
|---|---|
| [delegation.yaml](delegation.yaml) | The `delegation:` block for the parent profile |
| [model-block.yaml](model-block.yaml) | The `model:` block for a profile that talks to the rig directly |
| [playbook.md](playbook.md) | The parent's delegation playbook, with placeholders |

Things that matter for the measurements in this repo:

- **Hermes sends `"reasoning_effort":"medium"` and `"stream":true`, and no sampling settings.** The server's defaults
  therefore decide temperature, top_p, top_k and min_p. Seen by capturing the request fields on the rig.
- **Three numbers must follow the server option**: `context_length`, the playbook's token number, and
  `max_concurrent_children` (equal to the server's slots). If they are left too high, long prompts are rejected and
  extra workers wait for a slot.
- **Every request starts with about 12,500 tokens** of system prompt and tool list, and subagents compact their
  context at about half the window, so a 65,536-token slot leaves about 18,000 tokens of working room.
- **All children run one model**; there is no per-task model in `delegate_task`.

No addresses, tokens, keys or account identifiers are included; `RIG-ADDRESS` is a placeholder.
