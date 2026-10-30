# AI use disclosure

- Tool: OpenAI Codex (AI coding assistant).
- Purpose: inspect the user-provided problem statement and fork, adapt the
  dispatch implementation to the repository API, add regression tests, and
  draft/update the requested Markdown documentation.
- Credits or tokens shown by the tool: not available.
- Verification performed: reviewed the repository's visible tests and ran
  them locally; all 234 passed under the available Python 3.9.6 interpreter.
  This interpreter is below the repository's Python 3.10+ requirement.
- Work accepted or changed: the dictionary-based approach and implementation
  were adapted to the existing `service.py` interface; the earlier standalone
  scaffold was not copied into the fork.
