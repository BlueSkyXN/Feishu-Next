---
name: feishu-im-chat-archive
description: Archive Feishu/Lark IM chats or message search results with pagination and evidence preservation. Use when the user asks to export, archive, summarize, preserve, or review chat history, group messages, direct messages, message resources, threads, reactions, or time-bounded IM activity.
---

# Feishu IM chat archive

Use this workflow for read-only IM archives. Sending messages, adding reactions,
pinning, changing group membership, or changing feed shortcuts are separate
write tasks and require explicit confirmation.

## Required runtime reads

```bash
lark-cli skills read lark-shared
lark-cli skills read lark-im
```

Pick the matching reference before running commands:

```bash
lark-cli skills read lark-im references/lark-im-chat-messages-list.md
lark-cli skills read lark-im references/lark-im-messages-search.md
```

If downloading files/images from messages:

```bash
lark-cli skills read lark-im references/lark-im-messages-resources-download.md
```

## Workflow

1. Define archive scope:

   - target: known `chat_id`, chat name query, direct user `open_id`, or search
     filters
   - identity: `--as user` or `--as bot`
   - time range with timezone
   - whether resource binaries should be downloaded
   - output directory and evidence format
   - whether generated archives can be committed or must remain local only

2. Resolve chat name to `chat_id` when needed:

   ```bash
   lark-cli im +chat-search --query '<chat name keyword>' --format json
   ```

   For bot identity, use bot identity for both search and list:

   ```bash
   lark-cli im +chat-search --as bot --query '<chat name keyword>' --format json
   ```

3. Pull a chat stream by page:

   ```bash
   lark-cli im +chat-messages-list \
     --chat-id '<oc_xxx>' \
     --start '<START_ISO_WITH_TIMEZONE>' \
     --end '<END_ISO_WITH_TIMEZONE>' \
     --order asc \
     --page-size 50 \
     --format json
   ```

   Continue while `has_more=true` using `--page-token`.

4. For cross-chat search, use user identity only:

   ```bash
   lark-cli im +messages-search \
     --query '<keyword-or-empty-string>' \
     --start '<START_ISO_WITH_TIMEZONE>' \
     --end '<END_ISO_WITH_TIMEZONE>' \
     --page-size 50 \
     --page-all \
     --format json
   ```

   Do not use `+messages-search --as bot`; the shortcut is user-only.

5. Download message resources only when explicitly needed:

   ```bash
   lark-cli im +chat-messages-list \
     --chat-id '<oc_xxx>' \
     --download-resources \
     --format json
   ```

   Resource download excludes stickers; single-resource failures should be
   recorded without discarding the page.

6. Expand threads when archive completeness requires it:

   ```bash
   lark-cli im +threads-messages-list --thread '<omt_xxx>' --order asc --page-size 50 --format json
   ```

7. Save generated archive files under `./chat-archives/` when a local artifact
   is requested. Treat raw message JSON, downloaded resources, and summaries as
   private by default.

## Evidence to preserve

For durable archives, keep raw JSON or NDJSON containing:

- `message_id`
- `chat_id` and chat name when available
- `create_time` and `update_time`
- sender ID/name
- `msg_type`
- full `content`
- `mentions`
- `reactions`
- `thread_id`
- deleted/updated flags
- resource local paths when downloaded

## Boundaries and common pitfalls

- `+chat-messages-list` supports user and bot identity; `--user-id` direct
  message resolution requires user identity.
- `+messages-search` is user-only and is for search filters across chats.
- Use `--query ""` for activity reviews when sender, chat, and time filters are
  the real constraints; generic words like "总结" or "聊天记录" can hide results.
- Table/pretty output may truncate content. Use JSON/NDJSON for archives.
- Permission failures usually mean missing `im:message:readonly`, `im:chat:read`,
  search scope, bot membership, app availability range, or user chat access.
- Do not archive broad or open-ended chat history without a time range unless
  the user explicitly asks for an exhaustive export and accepts the size/privacy
  implications.
