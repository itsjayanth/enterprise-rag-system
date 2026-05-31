# Chunking Visual Examples

## Example 1: Basic Chunking with Metadata Preservation

### Input Document
```
┌─────────────────────────────────────────────────────────────────┐
│ Financial_Report_Q2_2026.pdf                                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ PAGE 1                                                          │
│ ================================================================│
│                                                                 │
│ # Q2 2026 Financial Report                                      │
│                                                                 │
│ ## Executive Summary                                            │
│                                                                 │
│ This quarter showed strong growth with revenue                  │
│ reaching $1.5M, a 25% increase from Q1.                         │
│                                                                 │
│ Key Performance Indicators:                                     │
│ - Customer acquisition: +40%                                    │
│ - Churn rate: -15%                                              │
│ - Net margin: 43%                                               │
│                                                                 │
│ ================================================================│
│                                                                 │
│ PAGE 2                                                          │
│ ================================================================│
│                                                                 │
│ ## Detailed Revenue Analysis                                    │
│                                                                 │
│ Revenue by segment:                                             │
│                                                                 │
│ | Segment    | Q1      | Q2      | Growth   |                  │
│ |------------|---------|---------|----------|                  │
│ | Enterprise | $700K   | $900K   | +28.5%   |                  │
│ | SMB        | $350K   | $420K   | +20%     |                  │
│ | Individual | $150K   | $180K   | +20%     |                  │
│                                                                 │
│ The enterprise segment continues to drive growth...             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### After Chunking (chunk_size=300, overlap=30)

```
┌─────────────────────────────────────────────────────────────────┐
│ CHUNK 0                                                          │
├─────────────────────────────────────────────────────────────────┤
│ Content:                                                         │
│   # Q2 2026 Financial Report                                     │
│                                                                  │
│   ## Executive Summary                                           │
│                                                                  │
│   This quarter showed strong growth with revenue                 │
│   reaching $1.5M, a 25% increase from Q1.                        │
│                                                                  │
│ Metadata:                                                        │
│   document_id: "doc_fin_q2_2026"                                │
│   chunk_index: 0                                                 │
│   page_number: 1                            ← PRESERVED         │
│   section_heading: "Q2 2026 Financial Report" ← PRESERVED       │
│   subsection: "Executive Summary"           ← PRESERVED          │
│   char_count: 187                                                │
│   token_count: 42                                                │
│   position: {start: 0, end: 187}            ← PRESERVED          │
│   contains_table: false                                          │
│   pii_masked: false                                              │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ CHUNK 1                                                          │
├─────────────────────────────────────────────────────────────────┤
│ Content:                                                         │
│   Key Performance Indicators:                                    │
│   - Customer acquisition: +40%                                   │
│   - Churn rate: -15%                                             │
│   - Net margin: 43%                                              │
│                                                                  │
│ Metadata:                                                        │
│   document_id: "doc_fin_q2_2026"                                │
│   chunk_index: 1                                                 │
│   page_number: 1                            ← PRESERVED          │
│   section_heading: "Q2 2026 Financial Report" ← PRESERVED       │
│   subsection: "Executive Summary"           ← PRESERVED          │
│   char_count: 152                                                │
│   token_count: 35                                                │
│   position: {start: 157, end: 309}          ← PRESERVED          │
│   contains_table: false                                          │
│   contains_list: true                       ← DETECTED           │
│   pii_masked: false                                              │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ CHUNK 2                                                          │
├─────────────────────────────────────────────────────────────────┤
│ Content:                                                         │
│   ## Detailed Revenue Analysis                                   │
│                                                                  │
│   Revenue by segment:                                            │
│                                                                  │
│   | Segment    | Q1      | Q2      | Growth   |                 │
│   |------------|---------|---------|----------|                 │
│   | Enterprise | $700K   | $900K   | +28.5%   |                 │
│   | SMB        | $350K   | $420K   | +20%     |                 │
│   | Individual | $150K   | $180K   | +20%     |                 │
│                                                                  │
│ Metadata:                                                        │
│   document_id: "doc_fin_q2_2026"                                │
│   chunk_index: 2                                                 │
│   page_number: 2                            ← PRESERVED          │
│   section_heading: "Q2 2026 Financial Report" ← PRESERVED       │
│   subsection: "Detailed Revenue Analysis"   ← PRESERVED          │
│   char_count: 285                                                │
│   token_count: 68                                                │
│   position: {start: 520, end: 805}          ← PRESERVED          │
│   contains_table: true                      ← DETECTED           │
│   table_content: "| Segment ... |"          ← PRESERVED          │
│   pii_masked: false                                              │
└─────────────────────────────────────────────────────────────────┘
```

---

## Example 2: Chunking with PII Masking

### Input Document (with sensitive data)
```
┌─────────────────────────────────────────────────────────────────┐
│ Customer_Support_Ticket_1234.txt                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│ Support Ticket #1234                                             │
│ Date: May 27, 2026                                               │
│                                                                  │
│ Customer Information:                                            │
│ Name: John Smith                                                 │
│ Email: john.smith@example.com                                    │
│ Phone: 555-123-4567                                              │
│ SSN: 123-45-6789                                                 │
│                                                                  │
│ Issue Description:                                               │
│ Customer reported unauthorized charge on credit card             │
│ ending in 4532-8765-1234-9876. The charge of $249.99             │
│ appeared on May 25, 2026.                                        │
│                                                                  │
│ Resolution:                                                      │
│ Refund processed. Customer will receive credit within            │
│ 3-5 business days to their account.                              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### After Chunking WITH PII Masking

