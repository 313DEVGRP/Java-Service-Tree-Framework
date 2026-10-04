---
description: List all templates by category (agents/commands/hooks/skills/scripts)
---

Use the `list_examples` MCP tool.

<% if (typeof $ARGUMENTS !== 'undefined' && $ARGUMENTS.trim()) { %>
Category: $ARGUMENTS
<% } else { %>
Show all categories.
<% } %>
