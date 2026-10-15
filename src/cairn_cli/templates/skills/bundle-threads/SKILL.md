---
name: "bundle-threads"
description: "Tie related Threads together (same underlying problem, a duplicate, or work that should ship together) so they show up as one group in the ledger and in lookups. Only links Threads: it doesn't merge them or change their stage or status. Also unbundles."
argument-hint: "two or more thread ids, an optional bundle name, or 'unbundle <thread id>'"
metadata:
  product: cairn
  source: "whats-next optional skills (bundle-threads)"
user-invocable: true
disable-model-invocation: false
---

## What this does

Records that two or more Threads belong together. Every Thread in the group gets the same `bundle` name and lists the others in `bundled_with`, so `cairn find <id>` on any of them shows the whole group, its signals, and its Specs.

It's only a link. Each Thread keeps its own stage, status, owner, signals, and Spec.

## Required inputs

1. Two or more Thread ids. If the PM gives only one, ask which Threads to tie it to. `cairn find "<key words>" --kind thread` gives likely candidates cheaply.
2. A short bundle name, such as `roster-export`. Suggest one from the Threads' titles and let the PM change it. If a Thread is already in a bundle, reuse that name. Don't create a second one.

## Rules

1. Keep the link the same in both directions: every member lists every other member in `bundled_with`, and all share one `bundle` name.
2. If two Threads are already in different bundles, ask whether to merge the bundles or leave them alone. Never merge them silently.
3. **Unbundle**: remove the Thread from its bundle, take it out of every other member's `bundled_with`, and clear its own `bundle` and `bundled_with`. If only one member is left, clear that one's fields too.
4. If the Threads look like the same ask (a duplicate), mention that `park-or-reject` can reject one as `duplicate`. Leave it to the PM.

## Output

Update each member Thread's frontmatter:

```yaml
bundle: roster-export
bundled_with: [THRD-004, THRD-009]   # every other member, not itself
```

Then tell the PM in one line which Threads are now bundled, and under which name.

## What you must not do

- Do not change any Thread's `stage`, `status`, signals, or Spec.
- Do not merge Thread files or move content between them.
- Do not bundle Threads the PM didn't name.
