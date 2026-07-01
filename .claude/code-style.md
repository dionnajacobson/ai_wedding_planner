---
paths:
  - "**/*.py"
---

# Code Style

## Principles

- DRY: Don't Repeat Yourself.

## Data Models

- Always use Pydantic over dataclasses.
- Attributes in data models should be alphabetized.
- Only define the parameters that are absolutely necessary for the implementation — others can be added later.

## Comments

- Don't explain WHAT code does, explain WHY we do it that way. If you don't know, don't comment.
- Attribute comments go above the attribute with a hash (e.g. `# This is a comment`).

## Functions

- Always add docstrings to functions and classes.
- Always return named variables from functions, e.g. `return value` instead of `return data[key].item`.
- Functions and class methods should be alphabetized within a file, public first then private (`_`-prefixed) at the bottom.
- Input arguments should be alphabetized.

## Imports

- Keep imports at the top of the file. Do not import inside functions or methods.

## Classes

- Inject stateless dependencies in `__init__` (services, clients, runners, registries) and build stateful dependencies in the method that uses them (e.g. per-request `Agent`, prompts, and run config inside `chat()` rather than on the class).

## Constants

- Constants should only be added if they're used multiple times. It's more readable to write strings in-line, where they are used.
