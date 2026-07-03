# System Architecture

## Components

### FastAPI

Provides REST endpoints for:

- Document creation
- Document updates
- Metadata search
- Semantic search
- Natural language search

---

### Repository Layer

Handles:

- Database operations
- CRUD functionality
- Version management

---

### Semantic Search Engine

Uses:

- TF-IDF Vectorization
- Cosine Similarity

Workflow:

User Query
↓
Vectorize Query
↓
Vectorize Documents
↓
Calculate Similarity
↓
Rank Documents
↓
Return Results

---

### Natural Language Parser

Converts human language into metadata filters.

Example:

Input:

show me approved structural drawings for tower a

Output:

{
"category": "Drawing",
"discipline": "Structural",
"status": "Approved",
"project_name": "Tower A"
}

---

### SQLite Database

Stores:

- Documents
- Document Versions