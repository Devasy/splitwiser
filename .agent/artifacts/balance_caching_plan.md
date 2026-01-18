# Balance Caching & Settlement Algorithm Refactoring Plan

## Overview

This document outlines the plan to simplify balance calculations by:
1. Caching net balances per group member in the Group document
2. Using the optimized settlement algorithm uniformly across all balance endpoints
3. Removing redundant calculation logic

## Current Architecture

### Data Flow
```
Expense Created → Settlements Created → Recalculate balances on every request
```

### Problems
1. **Redundant Calculations**: `get_friends_balance_summary()`, `get_overall_balance_summary()`, and `calculate_optimized_settlements()` all have similar aggregation logic
2. **N+1 Queries**: `get_overall_balance_summary()` runs one aggregation per group
3. **No Caching**: Every balance request recalculates from settlements

## Proposed Architecture

### New Data Flow
```
Expense Created → Settlements Created → Update Cached Balances → Read from cache
```

### Group Document Schema Enhancement
```python
{
    "_id": ObjectId,
    "name": "Trip 2024",
    "members": [...],
    "currency": "USD",
    # NEW: Cached balances (updated on expense/settlement changes)
    "cachedBalances": {
        "user1_id": 75.50,     # positive = owed by others
        "user2_id": -50.00,    # negative = owes to others
        "user3_id": -25.50,
    },
    "balancesUpdatedAt": datetime
}
```

## Implementation Steps

### Phase 1: Add Balance Caching Infrastructure

#### 1.1 Update Group Schema
Add `cachedBalances` field to GroupResponse and database model.

#### 1.2 Create `_recalculate_group_balances()` method
- Calculates per-member net balances using `_calculate_advanced_settlements()`
- Updates the `cachedBalances` field in the group document
- Returns the calculated balances

```python
async def _recalculate_group_balances(self, group_id: str) -> Dict[str, float]:
    """Recalculate and cache member balances for a group."""
    # Get optimized settlements
    optimized = await self._calculate_advanced_settlements(group_id)
    
    # Convert to per-member balances
    member_balances = defaultdict(float)
    for settlement in optimized:
        member_balances[settlement.fromUserId] -= settlement.amount  # owes
        member_balances[settlement.toUserId] += settlement.amount    # owed
    
    # Update group document with cached balances
    await self.groups_collection.update_one(
        {"_id": ObjectId(group_id)},
        {
            "$set": {
                "cachedBalances": dict(member_balances),
                "balancesUpdatedAt": datetime.now(timezone.utc)
            }
        }
    )
    
    return dict(member_balances)
```

### Phase 2: Update Balance Calculation Triggers

#### 2.1 After `create_expense()` - call `_recalculate_group_balances()`
#### 2.2 After `update_expense()` - call `_recalculate_group_balances()`
#### 2.3 After `delete_expense()` - call `_recalculate_group_balances()`
#### 2.4 After `create_manual_settlement()` - call `_recalculate_group_balances()`
#### 2.5 After `update_settlement_status()` - call `_recalculate_group_balances()`

### Phase 3: Simplify Balance Endpoints

#### 3.1 Refactor `get_overall_balance_summary()`
Instead of N aggregations (one per group), read from cached balances:

```python
async def get_overall_balance_summary(self, user_id: str) -> Dict[str, Any]:
    """Get overall balance summary using cached balances."""
    groups = await self.groups_collection.find(
        {"members.userId": user_id}
    ).to_list(None)
    
    total_owed_to_you = 0
    total_you_owe = 0
    groups_summary = []
    
    for group in groups:
        # Read from cache
        cached = group.get("cachedBalances", {})
        user_balance = cached.get(user_id, 0)
        
        if abs(user_balance) > 0.01:
            groups_summary.append({
                "group_id": str(group["_id"]),
                "group_name": group["name"],
                "yourBalanceInGroup": user_balance,
            })
            if user_balance > 0:
                total_owed_to_you += user_balance
            else:
                total_you_owe += abs(user_balance)
    
    return {
        "totalOwedToYou": total_owed_to_you,
        "totalYouOwe": total_you_owe,
        "netBalance": total_owed_to_you - total_you_owe,
        "currency": "USD",
        "groupsSummary": groups_summary,
    }
```

