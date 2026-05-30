# Expected Chat Checklist

Use this checklist when validating Phase 10 and the frontend flow.

## Answer quality rules

- Answers should stay grounded in retrieved context.
- Unsupported questions should produce a cautious answer such as: `I do not have enough information in the provided documents.`
- Answers should cite sources when the backend includes them.
- Responses should not merge unrelated policies from different fixtures unless the user explicitly asks for a comparison.

## Good chat checks

### PTO policy question
- answer should mention `10 business days`
- answer should cite the handbook fixture

### Incident channel question
- answer should mention `#incident-war-room`
- answer should cite the incident playbook fixture

### Embedding model consistency question
- answer should mention `BAAI/bge-m3`
- answer should explain that document chunks and queries use the same embedding model
- answer may mention that the query text uses an instruction prefix

### Unsupported question
- answer should say the documents do not contain the needed information
- answer should not invent stock policy, salaries, or benefits not present in the fixtures

