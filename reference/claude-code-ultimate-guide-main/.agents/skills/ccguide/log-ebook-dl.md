---
description: Log an ebook download into the tracking CSV from a screenshot
argument-hint: "[screenshot path or description]"
---

Look at the screenshot provided (or the context given) and extract:
- **date**: download date (format YYYY-MM-DD, use today if not visible)
- **prenom**: recipient's first name
- **email**: recipient's email address
- **ebook**: guide/ebook name (e.g. "Prompts Efficaces", "Introduction à l'IA", etc.)
- **langue**: FR or EN based on the ebook name/content
- **notes**: any relevant context (leave empty if nothing notable)

Then append a new line to:
`/Users/florianbruniaux/Sites/perso/claude-code-ultimate-guide/claudedocs/ebook-downloads.csv`

Use this exact CSV format (no quotes unless the field contains a comma):
```
YYYY-MM-DD,Prenom,email@example.com,Ebook Name,FR,notes
```

After writing, confirm: "Logged: [Prenom] — [email] — [ebook] ([date])"

$ARGUMENTS
