# Splitwise Data Import Integration Plan

## Overview

This document outlines a comprehensive plan to integrate Splitwise API for importing user data into Splitwiser, enabling seamless migration and data synchronization.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Data Mapping Strategy](#data-mapping-strategy)
3. [Import Process Flow](#import-process-flow)
4. [API Integration Details](#api-integration-details)
5. [Implementation Phases](#implementation-phases)
6. [Security & Privacy Considerations](#security--privacy-considerations)
7. [Error Handling & Rollback](#error-handling--rollback)
8. [Testing Strategy](#testing-strategy)

---

## Architecture Overview

### High-Level Architecture

```
┌─────────────────┐      OAuth 2.0      ┌──────────────────┐
│                 │ ◄─────────────────── │                  │
│  Splitwise API  │                      │  Splitwiser App  │
│                 │ ──────────────────► │  (Backend)       │
└─────────────────┘   Import Data       └──────────────────┘
                                                │
                                                ▼
                                         ┌──────────────────┐
                                         │   MongoDB        │
                                         │   (Splitwiser)   │
                                         └──────────────────┘
```

### Components to Build

1. **Splitwise OAuth Integration Module** (`backend/app/integrations/splitwise/`)
2. **Data Import Service** (`backend/app/integrations/import_service.py`)
3. **Import API Endpoints** (`backend/app/integrations/router.py`)
4. **Data Transformation Layer** (`backend/app/integrations/transformers.py`)
5. **Import Status Tracking** (MongoDB collection: `import_jobs`)

---

## Data Mapping Strategy

### 1. User Data Mapping

**Splitwise → Splitwiser**

| Splitwise Field | Splitwiser Field | Transformation |
|----------------|------------------|----------------|
| `id` | Store in `splitwiseId` (new field) | Direct |
| `first_name` + `last_name` | `name` | Concatenate |
| `email` | `email` | Direct (handle conflicts) |
| `picture.medium` | `imageUrl` | Direct URL |
| `default_currency` | `currency` | Direct |
| `registration_status` | Skip | Not needed |

**Note**: For email conflicts, append suffix or prompt user to link accounts.

### 2. Group Data Mapping

| Splitwise Field | Splitwiser Field | Transformation |
|----------------|------------------|----------------|
| `id` | Store in `splitwiseGroupId` | Direct |
| `name` | `name` | Direct |
| `group_type` | Skip/Tag | Optional tag |
| `whiteboard_image` | `imageUrl` | Direct URL |
| `members[].id` | `members[].userId` | Map to Splitwiser user ID |
| `members[].balance` | Skip | Calculated from expenses |
| `simplify_by_default` | Skip | Not supported yet |

### 3. Expense Data Mapping

| Splitwise Field | Splitwiser Field | Transformation |
|----------------|------------------|----------------|
| `id` | Store in `splitwiseExpenseId` | Direct |
| `description` | `description` | Direct |
| `cost` | `amount` | Direct |
| `currency_code` | Group's currency | Use group currency |
| `date` | `createdAt` | Parse date |
| `group_id` | `groupId` | Map to Splitwiser group ID |
| `users[].user_id` (paid_share > 0) | `paidBy` | First user with paid_share |
| `users[].owed_share` | `splits[].amount` | Create split records |
| `category.name` | `tags[]` | Add as tag |
| `receipt.original` | `receiptUrls[]` | Add receipt URL |
| `comments[]` | `comments[]` | Transform comments |
| `updated_at` | `updatedAt` | Parse date |

### 4. Friendship/Friend Data

**Strategy**: Import friends as potential group members. Create a "Friends" group or allow adding to existing groups.

| Splitwise Field | Action |
|----------------|--------|
| `id` | Map to user |
| `balance[]` | Create settlement records |
| `groups[]` | Already handled in groups import |

---

## Import Process Flow

### Phase 1: Authentication & Authorization

```
1. User initiates import from Splitwiser app
2. Redirect to Splitwise OAuth authorization page
3. User grants permissions (read-only)
4. Receive OAuth access token
5. Store token securely (encrypted) with user record
```

**Required OAuth Scopes**: 
- Read user data
- Read groups
- Read expenses
- Read friends

### Phase 2: Data Discovery & Analysis

```
1. Fetch current user data (GET /get_current_user)
2. Fetch all groups (GET /get_groups)
3. Count total expenses across all groups (GET /get_expenses with pagination)
4. Fetch friends list (GET /get_friends)
5. Present import summary to user:
   - X groups
   - Y expenses
   - Z friends
   - Estimated time
6. Get user confirmation
```

### Phase 3: Incremental Import

#### Step 3.1: Import User Profile

```python
# Pseudocode
current_user = splitwise_api.get_current_user()
splitwiser_user = transform_user(current_user)
# Check if user exists, update or create
# Store mapping: splitwise_id → splitwiser_id
```

#### Step 3.2: Import Friends as Users

```python
friends = splitwise_api.get_friends()
for friend in friends:
    # Create user record if doesn't exist
    # Store mapping: splitwise_friend_id → splitwiser_user_id
    # Track relationships for later group assignments
```

#### Step 3.3: Import Groups

```python
groups = splitwise_api.get_groups()
for group in groups:
    # Create group in Splitwiser
    # Add members (using mapped user IDs)
    # Store mapping: splitwise_group_id → splitwiser_group_id
    # Set creator to current user
```

#### Step 3.4: Import Expenses (Most Complex)

```python
for group in imported_groups:
    expenses = splitwise_api.get_expenses(group_id=group.splitwise_id)
    for expense in expenses:
        # Transform expense data
        # Map user IDs in splits
        # Handle deleted/archived expenses
        # Create expense in Splitwiser
        # Store mapping: splitwise_expense_id → splitwiser_expense_id
        # Update import progress
```

#### Step 3.5: Import Comments

```python
for expense in imported_expenses:
    comments = expense.get('comments', [])
    for comment in comments:
        # Add comment to Splitwiser expense
        # Preserve original timestamp and author
```

#### Step 3.6: Calculate & Import Settlements

```python
# Splitwise provides balance information
# Calculate settlements from imported expenses
# Create settlement records for completed payments
```

### Phase 4: Verification & Reconciliation

```
1. Count imported records vs. Splitwise records
2. Verify total balances match
3. Check for missing relationships
4. Generate import report
```

---

## API Integration Details

### Required Splitwise API Endpoints

#### 1. User & Authentication

```http
GET /get_current_user
Response: User details
```

#### 2. Groups

```http
GET /get_groups
Response: Array of groups with members

GET /get_group/{id}
Response: Detailed group info
```

#### 3. Expenses

```http
GET /get_expenses?group_id={id}&limit=100&offset=0
Parameters:
- group_id (optional): Filter by group
- dated_after (optional): Filter by date
- dated_before (optional): Filter by date
- limit: Max results (default 100)
- offset: Pagination

Response: Array of expenses with splits
```

#### 4. Friends

```http
GET /get_friends
Response: Array of friends with balance info
```

#### 5. Comments

```http
GET /get_comments?expense_id={id}
Response: Array of comments
```

### Rate Limiting Strategy

Splitwise API has rate limits (not publicly documented, but conservative approach):

- **Estimated limit**: 200-400 requests/hour
- **Strategy**: 
  - Batch requests where possible
  - Implement exponential backoff
  - Use pagination efficiently
  - Cache responses during import
  - Queue-based import with delays

```python
# Example rate limiting
import time
from ratelimit import limits, sleep_and_retry

CALLS_PER_HOUR = 200
ONE_HOUR = 3600

@sleep_and_retry
@limits(calls=CALLS_PER_HOUR, period=ONE_HOUR)
def call_splitwise_api(endpoint):
    return requests.get(endpoint)
```

---

## Implementation Phases

### Phase 1: Foundation (Week 1)

**Tasks**:
1. Create OAuth integration module
2. Set up Splitwise API client
3. Implement token storage (encrypted)
4. Create import_jobs collection schema
5. Build basic data transformers

**Deliverables**:
- OAuth flow working
- Can fetch current user data
- Token storage implemented

### Phase 2: Core Import Logic (Week 2)

**Tasks**:
1. Implement user import
2. Implement group import with members
3. Create ID mapping storage
4. Build progress tracking
5. Add error handling

**Deliverables**:
- Can import users and groups
- ID mapping works correctly
- Progress tracked in database

### Phase 3: Expense Import (Week 3)

**Tasks**:
1. Implement expense transformation logic
2. Handle different split types
3. Import receipts (download and upload to our storage)
4. Import comments
5. Handle edge cases (deleted users, archived expenses)

**Deliverables**:
- Expenses imported correctly
- Comments preserved
- Receipts migrated

### Phase 4: Settlement & Balances (Week 4)

**Tasks**:
1. Calculate settlements from imported data
2. Verify balance consistency
3. Import payment history (if available)
4. Generate reconciliation report

**Deliverables**:
- Balances match Splitwise
- Settlement records created

### Phase 5: UI & Polish (Week 5)

**Tasks**:
1. Create import UI (web and mobile)
2. Add progress indicators
3. Implement import preview
4. Add rollback functionality
5. Create user documentation

**Deliverables**:
- User-friendly import interface
- Can preview before import
- Rollback works

### Phase 6: Testing & Launch (Week 6)

**Tasks**:
1. Integration testing
2. Load testing with large datasets
3. Security audit
4. Beta testing with real users
5. Documentation

**Deliverables**:
- Tested with 1000+ expense imports
- Security review passed
- Ready for production

---

## Security & Privacy Considerations

### 1. OAuth Token Security

```python
# Encrypt tokens before storage
from cryptography.fernet import Fernet

class TokenManager:
    def __init__(self, encryption_key):
        self.cipher = Fernet(encryption_key)
    
    def encrypt_token(self, token):
        return self.cipher.encrypt(token.encode()).decode()
    
    def decrypt_token(self, encrypted_token):
        return self.cipher.decrypt(encrypted_token.encode()).decode()
```

Store encryption key in environment variables, never in code.

### 2. Data Privacy

- **User Consent**: Explicit consent before import
- **Data Minimization**: Only import necessary data
- **Right to Delete**: Provide way to remove imported data
- **Transparency**: Show what data will be imported

### 3. Access Control

- Only user who authorized can trigger import
- Can't import other users' data without permission
- Revoke OAuth token after import completes (optional)

### 4. Audit Trail

```javascript
// Track all import operations
{
  userId: ObjectId,
  importJobId: ObjectId,
  operation: "import_started",
  splitwiseUserId: String,
  timestamp: Date,
  metadata: {
    groupsImported: Number,
    expensesImported: Number,
    errors: Array
  }
}
```

---

## Error Handling & Rollback

### Error Categories

#### 1. Network Errors
- **Issue**: API unavailable, timeout
- **Handling**: Retry with exponential backoff, queue job for later
- **Rollback**: None needed if no data written

#### 2. Authentication Errors
- **Issue**: Token expired, invalid, revoked
- **Handling**: Request re-authorization
- **Rollback**: Pause import, notify user

#### 3. Data Validation Errors
- **Issue**: Invalid data from Splitwise
- **Handling**: Log error, skip record, continue import
- **Rollback**: None needed, partial import acceptable

#### 4. Conflict Errors
- **Issue**: Email already exists, duplicate data
- **Handling**: 
  - Emails: Append suffix or prompt user
  - Duplicates: Skip or update existing
- **Rollback**: Depends on user choice

#### 5. System Errors
- **Issue**: Database failure, service crash
- **Handling**: Full rollback
- **Rollback**: Delete all imported records for this job

### Rollback Strategy

```python
class ImportRollback:
    def __init__(self, import_job_id):
        self.job_id = import_job_id
        self.mappings = self.load_mappings()
    
    async def rollback(self):
        # Delete in reverse order of creation
        await self.delete_settlements()
        await self.delete_expenses()
        await self.delete_groups()
        await self.delete_imported_users()  # Only if created during import
        await self.delete_import_job()
        await self.delete_mappings()
```

### Progress Checkpointing

```javascript
// import_jobs collection
{
  _id: ObjectId,
  userId: ObjectId,
  status: "in_progress", // "pending", "in_progress", "completed", "failed", "rolled_back"
  startedAt: Date,
  completedAt: Date,
  checkpoints: {
    userImported: true,
    friendsImported: true,
    groupsImported: { completed: 5, total: 8 },
    expensesImported: { completed: 143, total: 500 }
  },
  errors: [
    {
      stage: "expense_import",
      expenseId: "123",
      error: "Invalid split data",
      timestamp: Date
    }
  ],
  summary: {
    usersCreated: Number,
    groupsCreated: Number,
    expensesCreated: Number,
    settlementsCreated: Number
  }
}
```

**Resume Logic**: If import fails, can resume from last checkpoint.

---

## Testing Strategy

### 1. Unit Tests

```python
# Test data transformers
def test_transform_splitwise_user():
    splitwise_user = {
        "id": 123,
        "first_name": "John",
        "last_name": "Doe",
        "email": "john@example.com",
        "default_currency": "USD"
    }
    result = transform_user(splitwise_user)
    assert result["name"] == "John Doe"
    assert result["splitwiseId"] == "123"
    assert result["currency"] == "USD"

# Test split calculations
def test_expense_split_mapping():
    # ...

# Test ID mapping
def test_id_mapper():
    # ...
```

### 2. Integration Tests

```python
# Test full import flow with mock Splitwise API
@pytest.mark.asyncio
async def test_full_import_flow(mock_splitwise_api, test_db):
    # Setup mock data
    mock_splitwise_api.get_current_user.return_value = {...}
    mock_splitwise_api.get_groups.return_value = [...]
    
    # Run import
    import_service = ImportService(test_db, mock_splitwise_api)
    result = await import_service.import_all_data(user_id)
    
    # Verify results
    assert result["groupsImported"] == 3
    assert result["expensesImported"] == 50
```

### 3. End-to-End Tests

- Test with real Splitwise sandbox account
- Import small dataset (5 groups, 20 expenses)
- Verify data integrity
- Test rollback
- Test resume after failure

### 4. Performance Tests

```python
# Test large dataset import
def test_import_1000_expenses(benchmark):
    # Measure time to import 1000 expenses
    result = benchmark(import_service.import_expenses, large_dataset)
    assert result["duration"] < 300  # Should complete in 5 minutes
```

### 5. Security Tests

- Test token encryption/decryption
- Test unauthorized access prevention
- Test SQL injection (though MongoDB)
- Test rate limiting

---

## Database Schema Additions

### 1. Add Import Tracking Fields to Existing Collections

```javascript
// users collection - add these fields
{
  // ... existing fields ...
  splitwiseId: String,          // Original Splitwise user ID
  importedFrom: String,         // "splitwise"
  importedAt: Date
}

// groups collection
{
  // ... existing fields ...
  splitwiseGroupId: String,
  importedFrom: String,
  importedAt: Date
}

// expenses collection
{
  // ... existing fields ...
  splitwiseExpenseId: String,
  importedFrom: String,
  importedAt: Date
}
```

### 2. New Collections

#### import_jobs Collection

```javascript
{
  _id: ObjectId,
  userId: ObjectId,              // Splitwiser user performing import
  status: String,                // "pending", "in_progress", "completed", "failed", "rolled_back"
  splitwiseAccessToken: String,  // Encrypted OAuth token
  startedAt: Date,
  completedAt: Date,
  lastCheckpoint: String,
  checkpoints: {
    userImported: Boolean,
    friendsImported: Boolean,
    groupsImported: {
      completed: Number,
      total: Number,
      currentGroup: String       // For resume
    },
    expensesImported: {
      completed: Number,
      total: Number,
      currentExpense: String
    }
  },
  errors: [
    {
      stage: String,
      message: String,
      details: Object,
      timestamp: Date
    }
  ],
  summary: {
    usersCreated: Number,
    groupsCreated: Number,
    expensesCreated: Number,
    commentsImported: Number,
    settlementsCreated: Number,
    receiptsMigrated: Number
  },
  metadata: {
    splitwiseUserId: String,
    totalDataSize: Number,
    estimatedDuration: Number
  }
}
```

#### splitwise_id_mappings Collection

```javascript
{
  _id: ObjectId,
  importJobId: ObjectId,
  entityType: String,           // "user", "group", "expense"
  splitwiseId: String,          // Original Splitwise ID
  splitwiserId: String,         // New Splitwiser ID
  createdAt: Date
}
```

// Index for fast lookups
db.splitwise_id_mappings.createIndex({ 
  importJobId: 1, 
  entityType: 1, 
  splitwiseId: 1 
}, { unique: true })
```

#### oauth_tokens Collection

```javascript
{
  _id: ObjectId,
  userId: ObjectId,
  provider: String,              // "splitwise"
  accessToken: String,           // Encrypted
  refreshToken: String,          // Encrypted (if available)
  expiresAt: Date,
  scope: [String],
  createdAt: Date,
  lastUsedAt: Date,
  revokedAt: Date                // null if active
}
```

---

## API Endpoints Specification

### Backend API Endpoints to Create

#### 1. Initiate Import

```http
POST /api/v1/import/splitwise/initiate
Authorization: Bearer {jwt_token}

Response:
{
  "authUrl": "https://secure.splitwise.com/oauth/authorize?...",
  "state": "random_state_token"
}
```

#### 2. OAuth Callback

```http
GET /api/v1/import/splitwise/callback?code={auth_code}&state={state}

Response:
{
  "success": true,
  "message": "Authorization successful",
  "canProceed": true
}
```

#### 3. Preview Import

```http
POST /api/v1/import/splitwise/preview
Authorization: Bearer {jwt_token}

Response:
{
  "splitwiseUser": {
    "name": "John Doe",
    "email": "john@example.com"
  },
  "summary": {
    "groups": 8,
    "expenses": 247,
    "friends": 15,
    "estimatedDuration": "3-5 minutes"
  },
  "warnings": [
    {
      "type": "email_conflict",
      "message": "Email john@example.com already exists",
      "resolution": "Will create with john+splitwise@example.com"
    }
  ]
}
```

#### 4. Start Import

```http
POST /api/v1/import/splitwise/start
Authorization: Bearer {jwt_token}
Content-Type: application/json

{
  "confirmWarnings": true,
  "options": {
    "importReceipts": true,
    "importComments": true,
    "importArchivedExpenses": false
  }
}

Response:
{
  "importJobId": "507f1f77bcf86cd799439011",
  "status": "in_progress",
  "estimatedCompletion": "2026-01-13T15:30:00Z"
}
```

#### 5. Check Import Status

```http
GET /api/v1/import/splitwise/status/{importJobId}
Authorization: Bearer {jwt_token}

Response:
{
  "importJobId": "507f1f77bcf86cd799439011",
  "status": "in_progress",
  "progress": {
    "current": 143,
    "total": 247,
    "percentage": 58,
    "currentStage": "Importing expenses",
    "stages": {
      "user": "completed",
      "friends": "completed",
      "groups": "completed",
      "expenses": "in_progress",
      "settlements": "pending"
    }
  },
  "errors": [],
  "startedAt": "2026-01-13T15:00:00Z",
  "estimatedCompletion": "2026-01-13T15:30:00Z"
}
```

#### 6. Rollback Import

```http
POST /api/v1/import/splitwise/rollback/{importJobId}
Authorization: Bearer {jwt_token}

Response:
{
  "success": true,
  "message": "Import rolled back successfully",
  "deletedRecords": {
    "groups": 8,
    "expenses": 143,
    "settlements": 25
  }
}
```

#### 7. List Import History

```http
GET /api/v1/import/history
Authorization: Bearer {jwt_token}

Response:
{
  "imports": [
    {
      "importJobId": "507f1f77bcf86cd799439011",
      "provider": "splitwise",
      "status": "completed",
      "summary": {...},
      "startedAt": "2026-01-13T15:00:00Z",
      "completedAt": "2026-01-13T15:28:00Z"
    }
  ]
}
```

---

## Implementation Checklist

### Backend

- [ ] Create `backend/app/integrations/` directory structure
- [ ] Implement Splitwise OAuth client
- [ ] Create OAuth token storage with encryption
- [ ] Build data transformer functions
- [ ] Implement ID mapping service
- [ ] Create import service with checkpointing
- [ ] Add import API endpoints
- [ ] Implement rate limiting
- [ ] Add rollback functionality
- [ ] Create background job queue (using Celery or similar)
- [ ] Add import status WebSocket for real-time updates
- [ ] Write unit tests for transformers
- [ ] Write integration tests
- [ ] Add API documentation

### Database

- [ ] Add migration script for new fields
- [ ] Create `import_jobs` collection
- [ ] Create `splitwise_id_mappings` collection
- [ ] Create `oauth_tokens` collection
- [ ] Add indexes for performance
- [ ] Create backup before import feature

### Frontend (Web)

- [ ] Create import wizard UI
- [ ] Add OAuth redirect handling
- [ ] Build import preview screen
- [ ] Add progress tracker component
- [ ] Create import history page
- [ ] Add rollback confirmation dialog
- [ ] Implement real-time progress updates
- [ ] Add error display and handling

### Frontend (Mobile)

- [ ] Create import flow screens
- [ ] Add OAuth handling (deep linking)
- [ ] Build import preview screen
- [ ] Add progress indicator
- [ ] Create import history screen
- [ ] Add rollback functionality

### Documentation

- [ ] User guide for importing from Splitwise
- [ ] API documentation
- [ ] Developer guide for adding other import sources
- [ ] Troubleshooting guide
- [ ] Privacy policy update

### Testing & QA

- [ ] Unit test coverage > 80%
- [ ] Integration tests for all endpoints
- [ ] E2E test with sandbox account
- [ ] Performance test with 1000+ expenses
- [ ] Security audit
- [ ] Beta test with 10 users
- [ ] Load test for concurrent imports

---

## Future Enhancements

1. **Incremental Sync**: Periodically sync new expenses from Splitwise
2. **Two-Way Sync**: Push expenses created in Splitwiser back to Splitwise
3. **Multiple Import Sources**: Support for other apps (Venmo, Zelle transaction history)
4. **Smart Deduplication**: Detect and merge duplicate expenses
5. **Import Templates**: Save import preferences for future imports
6. **Export to Splitwise**: Allow exporting Splitwiser data back to Splitwise
7. **Selective Import**: Choose specific groups/expenses to import
8. **Import Scheduling**: Schedule imports to run at specific times

---

## Estimated Effort

| Phase | Duration | Team Size | Priority |
|-------|----------|-----------|----------|
| Foundation | 1 week | 1 developer | High |
| Core Import | 1 week | 1-2 developers | High |
| Expense Import | 1 week | 1-2 developers | High |
| Settlements | 1 week | 1 developer | Medium |
| UI/UX | 1 week | 1 frontend dev | High |
| Testing | 1 week | 1 QA + 1 dev | High |
| **Total** | **6 weeks** | **2-3 people** | - |

---

## Success Metrics

1. **Functionality**:
   - 95%+ of expenses imported successfully
   - Balance totals match Splitwise within $0.01
   - All group memberships preserved

2. **Performance**:
   - Import 100 expenses in < 2 minutes
   - Import 1000 expenses in < 15 minutes
   - No timeout errors for datasets < 5000 expenses

3. **User Experience**:
   - < 5% of imports require manual intervention
   - < 1% rollback rate
   - User satisfaction score > 4.5/5

4. **Reliability**:
   - 99% success rate for imports
   - Zero data loss incidents
   - Rollback works 100% of the time

---

## Risk Assessment

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Splitwise API changes | High | Medium | Version API client, monitor for changes |
| Rate limiting issues | Medium | High | Implement smart rate limiting, queue system |
| Data inconsistencies | High | Medium | Extensive validation, reconciliation checks |
| Large dataset imports timeout | Medium | Medium | Pagination, background jobs, checkpointing |
| OAuth token expiry mid-import | Medium | Low | Refresh token handling, graceful pause/resume |
| User privacy concerns | High | Low | Clear communication, consent, data minimization |
| Duplicate data on re-import | Medium | Medium | Deduplication logic, import tracking |

---

## Conclusion

This comprehensive plan provides a roadmap for implementing Splitwise data import into Splitwiser. The phased approach ensures steady progress while maintaining data integrity and user experience. The implementation prioritizes security, error handling, and user control throughout the import process.

**Next Steps**:
1. Review and approve this plan
2. Set up development environment with Splitwise API credentials
3. Begin Phase 1 implementation
4. Schedule weekly progress reviews

**Questions to Resolve**:
1. Should we support continuous sync or one-time import only?
2. How to handle conflicts (email duplicates, etc.)?
3. Should imported data be marked/tagged differently in the UI?
4. What's our policy on deleting imported data?
