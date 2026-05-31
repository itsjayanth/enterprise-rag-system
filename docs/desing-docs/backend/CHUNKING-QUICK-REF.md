# Chunking Quick Reference Guide

## 🔍 What is Chunking?

**Chunking** is the process of breaking down large documents into smaller, manageable pieces (chunks) for:
- **Vector embedding** (models have max token limits)
- **Precise retrieval** (smaller chunks = more accurate search)
- **Better citations** (users can see exact source locations)

---

## ⚡ Quick Example

```
Original Document (5000 chars):
┌──────────────────────────────────────────┐
│ # Introduction                           │
│ This is a long document about ML...      │
│                                          │
│ ## Section 1: Basics                     │
│ Machine learning is...                   │
│                                          │
│ ## Section 2: Advanced Topics            │
│ Deep learning uses...                    │
│                                          │
│ ... continues for many pages ...         │
└──────────────────────────────────────────┘
                      │
                      ▼ CHUNKING (512 chars each)
                      │
        ┌─────────────┼─────────────┐
        │             │             │
        ▼             ▼             ▼
    ┌───────┐    ┌───────┐    ┌───────┐
    │Chunk 0│    │Chunk 1│    │Chunk 2│
    │Page:1 │    │Page:1 │    │Page:2 │
    │512ch  │    │512ch  │    │512ch  │
    └───────┘    └───────┘    └───────┘
```

---

## 📋 How Chunking Works (Step-by-Step)

### **Step 1: Pre-Processing**
```python
# Extract document structure
text = extract_text_from_pdf("document.pdf")
# → "# Introduction\n\nThis is a long..."

# Detect headings, sections, tables
structure = detect_structure(text)
# → {0: "# Introduction", 1024: "## Section 1"}
```

### **Step 2: Split into Chunks**
```python
# Recursive splitting with smart separators
chunks = split_text(
    text=text,
    chunk_size=512,      # ~400 tokens
    chunk_overlap=50,    # 10% overlap for context
    separators=["\n\n", "\n", ". ", " "]  # Try paragraphs first
)
# → ["Chunk 0 text...", "Chunk 1 text...", ...]
```

### **Step 3: Add Metadata**
```python
# Enrich each chunk with metadata
for i, chunk_text in enumerate(chunks):
    chunk_data = {
        "content": chunk_text,
        "chunk_index": i,
        "page_number": 1,  # Estimated from position
        "section_heading": "# Introduction",
        "document_id": "doc_123",
        "user_id": "user_456",
        "char_count": 512,
        "token_count": 400
    }
```

---

## 🔐 Preserving & Masking Information

### **Preserve: Keep Important Context**

#### ✅ Preserve Section Headings
```python
# BEFORE chunking:
"Introduction to ML\n\nMachine learning is..."

# AFTER chunking (with heading preserved):
chunk = {
    "content": "Machine learning is...",
    "section_heading": "Introduction to ML",  # ← PRESERVED
    "subsection": None
}

# When embedded, you can prepend heading for context:
embedded_text = "[Section: Introduction to ML]\nMachine learning is..."
```

#### ✅ Preserve Page Numbers
```python
chunk = {
    "content": "Deep learning uses neural networks...",
    "page_number": 5,        # ← PRESERVED
    "position": {
        "start_char": 2048,  # ← PRESERVED
        "end_char": 2560     # ← PRESERVED
    }
}
```

#### ✅ Preserve Table/List Structure
```python
# Detect tables
table_text = """
| Metric  | Value |
|---------|-------|
| Revenue | $1.5M |
"""

chunk = {
    "content": table_text,
    "contains_table": True,     # ← FLAG
    "table_content": table_text # ← PRESERVED
}
```

### **Mask: Hide Sensitive Information**

#### 🔒 Mask PII (Personally Identifiable Information)

```python
# ORIGINAL TEXT:
"Customer john.doe@example.com called about account 123-45-6789"

# ↓ APPLY PII MASKING ↓

# MASKED TEXT:
"Customer [EMAIL_REDACTED] called about account [SSN_REDACTED]"

# METADATA (stored securely):
{
    "masked_items": [
        {
            "pattern": "email",
            "category": "contact",
            "original": "john.doe@example.com",  # Encrypted/hashed
            "masked_value": "[EMAIL_REDACTED]"
        },
        {
            "pattern": "ssn",
            "category": "government_id",
            "original": "123-45-6789",           # Encrypted/hashed
            "masked_value": "[SSN_REDACTED]"
        }
    ]
}
```

#### Different Masking Strategies

| Strategy | Example | Use Case |
|----------|---------|----------|
| **REDACT** | `john@example.com` → `[EMAIL_REDACTED]` | Complete removal |
| **HASH** | `555-1234` → `[PHONE_a3f9c2]` | Pseudonymization (consistent) |
| **ANONYMIZE** | `John Smith` → `Person_001` | Preserve relationships |
| **ENCRYPT** | `4532-1234-5678-9876` → `[ENCRYPTED:a3f9...]` | Reversible for admins |

---

## 🎯 Complete Workflow Example