```
┌─────────────────────────────────────────────────────────────────┐
│ CHUNK 0 (MASKED)                                                 │
├─────────────────────────────────────────────────────────────────┤
│ Content (AFTER masking):                                         │
│   Support Ticket #1234                                           │
│   Date: May 27, 2026                                             │
│                                                                  │
│   Customer Information:                                          │
│   Name: Person_001                         ← ANONYMIZED          │
│   Email: [EMAIL_REDACTED]                  ← REDACTED            │
│   Phone: [PHONE_US_7d8e9f12]               ← HASHED              │
│   SSN: [SSN_REDACTED]                      ← REDACTED            │
│                                                                  │
│ Metadata:                                                        │
│   document_id: "ticket_1234"                                    │
│   chunk_index: 0                                                 │
│   page_number: 1                                                 │
│   pii_masked: true                         ← FLAG                │
│   masking_applied: true                                          │
│                                                                  │
│ Masking Details (stored securely, encrypted):                   │
│   {                                                              │
│     "masked_items": [                                            │
│       {                                                          │
│         "pattern": "person_name",                                │
│         "category": "identity",                                  │
│         "original": "John Smith",          ← ENCRYPTED           │
│         "masked_value": "Person_001",                            │
│         "strategy": "anonymize"                                  │
│       },                                                         │
│       {                                                          │
│         "pattern": "email",                                      │
│         "category": "contact",                                   │
│         "original": "john.smith@example.com", ← ENCRYPTED        │
│         "masked_value": "[EMAIL_REDACTED]",                      │
│         "strategy": "redact"                                     │
│       },                                                         │
│       {                                                          │
│         "pattern": "phone_us",                                   │
│         "category": "contact",                                   │
│         "original": "555-123-4567",        ← ENCRYPTED           │
│         "masked_value": "[PHONE_US_7d8e9f12]",                   │
│         "strategy": "hash"                                       │
│       },                                                         │
│       {                                                          │
│         "pattern": "ssn",                                        │
│         "category": "government_id",                             │
│         "original": "123-45-6789",         ← ENCRYPTED           │
│         "masked_value": "[SSN_REDACTED]",                        │
│         "strategy": "redact"                                     │
│       }                                                          │
│     ]                                                            │
│   }                                                              │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ CHUNK 1 (MASKED)                                                 │
├─────────────────────────────────────────────────────────────────┤
│ Content (AFTER masking):                                         │
│   Issue Description:                                             │
│   Customer reported unauthorized charge on credit card           │
│   ending in [CREDIT_CARD_REDACTED]. The charge of $249.99       │
│   appeared on May 25, 2026.                                      │
│                                                                  │
│ Metadata:                                                        │
│   document_id: "ticket_1234"                                    │
│   chunk_index: 1                                                 │
│   page_number: 1                                                 │
│   pii_masked: true                         ← FLAG                │
│                                                                  │
│ Masking Details:                                                 │
│   {                                                              │
│     "masked_items": [                                            │
│       {                                                          │
│         "pattern": "credit_card",                                │
│         "category": "financial",                                 │
│         "original": "4532-8765-1234-9876", ← ENCRYPTED           │
│         "masked_value": "[CREDIT_CARD_REDACTED]",                │
│         "strategy": "redact"                                     │
│       }                                                          │
│     ]                                                            │
│   }                                                              │
└─────────────────────────────────────────────────────────────────┘
```

### What Happens During Retrieval?

```
User Query: "What was the issue with ticket 1234?"

1. Query is embedded → vector search in Pinecone

2. Top chunks retrieved (MASKED versions):
   ┌─────────────────────────────────────────┐
   │ Customer Person_001 reported issue...   │  ← User sees masked
   │ Credit card [CREDIT_CARD_REDACTED]      │     version
   └─────────────────────────────────────────┘

3. LLM generates answer using MASKED data:
   "The customer reported an unauthorized charge on their 
    credit card ending in [CREDIT_CARD_REDACTED] for $249.99."

4. For authorized admin users, unmask option available:
   Original data retrieved from encrypted storage
   ┌─────────────────────────────────────────┐
   │ [UNMASK] Authorized view requested      │
   │ Customer John Smith reported...         │  ← Admin sees
   │ Credit card 4532-8765-1234-9876         │     original
   └─────────────────────────────────────────┘
```

---

## Example 3: Preserving Structure (Tables)

