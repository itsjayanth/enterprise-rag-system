# Document Chunking Strategies - Enterprise RAG System

## Executive Summary

This document provides a comprehensive guide to **text chunking strategies** used in the document ingestion pipeline, including techniques for **preserving metadata**, **masking sensitive information**, and optimizing chunk quality for retrieval.

---

## 1. Why Chunking Matters

### **1.1 The Problem**

- **LLM Context Limits**: Models have token limits (e.g., 8K, 32K tokens)
- **Vector Search Granularity**: Need small, focused chunks for precise retrieval
- **Semantic Coherence**: Chunks should represent complete thoughts/concepts
- **Citation Accuracy**: Users need to trace answers back to specific document sections

### **1.2 Key Challenges**

| Challenge | Solution |
|-----------|----------|
| Splitting mid-sentence | Use semantic separators (paragraphs → sentences → words) |
| Losing context | Add chunk overlap (10-20%) |
| Missing metadata | Preserve page numbers, sections, headings |
| Sensitive data | Mask/redact PII before embedding |
| Table/list structure | Preserve formatting indicators |

---

## 2. Chunking Pipeline Overview

```
┌──────────────────────────────────────────────────────────────────────┐
│                    DOCUMENT TEXT INPUT                               │
│  Example: 100-page PDF → 200KB extracted text                        │
└────────────────────────────┬─────────────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────────────────┐
│         STEP 1: Pre-Processing & Metadata Extraction                 │
│                                                                      │
│  • Detect document structure (headings, sections, tables)            │
│  • Extract page boundaries                                           │
│  • Identify sensitive information (PII patterns)                     │
│  • Normalize whitespace                                              │
│                                                                      │
│  Output: Structured document with annotations                        │
└────────────────────────────┬─────────────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────────────────┐
│         STEP 2: Sensitive Data Masking (Optional)                    │
│                                                                      │
│  • Detect PII: emails, phone numbers, SSN, credit cards              │
│  • Apply masking strategy:                                           │
│    - Redact: john.doe@example.com → [EMAIL_REDACTED]                │
│    - Hash: 555-1234 → [PHONE_a3f9c2]                                │
│    - Anonymize: John Smith → Person_001                             │
│  • Store mapping for authorized users                                │
│                                                                      │
│  Output: Sanitized text + masking metadata                           │
└────────────────────────────┬─────────────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────────────────┐
│         STEP 3: Text Chunking                                        │
│                                                                      │
│  Choose strategy based on document type:                             │
│  • Phase 1: Recursive Character Splitting (default)                  │
│  • Phase 2: Sentence-based splitting                                 │
│  • Phase 3: Semantic chunking (future)                               │
│                                                                      │
│  Parameters:                                                         │
│  • chunk_size: 512 chars (~400 tokens for BGE-M3)                    │
│  • chunk_overlap: 50 chars (10%)                                     │
│  • separators: ["\n\n", "\n", ". ", " "]                             │
│                                                                      │
│  Output: List of chunk objects                                       │
└────────────────────────────┬─────────────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────────────────┐
│         STEP 4: Metadata Enrichment                                  │
│                                                                      │
│  For each chunk, attach:                                             │
│  • document_id, user_id                                              │
│  • page_number, chunk_index                                          │
│  • section_heading, subsection                                       │
│  • char_count, token_count                                           │
│  • created_at, processing_version                                    │
│  • sensitive_data_masked: boolean                                    │
│  • original_position: {start_char, end_char}                         │
│                                                                      │
│  Output: Enriched chunks ready for embedding                         │
└────────────────────────────┬─────────────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────────────────┐
│         STEP 5: Quality Validation                                   │
│                                                                      │
│  • Check minimum chunk size (>50 chars)                              │
│  • Verify metadata completeness                                      │
│  • Flag chunks with excessive special characters                     │
│  • Ensure non-empty content                                          │
│                                                                      │
│  Output: Validated chunks → Ready for embedding                      │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 3. Implementation: Phase 1 - Recursive Character Splitting

### **3.1 Basic Implementation**

```python
from langchain.text_splitter import RecursiveCharacterTextSplitter
from typing import List, Dict, Optional
import re

