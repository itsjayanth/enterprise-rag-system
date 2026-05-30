# Expected Chunking Checklist

Use this as a manual validation guide after Phase 5.

## Target expectations

### `employee-handbook-excerpt.txt`
- should produce a small number of chunks, typically 2-4 depending on splitter behavior
- one chunk should contain the PTO rule
- one chunk should contain the remote work rule
- one chunk should contain the expenses and badge reporting rules

### `incident-response-playbook.txt`
- should produce 2-4 chunks
- the `15 minutes` acknowledgment rule should remain intact in one chunk
- the `#incident-war-room` channel should remain intact in one chunk
- the `5 business days` postmortem rule should remain intact in one chunk

### `rag-onboarding-guide.pdf`
- chunking should preserve page numbers
- one page should mention `512 character target` and `50 character overlap`
- one page should mention `BAAI/bge-m3`, `Pinecone`, and `bge-reranker-v2-m3`

### `unicode-formatting.txt`
- chunker should not drop Unicode bullets or multilingual lines
- retrieval should still be able to find the sentence about using the same embedding model

### `empty-document.txt`
- parser should return no usable text
- pipeline should mark it as failed or empty, not completed with fake chunks

