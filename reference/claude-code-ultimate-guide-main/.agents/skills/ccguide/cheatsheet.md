---
description: Show the Claude Code cheatsheet (full or filtered by section)
---

Use the `get_cheatsheet` MCP tool.

<% if (typeof $ARGUMENTS !== 'undefined' && $ARGUMENTS.trim()) { %>
Filter to section: $ARGUMENTS
<% } else { %>
Return the full cheatsheet.
<% } %>