---
name: show-code
description: >-
  Use when the user asks to see a line or block of lines of code or
  other content in any text-based file (source code, markdown, config,
  etc.) within a project that is being discussed, analyzed, or worked
  on — e.g. while reporting a finding during code authoring, debugging,
  refactoring, or review. Also use proactively when referencing a
  specific line or block in your own analysis — render it, don't just
  cite it.
---

# Show Code in Context

When the user asks to see code, or when you reference specific lines
in your analysis — **read the file and render the content directly in
chat as a fenced code block.** One tool call, one output. Done.

## Rules

1. **Read the file** with the Read tool.
2. **Immediately render** the relevant lines in a fenced code block
   with the appropriate language tag.
3. **Default context: 10 lines above and below** the target line(s),
   unless the user specifies a different amount.
4. **Show the file path and line range** above the block.

## Output format

```
`path/to/file.py` lines 30–50:
```

Followed by a fenced code block with the content and line numbers.

## The one rule

**The user cannot see Read tool results.** They only see your text
output. If you read a file and don't render the content in your
response, the user sees nothing. Every Read must be followed by
rendered output.

## Anti-patterns

- Reading a file and saying "There it is" — the user sees nothing.
- Multiple round-trips before rendering — just show it.
- Asking clarifying questions instead of showing the code — show
  first, ask after.
- Paraphrasing or summarizing code the user asked to see verbatim.
