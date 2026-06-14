# Database Schema

## documents

| Column | Type |
|----------|----------|
| id | Integer |
| document_code | String |
| title | String |
| category | String |
| project_name | String |
| discipline | String |
| author | String |
| status | String |
| description | Text |
| content | Text |
| current_version | Integer |
| created_at | DateTime |

---

## document_versions

| Column | Type |
|----------|----------|
| id | Integer |
| document_id | Integer |
| version_number | Integer |
| file_name | String |
| checksum | String |
| change_summary | Text |
| uploaded_at | DateTime |

---

## Relationship

documents

1 → many

document_versions

A document can have multiple versions.

---

## Example

Document:

DOC-001

Version History:

v1 Initial Submission

v2 Design Revision

v3 Approved Issue