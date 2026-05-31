# Test Matrix

| Document | Upload | Parse | Chunk | Embed | Retrieve | Chat | Edge-case focus |
|---------|--------|-------|-------|-------|----------|------|-----------------|
| `employee-handbook-excerpt.txt` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | policy lookup |
| `incident-response-playbook.txt` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | operations guidance |
| `rag-onboarding-guide.pdf` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | PDF + RAG-specific facts |
| `compliance-faq.pdf` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | FAQ-style retrieval |
| `architecture-overview.pdf` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | multi-page PDF |
| `empty-document.txt` | ✅ | ✅ | ✅ | n/a | n/a | n/a | empty input handling |
| `repeated-paragraphs.txt` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | duplicate chunk behavior |
| `unicode-formatting.txt` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | Unicode and multilingual parsing |
| `sparse-text.pdf` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | low-text PDF |

## Suggested smoke-test sequence

1. Upload `employee-handbook-excerpt.txt`
2. Confirm chunks are created
3. Verify embeddings are generated
4. Query: `How many business days in advance should PTO be requested?`
5. Confirm top source is the handbook fixture
6. Ask the same question through chat and confirm the answer cites the handbook

