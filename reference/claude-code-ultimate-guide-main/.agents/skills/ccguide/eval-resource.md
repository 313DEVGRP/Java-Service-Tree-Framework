# Eval Resource

Évalue une ressource (URL ou texte copié) pour déterminer sa pertinence pour un guide/projet cible.

## Input Detection

Le skill accepte deux types d'input via `$ARGUMENTS`:

1. **URL** : Commence par `http://` ou `https://`
2. **Texte copié** : Tout autre contenu (markdown, texte brut, notes)

## Instructions

### Étape 0: Detect Input Type

```
SI $ARGUMENTS commence par "http://" ou "https://" :
  → input_type = "url"
  → source_url = $ARGUMENTS
SINON :
  → input_type = "text"
  → content = $ARGUMENTS
  → source_url = null
```

### Étape 1: Fetch & Summarize

**Si URL:**
Utiliser `WebFetch` sur l'URL pour:
- Extraire le contenu principal
- Identifier les points clés (3-5 max)
- Noter le type de contenu (tutoriel, référence, blog, vidéo transcript, etc.)

**Si texte copié:**
Analyser directement le contenu fourni:
- Identifier les points clés (3-5 max)
- Noter le type de contenu (notes personnelles, récap, documentation, etc.)
- Identifier les sources citées dans le texte (pour fact-check ultérieur)

### Étape 2: Context Check

**Déterminer le guide/projet cible:**

1. Si dans un projet avec `machine-readable/reference.yaml` → utiliser ce fichier
2. Si dans un projet avec `CLAUDE.md` → analyser la structure documentée
3. Si aucun contexte → demander à l'utilisateur:
   ```
   Quel guide/projet cible pour cette évaluation?
   1. Claude Code Ultimate Guide (si disponible)
   2. Documentation du projet actuel
   3. Autre (préciser)
   ```

**Analyser le contexte cible:**
- La structure actuelle du guide/projet
- Les sections existantes
- Les gaps potentiels

### Étape 3: Gap Analysis

Utiliser `grepai_search` avec les concepts clés extraits pour:
- Trouver si/où c'est déjà documenté
- Identifier les sections similaires
- Repérer les manques

### Étape 4: Output

Produire le rapport structuré ci-dessous.

### Étape 5: Challenge (Auto-critique)

Utiliser le `Task` tool avec `subagent_type: technical-writer` pour:
- Challenger la décision de pertinence
- Identifier ce qui aurait pu être manqué
- Proposer des améliorations au plan d'intégration

Prompt pour l'agent:
```
Critique cette évaluation de ressource pour le Claude Code Ultimate Guide:

[Coller le rapport généré à l'étape 4]

Challenge:
1. Le score est-il justifié ? Arguments pour un score +1 ou -1 ?
2. Y a-t-il des aspects de la ressource non mentionnés ?
3. Les recommandations d'intégration sont-elles les meilleures ?
4. Quels risques si on n'intègre PAS cette ressource ?

Sois brutal et direct.
```

### Étape 6: Fact-Check (Vérification)

**OBLIGATOIRE avant de finaliser.**

**Si URL:**
1. **Re-lire la source**: WebFetch à nouveau l'URL pour vérifier chaque affirmation
2. **Vérifier les stats/citations**:
   - Chaque chiffre mentionné (%, x fois, etc.) → vérifier qu'il est dans l'article
   - Chaque attribution (auteur, entreprise, étude) → vérifier l'exactitude
   - Chaque date → vérifier (attention: on est en 2026, pas 2024!)

**Si texte copié:**
1. **Identifier les claims vérifiables**: Stats, benchmarks, attributions, dates
2. **Utiliser Perplexity** (`mcp__perplexity__perplexity_search`) pour vérifier chaque claim majeur
3. **Croiser les sources**: Ne pas se fier à une seule source

**Dans tous les cas:**
3. **Si doute sur une source secondaire**: Demander à l'utilisateur:
   ```
   ⚠️ Stats non vérifiables:
   - "[stat X]" - source citée: [Y]

   Voulez-vous une recherche Perplexity approfondie?
   ```
4. **Corriger le rapport** avec les infos vérifiées

**Checklist fact-check:**
- [ ] Auteur/rôle correct?
- [ ] Date de publication correcte?
- [ ] Stats citées présentes dans l'article?
- [ ] Sources secondaires identifiées?
- [ ] Aucune hallucination de chiffres?

---

## Output Format

### 📄 Résumé du contenu

[3-5 bullet points des points clés de la ressource]

### 🎯 Score de pertinence (1-5)

| Score | Signification |
|-------|---------------|
| 5 | Essentiel - Gap majeur dans le guide |
| 4 | Très pertinent - Amélioration significative |
| 3 | Pertinent - Complément utile |
| 2 | Marginal - Info secondaire |
| 1 | Hors scope - Non pertinent |

**Score: X/5**

Justification: [Pourquoi ce score]

### ⚖️ Comparatif

| Aspect | Cette ressource | Notre guide |
|--------|----------------|-------------|
| [Topic 1] | ✅ Couvert / ➕ Plus détaillé | ❌ Manquant / ✅ Présent |
| [Topic 2] | ... | ... |
| [Topic 3] | ... | ... |

### 📍 Recommandations

**Si pertinent (score ≥ 3):**

1. **Où documenter**: `guide/[fichier].md` ligne ~XXX
2. **Comment intégrer**: [Description courte]
3. **Priorité**: Haute/Moyenne/Basse

**Si non pertinent (score < 3):**

Raison du rejet et éventuelle alternative.

### 🔥 Challenge (technical-writer)

[Résultat de l'agent technical-writer]

- **Score ajusté**: X/5 (si changement)
- **Points manqués**: [...]
- **Risques de non-intégration**: [...]

### ✅ Fact-Check

| Affirmation | Vérifiée | Source |
|-------------|----------|--------|
| [Stat/claim 1] | ✅/❌/⚠️ | [où trouvée ou "non trouvée"] |
| [Stat/claim 2] | ... | ... |

**Corrections apportées**: [si applicable]

**Stats nécessitant recherche externe**: [si applicable, proposer Perplexity]

### 🎯 Décision finale

- **Score final**: X/5
- **Action**: Intégrer / Ne pas intégrer / À discuter
- **Confiance**: Haute / Moyenne / Basse (basée sur fact-check)

---

## URL à analyser

$ARGUMENTS
