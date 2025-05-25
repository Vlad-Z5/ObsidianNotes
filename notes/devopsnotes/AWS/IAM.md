**Scope:** Global

**Policy:** JSON document that defines permissions  
- Identity or resource based
- Session based issued by STS to create token or assume role
- **SCP**: Org-level policy that limits permissions across accounts. Allow in SCP actually denies everything, but the allow list
- Permission Boundary: IAM user or role equivalent of SCP

**User:** A single entity (person, app, or svc)
**Group:** Collection of users, can't contain groups
**Role:** User without credentials. For temporary access

**IAM Credentials report:** Account-level report that lists all users and their respective credentials statuses

**IAM Access Advisor:** User-level report that shows user permissions and when those services were accessed

**IAM Access Analyser:** Helps identify resources shared publicly or with other accounts
