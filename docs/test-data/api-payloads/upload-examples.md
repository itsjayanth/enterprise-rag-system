# Upload Examples

## TXT upload

```bash
curl -X POST \
  -F "file=@docs/test-data/sample-documents/small-txt/employee-handbook-excerpt.txt" \
  http://localhost:8000/api/documents/upload
```

## PDF upload

```bash
curl -X POST \
  -F "file=@docs/test-data/sample-documents/small-pdf/rag-onboarding-guide.pdf" \
  http://localhost:8000/api/documents/upload
```

## Edge-case upload

```bash
curl -X POST \
  -F "file=@docs/test-data/sample-documents/edge-cases/unicode-formatting.txt" \
  http://localhost:8000/api/documents/upload
```

## Suggested manual sequence

1. upload a TXT file
2. upload a PDF file
3. upload one edge-case file
4. verify document status transitions
5. run retrieval queries from `docs/test-data/queries/`

