# CLAUDE.md

This file gives guidance to Claude Code (and other AI assistants) when working in
this repository.

## Current state of the repository

> **Heads up:** As of this writing, `capitan-cavernicola` is a freshly
> initialized repository. It contains only this file and a placeholder
> `README.md` — there is **no application code, build system, dependency
> manifest, tests, or CI configuration yet.**

Because the project has no established structure or conventions, most of the
sections below are intentionally forward-looking. **When real code lands, update
this file to match reality** rather than leaving the placeholders in place.
Document what *is*, not what *might be*.

## Repository layout

```
.
├── CLAUDE.md   # This file — guidance for AI assistants
└── README.md   # Project title placeholder
```

There is no source directory, package manifest, or tooling configuration present.

## Working in an empty repository

When asked to add features or scaffolding, follow these principles:

- **Confirm the stack before scaffolding.** The name and contents give no
  indication of the intended language, framework, or purpose. Don't assume —
  ask the user what they're building (language, framework, target platform)
  before generating a project skeleton.
- **Establish conventions deliberately.** The first code added effectively sets
  the conventions for everything after it (formatting, directory layout, naming,
  test framework). Pick sensible, idiomatic defaults for the chosen stack and
  apply them consistently.
- **Add tooling alongside code.** When introducing a language/framework, also add
  its standard companions: a dependency manifest, a `.gitignore`, a linter/
  formatter config, and a test runner. Then document the commands here.
- **Keep `README.md` current.** Update it from a bare title to a real description
  as soon as the project's purpose is known.

## Development workflow

### Git & branching

- The default branch is `main`.
- Development happens on feature branches; do not commit directly to `main`.
- Use clear, descriptive commit messages written in the imperative mood
  (e.g. "Add user authentication", not "added auth").
- Push feature branches and open a pull request for review. **Do not open a pull
  request unless explicitly asked.**

### Build, test, and lint commands

_None yet — no build system or tests exist._

When tooling is added, document the canonical commands here, for example:

```
# install dependencies
# run the app
# run tests
# run the linter / formatter
```

Keeping these accurate is the single most useful thing this file can do for an
AI assistant, so prioritize updating this section.

## Conventions for AI assistants

- **Don't invent structure.** Since there are no existing patterns to match,
  avoid fabricating elaborate scaffolding. Make the smallest change that
  satisfies the request and let conventions emerge intentionally.
- **Verify before claiming.** With no tests or build yet, manually confirm that
  anything you add actually runs before reporting it as working.
- **Update this file.** Whenever you add code, tooling, or workflows that change
  how someone should work in this repo, reflect that here in the same change.