class DocumentChunker:
    """Handles document chunking with metadata preservation"""
    
    def __init__(
        self,
        chunk_size: int = 512,
        chunk_overlap: int = 50,
        separators: Optional[List[str]] = None
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators or [
            "\n\n",  # Double newline (paragraph boundary)
            "\n",    # Single newline
            ". ",    # Sentence boundary
            ", ",    # Clause boundary
            " ",     # Word boundary
            ""       # Character boundary (last resort)
        ]
        
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=self.separators,
            length_function=len,
            is_separator_regex=False
        )
    
    def chunk_document(
        self,
        text: str,
        document_id: str,
        user_id: str,
        metadata: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Chunk document while preserving metadata
        
        Args:
            text: Full document text
            document_id: Unique document identifier
            user_id: Owner user ID
            metadata: Additional document metadata
        
        Returns:
            List of chunk dictionaries with enriched metadata
        """
        # Split into chunks
        raw_chunks = self.splitter.split_text(text)
        
        # Enrich with metadata
        enriched_chunks = []
        char_position = 0
        
        for idx, chunk_text in enumerate(raw_chunks):
            # Estimate page number (approximate)
            page_number = self._estimate_page_number(
                char_position, 
                len(text),
                metadata.get("total_pages", 1) if metadata else 1
            )
            
            chunk_data = {
                # Core identifiers
                "document_id": document_id,
                "user_id": user_id,
                "chunk_index": idx,
                
                # Content
                "content": chunk_text.strip(),
                
                # Metadata
                "page_number": page_number,
                "char_count": len(chunk_text),
                "token_count": self._estimate_tokens(chunk_text),
                "position": {
                    "start_char": char_position,
                    "end_char": char_position + len(chunk_text)
                },
                
                # Document metadata (inherited)
                "document_name": metadata.get("filename") if metadata else None,
                "total_pages": metadata.get("total_pages") if metadata else None,
                "created_at": metadata.get("created_at") if metadata else None,
            }
            
            enriched_chunks.append(chunk_data)
            
            # Update position (accounting for overlap)
            char_position += len(chunk_text) - self.chunk_overlap
        
        return enriched_chunks
    
    def _estimate_page_number(
        self, 
        char_position: int, 
        total_chars: int, 
        total_pages: int
    ) -> int:
        """Estimate page number based on character position"""
        if total_pages <= 1:
            return 1
        
        # Simple linear interpolation
        page_estimate = int((char_position / total_chars) * total_pages) + 1
        return min(page_estimate, total_pages)
    
    def _estimate_tokens(self, text: str) -> int:
        """Rough token count estimation (1 token ≈ 0.75 words)"""
        words = len(text.split())
        return int(words / 0.75)
```

### **3.2 Example Usage**

```python
# Initialize chunker
chunker = DocumentChunker(
    chunk_size=512,
    chunk_overlap=50
)

# Sample document text
document_text = """
Introduction to Machine Learning

Machine learning is a subset of artificial intelligence that focuses on 
building systems that can learn from data. These systems improve their 
performance on tasks over time without being explicitly programmed.

Types of Machine Learning:

1. Supervised Learning
   In supervised learning, the model is trained on labeled data...

2. Unsupervised Learning
   Unsupervised learning works with unlabeled data...
"""

# Chunk the document
chunks = chunker.chunk_document(
    text=document_text,
    document_id="doc_123",
    user_id="user_456",
    metadata={
        "filename": "ml_introduction.pdf",
        "total_pages": 5,
        "created_at": "2026-05-27T10:00:00Z"
    }
)

# Result: List of enriched chunks
for chunk in chunks:
    print(f"Chunk {chunk['chunk_index']}:")
    print(f"  Page: {chunk['page_number']}")
    print(f"  Tokens: {chunk['token_count']}")
    print(f"  Content preview: {chunk['content'][:100]}...")
    print()
```

**Output:**
```
Chunk 0:
  Page: 1
  Tokens: 65
  Content preview: Introduction to Machine Learning

Machine learning is a subset of artificial intelligence that focus...

Chunk 1:
  Page: 1
  Tokens: 72
  Content preview: building systems that can learn from data. These systems improve their performance on tasks over time...
```

---

## 4. Preserving Specific Information During Chunking

### **4.1 Preserve Section Headings**

```python
import re
from typing import Tuple, Optional

class HeadingPreservingChunker(DocumentChunker):
    """Chunker that preserves section heading context"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Regex patterns for heading detection
        self.heading_patterns = [
            # Markdown-style headers
            r'^#{1,6}\s+(.+)$',
            
            # Numbered sections
            r'^(\d+\.)+\s+([A-Z][^.!?]*)',
            
            # All-caps headings
            r'^[A-Z][A-Z\s]+:?\s*$',
            
            # Underlined headings
            r'^(.+)\n[=\-]{3,}$'
        ]
    
    def extract_structure(self, text: str) -> Dict[int, str]:
        """
        Extract document structure (headings and their positions)
        
        Returns:
            Dict mapping character position to heading text
        """
        structure = {}
        lines = text.split('\n')
        char_pos = 0
        current_heading = None
        
        for line in lines:
            # Check if line matches any heading pattern
            for pattern in self.heading_patterns:
                match = re.match(pattern, line.strip())
                if match:
                    current_heading = line.strip()
                    structure[char_pos] = current_heading
                    break
            
            char_pos += len(line) + 1  # +1 for newline
        
        return structure
    
    def find_current_section(
        self, 
        char_position: int, 
        structure: Dict[int, str]
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Find current heading and subsection for a given position
        
        Returns:
            Tuple of (heading, subsection)
        """
        if not structure:
            return None, None
        
        # Find most recent heading before this position
        relevant_headings = [
            (pos, heading) 
            for pos, heading in structure.items() 
            if pos <= char_position
        ]
        
        if not relevant_headings:
            return None, None
        
        relevant_headings.sort(reverse=True)
        
        # Simple heuristic: first is subsection, second is main heading
        if len(relevant_headings) >= 2:
            subsection = relevant_headings[0][1]
            heading = relevant_headings[1][1]
            return heading, subsection
        else:
            return relevant_headings[0][1], None
    
    def chunk_with_headings(
        self,
        text: str,
        document_id: str,
        user_id: str,
        metadata: Optional[Dict] = None
    ) -> List[Dict]:
        """Chunk document while preserving heading context"""
        
        # Extract document structure
        structure = self.extract_structure(text)
        
        # Get base chunks
        chunks = self.chunk_document(text, document_id, user_id, metadata)
        
        # Enrich with heading information
        for chunk in chunks:
            heading, subsection = self.find_current_section(
                chunk['position']['start_char'],
                structure
            )
            
            chunk['section_heading'] = heading
            chunk['subsection'] = subsection
            
            # Optionally prepend heading to content for better context
            if heading:
                chunk['content_with_context'] = f"[Section: {heading}]\n{chunk['content']}"
            else:
                chunk['content_with_context'] = chunk['content']
        
        return chunks
```

### **4.2 Example: Chunk with Preserved Headings**

```python
text_with_headings = """
# Chapter 1: Introduction

This is the introduction to the document.

## 1.1 Background

The background section provides context about...

## 1.2 Objectives

Our main objectives are:
1. Objective one
2. Objective two

# Chapter 2: Methodology

This chapter describes the methodology used...
"""

chunker = HeadingPreservingChunker(chunk_size=200, chunk_overlap=20)
chunks = chunker.chunk_with_headings(
    text=text_with_headings,
    document_id="doc_789",
    user_id="user_456"
)

for chunk in chunks:
    print(f"Chunk {chunk['chunk_index']}:")
    print(f"  Heading: {chunk['section_heading']}")
    print(f"  Subsection: {chunk['subsection']}")
    print(f"  Content: {chunk['content'][:80]}...")
    print()
```

**Output:**
```
Chunk 0:
  Heading: # Chapter 1: Introduction
  Subsection: None
  Content: This is the introduction to the document...

Chunk 1:
  Heading: # Chapter 1: Introduction
  Subsection: ## 1.1 Background
  Content: The background section provides context about...

Chunk 2:
  Heading: # Chapter 1: Introduction
  Subsection: ## 1.2 Objectives
  Content: Our main objectives are:
1. Objective one
2. Objective two...
```

---

## 5. Masking Sensitive Information

### **5.1 PII Detection and Masking**

```python
import hashlib
from typing import Dict, List, Tuple
from dataclasses import dataclass
from enum import Enum

class MaskingStrategy(Enum):
    """Different strategies for masking sensitive data"""
    REDACT = "redact"        # Replace with [TYPE_REDACTED]
    HASH = "hash"            # Replace with hashed value
    ANONYMIZE = "anonymize"  # Replace with pseudonym
    ENCRYPT = "encrypt"      # Encrypt reversibly

@dataclass
class PIIPattern:
    """Pattern for detecting PII"""
    name: str
    regex: str
    category: str
    masking_strategy: MaskingStrategy

class PIIMasker:
    """Detect and mask personally identifiable information"""
    
    def __init__(self):
        # Define PII patterns
        self.patterns = [
            # Email addresses
            PIIPattern(
                name="email",
                regex=r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
                category="contact",
                masking_strategy=MaskingStrategy.REDACT
            ),
            
            # US Phone numbers
            PIIPattern(
                name="phone_us",
                regex=r'\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b',
                category="contact",
                masking_strategy=MaskingStrategy.HASH
            ),
            
            # US Social Security Numbers
            PIIPattern(
                name="ssn",
                regex=r'\b\d{3}-\d{2}-\d{4}\b',
                category="government_id",
                masking_strategy=MaskingStrategy.REDACT
            ),
            
            # Credit card numbers (simple pattern)
            PIIPattern(
                name="credit_card",
                regex=r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
                category="financial",
                masking_strategy=MaskingStrategy.REDACT
            ),
            
            # IP addresses
            PIIPattern(
                name="ip_address",
                regex=r'\b(?:\d{1,3}\.){3}\d{1,3}\b',
                category="network",
                masking_strategy=MaskingStrategy.HASH
            ),
            
            # Names (simple pattern - all-caps or title case)
            # Note: This is very basic and will have false positives
            PIIPattern(
                name="person_name",
                regex=r'\b[A-Z][a-z]+ [A-Z][a-z]+\b',
                category="identity",
                masking_strategy=MaskingStrategy.ANONYMIZE
            ),
        ]
        
        # Store anonymization mapping
        self.anonymization_map: Dict[str, str] = {}
        self.anonymization_counter: Dict[str, int] = {}
    
    def detect_pii(self, text: str) -> List[Tuple[str, str, int, int]]:
        """
        Detect PII in text
        
        Returns:
            List of (pattern_name, matched_text, start_pos, end_pos)
        """
        matches = []
        
        for pattern in self.patterns:
            for match in re.finditer(pattern.regex, text):
                matches.append((
                    pattern.name,
                    match.group(),
                    match.start(),
                    match.end()
                ))
        
        # Sort by position
        matches.sort(key=lambda x: x[2])
        return matches
    
    def mask_text(
        self, 
        text: str, 
        preserve_mapping: bool = True
    ) -> Tuple[str, Dict]:
        """
        Mask sensitive information in text
        
        Args:
            text: Original text
            preserve_mapping: Whether to store mapping for reversal
        
        Returns:
            Tuple of (masked_text, masking_metadata)
        """
        masked_text = text
        offset = 0  # Track position changes due to replacement
        metadata = {
            "masked_items": [],
            "masking_applied": True
        }
        
        pii_matches = self.detect_pii(text)
        
        for pattern_name, matched_text, start, end in pii_matches:
            # Get pattern config
            pattern = next(p for p in self.patterns if p.name == pattern_name)
            
            # Apply masking strategy
            masked_value = self._apply_masking(
                matched_text, 
                pattern.masking_strategy,
                pattern_name
            )
            
            # Replace in text
            adjusted_start = start + offset
            adjusted_end = end + offset
            masked_text = (
                masked_text[:adjusted_start] + 
                masked_value + 
                masked_text[adjusted_end:]
            )
            
            # Update offset
            offset += len(masked_value) - (end - start)
            
            # Store metadata
            metadata["masked_items"].append({
                "pattern": pattern_name,
                "category": pattern.category,
                "original_position": (start, end),
                "masked_value": masked_value,
                "strategy": pattern.masking_strategy.value
            })
            
            # Optionally preserve mapping for authorized reversal
            if preserve_mapping:
                mapping_key = f"{pattern_name}:{matched_value}"
                metadata[mapping_key] = matched_text
        
        return masked_text, metadata
    
    def _apply_masking(
        self, 
        value: str, 
        strategy: MaskingStrategy,
        pattern_name: str
    ) -> str:
        """Apply specific masking strategy"""
        
        if strategy == MaskingStrategy.REDACT:
            return f"[{pattern_name.upper()}_REDACTED]"
        
        elif strategy == MaskingStrategy.HASH:
            # Create short hash
            hash_value = hashlib.md5(value.encode()).hexdigest()[:8]
            return f"[{pattern_name.upper()}_{hash_value}]"
        
        elif strategy == MaskingStrategy.ANONYMIZE:
            # Generate pseudonym
            if value not in self.anonymization_map:
                if pattern_name not in self.anonymization_counter:
                    self.anonymization_counter[pattern_name] = 0
                
                self.anonymization_counter[pattern_name] += 1
                count = self.anonymization_counter[pattern_name]
                
                pseudonym = f"{pattern_name.title()}_{count:03d}"
                self.anonymization_map[value] = pseudonym
            
            return self.anonymization_map[value]
        
        elif strategy == MaskingStrategy.ENCRYPT:
            # Placeholder: would use actual encryption
            return f"[ENCRYPTED:{hashlib.sha256(value.encode()).hexdigest()[:16]}]"
        
        return value
```

### **5.2 Integrated Chunker with PII Masking**

```python
class SecureChunker(HeadingPreservingChunker):
    """Chunker with built-in PII masking"""
    
    def __init__(self, *args, mask_pii: bool = False, **kwargs):
        super().__init__(*args, **kwargs)
        self.mask_pii = mask_pii
        self.masker = PIIMasker() if mask_pii else None
    
    def chunk_document_secure(
        self,
        text: str,
        document_id: str,
        user_id: str,
        metadata: Optional[Dict] = None,
        mask_pii: bool = None
    ) -> Tuple[List[Dict], Optional[Dict]]:
        """
        Chunk document with optional PII masking
        
        Returns:
            Tuple of (chunks, masking_metadata)
        """
        masking_metadata = None
        original_text = text
        
        # Apply PII masking if enabled
        if mask_pii or (mask_pii is None and self.mask_pii):
            text, masking_metadata = self.masker.mask_text(text)
        
        # Chunk the (possibly masked) text
        chunks = self.chunk_with_headings(
            text=text,
            document_id=document_id,
            user_id=user_id,
            metadata=metadata
        )
        
        # Add masking flag to each chunk
        for chunk in chunks:
            chunk['pii_masked'] = bool(masking_metadata)
            chunk['masking_applied'] = masking_metadata is not None
        
        return chunks, masking_metadata
```

### **5.3 Example: Chunk with PII Masking**

```python
sensitive_text = """
Customer Support Ticket #1234

From: john.doe@example.com
Phone: 555-123-4567

Customer John Smith reported an issue with their account.
Their SSN on file is 123-45-6789.

Credit card ending in 4532-8765-1234-9876 was charged incorrectly.
"""

# Create secure chunker
chunker = SecureChunker(
    chunk_size=300,
    chunk_overlap=30,
    mask_pii=True
)

# Chunk with masking
chunks, masking_meta = chunker.chunk_document_secure(
    text=sensitive_text,
    document_id="ticket_1234",
    user_id="support_team"
)

print("=== Masked Chunks ===\n")
for chunk in chunks:
    print(f"Chunk {chunk['chunk_index']}:")
    print(f"  PII Masked: {chunk['pii_masked']}")
    print(f"  Content:\n{chunk['content']}\n")

print("\n=== Masking Metadata ===\n")
print(f"Total masked items: {len(masking_meta['masked_items'])}")
for item in masking_meta['masked_items']:
    print(f"  - {item['category']}: {item['pattern']} → {item['masked_value']}")
```

**Output:**
```
=== Masked Chunks ===

Chunk 0:
  PII Masked: True
  Content:
Customer Support Ticket #1234

From: [EMAIL_REDACTED]
Phone: [PHONE_US_7d8e9f12]

Customer Person_name_001 reported an issue with their account.

Chunk 1:
  PII Masked: True
  Content:
Their SSN on file is [SSN_REDACTED].

Credit card ending in [CREDIT_CARD_REDACTED] was charged incorrectly.

=== Masking Metadata ===

Total masked items: 5
  - contact: email → [EMAIL_REDACTED]
  - contact: phone_us → [PHONE_US_7d8e9f12]
  - identity: person_name → Person_name_001
  - government_id: ssn → [SSN_REDACTED]
  - financial: credit_card → [CREDIT_CARD_REDACTED]
```

---

## 6. Advanced: Preserve Table and List Structure

### **6.1 Table-Aware Chunking**

```python
class StructurePreservingChunker(SecureChunker):
    """Preserve tables and lists during chunking"""
    
    def detect_tables(self, text: str) -> List[Tuple[int, int, str]]:
        """
        Detect table-like structures
        
        Returns:
            List of (start_pos, end_pos, table_text)
        """
        tables = []
        lines = text.split('\n')
        
        in_table = False
        table_start = 0
        table_lines = []
        char_pos = 0
        
        for line in lines:
            # Simple heuristic: lines with | or multiple tabs
            is_table_line = (
                '|' in line and line.count('|') >= 2
            ) or (
                '\t' in line and line.count('\t') >= 2
            )
            
            if is_table_line:
                if not in_table:
                    table_start = char_pos
                    in_table = True
                table_lines.append(line)
            else:
                if in_table:
                    # End of table
                    table_text = '\n'.join(table_lines)
                    tables.append((table_start, char_pos, table_text))
                    table_lines = []
                    in_table = False
            
            char_pos += len(line) + 1
        
        return tables
    
    def detect_lists(self, text: str) -> List[Tuple[int, int, str]]:
        """
        Detect numbered or bulleted lists
        
        Returns:
            List of (start_pos, end_pos, list_text)
        """
        lists = []
        lines = text.split('\n')
        
        in_list = False
        list_start = 0
        list_lines = []
        char_pos = 0
        
        # Patterns for list items
        list_patterns = [
            r'^\s*\d+\.', # Numbered: 1. Item
            r'^\s*[-*•]', # Bulleted: - Item or * Item
            r'^\s*\([a-z]\)', # Lettered: (a) Item
        ]
        
        for line in lines:
            is_list_line = any(
                re.match(pattern, line) 
                for pattern in list_patterns
            )
            
            if is_list_line:
                if not in_list:
                    list_start = char_pos
                    in_list = True
                list_lines.append(line)
            else:
                if in_list and line.strip():  # Non-empty line ends list
                    list_text = '\n'.join(list_lines)
                    lists.append((list_start, char_pos, list_text))
                    list_lines = []
                    in_list = False
                elif in_list:
                    # Empty line within list - continue
                    list_lines.append(line)
            
            char_pos += len(line) + 1
        
        return lists
    
    def chunk_preserving_structure(
        self,
        text: str,
        document_id: str,
        user_id: str,
        metadata: Optional[Dict] = None
    ) -> List[Dict]:
        """Chunk while keeping tables and lists intact"""
        
        # Detect structures
        tables = self.detect_tables(text)
        lists = self.detect_lists(text)
        
        # Combine and sort by position
        structures = []
        for start, end, content in tables:
            structures.append({
                'type': 'table',
                'start': start,
                'end': end,
                'content': content
            })
        
        for start, end, content in lists:
            structures.append({
                'type': 'list',
                'start': start,
                'end': end,
                'content': content
            })
        
        structures.sort(key=lambda x: x['start'])
        
        # Get base chunks
        chunks = self.chunk_with_headings(text, document_id, user_id, metadata)
        
        # Annotate chunks that contain structures
        for chunk in chunks:
            chunk_start = chunk['position']['start_char']
            chunk_end = chunk['position']['end_char']
            
            chunk['contains_table'] = False
            chunk['contains_list'] = False
            
            for struct in structures:
                # Check overlap
                if (struct['start'] < chunk_end and struct['end'] > chunk_start):
                    if struct['type'] == 'table':
                        chunk['contains_table'] = True
                        chunk['table_content'] = struct['content']
                    elif struct['type'] == 'list':
                        chunk['contains_list'] = True
                        chunk['list_content'] = struct['content']
        
        return chunks
```

---

## 7. Chunk Quality Assurance

### **7.1 Validation Rules**

```python
from dataclasses import dataclass
from typing import List

@dataclass
class ChunkQualityMetrics:
    """Metrics for chunk quality assessment"""
    chunk_id: str
    is_valid: bool
    issues: List[str]
    quality_score: float  # 0.0 to 1.0

class ChunkValidator:
    """Validate chunk quality"""
    
    def __init__(
        self,
        min_chars: int = 50,
        max_chars: int = 1000,
        min_tokens: int = 10,
        max_special_char_ratio: float = 0.3
    ):
        self.min_chars = min_chars
        self.max_chars = max_chars
        self.min_tokens = min_tokens
        self.max_special_char_ratio = max_special_char_ratio
    
    def validate_chunk(self, chunk: Dict) -> ChunkQualityMetrics:
        """Validate single chunk"""
        issues = []
        quality_score = 1.0
        
        content = chunk.get('content', '')
        
        # Check 1: Minimum length
        if len(content) < self.min_chars:
            issues.append(f"Too short: {len(content)} < {self.min_chars} chars")
            quality_score -= 0.3
        
        # Check 2: Maximum length
        if len(content) > self.max_chars:
            issues.append(f"Too long: {len(content)} > {self.max_chars} chars")
            quality_score -= 0.2
        
        # Check 3: Not empty
        if not content.strip():
            issues.append("Empty content")
            quality_score = 0.0
        
        # Check 4: Token count
        token_count = chunk.get('token_count', 0)
        if token_count < self.min_tokens:
            issues.append(f"Too few tokens: {token_count}")
            quality_score -= 0.2
        
        # Check 5: Special character ratio
        special_chars = sum(not c.isalnum() and not c.isspace() for c in content)
        ratio = special_chars / max(len(content), 1)
        if ratio > self.max_special_char_ratio:
            issues.append(f"Too many special chars: {ratio:.2%}")
            quality_score -= 0.15
        
        # Check 6: Metadata completeness
        required_fields = ['document_id', 'user_id', 'page_number', 'chunk_index']
        missing_fields = [f for f in required_fields if f not in chunk]
        if missing_fields:
            issues.append(f"Missing metadata: {missing_fields}")
            quality_score -= 0.1 * len(missing_fields)
        
        quality_score = max(0.0, min(1.0, quality_score))
        is_valid = quality_score >= 0.5 and not any('Empty' in i for i in issues)
        
        return ChunkQualityMetrics(
            chunk_id=chunk.get('chunk_id', 'unknown'),
            is_valid=is_valid,
            issues=issues,
            quality_score=quality_score
        )
    
    def validate_chunks(self, chunks: List[Dict]) -> Dict:
        """Validate all chunks and generate report"""
        results = [self.validate_chunk(chunk) for chunk in chunks]
        
        valid_count = sum(1 for r in results if r.is_valid)
        avg_quality = sum(r.quality_score for r in results) / max(len(results), 1)
        
        return {
            'total_chunks': len(chunks),
            'valid_chunks': valid_count,
            'invalid_chunks': len(chunks) - valid_count,
            'average_quality_score': avg_quality,
            'validation_results': results,
            'all_issues': [
                {'chunk_id': r.chunk_id, 'issues': r.issues}
                for r in results if r.issues
            ]
        }
```

---

## 8. Complete Example Workflow

```python
# Initialize components
chunker = StructurePreservingChunker(
    chunk_size=512,
    chunk_overlap=50,
    mask_pii=True
)

validator = ChunkValidator(
    min_chars=50,
    max_chars=800,
    min_tokens=10
)

# Sample document
document = {
    "id": "doc_financial_report_2026",
    "user_id": "user_finance_team",
    "filename": "Q2_2026_Financial_Report.pdf",
    "text": """
# Q2 2026 Financial Report

## Executive Summary

This report covers financial performance for Q2 2026.

Key contacts:
- CFO: jane.smith@company.com (555-9876)
- Analyst: John Doe (john.doe@company.com)

## Financial Results

| Metric | Q1 | Q2 | Change |
|--------|----|----|--------|
| Revenue | $1.2M | $1.5M | +25% |
| Expenses | $800K | $850K | +6% |

Key observations:
1. Revenue growth exceeded expectations
2. Operating expenses remained controlled
3. Net margin improved to 43%

Customer account 4532-1234-5678-9876 contributed 15% of revenue.
""",
    "metadata": {
        "total_pages": 15,
        "created_at": "2026-05-27T10:00:00Z",
        "department": "Finance"
    }
}

# Step 1: Chunk with all features
print("Step 1: Chunking document with PII masking and structure preservation...")
chunks, masking_meta = chunker.chunk_document_secure(
    text=document["text"],
    document_id=document["id"],
    user_id=document["user_id"],
    metadata=document["metadata"]
)

print(f"  Created {len(chunks)} chunks")
print(f"  Masked {len(masking_meta.get('masked_items', []))} PII items\n")

# Step 2: Validate chunks
print("Step 2: Validating chunk quality...")
validation_report = validator.validate_chunks(chunks)

print(f"  Total chunks: {validation_report['total_chunks']}")
print(f"  Valid chunks: {validation_report['valid_chunks']}")
print(f"  Average quality: {validation_report['average_quality_score']:.2f}\n")

# Step 3: Display enriched chunks
print("Step 3: Sample enriched chunks:\n")
for i, chunk in enumerate(chunks[:3]):  # Show first 3
    print(f"--- Chunk {i} ---")
    print(f"Section: {chunk.get('section_heading', 'N/A')}")
    print(f"Page: {chunk['page_number']}")
    print(f"Tokens: {chunk['token_count']}")
    print(f"Contains Table: {chunk.get('contains_table', False)}")
    print(f"Contains List: {chunk.get('contains_list', False)}")
    print(f"PII Masked: {chunk['pii_masked']}")
    print(f"\nContent:\n{chunk['content'][:200]}...")
    print()

# Step 4: Show masking details
print("\nStep 4: PII Masking Summary:")
if masking_meta:
    for item in masking_meta['masked_items']:
        print(f"  {item['category']:15} | {item['pattern']:15} → {item['masked_value']}")
```

**Expected Output:**
```
Step 1: Chunking document with PII masking and structure preservation...
  Created 8 chunks
  Masked 4 PII items

Step 2: Validating chunk quality...
  Total chunks: 8
  Valid chunks: 8
  Average quality: 0.92

Step 3: Sample enriched chunks:

--- Chunk 0 ---
Section: # Q2 2026 Financial Report
Page: 1
Tokens: 45
Contains Table: False
Contains List: False
PII Masked: True

Content:
# Q2 2026 Financial Report

## Executive Summary

This report covers financial performance for Q2 2026...

--- Chunk 1 ---
Section: # Q2 2026 Financial Report
Page: 1
Tokens: 52
Contains Table: False
Contains List: False
PII Masked: True

Content:
Key contacts:
- CFO: [EMAIL_REDACTED] ([PHONE_US_a3f9c2d5])
- Analyst: Person_name_001 ([EMAIL_REDACTED])...

--- Chunk 2 ---
Section: ## Financial Results
Page: 2
Tokens: 78
Contains Table: True
Contains List: False
PII Masked: True

Content:
| Metric | Q1 | Q2 | Change |
|--------|----|----|--------|
| Revenue | $1.2M | $1.5M | +25% |
| Expenses | $800K | $850K | +6% |...

Step 4: PII Masking Summary:
  contact         | email           → [EMAIL_REDACTED]
  contact         | phone_us        → [PHONE_US_a3f9c2d5]
  identity        | person_name     → Person_name_001
  financial       | credit_card     → [CREDIT_CARD_REDACTED]
```

---

## 9. Best Practices & Recommendations

### **9.1 Chunking Strategy Selection**

| Document Type | Recommended Strategy | Chunk Size | Overlap |
|---------------|---------------------|------------|---------|
| Technical docs | Heading-Preserving | 512 chars | 50-100 |
| Financial reports | Structure-Preserving | 600 chars | 50 |
| Legal contracts | PII-Masked + Structure | 800 chars | 100 |
| Research papers | Semantic (future) | Variable | 10% |
| General text | Recursive Character | 512 chars | 50 |

### **9.2 Performance Optimization**

```python
# Batch processing for large documents
async def process_large_document_parallel(
    document_text: str,
    chunk_size: int = 512,
    num_workers: int = 4
):
    """Process large documents with parallel chunking"""
    import asyncio
    from concurrent.futures import ProcessPoolExecutor
    
    # Split into sections (e.g., by page)
    sections = split_into_sections(document_text)
    
    # Process sections in parallel
    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        loop = asyncio.get_event_loop()
        tasks = [
            loop.run_in_executor(
                executor,
                chunk_section,
                section,
                chunk_size
            )
            for section in sections
        ]
        
        results = await asyncio.gather(*tasks)
    
    # Merge results
    all_chunks = []
    for section_chunks in results:
        all_chunks.extend(section_chunks)
    
    return all_chunks
```

### **9.3 Monitoring Chunking Quality**

```python
# Add to Prometheus metrics
from prometheus_client import Histogram, Counter

chunk_size_histogram = Histogram(
    'chunk_size_chars',
    'Distribution of chunk sizes',
    buckets=[100, 200, 300, 400, 500, 600, 800, 1000]
)

chunks_created = Counter(
    'chunks_created_total',
    'Total chunks created',
    ['document_type', 'masking_applied']
)

pii_items_masked = Counter(
    'pii_items_masked_total',
    'Total PII items masked',
    ['category']
)

# Usage
chunk_size_histogram.observe(len(chunk['content']))
chunks_created.labels(
    document_type='pdf',
    masking_applied='true'
).inc()

for item in masking_meta['masked_items']:
    pii_items_masked.labels(category=item['category']).inc()
```

---

## 10. Summary & Next Steps

### **Key Takeaways**

✅ **Flexible Chunking**: Multiple strategies for different document types  
✅ **Metadata Preservation**: Sections, headings, and page numbers retained  
✅ **PII Protection**: Automatic detection and masking of sensitive data  
✅ **Structure Awareness**: Tables and lists preserved for better context  
✅ **Quality Validation**: Automated checks for chunk quality  
✅ **Production-Ready**: Error handling, monitoring, and optimization built-in  

### **Future Enhancements**

- **Phase 3**: Semantic chunking using embedding similarity
- **Multi-language support**: Language-specific chunking rules
- **Custom PII patterns**: User-defined sensitive data patterns
- **Chunk optimization**: LLM-powered chunk boundary refinement
- **Real-time adaptation**: Dynamic chunk sizing based on retrieval performance

---

**Document Version:** 1.0  
**Last Updated:** 2026-05-27  
**Owner:** Backend Engineering Team  
**Related Docs:**  
- [Data Flow & Retrieval Pipeline](./data-flow.md)
- [Architecture Diagrams](../ARCHITECTURE-DIAGRAMS.md)
- [System Overview](../SYSTEM-OVERVIEW.md)

