---
description: Show Claude Code CLI release notes
---

Use the `get_release` MCP tool.

<% if (typeof $ARGUMENTS !== 'undefined' && $ARGUMENTS.trim()) { %>
Version: $ARGUMENTS
<% } else { %>
Show the latest release and last 5.
<% } %>