### Input: Document with Table
```
┌─────────────────────────────────────────────────────────────────┐
│ ## Sales Performance by Region                                   │
│                                                                  │
│ | Region      | Q1 Sales | Q2 Sales | Growth |                  │
│ |-------------|----------|----------|--------|                  │
│ | North       | $500K    | $650K    | +30%   |                  │
│ | South       | $300K    | $340K    | +13%   |                  │
│ | East        | $450K    | $580K    | +29%   |                  │
│ | West        | $550K    | $730K    | +33%   |                  │
│                                                                  │
│ The West region showed exceptional performance due to            │
│ new customer acquisitions and expanded partnerships.             │
└─────────────────────────────────────────────────────────────────┘
```

### Smart Chunking: Table Kept Intact

```
❌ BAD: Table split across chunks
┌──────────────────────────────┐  ┌──────────────────────────────┐
│ CHUNK 0                      │  │ CHUNK 1                      │
│                              │  │                              │
│ | Region   | Q1    | Q2    | │  │ | Growth |                   │
│ |----------|-------|-------|  │  │ |--------|                   │
│ | North    | $500K | $650K |  │  │ | +30%   |                   │
│ | South    | $300K | $340K |  │  │ | +13%   |                   │
└──────────────────────────────┘  └──────────────────────────────┘
         ⚠️ Table structure broken!

✅ GOOD: Table preserved in single chunk
┌─────────────────────────────────────────────────────────────────┐
│ CHUNK 0                                                          │
│                                                                  │
│ ## Sales Performance by Region                                   │
│                                                                  │
│ | Region   | Q1 Sales | Q2 Sales | Growth |                     │
│ |----------|----------|----------|--------|                     │
│ | North    | $500K    | $650K    | +30%   |                     │
│ | South    | $300K    | $340K    | +13%   |                     │
│ | East     | $450K    | $580K    | +29%   |                     │
│ | West     | $550K    | $730K    | +33%   |                     │
│                                                                  │
│ Metadata:                                                        │
│   contains_table: true          ← FLAGGED                        │
│   table_content: "| Region..."  ← PRESERVED                      │
│   section_heading: "Sales Performance by Region" ← PRESERVED     │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ CHUNK 1                                                          │
│                                                                  │
│ The West region showed exceptional performance due to            │
│ new customer acquisitions and expanded partnerships.             │
│                                                                  │
│ Metadata:                                                        │
│   contains_table: false                                          │
│   section_heading: "Sales Performance by Region" ← PRESERVED     │
└─────────────────────────────────────────────────────────────────┘
```

---

## Visual: Complete Chunking Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│          INPUT: PDF DOCUMENT (100 pages)                         │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
          ┌─────────────────────────────────┐
          │   1. Extract Text & Metadata    │
          │   • pypdfium2 library           │
          │   • Page boundaries             │
          │   • Heading detection           │
          │   Result: 200KB text            │
          └─────────────┬───────────────────┘
                        │
                        ▼
          ┌─────────────────────────────────┐
          │   2. Optional: Mask PII         │
          │   • Detect: emails, phones, SSN │
          │   • Apply masking strategy      │
          │   • Store mapping securely      │
          │   Result: Sanitized text        │
          └─────────────┬───────────────────┘
                        │
                        ▼
          ┌─────────────────────────────────┐
          │   3. Chunking                   │
          │   • Recursive splitting         │
          │   • Smart separators            │
          │   • Preserve tables/lists       │
          │   Result: ~400 chunks           │
          └─────────────┬───────────────────┘
                        │
                        ▼
          ┌─────────────────────────────────┐
          │   4. Metadata Enrichment        │
          │   • Add page numbers            │
          │   • Add section headings        │
          │   • Add position info           │
          │   • Flag structures             │
          └─────────────┬───────────────────┘
                        │
                        ▼
          ┌─────────────────────────────────┐
          │   5. Quality Validation         │
          │   • Check min/max size          │
          │   • Verify metadata             │
          │   • Score quality               │
          │   Result: Valid chunks only     │
          └─────────────┬───────────────────┘
                        │
                        ▼
          ┌─────────────────────────────────┐
          │   6. Save to Database           │
          │   • PostgreSQL: chunks table    │
          │   • Include all metadata        │
          │   Result: Ready for embedding   │
          └─────────────┬───────────────────┘
                        │
                        ▼
          ┌─────────────────────────────────┐
          │   7. Batch for Embedding        │
          │   • Group into batches of 32    │
          │   • Queue for GPU processing    │
          │   Result: ~13 batches queued    │
          └─────────────────────────────────┘
```

---

## Key Formulas

### Chunk Overlap Calculation
```
Effective chunk start position:
position[i] = (i × chunk_size) - (i × overlap)

Example:
  chunk_size = 512
  overlap = 50
  
  Chunk 0: position 0 to 512
  Chunk 1: position 462 to 974  (512 - 50 = 462)
  Chunk 2: position 924 to 1436 (974 - 50 = 924)
           ↑
           50 chars shared with previous chunk
```

### Estimated Chunks per Document
```
estimated_chunks = (total_chars / (chunk_size - overlap)) + 1

Example:
  Document: 50,000 chars
  Chunk size: 512
  Overlap: 50
  
  Chunks = 50,000 / (512 - 50) + 1
         = 50,000 / 462 + 1
         ≈ 109 chunks
```

---

**Last Updated:** 2026-05-27  
**Visual Examples for:** Enterprise RAG Document Chunking

