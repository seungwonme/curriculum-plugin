---
name: notion
description: "Notion workspace automation with ntn CLI for page/data-source search, read, query, create, update, upload, move, comments, and Markdown round-trip. Use when user asks for Notion/노션 page or DB work, ntn, Notion REST, page upload/update, media preservation, or workspace lookup. Do NOT use for curriculum design or lecture-material sync, Google Docs, Obsidian llm-wiki CRUD, generic markdown writing, or non-Notion planning/research/spec work."
---

# Notion

Transport skill for Notion workspaces. Use direct `ntn` commands and Notion REST; do not route to removed workflow sub-skills or legacy MCP-style Notion tool names.

## 기본 원칙

- Treat Notion as read-only by default.
- Run workspace-scoped commands through `scripts/ntn-ws.py <workspace> ...` — it resolves the name/alias to the full UUID and injects `NOTION_WORKSPACE_ID`, so raw IDs stay out of docs and logs. `NOTION_WORKSPACE_ID=<full-uuid> ntn ...` directly is fine when you already hold the UUID (e.g. from a project `AGENTS.md`); never use a UUID prefix — it looks like an auth failure.
- Start search/read work with `/v1/search` or `ntn pages get`.
- If the task is curriculum design or lecture-material Notion sync, use the curriculum skill family (`curriculum-notion-sync` for publishing) instead.

## Workspaces

Workspace IDs are user config, not skill content. `ntn` keeps registrations in `~/.config/notion/workspaces.json`; optional aliases live in `~/.config/notion/aliases.json` (user-managed).

```bash
scripts/ntn-ws.py --list                  # registered workspaces + aliases
scripts/ntn-ws.py --alias <alias> <name>  # save an alias (name fragment or full UUID)
```

## Quick Start

```bash
# Search recent pages
scripts/ntn-ws.py <workspace> api /v1/search -d '{"query":"검색어","page_size":10,"sort":{"direction":"descending","timestamp":"last_edited_time"}}'

# Read a page as Markdown
scripts/ntn-ws.py <workspace> pages get <page-id>

# Verify the selected workspace token
scripts/ntn-ws.py <workspace> api /v1/users/me
```

## Write Safety

`search`, `get`, and `query` are reads. `create`, `update`, `PATCH`, `move`, `comment`, `upload`, `trash`, `delete`, `archive`, and `--allow-deleting-content` are writes.

Before writes:

- Read `references/ntn-cli.md`.
- Fetch the current page or data source first.
- Preserve existing media, bookmarks, unknown blocks, and child pages unless the user explicitly says otherwise.
- Round-trip check after page updates.
- For large body replacements, generate a review HTML with `scripts/ntn-diff-viewer.py`, let the user check the changes they want in the browser, and write only the changes listed in the exported request file.
- For `trash`, `delete`, or `archive`, show candidates, count, reversibility, and exact command, then get separate explicit approval.

## Reference Routing

| Task | Read |
| --- | --- |
| Workspace switching/auth, direct REST, page/data-source query, create/update/move/comment/upload, divergence gates | `references/ntn-cli.md` |
| Markdown page creation/update, callouts, toggles, tables, round-trip checks | `references/markdown-to-blocks.md` |
| Copying images, links, descriptions, or page sections between Notion pages in the same workspace | `references/page-transplant.md` |

## Scripts

- `scripts/ntn-ws.py <name-or-alias> <ntn args...>` - workspace resolver: looks up the full UUID from ntn's config (plus user aliases) and execs ntn with `NOTION_WORKSPACE_ID` set. `--list` shows workspaces, `--alias` saves one. Run it, do not read it; details in `--help`.
- `scripts/ntn-diff-viewer.py OLD NEW [-o out.html] [--exclude '*.changes.md']` - renders Notion-flavored Markdown (ntn dump tags: callout, columns, pipe/HTML tables, bookmark, video, mention, images, frontmatter) into one review HTML: shared-scroll before/after, a rendered diff tab (red=deleted, green=added), a source line-diff tab, and a per-change checkbox with change-to-change navigation. The user checks the changes to keep and exports a `notion-revert-request/v1` JSON file; read that file and apply only the selected changes. OLD/NEW are each a `.md` file or a directory (paired by relative path). Run it, do not read it; details in `--help`. When it warns that a tag could not be rendered, that tag shows up as raw text in the panels and hides the real changes - add a handler in `render()` before trusting the review.

## Common Flows

For read/search requests, run search or `pages get` and report the relevant page IDs, titles, and evidence.

For page updates, fetch the page, make the smallest Markdown change, run `ntn pages update`, then fetch again to verify the intended delta.

For page creation, identify the parent page or data source first, confirm required properties for data-source children, then create with the smallest content that satisfies the request.

For destructive cleanup, stop after a read-only candidate list unless the user gives explicit deletion/trash/archive approval.