#### 3.2 Refactor `get_friends_balance_summary()`
Use optimized settlements per group, then aggregate by friend:

```python
async def get_friends_balance_summary(self, user_id: str) -> Dict[str, Any]:
    """Get friend balances using optimized settlements per group."""
    groups = await self.groups_collection.find(
        {"members.userId": user_id}
    ).to_list(None)
    
    friend_balances = defaultdict(lambda: {"balance": 0, "groups": []})
    
    for group in groups:
        group_id = str(group["_id"])
        
        # Get optimized settlements for this group
        optimized = await self.calculate_optimized_settlements(group_id)
        
        for settlement in optimized:
            # Check if user is involved
            if settlement.fromUserId == user_id:
                # User owes friend (negative)
                friend_id = settlement.toUserId
                friend_balances[friend_id]["balance"] -= settlement.amount
                friend_balances[friend_id]["groups"].append({
                    "groupId": group_id,
                    "groupName": group["name"],
                    "balance": -settlement.amount
                })
            elif settlement.toUserId == user_id:
                # Friend owes user (positive)
                friend_id = settlement.fromUserId
                friend_balances[friend_id]["balance"] += settlement.amount
                friend_balances[friend_id]["groups"].append({
                    "groupId": group_id,
                    "groupName": group["name"],
                    "balance": settlement.amount
                })
    
    # Build response with user details
    # ... (fetch user details in batch, build response)
```

### Phase 4: Migration

#### 4.1 Create migration script to initialize `cachedBalances`
For all existing groups, calculate and store initial cached balances.

```python
async def migrate_cached_balances():
    """Initialize cachedBalances for all existing groups."""
    groups = await groups_collection.find({}).to_list(None)
    
    for group in groups:
        group_id = str(group["_id"])
        await expense_service._recalculate_group_balances(group_id)
```

## Benefits

1. **Performance**: O(1) for balance reads (from cache) vs O(N) aggregations
2. **Simplicity**: One source of truth for balance calculations
3. **Consistency**: All endpoints use the same optimized settlement algorithm
4. **Reduced Complexity**: Remove duplicated aggregation pipelines

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Cache staleness | Always update cache on any expense/settlement change |
| Migration failures | Run migration in batches with retry logic |
| Edge cases | Keep fallback to recalculate on-demand if cache missing |

## Testing Plan

1. Unit tests for `_recalculate_group_balances()`
2. Integration tests for balance endpoints with cached data
3. Migration testing on staging database
4. Performance benchmarks before/after

---

## Implementation Order

1. ✅ Create this plan
2. ✅ Add `_recalculate_group_balances()` method
3. ✅ Add `_get_cached_balances()` helper method
4. ✅ Add cache update calls to expense/settlement methods:
   - ✅ `create_expense()`
   - ✅ `update_expense()`
   - ✅ `delete_expense()`
   - ✅ `create_manual_settlement()`
5. ✅ Refactor `get_overall_balance_summary()` to use cache
6. ✅ Refactor `get_friends_balance_summary()` to use optimized settlements
7. ✅ Create migration script (`005_init_cached_balances.py`)
8. 🔲 Run migration on your database
9. 🔲 Write tests
10. 🔲 Deploy migration

## How to Run Migration

```bash
cd backend
python -m migrations.005_init_cached_balances
```

## Summary of Changes

### New Methods Added to `ExpenseService`:
- `_recalculate_group_balances(group_id)` - Calculates and caches per-member balances
- `_get_cached_balances(group_id)` - Gets cached balances with fallback to recalculation

### Modified Methods:
- `create_expense()` - Now calls `_recalculate_group_balances()` after expense creation
- `update_expense()` - Now calls `_recalculate_group_balances()` after expense update
- `delete_expense()` - Now calls `_recalculate_group_balances()` after expense deletion
- `create_manual_settlement()` - Now calls `_recalculate_group_balances()` after settlement creation
- `get_overall_balance_summary()` - Now reads from cached balances (simple O(1) reads)
- `get_friends_balance_summary()` - Now uses `calculate_optimized_settlements()` per group

### New Migration:
- `005_init_cached_balances.py` - Initializes cached balances for all existing groups
