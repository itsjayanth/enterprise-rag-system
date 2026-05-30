# Expected Retrieval Checklist

Use this checklist to validate retrieval quality during Phases 7-10.

## High-confidence mappings

| Query | Expected top document | Expected signal |
|------|------------------------|-----------------|
| When must PTO requests be submitted? | `employee-handbook-excerpt.txt` | `10 business days` |
| Which days can hybrid employees work remotely? | `employee-handbook-excerpt.txt` | `Tuesday, Wednesday, Thursday` |
| What is the incident response Slack channel? | `incident-response-playbook.txt` | `#incident-war-room` |
| How quickly must a Severity 1 incident be acknowledged? | `incident-response-playbook.txt` | `15 minutes` |
| What chunk overlap is recommended? | `rag-onboarding-guide.pdf` | `50 character overlap` |
| Which embedding model should be used for both queries and document chunks? | `rag-onboarding-guide.pdf` or `architecture-overview.pdf` | `BAAI/bge-m3` |
| How long are audit logs retained? | `compliance-faq.pdf` | `365 days` |
| What vector database does the architecture use? | `architecture-overview.pdf` | `Pinecone` |

## Failure expectations

- Unsupported questions should not retrieve unrelated chunks with high confidence.
- The empty document should never become the best source.
- Repeated paragraphs should not dominate the top-k if more relevant chunks exist elsewhere.

