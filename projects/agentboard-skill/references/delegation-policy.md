# Delegation and subagent policy

The skill routes accountability, not necessarily execution. A named role does not imply a separately running agent.

- Use real subagent execution **only when the user explicitly requests it or the selected command explicitly requires them (Create-Screens builder/reviewer), or the active project configures subagents and the runtime supports launching them**. Confirm successful invocation through actual tool results.
- If no subagent tool is available, act in the designated role sequentially and accurately say a role perspective was applied—not that an agent was spawned.
- Invoke only the minimum roles necessary. Typical ownership: Vision/Stories → Product Manager; Architecture → Solution Architect (consult Backend/Frontend as needed); Design → Product Designer (consult Frontend as needed); Review → Code Reviewer plus domain consultation.
- No agent may override an approved human constraint without flagging the conflict.
- Do not let agents independently invent product scope to fill missing inputs. Surface assumptions and blockers.
- Separate creator and reviewer wherever practical. When one runtime executes both, state that review is a self-check rather than independent validation.
- Delegation must return a traceable artifact or structured finding—not only "done".

Role definitions in `roles/*.md` are portable prompts and responsibilities. They are **not** automatically installed AgentBoard agent records. The Setup command reconciles them through verified app capabilities.

Create-Screens exception: a separate reviewer is mandatory for verified completion; the sequential role-perspective fallback remains partial/blocked and cannot be called independent review. See `screen-verification.md`.