```python
from chunking import SecureChunker, ChunkValidator

# 1. Initialize chunker with PII masking
chunker = SecureChunker(
    chunk_size=512,
    chunk_overlap=50,
    mask_pii=True  # Enable PII masking
)

# 2. Chunk document
chunks, masking_metadata = chunker.chunk_document_secure(
    text=document_text,
    document_id="doc_123",
    user_id="user_456",
    metadata={
        "filename": "report.pdf",
        "total_pages": 10
    }
)

# 3. Result: Enriched chunks
for chunk in chunks:
    print(f"""
    Chunk {chunk['chunk_index']}:
      Content: {chunk['content'][:100]}...
      Page: {chunk['page_number']}
      Section: {chunk['section_heading']}
      PII Masked: {chunk['pii_masked']}
      Contains Table: {chunk['contains_table']}
    """)

# 4. Masking summary
print(f"Masked {len(masking_metadata['masked_items'])} PII items:")
for item in masking_metadata['masked_items']:
    print(f"  - {item['category']}: {item['pattern']}")
```

**Output:**
```
Chunk 0:
  Content: # Introduction to Machine Learning
           Machine learning is a subset of AI...
  Page: 1
  Section: Introduction to Machine Learning
  PII Masked: True
  Contains Table: False

Chunk 1:
  Content: Contact us at [EMAIL_REDACTED] or call [PHONE_US_a3f9c2]...
  Page: 2
  Section: Contact Information
  PII Masked: True
  Contains Table: False

Masked 2 PII items:
  - contact: email
  - contact: phone_us
```

---

## 📊 What Gets Preserved vs Masked

### ✅ Always Preserve

| Information | Why |
|-------------|-----|
| **Section headings** | Provides context for retrieval |
| **Page numbers** | Enables accurate citations |
| **Document structure** | Tables, lists, formatting |
| **Chunk position** | Helps reconstruct original |
| **Document metadata** | Filename, upload date, author |

### 🔒 Optionally Mask

| Information | Detection Method |
|-------------|-----------------|
| **Email addresses** | Regex: `\b[\w.-]+@[\w.-]+\.\w+\b` |
| **Phone numbers** | Regex: `\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b` |
| **SSN** | Regex: `\b\d{3}-\d{2}-\d{4}\b` |
| **Credit cards** | Regex + Luhn algorithm |
| **Names** | NER (Named Entity Recognition) |
| **Addresses** | NER + pattern matching |

---

## 🔧 Configuration Examples

### Basic Chunking (No Masking)
```python
chunker = DocumentChunker(
    chunk_size=512,
    chunk_overlap=50
)

chunks = chunker.chunk_document(text, doc_id, user_id)
```

### With Heading Preservation
```python
chunker = HeadingPreservingChunker(
    chunk_size=512,
    chunk_overlap=50
)

chunks = chunker.chunk_with_headings(text, doc_id, user_id)
# → Each chunk has: section_heading, subsection
```

### With PII Masking
```python
chunker = SecureChunker(
    chunk_size=512,
    chunk_overlap=50,
    mask_pii=True
)

chunks, masking_meta = chunker.chunk_document_secure(
    text, doc_id, user_id
)
# → Sensitive data masked, mapping stored securely
```

### With Structure Preservation
```python
chunker = StructurePreservingChunker(
    chunk_size=512,
    chunk_overlap=50
)

chunks = chunker.chunk_preserving_structure(text, doc_id, user_id)
# → Tables and lists kept intact, flagged in metadata
```

---

## ⚙️ Chunking Parameters Guide

| Parameter | Default | Range | Impact |
|-----------|---------|-------|--------|
| `chunk_size` | 512 chars | 200-1000 | Smaller = more precise, more chunks |
| `chunk_overlap` | 50 chars | 0-200 | Larger = better context, more redundancy |
| `separators` | `["\n\n", "\n", ". ", " "]` | Custom | Determines split points |

**Recommendations:**

- **Technical docs**: 512 chars, 50 overlap, preserve headings
- **Financial reports**: 600 chars, 50 overlap, mask PII, preserve tables
- **Legal contracts**: 800 chars, 100 overlap, mask PII
- **General text**: 512 chars, 50 overlap

---

## 📈 Chunk Quality Validation

```python
validator = ChunkValidator(
    min_chars=50,      # Reject very small chunks
    max_chars=1000,    # Warn on very large chunks
    min_tokens=10      # Minimum viable chunk
)

report = validator.validate_chunks(chunks)

print(f"""
Quality Report:
  Total chunks: {report['total_chunks']}
  Valid chunks: {report['valid_chunks']}
  Quality score: {report['average_quality_score']:.2f}
""")
```

---

## 🎓 Key Takeaways

1. **Chunking is essential** for RAG systems (enables precise retrieval)
2. **Preserve context** via headings, page numbers, structure
3. **Mask sensitive data** before embedding (PII, confidential info)
4. **Validate quality** to ensure chunks are usable
5. **Choose right strategy** based on document type

---

## 📚 Learn More

- **Full Guide**: [CHUNKING-STRATEGIES.md](./CHUNKING-STRATEGIES.md)
- **Data Flow**: [data-flow.md](./data-flow.md)
- **Architecture**: [architecture.md](./architecture.md)

---

**Last Updated:** 2026-05-27  
**Quick Reference for:** Document Chunking in Enterprise RAG System

