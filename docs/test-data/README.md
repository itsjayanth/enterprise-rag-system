# Test Data for Development

This directory contains **small, safe, reproducible development data** used to test the Enterprise RAG workflow end to end.

Use it during local development for:

- upload testing
- parsing/chunking validation
- embedding/retrieval checks
- chat prompt and citation checks
- manual demos

---

## ✅ What should be kept here

Keep only **source test inputs** and **expected validation artifacts** that are useful for development.

### Current starter corpus in this repo

The repository now includes:

- **TXT fixtures**
  - `sample-documents/small-txt/employee-handbook-excerpt.txt`
  - `sample-documents/small-txt/incident-response-playbook.txt`
- **PDF fixtures**
  - `sample-documents/small-pdf/rag-onboarding-guide.pdf`
  - `sample-documents/small-pdf/compliance-faq.pdf`
  - `sample-documents/medium-pdf/architecture-overview.pdf`
  - `sample-documents/edge-cases/sparse-text.pdf`
- **Edge-case text fixtures**
  - `sample-documents/edge-cases/empty-document.txt`
  - `sample-documents/edge-cases/repeated-paragraphs.txt`
  - `sample-documents/edge-cases/unicode-formatting.txt`
- **Queries**
  - `queries/happy-path.json`
  - `queries/edge-cases.json`
  - `queries/retrieval-smoke-tests.json`
- **Expected manual checks**
  - `expected-results/chunking/expected-chunking-checklist.md`
  - `expected-results/retrieval/expected-retrieval-checklist.md`
  - `expected-results/chat/expected-chat-checklist.md`
- **Metadata**
  - `metadata/sample-documents-index.json`
  - `metadata/test-matrix.md`
- **API payload examples**
  - `api-payloads/upload-examples.md`
  - `api-payloads/retrieval-examples.json`
  - `api-payloads/chat-examples.json`

The checked-in script `generate_pdf_fixtures.py` can regenerate the PDF fixtures if you ever need to rebuild them.

### Recommended structure

```text
docs/test-data/
├── README.md
├── sample-documents/
│   ├── small-pdf/
│   ├── small-txt/
│   ├── medium-pdf/
│   └── edge-cases/
├── queries/
│   ├── happy-path.json
│   ├── edge-cases.json
│   └── retrieval-smoke-tests.json
├── expected-results/
│   ├── chunking/
│   ├── retrieval/
│   └── chat/
├── metadata/
│   ├── sample-documents-index.json
│   └── test-matrix.md
└── api-payloads/
    ├── upload-examples.md
    ├── retrieval-examples.json
    └── chat-examples.json
```

---

## 1. `sample-documents/`

Store small development documents that represent the kinds of files users will upload.

### Suggested content

#### `sample-documents/small-pdf/`
Use short PDFs, 1-5 pages, for quick local testing.

Examples:
- policy summary
- employee handbook excerpt
- invoice sample
- FAQ sheet

#### `sample-documents/small-txt/`
Use plain text files for parser/chunker smoke tests.

Examples:
- short knowledge-base article
- markdown-like plain text note
- technical troubleshooting note

#### `sample-documents/medium-pdf/`
Use a few realistic but still manageable PDFs.

Examples:
- 10-20 page internal manual
- architecture note
- onboarding guide

#### `sample-documents/edge-cases/`
Use tricky files that help test failure handling.

Examples:
- empty document
- mostly blank PDF
- repeated paragraphs
- large page with long uninterrupted text
- strange Unicode text
- mixed headers/bullets/tables

---

## 2. `queries/`

Store reusable query sets for retrieval and chat testing.

### Recommended query groups

#### `happy-path.json`
Questions that should clearly match known document content.

Examples:
- direct factual lookup
- short summary question
- section-specific question
- question referencing one exact heading

#### `edge-cases.json`
Questions that should test robustness.

Examples:
- vague question
- ambiguous wording
- question with no answer in the document
- very short query
- long query with extra noise

#### `retrieval-smoke-tests.json`
Focused retrieval checks.

For each query, include:
- `query`
- `target_document`
- expected `page_number` or section
- expected keywords that should appear in returned chunks

---

## 3. `expected-results/`

Store lightweight expectations used to manually verify behavior.

### `expected-results/chunking/`
Keep examples of what chunking should roughly produce.

Useful content:
- expected chunk counts for a sample file
- expected page-to-chunk mapping
- notes about overlap behavior

### `expected-results/retrieval/`
Keep retrieval expectations.

Useful content:
- top expected source document
- expected page numbers
- expected keywords in top-k results

### `expected-results/chat/`
Keep expected answer characteristics.

Useful content:
- should cite source 1 or source 2
- should say “not enough information” for unsupported questions
- should not hallucinate facts outside the document

These do not need to be perfect golden outputs; they just need to be good enough for development checks.

---

## 4. `metadata/`

Store human-readable metadata about the test corpus.

### `sample-documents-index.json`
Track each sample document with fields like:
- file name
- type
- purpose
- approximate length
- main topics
- edge cases covered

### `test-matrix.md`
Track which documents are used for which checks.

Example columns:
- document
- upload
- parse
- chunk
- embed
- retrieve
- chat
- edge-case category

---

## 5. `api-payloads/`

Store reusable request payload examples.

Useful files:
- upload curl examples
- retrieval request JSON
- chat request JSON
- sample SSE event formats

This helps when manually testing APIs without rebuilding payloads each time.

---

## 🎯 What data is most valuable during development

For this project, the highest-value data to keep here is:

1. **small representative PDFs/TXT files**
2. **known-good queries tied to those files**
3. **expected retrieval/citation notes**
4. **edge-case documents for parser/chunker testing**
5. **manual API payload samples**

That is enough to validate the core flow:

**upload → parse → chunk → embed → retrieve → answer**

---

## ❌ What should NOT be kept here

Do not keep large or generated runtime data in `docs/test-data/`.

Avoid storing:

- uploaded runtime files from real users
- Pinecone vectors / embeddings dumps
- database exports with sensitive data
- huge PDFs or model files
- anything secret or licensed without permission
- production logs
- generated cache files

These belong elsewhere:

- runtime uploads → `data/uploads/`
- model cache → `data/models/`
- DB data → PostgreSQL
- vectors → Pinecone

---

## 📏 Guidelines

Keep everything here:

- small
- deterministic
- safe to commit
- anonymized
- useful for repeated manual testing

Recommended limits:

- individual file size: ideally under 5 MB
- total directory size: small enough to keep the repo lightweight

---

## ✅ Minimum starter set

If you want the smallest useful development dataset, start with:

1. one short PDF with headings and paragraphs
2. one short TXT file
3. one edge-case PDF with sparse text
4. one JSON file with 10 retrieval/chat queries
5. one markdown file listing expected top sources for those queries

That is enough to validate most phases of the MVP.

---

## Suggested next step

This starter corpus is enough to begin manual testing across upload, parsing, chunking, retrieval, and chat phases.

If you extend it later, add:

- one invoice-style PDF
- one table-heavy PDF
- one long technical manual
- more no-answer and multi-document comparison queries

