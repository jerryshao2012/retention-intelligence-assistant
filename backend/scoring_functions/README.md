# Scoring Functions

This folder version-controls LLM-judge scoring functions.

Structure:
```
backend/scoring_functions/
  <scoring_id>/
    <version>/
      spec.json
      README.md
```

Each scoring function version contains:
- `spec.json`: prompt template, JSON schema, and model used for evaluation.
- `README.md`: human-readable description and changes.

Use `scoring_id` + `version` + derived `revision_id` to reproduce and roll back evaluations.
