import asyncio
from datetime import datetime, timedelta, timezone
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from app.expenses.schemas import ExpenseCreateRequest, ExpenseSplit, SplitType
from app.expenses.service import ExpenseService
from bson import ObjectId, errors
from fastapi import HTTPException


@pytest.fixture
def expense_service():
    """Create an ExpenseService instance with mocked database"""
    service = ExpenseService()
    return service


@pytest.fixture
def mock_group_data():
    """Mock group data for testing"""
    return {
        "_id": ObjectId("65f1a2b3c4d5e6f7a8b9c0d0"),
        "name": "Test Group",
        "members": [
            {"userId": "user_a", "role": "admin"},
            {"userId": "user_b", "role": "member"},
            {"userId": "user_c", "role": "member"},
        ],
    }


@pytest.fixture
def mock_expense_data():
    """Mock expense data for testing"""
    return {
        "_id": ObjectId("65f1a2b3c4d5e6f7a8b9c0d1"),
        "groupId": "65f1a2b3c4d5e6f7a8b9c0d0",
        "createdBy": "user_a",
        "description": "Test Dinner",
        "amount": 100.0,
        "splits": [
            {"userId": "user_a", "amount": 50.0, "type": "equal"},
            {"userId": "user_b", "amount": 50.0, "type": "equal"},
        ],
        "splitType": "equal",
        "tags": ["dinner"],
        "receiptUrls": [],
        "comments": [],
        "history": [],
        "createdAt": datetime.now(timezone.utc),
        "updatedAt": datetime.now(timezone.utc),
    }


@pytest.mark.asyncio
async def test_create_expense_success(expense_service, mock_group_data):
    """Test successful expense creation"""
    expense_request = ExpenseCreateRequest(
        description="Test Dinner",
        amount=100.0,
        splits=[
            ExpenseSplit(userId="user_a", amount=50.0),
            ExpenseSplit(userId="user_b", amount=50.0),
        ],
        splitType=SplitType.EQUAL,
        paidBy="user_a",  # Added required paidBy field
        tags=["dinner"],
    )

    with patch("app.expenses.service.mongodb") as mock_mongodb, patch.object(
        expense_service, "_create_settlements_for_expense"
    ) as mock_settlements, patch.object(
        expense_service, "calculate_optimized_settlements"
    ) as mock_optimized, patch.object(
        expense_service, "_get_group_summary"
    ) as mock_summary, patch.object(
        expense_service, "_expense_doc_to_response"
    ) as mock_response:

        # Mock database collections
        mock_db = MagicMock()
        mock_mongodb.database = mock_db

        mock_db.groups.find_one = AsyncMock(return_value=mock_group_data)
        mock_db.expenses.insert_one = AsyncMock()

        mock_settlements.return_value = []
        mock_optimized.return_value = []
        mock_summary.return_value = {
            "totalExpenses": 100.0,
            "totalSettlements": 1,
            "optimizedSettlements": [],
        }
        mock_response.return_value = {"id": "test_id", "description": "Test Dinner"}

        result = await expense_service.create_expense(
            "65f1a2b3c4d5e6f7a8b9c0d0", expense_request, "user_a"
        )

        # Assertions
        assert result is not None
        assert "expense" in result
        assert "settlements" in result
        assert "groupSummary" in result
        mock_db.groups.find_one.assert_called_once()
        mock_db.expenses.insert_one.assert_called_once()


@pytest.mark.asyncio
async def test_create_expense_invalid_group(expense_service):
    """Test expense creation with invalid group"""
    expense_request = ExpenseCreateRequest(
        description="Test Dinner",
        amount=100.0,
        splits=[ExpenseSplit(userId="user_a", amount=100.0)],
        paidBy="user_a",  # Added required paidBy field
    )

    with patch("app.expenses.service.mongodb") as mock_mongodb:
        mock_db = MagicMock()
        mock_mongodb.database = mock_db
        mock_db.groups.find_one = AsyncMock(return_value=None)

        """# Test with invalid ObjectId format
        with pytest.raises(ValueError, match="Group not found or user not a member"):
            await expense_service.create_expense(
                "invalid_group", expense_request, "user_a"
            )

        # Test with valid ObjectId format but non-existent group
        with pytest.raises(ValueError, match="Group not found or user not a member"):
            await expense_service.create_expense("65f1a2b3c4d5e6f7a8b9c0d0", expense_request, "user_a")"""
        # Updated after stricter exception handling (July 2025)
        # Case 1: Invalid ObjectId format
        with pytest.raises(HTTPException) as exc_info_1:
            await expense_service.create_expense(
                "invalid_group", expense_request, "user_a"
            )
        assert exc_info_1.value.status_code == 400
        assert "Invalid group ID" in str(exc_info_1.value.detail)

        # Case 2: Valid ObjectId format but group not found or user not a member
        with pytest.raises(HTTPException) as exc_info_2:
            await expense_service.create_expense(
                str(ObjectId()), expense_request, "user_a"
            )
        assert exc_info_2.value.status_code == 403
        assert "not a member of this group" in str(exc_info_2.value.detail)


@pytest.mark.asyncio
async def test_create_expense_payer_not_member(expense_service, mock_group_data):
    """Test expense creation with payer who is not a member of the group"""
    expense_request = ExpenseCreateRequest(
        description="Test Dinner",
        amount=100.0,
        splits=[
            ExpenseSplit(userId="user_a", amount=50.0),
            ExpenseSplit(userId="user_b", amount=50.0),
        ],
        splitType=SplitType.EQUAL,
        paidBy="non_member_user",  # User who is NOT in the group
        tags=["dinner"],
    )

    with patch("app.expenses.service.mongodb") as mock_mongodb:
        mock_db = MagicMock()
        mock_mongodb.database = mock_db

        mock_db.groups.find_one = AsyncMock(return_value=mock_group_data)

        with pytest.raises(HTTPException) as exc_info:
            await expense_service.create_expense(
                "65f1a2b3c4d5e6f7a8b9c0d0", expense_request, "user_a"
            )

        assert exc_info.value.status_code == 400
        assert "The selected payer is not a member of this group" in str(
            exc_info.value.detail
        )


@pytest.mark.asyncio
async def test_calculate_optimized_settlements_advanced(expense_service):
    """Test advanced settlement algorithm with real optimization logic"""
    group_id = "test_group_123"

    # Create proper ObjectIds for users
    user_a_id = ObjectId()
    user_b_id = ObjectId()
    user_c_id = ObjectId()

    # Mock settlements representing: B owes A $100, C owes B $100
    # Expected optimization: C should pay A $100 directly (instead of C->B and B->A)
    mock_settlements = [
        {
            "_id": ObjectId(),
            "groupId": group_id,
            "payerId": str(user_b_id),
            "payeeId": str(user_a_id),
            "amount": 100.0,
            "status": "pending",
            "payerName": "Bob",
            "payeeName": "Alice",
        },
        {
            "_id": ObjectId(),
            "groupId": group_id,
            "payerId": str(user_c_id),
            "payeeId": str(user_b_id),
            "amount": 100.0,
            "status": "pending",
            "payerName": "Charlie",
            "payeeName": "Bob",
        },
    ]

    # Mock user data
    mock_users = {
        str(user_a_id): {"_id": user_a_id, "name": "Alice"},
        str(user_b_id): {"_id": user_b_id, "name": "Bob"},
        str(user_c_id): {"_id": user_c_id, "name": "Charlie"},
    }

    with patch("app.expenses.service.mongodb") as mock_mongodb:
        mock_db = MagicMock()
        mock_mongodb.database = mock_db

        # Setup async iterator for settlements
        mock_cursor = AsyncMock()
        mock_cursor.to_list.return_value = mock_settlements
        mock_db.settlements.find.return_value = mock_cursor

        # Setup user lookups
        async def mock_user_find_one(query):
            user_id = str(query["_id"])
            return mock_users.get(user_id)

        mock_db.users.find_one = AsyncMock(side_effect=mock_user_find_one)

        result = await expense_service.calculate_optimized_settlements(
            group_id, "advanced"
        )

        # Verify optimization: should result in 1 transaction instead of 2
        assert len(result) == 1
        # The optimized result should be Charlie paying Alice $100
        # (Bob owes Alice $100, Charlie owes Bob $100 -> Charlie owes Alice $100)
        settlement = result[0]
        assert settlement.amount == 100.0
        assert settlement.fromUserName == "Charlie"
        assert settlement.toUserName == "Alice"
        assert settlement.fromUserId == str(user_c_id)
        assert settlement.toUserId == str(user_a_id)


@pytest.mark.asyncio
async def test_calculate_optimized_settlements_normal(expense_service):
    """Test normal settlement algorithm - only simplifies direct relationships"""
    group_id = "test_group_123"

    # Create proper ObjectIds for users
    user_a_id = ObjectId()
    user_b_id = ObjectId()

    # Mock settlements: A owes B $100, B owes A $30
    mock_settlements = [
        {
            "_id": ObjectId(),
            "groupId": group_id,
            "payerId": str(user_b_id),
            "payeeId": str(user_a_id),
            "amount": 100.0,
            "status": "pending",
            "payerName": "Bob",
            "payeeName": "Alice",
        },
        {
            "_id": ObjectId(),
            "groupId": group_id,
            "payerId": str(user_a_id),
            "payeeId": str(user_b_id),
            "amount": 30.0,
            "status": "pending",
            "payerName": "Alice",
            "payeeName": "Bob",
        },
    ]

    mock_users = {
        str(user_a_id): {"_id": user_a_id, "name": "Alice"},
        str(user_b_id): {"_id": user_b_id, "name": "Bob"},
    }

    with patch("app.expenses.service.mongodb") as mock_mongodb:
        mock_db = MagicMock()
        mock_mongodb.database = mock_db

        mock_cursor = AsyncMock()
        mock_cursor.to_list.return_value = mock_settlements
        mock_db.settlements.find.return_value = mock_cursor

        async def mock_user_find_one(query):
            user_id = str(query["_id"])
            return mock_users.get(user_id)

        mock_db.users.find_one = AsyncMock(side_effect=mock_user_find_one)

        result = await expense_service.calculate_optimized_settlements(
            group_id, "normal"
        )

        # Should result in optimized settlements. The normal algorithm may produce duplicates
        # but should calculate the correct net amount
        assert len(result) >= 1

        # Find the settlement where Bob pays Alice
        bob_to_alice_settlements = [
            s for s in result if s.fromUserName == "Bob" and s.toUserName == "Alice"
        ]
        assert len(bob_to_alice_settlements) >= 1

        # Verify the amount is correct (100 - 30 = 70)
        settlement = bob_to_alice_settlements[0]
        assert settlement.amount == 70.0
        assert settlement.fromUserId == str(user_b_id)
        assert settlement.toUserId == str(user_a_id)


@pytest.mark.asyncio
async def test_update_expense_success(expense_service, mock_expense_data):
    """Test successful expense update"""
    from app.expenses.schemas import ExpenseUpdateRequest

    update_request = ExpenseUpdateRequest(description="Updated Dinner", amount=120.0)

    updated_expense_data = mock_expense_data.copy()
    updated_expense_data["description"] = "Updated Dinner"
    updated_expense_data["amount"] = 120.0

    with patch("app.expenses.service.mongodb") as mock_mongodb:
        mock_db = MagicMock()
        mock_mongodb.database = mock_db

        # Mock finding the expense
        mock_db.expenses.find_one = AsyncMock(
            side_effect=[mock_expense_data, updated_expense_data]
        )

        # Mock user lookup
        mock_db.users.find_one = AsyncMock(
            return_value={"_id": ObjectId("65f1a2b3c4d5e6f7a8b9c0d2"), "name": "Alice"}
        )

        # Mock update operation
        mock_update_result = MagicMock()
        mock_update_result.matched_count = 1
        mock_db.expenses.update_one = AsyncMock(return_value=mock_update_result)

        with patch.object(expense_service, "_expense_doc_to_response") as mock_response:
            mock_response.return_value = {
                "id": "test_id",
                "description": "Updated Dinner",
            }

            result = await expense_service.update_expense(
                "65f1a2b3c4d5e6f7a8b9c0d0",
                "65f1a2b3c4d5e6f7a8b9c0d1",
                update_request,
                "user_a",
            )

            assert result is not None
            mock_db.expenses.update_one.assert_called_once()


@pytest.mark.asyncio
async def test_update_expense_unauthorized(expense_service):
    """Test expense update by non-creator"""
    from app.expenses.schemas import ExpenseUpdateRequest

    update_request = ExpenseUpdateRequest(
        description="Unauthorized Update", amount=150.0
    )

    with patch("app.expenses.service.mongodb") as mock_mongodb:
        mock_db = MagicMock()
        mock_mongodb.database = mock_db

        # Mock finding no expense (user not creator)
        mock_db.expenses.find_one = AsyncMock(return_value=None)

        """with pytest.raises(ValueError, match="Expense not found or not authorized to edit"):
            await expense_service.update_expense(
                "group_id", 
                "65f1a2b3c4d5e6f7a8b9c0d1",
                update_request, 
                "unauthorized_user"
            )"""
        # Updated test
        with pytest.raises(HTTPException) as exc_info:
            await expense_service.update_expense(
                "group_id",
                "65f1a2b3c4d5e6f7a8b9c0d1",
                update_request,
                "unauthorized_user",
            )
        assert exc_info.value.status_code == 403
        assert "Not authorized" in str(exc_info.value.detail)


def test_expense_split_validation():
    """Test expense split validation with proper assertions"""
    # Valid split - should not raise exception
    splits = [
        ExpenseSplit(userId="user_a", amount=50.0),
        ExpenseSplit(userId="user_b", amount=50.0),
    ]

    expense_request = ExpenseCreateRequest(
        description="Test expense",
        amount=100.0,
        splits=splits,
        paidBy="user_a",  # Added required paidBy field
    )

    # Verify the expense was created successfully
    assert expense_request.amount == 100.0
    assert len(expense_request.splits) == 2
    assert sum(split.amount for split in expense_request.splits) == 100.0

    # Invalid split - should raise validation error
    with pytest.raises(
        ValueError, match="Split amounts must sum to total expense amount"
    ):
        invalid_splits = [
            ExpenseSplit(userId="user_a", amount=40.0),
            # Total 90, but expense is 100
            ExpenseSplit(userId="user_b", amount=50.0),
        ]

        ExpenseCreateRequest(
            description="Test expense",
            amount=100.0,
            splits=invalid_splits,
            paidBy="user_a",  # Added required paidBy field
        )


def test_split_types():
    """Test different split types with proper validation"""
    # Equal split
    equal_splits = [
        ExpenseSplit(userId="user_a", amount=33.33, type=SplitType.EQUAL),
        ExpenseSplit(userId="user_b", amount=33.33, type=SplitType.EQUAL),
        ExpenseSplit(userId="user_c", amount=33.34, type=SplitType.EQUAL),
    ]

    expense = ExpenseCreateRequest(
        description="Equal split expense",
        amount=100.0,
        splits=equal_splits,
        splitType=SplitType.EQUAL,
        paidBy="user_a",  # Added required paidBy field
    )

    assert expense.splitType == SplitType.EQUAL
    assert len(expense.splits) == 3
    # Verify total with floating point tolerance
    total = sum(split.amount for split in expense.splits)
    assert abs(total - 100.0) < 0.01

    # Unequal split
    unequal_splits = [
        ExpenseSplit(userId="user_a", amount=60.0, type=SplitType.UNEQUAL),
        ExpenseSplit(userId="user_b", amount=40.0, type=SplitType.UNEQUAL),
    ]

    expense = ExpenseCreateRequest(
        description="Unequal split expense",
        amount=100.0,
        splits=unequal_splits,
        splitType=SplitType.UNEQUAL,
        paidBy="user_a",  # Added required paidBy field
    )

    assert expense.splitType == SplitType.UNEQUAL
    assert expense.splits[0].amount == 60.0
    assert expense.splits[1].amount == 40.0


@pytest.mark.asyncio
async def test_get_expense_by_id_success(expense_service, mock_expense_data):
    """Test successful expense retrieval"""
    with patch("app.expenses.service.mongodb") as mock_mongodb:
        mock_db = MagicMock()
        mock_mongodb.database = mock_db

        # Mock group membership check
        mock_db.groups.find_one = AsyncMock(
            return_value={"_id": ObjectId("65f1a2b3c4d5e6f7a8b9c0d0")}
        )

        # Mock expense lookup
        mock_db.expenses.find_one = AsyncMock(return_value=mock_expense_data)

        # Mock settlements lookup
        mock_cursor = AsyncMock()
        mock_cursor.to_list.return_value = []
        mock_db.settlements.find.return_value = mock_cursor

        with patch.object(expense_service, "_expense_doc_to_response") as mock_response:
            mock_response.return_value = {
                "id": "expense_id",
                "description": "Test Dinner",
            }

            result = await expense_service.get_expense_by_id(
                "65f1a2b3c4d5e6f7a8b9c0d0", "65f1a2b3c4d5e6f7a8b9c0d1", "user_a"
            )

            assert result is not None
            mock_db.groups.find_one.assert_called_once()
            mock_db.expenses.find_one.assert_called_once()


@pytest.mark.asyncio
async def test_get_expense_by_id_not_found(expense_service):
    """Test expense retrieval when expense doesn't exist"""
    with patch("app.expenses.service.mongodb") as mock_mongodb:
        mock_db = MagicMock()
        mock_mongodb.database = mock_db

        # Mock group membership check
        mock_db.groups.find_one = AsyncMock(
            return_value={"_id": ObjectId("65f1a2b3c4d5e6f7a8b9c0d0")}
        )

        # Mock expense not found
        mock_db.expenses.find_one = AsyncMock(return_value=None)

        """ with pytest.raises(ValueError, match="Expense not found"):
            await expense_service.get_expense_by_id("65f1a2b3c4d5e6f7a8b9c0d0", "65f1a2b3c4d5e6f7a8b9c0d1", "user_a")"""
        # Updated after stricter exception handling (July 2025)
        with pytest.raises(HTTPException) as exc_info:
            await expense_service.get_expense_by_id(
                "65f1a2b3c4d5e6f7a8b9c0d0", "65f1a2b3c4d5e6f7a8b9c0d1", "user_a"
            )
        assert exc_info.value.status_code == 404
        assert "Expense not found" in exc_info.value.detail


@pytest.mark.asyncio
async def test_list_group_expenses_success(
    expense_service, mock_group_data, mock_expense_data
):
    """Test successful listing of group expenses"""
    with patch("app.expenses.service.mongodb") as mock_mongodb:
        mock_db = MagicMock()
        mock_mongodb.database = mock_db

        # Mock group membership check
        mock_db.groups.find_one = AsyncMock(return_value=mock_group_data)

        # Mock expense lookup
        mock_expense_cursor = AsyncMock()
        mock_expense_cursor.to_list.return_value = [mock_expense_data]
        mock_db.expenses.find.return_value.sort.return_value.skip.return_value.limit.return_value = (
            mock_expense_cursor
        )
        mock_db.expenses.count_documents = AsyncMock(return_value=1)

        # Mock aggregation for summary
        mock_aggregate_cursor = AsyncMock()
        mock_aggregate_cursor.to_list.return_value = [
            {"totalAmount": 100.0, "expenseCount": 1, "avgExpense": 100.0}
        ]
        mock_db.expenses.aggregate.return_value = mock_aggregate_cursor

        with patch.object(
            expense_service, "_expense_doc_to_response", new_callable=AsyncMock
        ) as mock_response:
            mock_response.return_value = {
                "id": "expense_id",
                "description": "Test Dinner",
            }

            result = await expense_service.list_group_expenses(
                "65f1a2b3c4d5e6f7a8b9c0d0", "user_a"
            )

            assert result is not None
            assert "expenses" in result
            assert len(result["expenses"]) == 1
            assert "pagination" in result
            assert result["pagination"]["total"] == 1
            assert "summary" in result
            assert result["summary"]["totalAmount"] == 100.0
            mock_db.groups.find_one.assert_called_once()
            mock_db.expenses.find.assert_called_once()
            mock_db.expenses.count_documents.assert_called_once()
            mock_db.expenses.aggregate.assert_called_once()


@pytest.mark.asyncio
async def test_list_group_expenses_empty(expense_service, mock_group_data):
    """Test listing group expenses when there are none"""
    with patch("app.expenses.service.mongodb") as mock_mongodb:
        mock_db = MagicMock()
        mock_mongodb.database = mock_db

        mock_db.groups.find_one = AsyncMock(return_value=mock_group_data)

        mock_expense_cursor = AsyncMock()
        mock_expense_cursor.to_list.return_value = []  # No expenses
        mock_db.expenses.find.return_value.sort.return_value.skip.return_value.limit.return_value = (
            mock_expense_cursor
        )
        mock_db.expenses.count_documents = AsyncMock(return_value=0)

        mock_aggregate_cursor = AsyncMock()
        mock_aggregate_cursor.to_list.return_value = []  # No summary
        mock_db.expenses.aggregate.return_value = mock_aggregate_cursor

        result = await expense_service.list_group_expenses(
            "65f1a2b3c4d5e6f7a8b9c0d0", "user_a"
        )

        assert result is not None
        assert len(result["expenses"]) == 0
        assert result["pagination"]["total"] == 0
        assert result["summary"]["totalAmount"] == 0


@pytest.mark.asyncio
async def test_list_group_expenses_pagination(
    expense_service, mock_group_data, mock_expense_data
):
    """Test pagination for listing group expenses"""
    with patch("app.expenses.service.mongodb") as mock_mongodb:
        mock_db = MagicMock()
        mock_mongodb.database = mock_db

        mock_db.groups.find_one = AsyncMock(return_value=mock_group_data)

        # Simulate 5 expenses, limit 2, page 2
        expenses_page_2 = [
            mock_expense_data,
            mock_expense_data,
        ]  # Dummy data for page 2

        mock_expense_cursor = AsyncMock()
        mock_expense_cursor.to_list.return_value = expenses_page_2
        mock_db.expenses.find.return_value.sort.return_value.skip.return_value.limit.return_value = (
            mock_expense_cursor
        )
        mock_db.expenses.count_documents = AsyncMock(return_value=5)  # Total 5 expenses

        mock_aggregate_cursor = AsyncMock()
        mock_aggregate_cursor.to_list.return_value = [
            {"totalAmount": 200.0, "expenseCount": 2, "avgExpense": 100.0}
        ]
        mock_db.expenses.aggregate.return_value = mock_aggregate_cursor

        with patch.object(
            expense_service, "_expense_doc_to_response", new_callable=AsyncMock
        ) as mock_response:
            # Each call to _expense_doc_to_response will return a unique dict to simulate different expenses
            mock_response.side_effect = [
                {"id": "expense_1", "description": "Dinner 1"},
                {"id": "expense_2", "description": "Dinner 2"},
            ]

            result = await expense_service.list_group_expenses(
                "65f1a2b3c4d5e6f7a8b9c0d0", "user_a", page=2, limit=2
            )

            assert len(result["expenses"]) == 2
            assert result["pagination"]["page"] == 2
            assert result["pagination"]["limit"] == 2
            assert result["pagination"]["total"] == 5
            assert result["pagination"]["totalPages"] == 3  # (5 + 2 - 1) // 2
            assert result["pagination"]["hasNext"] is True
            assert result["pagination"]["hasPrev"] is True
            # Check skip value: (page - 1) * limit = (2 - 1) * 2 = 2
            mock_db.expenses.find.return_value.sort.return_value.skip.assert_called_with(
                2
            )
            mock_db.expenses.find.return_value.sort.return_value.skip.return_value.limit.assert_called_with(
                2
            )


@pytest.mark.asyncio
async def test_list_group_expenses_filters(
    expense_service, mock_group_data, mock_expense_data
):
    """Test filters (date, tags) for listing group expenses"""
    from_date = datetime(2023, 1, 1, tzinfo=timezone.utc)
    to_date = datetime(2023, 1, 31, tzinfo=timezone.utc)
    tags = ["food", "urgent"]

    with patch("app.expenses.service.mongodb") as mock_mongodb:
        mock_db = MagicMock()
        mock_mongodb.database = mock_db

        mock_db.groups.find_one = AsyncMock(return_value=mock_group_data)

        mock_expense_cursor = AsyncMock()
        mock_expense_cursor.to_list.return_value = [mock_expense_data]
        mock_db.expenses.find.return_value.sort.return_value.skip.return_value.limit.return_value = (
            mock_expense_cursor
        )
        mock_db.expenses.count_documents = AsyncMock(return_value=1)

        mock_aggregate_cursor = AsyncMock()
        mock_aggregate_cursor.to_list.return_value = [
            {"totalAmount": 100.0, "expenseCount": 1, "avgExpense": 100.0}
        ]
        mock_db.expenses.aggregate.return_value = mock_aggregate_cursor

        with patch.object(
            expense_service, "_expense_doc_to_response", new_callable=AsyncMock
        ) as mock_response:
            mock_response.return_value = {
                "id": "expense_id",
                "description": "Filtered Dinner",
            }

            await expense_service.list_group_expenses(
                "65f1a2b3c4d5e6f7a8b9c0d0",
                "user_a",
                from_date=from_date,
                to_date=to_date,
                tags=tags,
            )

            # Check if find query was called with correct filters
            call_args = mock_db.expenses.find.call_args[0][0]
            assert "createdAt" in call_args
            assert call_args["createdAt"]["$gte"] == from_date
            assert call_args["createdAt"]["$lte"] == to_date
            assert "tags" in call_args
            assert call_args["tags"]["$in"] == tags

            # Check if aggregate query was also called with correct filters
            aggregate_call_args = mock_db.expenses.aggregate.call_args[0][0]
            assert "$match" in aggregate_call_args[0]
            match_query = aggregate_call_args[0]["$match"]
            assert "createdAt" in match_query
            assert match_query["createdAt"]["$gte"] == from_date
            assert match_query["createdAt"]["$lte"] == to_date
            assert "tags" in match_query
            assert match_query["tags"]["$in"] == tags


@pytest.mark.asyncio
async def test_list_group_expenses_group_not_found(expense_service):
    """Test listing expenses when group is not found or user not member"""
    valid_but_non_existent_group_id = str(ObjectId())
    with patch("app.expenses.service.mongodb") as mock_mongodb:
        mock_db = MagicMock()
        mock_mongodb.database = mock_db
        mock_db.groups.find_one = AsyncMock(return_value=None)  # Group not found

        with pytest.raises(ValueError, match="Group not found or user not a member"):
            await expense_service.list_group_expenses(
                valid_but_non_existent_group_id, "user_a"
            )


@pytest.mark.asyncio
async def test_delete_expense_success(expense_service, mock_expense_data):
    """Test successful deletion of an expense"""
    group_id = mock_expense_data["groupId"]
    expense_id = str(mock_expense_data["_id"])
    user_id = mock_expense_data["createdBy"]

    with patch("app.expenses.service.mongodb") as mock_mongodb:
        mock_db = MagicMock()
        mock_mongodb.database = mock_db

        # Mock finding the expense to be deleted
        mock_db.expenses.find_one = AsyncMock(return_value=mock_expense_data)

        # Mock successful deletion of expense
        mock_delete_expense_result = MagicMock()
        mock_delete_expense_result.deleted_count = 1
        mock_db.expenses.delete_one = AsyncMock(return_value=mock_delete_expense_result)

        # Mock successful deletion of related settlements
        mock_delete_settlements_result = MagicMock()
        mock_delete_settlements_result.deleted_count = 2  # Assume 2 settlements deleted
        mock_db.settlements.delete_many = AsyncMock(
            return_value=mock_delete_settlements_result
        )

        result = await expense_service.delete_expense(group_id, expense_id, user_id)

        assert result is True
        mock_db.expenses.find_one.assert_called_once_with(
            {"_id": ObjectId(expense_id), "groupId": group_id, "createdBy": user_id}
        )
        mock_db.settlements.delete_many.assert_called_once_with(
            {"expenseId": expense_id}
        )
        mock_db.expenses.delete_one.assert_called_once_with(
            {"_id": ObjectId(expense_id)}
        )


@pytest.mark.asyncio
async def test_delete_expense_not_found(expense_service):
    """Test deleting an expense that is not found or user not authorized"""
    group_id = str(ObjectId())  # Valid format
    expense_id = str(ObjectId())  # Valid format
    user_id = "user_id_test"  # This is used for matching createdBy, can be string

    with patch("app.expenses.service.mongodb") as mock_mongodb:
        mock_db = MagicMock()
        mock_mongodb.database = mock_db

        # Mock finding no expense
        mock_db.expenses.find_one = AsyncMock(return_value=None)

        mock_db.settlements.delete_many = (
            AsyncMock()
        )  # Should not be called if expense not found
        mock_db.expenses.delete_one = AsyncMock()  # Should not be called

        """with pytest.raises(ValueError, match="Expense not found or not authorized to delete"):
            await expense_service.delete_expense(group_id, expense_id, user_id)

        mock_db.settlements.delete_many.assert_not_called()
        mock_db.expenses.delete_one.assert_not_called()"""
        # Updated after stricter exception handling (July 2025)
        with pytest.raises(HTTPException) as exc_info:
            await expense_service.delete_expense(group_id, expense_id, user_id)

        assert exc_info.value.status_code == 403
        assert (
            exc_info.value.detail
            == "Not authorized to delete this expense or it does not exist"
        )

        mock_db.settlements.delete_many.assert_not_called()
        mock_db.expenses.delete_one.assert_not_called()


@pytest.mark.asyncio
async def test_delete_expense_failed_deletion(expense_service, mock_expense_data):
    """Test scenario where expense deletion from DB fails"""
    group_id = mock_expense_data["groupId"]
    expense_id = str(mock_expense_data["_id"])
    user_id = mock_expense_data["createdBy"]

    with patch("app.expenses.service.mongodb") as mock_mongodb:
        mock_db = MagicMock()
        mock_mongodb.database = mock_db

        mock_db.expenses.find_one = AsyncMock(return_value=mock_expense_data)

        mock_delete_expense_result = MagicMock()
        mock_delete_expense_result.deleted_count = 0  # Simulate DB deletion failure
        mock_db.expenses.delete_one = AsyncMock(return_value=mock_delete_expense_result)

        mock_db.settlements.delete_many = AsyncMock()

        result = await expense_service.delete_expense(group_id, expense_id, user_id)

        assert result is False  # Deletion failed
        # Settlements should still be attempted to be deleted
        mock_db.settlements.delete_many.assert_called_once()
        mock_db.expenses.delete_one.assert_called_once()


@pytest.mark.asyncio
async def test_create_manual_settlement_success(expense_service, mock_group_data):
    """Test successful creation of a manual settlement"""
    from app.expenses.schemas import SettlementCreateRequest

    group_id = str(mock_group_data["_id"])
    user_id = "user_a"  # User creating the settlement
    payer_id_obj = ObjectId()
    payee_id_obj = ObjectId()
    payer_id_str = str(payer_id_obj)
    payee_id_str = str(payee_id_obj)

    settlement_request = SettlementCreateRequest(
        payer_id=payer_id_str,
        payee_id=payee_id_str,
        amount=50.0,
        description="Manual payback",
    )

    mock_user_b_data = {"_id": payer_id_obj, "name": "User B"}
    mock_user_c_data = {"_id": payee_id_obj, "name": "User C"}

    with patch("app.expenses.service.mongodb") as mock_mongodb:
        mock_db = MagicMock()
        mock_mongodb.database = mock_db

        # Mock group membership check
        mock_db.groups.find_one = AsyncMock(return_value=mock_group_data)

        # Mock user lookups for names
        # This function will be the side_effect for mock_db.users.find
        # It needs to be a sync function that returns a cursor mock.
        def sync_mock_user_find_cursor_factory(query, *args, **kwargs):
            ids_in_query_objs = query["_id"]["$in"]
            users_to_return = []
            if payer_id_obj in ids_in_query_objs:
                users_to_return.append(mock_user_b_data)
            if payee_id_obj in ids_in_query_objs:
                users_to_return.append(mock_user_c_data)

            cursor_mock = AsyncMock()  # This is the cursor mock
            cursor_mock.to_list = AsyncMock(
                return_value=users_to_return
            )  # .to_list() is an async method on the cursor
            return cursor_mock  # The factory returns the configured cursor mock

        # mock_db.users.find is a MagicMock because .find() is a synchronous method.
        # Its side_effect (our factory) is called when mock_db.users.find() is invoked.
        mock_db.users.find = MagicMock(side_effect=sync_mock_user_find_cursor_factory)

        # Mock settlement insertion
        mock_db.settlements.insert_one = AsyncMock()

        result = await expense_service.create_manual_settlement(
            group_id, settlement_request, user_id
        )

        assert result is not None
        assert result.groupId == group_id
        assert result.payerId == payer_id_str
        assert result.payeeId == payee_id_str
        assert result.amount == 50.0
        assert result.description == "Manual payback"
        assert result.status == "completed"  # Manual settlements are marked completed
        assert result.payerName == "User B"
        assert result.payeeName == "User C"

        # groups.find_one is called (exact query format may vary due to $or support)
        mock_db.groups.find_one.assert_called_once()
        mock_db.users.find.assert_called_once()
        mock_db.settlements.insert_one.assert_called_once()
        inserted_doc = mock_db.settlements.insert_one.call_args[0][0]
        # Manual settlements have no expenseId
        assert inserted_doc["expenseId"] is None


@pytest.mark.asyncio
async def test_create_manual_settlement_group_not_found(expense_service):
    """Test creating manual settlement when group is not found or user not member"""
    from app.expenses.schemas import SettlementCreateRequest

    group_id = str(ObjectId())  # Valid format
    user_id = "user_a"
    settlement_request = SettlementCreateRequest(
        payer_id=str(ObjectId()),  # Valid format
        payee_id=str(ObjectId()),  # Valid format
        amount=50.0,
    )

    with patch("app.expenses.service.mongodb") as mock_mongodb:
        mock_db = MagicMock()
        mock_mongodb.database = mock_db
        mock_db.groups.find_one = AsyncMock(return_value=None)  # Group not found

        """with pytest.raises(ValueError, match="Group not found or user not a member"):
            await expense_service.create_manual_settlement(group_id, settlement_request, user_id)

        mock_db.settlements.insert_one.assert_not_called()"""
        # Updated after stricter exception handling (July 2025)
        with pytest.raises(HTTPException) as exc_info:
            await expense_service.create_manual_settlement(
                group_id, settlement_request, user_id
            )

        assert exc_info.value.status_code == 403
        assert exc_info.value.detail == "Group not found or user not a member"

        mock_db.settlements.insert_one.assert_not_called()


@pytest.mark.asyncio
async def test_get_group_settlements_success(expense_service, mock_group_data):
    """Test successful listing of group settlements"""
    group_id = str(mock_group_data["_id"])
    user_id = "user_a"

    mock_settlement_doc = {
        "_id": ObjectId(),
        "groupId": group_id,
        "payerId": "user_b",
        "payeeId": "user_c",
        "amount": 50.0,
        "status": "pending",
        "description": "A settlement",
        "createdAt": datetime.now(timezone.utc),
        "payerName": "User B",
        "payeeName": "User C",
    }

    with patch("app.expenses.service.mongodb") as mock_mongodb:
        mock_db = MagicMock()
        mock_mongodb.database = mock_db

        mock_db.groups.find_one = AsyncMock(return_value=mock_group_data)

        mock_settlements_cursor = AsyncMock()
        mock_settlements_cursor.to_list.return_value = [mock_settlement_doc]
        mock_db.settlements.find.return_value.sort.return_value.skip.return_value.limit.return_value = (
            mock_settlements_cursor
        )
        mock_db.settlements.count_documents = AsyncMock(return_value=1)

        result = await expense_service.get_group_settlements(group_id, user_id)

        assert result is not None
        assert "settlements" in result
        assert len(result["settlements"]) == 1
        assert result["settlements"][0].amount == 50.0
        assert "total" in result
        assert result["total"] == 1
        assert "page" in result
        assert "limit" in result

        mock_db.groups.find_one.assert_called_once()
        mock_db.settlements.find.assert_called_once()
        mock_db.settlements.count_documents.assert_called_once()
        # Check default sort, skip, limit
        mock_db.settlements.find.return_value.sort.assert_called_with("createdAt", -1)
        mock_db.settlements.find.return_value.sort.return_value.skip.assert_called_with(
            0
        )  # (1-1)*50
        mock_db.settlements.find.return_value.sort.return_value.skip.return_value.limit.assert_called_with(
            50
        )


@pytest.mark.asyncio
async def test_get_group_settlements_with_filters_and_pagination(
    expense_service, mock_group_data
):
    """Test listing group settlements with status filter and pagination"""
    group_id = str(mock_group_data["_id"])
    user_id = "user_a"
    status_filter = "completed"
    page = 2
    limit = 10

    mock_settlement_doc = {
        "_id": ObjectId(),
        "groupId": group_id,
        "payerId": "user_b",
        "payeeId": "user_c",
        "amount": 50.0,
        "status": "completed",
        "description": "A settlement",
        "createdAt": datetime.now(timezone.utc),
        "payerName": "User B",
        "payeeName": "User C",
    }

    with patch("app.expenses.service.mongodb") as mock_mongodb:
        mock_db = MagicMock()
        mock_mongodb.database = mock_db

        mock_db.groups.find_one = AsyncMock(return_value=mock_group_data)

        mock_settlements_cursor = AsyncMock()
        mock_settlements_cursor.to_list.return_value = [
            mock_settlement_doc
        ] * 5  # Simulate 5 settlements for this page
        mock_db.settlements.find.return_value.sort.return_value.skip.return_value.limit.return_value = (
            mock_settlements_cursor
        )
        mock_db.settlements.count_documents = AsyncMock(
            return_value=15
        )  # Total 15 settlements matching filter

        result = await expense_service.get_group_settlements(
            group_id, user_id, status_filter=status_filter, page=page, limit=limit
        )

        assert len(result["settlements"]) == 5
        assert result["total"] == 15
        assert result["page"] == page
        assert result["limit"] == limit

        # Verify find query
        find_call_args = mock_db.settlements.find.call_args[0][0]
        assert find_call_args["groupId"] == group_id
        assert find_call_args["status"] == status_filter

        # Verify count_documents query
        count_call_args = mock_db.settlements.count_documents.call_args[0][0]
        assert count_call_args["groupId"] == group_id
        assert count_call_args["status"] == status_filter

        # Verify skip and limit
        mock_db.settlements.find.return_value.sort.return_value.skip.assert_called_with(
            (page - 1) * limit
        )
        mock_db.settlements.find.return_value.sort.return_value.skip.return_value.limit.assert_called_with(
            limit
        )


@pytest.mark.asyncio
async def test_get_group_settlements_group_not_found(expense_service):
    """Test listing settlements when group not found or user not member"""
    group_id = str(ObjectId())  # Valid format
    user_id = "user_a"

    with patch("app.expenses.service.mongodb") as mock_mongodb:
        mock_db = MagicMock()
        mock_mongodb.database = mock_db
        mock_db.groups.find_one = AsyncMock(return_value=None)  # Group not found

        """with pytest.raises(ValueError, match="Group not found or user not a member"):
            await expense_service.get_group_settlements(group_id, user_id)"""
        # Updated after stricter exception handling (July 2025)
        with pytest.raises(HTTPException) as exc_info:
            await expense_service.get_group_settlements(group_id, user_id)

        assert exc_info.value.status_code == 403
        assert exc_info.value.detail == "Group not found or user not a member"

        mock_db.settlements.find.assert_not_called()
        mock_db.settlements.count_documents.assert_not_called()


@pytest.mark.asyncio
async def test_get_settlement_by_id_success(expense_service, mock_group_data):
    """Test successful retrieval of a settlement by ID"""
    group_id = str(mock_group_data["_id"])
    user_id = "user_a"
    settlement_id_obj = ObjectId()
    settlement_id_str = str(settlement_id_obj)

    mock_settlement_doc = {
        "_id": settlement_id_obj,
        "groupId": group_id,
        "payerId": "user_b",
        "payeeId": "user_c",
        "amount": 75.0,
        "status": "pending",
        "description": "Specific settlement",
        "createdAt": datetime.now(timezone.utc),
        "payerName": "User B",
        "payeeName": "User C",
    }

    with patch("app.expenses.service.mongodb") as mock_mongodb:
        mock_db = MagicMock()
        mock_mongodb.database = mock_db

        mock_db.groups.find_one = AsyncMock(return_value=mock_group_data)
        mock_db.settlements.find_one = AsyncMock(return_value=mock_settlement_doc)

        result = await expense_service.get_settlement_by_id(
            group_id, settlement_id_str, user_id
        )

        assert result is not None
        assert result.id == settlement_id_str  # Changed from _id to id
        assert result.amount == 75.0
        assert result.description == "Specific settlement"

        # groups.find_one is called (exact query format may vary due to $or support)
        mock_db.groups.find_one.assert_called_once()
        mock_db.settlements.find_one.assert_called_once_with(
            {"_id": ObjectId(settlement_id_str), "groupId": group_id}
        )


@pytest.mark.asyncio
async def test_get_settlement_by_id_not_found(expense_service, mock_group_data):
    """Test retrieving a settlement by ID when it's not found"""
    group_id = str(mock_group_data["_id"])
    user_id = "user_a"
    settlement_id_str = str(ObjectId())  # Non-existent ID

    with patch("app.expenses.service.mongodb") as mock_mongodb:
        mock_db = MagicMock()
        mock_mongodb.database = mock_db

        mock_db.groups.find_one = AsyncMock(return_value=mock_group_data)
        mock_db.settlements.find_one = AsyncMock(
            return_value=None
        )  # Settlement not found

        """with pytest.raises(ValueError, match="Settlement not found"):
            await expense_service.get_settlement_by_id(group_id, settlement_id_str, user_id)"""
        # Updated after stricter exception handling (July 2025)
        with pytest.raises(HTTPException) as exc_info:
            await expense_service.get_settlement_by_id(
                group_id, settlement_id_str, user_id
            )

        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "Settlement not found"


@pytest.mark.asyncio
async def test_get_settlement_by_id_group_access_denied(expense_service):
    """Test retrieving settlement when user not member of the group"""
    group_id = str(ObjectId())
    user_id = "user_a"
    settlement_id_str = str(ObjectId())

    with patch("app.expenses.service.mongodb") as mock_mongodb:
        mock_db = MagicMock()
        mock_mongodb.database = mock_db

        mock_db.groups.find_one = AsyncMock(
            return_value=None
        )  # User not in group / group doesn't exist

        """with pytest.raises(ValueError, match="Group not found or user not a member"):
            await expense_service.get_settlement_by_id(group_id, settlement_id_str, user_id)"""
        # Updated after stricter exception handling (July 2025)
        with pytest.raises(HTTPException) as exc_info:
            await expense_service.get_settlement_by_id(
                group_id, settlement_id_str, user_id
            )

        assert exc_info.value.status_code == 403
        assert exc_info.value.detail == "Group not found or user not a member"

        mock_db.settlements.find_one.assert_not_called()


@pytest.mark.asyncio
async def test_update_settlement_status_success(expense_service):
    """Test successful update of settlement status"""
    from app.expenses.schemas import SettlementStatus

    group_id = str(ObjectId())
    settlement_id_obj = ObjectId()
    settlement_id_str = str(settlement_id_obj)
    new_status = SettlementStatus.COMPLETED
    paid_at_time = datetime.now(timezone.utc)

    # Original settlement doc (before update)
    original_settlement_doc = {
        "_id": settlement_id_obj,
        "groupId": group_id,
        "status": "pending",
        "payerId": "p1",
        "payeeId": "p2",
        "amount": 10,
        "payerName": "P1",
        "payeeName": "P2",
        "createdAt": datetime.now(timezone.utc) - timedelta(days=1),
    }
    # Settlement doc after update
    updated_settlement_doc = original_settlement_doc.copy()
    updated_settlement_doc["status"] = new_status.value
    updated_settlement_doc["paidAt"] = paid_at_time
    updated_settlement_doc["updatedAt"] = datetime.now(
        timezone.utc
    )  # Will be set by the method

    with patch("app.expenses.service.mongodb") as mock_mongodb:
        mock_db = MagicMock()
        mock_mongodb.database = mock_db

        mock_update_result = MagicMock()
        mock_update_result.matched_count = 1
        mock_db.settlements.update_one = AsyncMock(return_value=mock_update_result)

        # find_one is called to retrieve the updated document
        mock_db.settlements.find_one = AsyncMock(return_value=updated_settlement_doc)

        result = await expense_service.update_settlement_status(
            group_id, settlement_id_str, new_status, paid_at=paid_at_time
        )

        assert result is not None
        assert result.id == settlement_id_str  # Changed from _id to id
        assert result.status == new_status.value
        assert result.paidAt == paid_at_time

        mock_db.settlements.update_one.assert_called_once()
        update_call_args = mock_db.settlements.update_one.call_args[0]
        assert update_call_args[0] == {
            "_id": settlement_id_obj,
            "groupId": group_id,
        }  # Filter query
        assert "$set" in update_call_args[1]
        set_doc = update_call_args[1]["$set"]
        assert set_doc["status"] == new_status.value
        assert set_doc["paidAt"] == paid_at_time
        assert "updatedAt" in set_doc

        mock_db.settlements.find_one.assert_called_once_with({"_id": settlement_id_obj})


@pytest.mark.asyncio
async def test_update_settlement_status_not_found(expense_service):
    """Test updating status for a non-existent settlement"""
    from app.expenses.schemas import SettlementStatus

    group_id = str(ObjectId())
    settlement_id_str = str(ObjectId())  # Non-existent ID
    new_status = SettlementStatus.CANCELLED

    with patch("app.expenses.service.mongodb") as mock_mongodb:
        mock_db = MagicMock()
        mock_mongodb.database = mock_db

        mock_update_result = MagicMock()
        mock_update_result.matched_count = 0  # Simulate settlement not found
        mock_db.settlements.update_one = AsyncMock(return_value=mock_update_result)

        mock_db.settlements.find_one = AsyncMock(return_value=None)

        """with pytest.raises(ValueError, match="Settlement not found"):
            await expense_service.update_settlement_status(
                group_id, settlement_id_str, new_status
            )"""
        # Updated after stricter exception handling (July 2025)
        with pytest.raises(HTTPException) as exc_info:
            await expense_service.update_settlement_status(
                group_id, settlement_id_str, new_status
            )

        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "Settlement not found"

        # Should not be called if update fails
        mock_db.settlements.find_one.assert_not_called()


@pytest.mark.asyncio
async def test_delete_settlement_success(expense_service, mock_group_data):
    """Test successful deletion of a settlement"""
    group_id = str(mock_group_data["_id"])
    user_id = "user_a"  # User performing the deletion
    settlement_id_obj = ObjectId()
    settlement_id_str = str(settlement_id_obj)

    with patch("app.expenses.service.mongodb") as mock_mongodb:
        mock_db = MagicMock()
        mock_mongodb.database = mock_db

        # Mock group membership check
        mock_db.groups.find_one = AsyncMock(return_value=mock_group_data)

        # Mock successful deletion
        mock_delete_result = MagicMock()
        mock_delete_result.deleted_count = 1
        mock_db.settlements.delete_one = AsyncMock(return_value=mock_delete_result)

        result = await expense_service.delete_settlement(
            group_id, settlement_id_str, user_id
        )

        assert result is True
        mock_db.groups.find_one.assert_called_once_with(
            {"_id": ObjectId(group_id), "members.userId": user_id}
        )
        mock_db.settlements.delete_one.assert_called_once_with(
            {"_id": ObjectId(settlement_id_str), "groupId": group_id}
        )


@pytest.mark.asyncio
async def test_delete_settlement_not_found(expense_service, mock_group_data):
    """Test deleting a settlement that is not found"""
    group_id = str(mock_group_data["_id"])
    user_id = "user_a"
    settlement_id_str = str(ObjectId())  # Non-existent ID

    with patch("app.expenses.service.mongodb") as mock_mongodb:
        mock_db = MagicMock()
        mock_mongodb.database = mock_db

        mock_db.groups.find_one = AsyncMock(return_value=mock_group_data)

        mock_delete_result = MagicMock()
        mock_delete_result.deleted_count = 0  # Simulate not found
        mock_db.settlements.delete_one = AsyncMock(return_value=mock_delete_result)

        result = await expense_service.delete_settlement(
            group_id, settlement_id_str, user_id
        )

        assert result is False


@pytest.mark.asyncio
async def test_delete_settlement_group_access_denied(expense_service):
    """Test deleting settlement when user not member of the group"""
    group_id = str(ObjectId())
    user_id = "user_a"
    settlement_id_str = str(ObjectId())

    with patch("app.expenses.service.mongodb") as mock_mongodb:
        mock_db = MagicMock()
        mock_mongodb.database = mock_db

        mock_db.groups.find_one = AsyncMock(return_value=None)  # User not in group

        """with pytest.raises(ValueError, match="Group not found or user not a member"):
            await expense_service.delete_settlement(group_id, settlement_id_str, user_id)"""
        # Updated after stricter exception handling (July 2025)
        with pytest.raises(HTTPException) as exc_info:
            await expense_service.delete_settlement(
                group_id, settlement_id_str, user_id
            )

        assert exc_info.value.status_code == 403
        assert exc_info.value.detail == "Group not found or user not a member"

        mock_db.settlements.delete_one.assert_not_called()


@pytest.mark.asyncio
async def test_get_user_balance_in_group_success(expense_service, mock_group_data):
    """Test successful retrieval of a user's balance in a group"""
    group_id = str(mock_group_data["_id"])
    target_user_id_obj = ObjectId()
    target_user_id_str = str(target_user_id_obj)
    current_user_id = "user_a"  # User making the request

    mock_target_user_doc = {"_id": target_user_id_obj, "name": "User B Target"}

    # Mock settlements involving target_user_id_str
    # User B paid 100 for User A (User A owes User B 100)
    # User C paid 50 for User B (User B owes User C 50)
    # Net for User B: Paid 100, Owed 50. Net Balance = 50 (User B is owed 50 overall)
    mock_settlements_aggregate = [{"_id": None, "totalPaid": 100.0, "totalOwed": 50.0}]
    mock_pending_settlements_docs = [  # User B is payee, i.e. is owed
        {
            "_id": ObjectId(),
            "groupId": group_id,
            "payerId": "user_a",
            "payeeId": target_user_id_str,
            "amount": 100.0,
            "status": "pending",
            "description": "Owed to B",
            "createdAt": datetime.now(timezone.utc),
            "payerName": "User A",
            "payeeName": "User B Target",
        }
    ]
    mock_recent_expenses_docs = [  # Expense created by B, B also has a split
        {
            "_id": ObjectId(),
            "groupId": group_id,
            "createdBy": target_user_id_str,
            "description": "Lunch by B",
            "amount": 150.0,
            "splits": [
                {"userId": target_user_id_str, "amount": 75.0},
                {"userId": "user_c", "amount": 75.0},
            ],
            "createdAt": datetime.now(timezone.utc),
        }
    ]

    with patch("app.expenses.service.mongodb") as mock_mongodb:
        mock_db = MagicMock()
        mock_mongodb.database = mock_db

        # Mock group membership check for current_user_id
        mock_db.groups.find_one = AsyncMock(return_value=mock_group_data)
        # Mock target user lookup
        mock_db.users.find_one = AsyncMock(return_value=mock_target_user_doc)

        # Mock settlements aggregation
        mock_aggregate_cursor = AsyncMock()
        mock_aggregate_cursor.to_list.return_value = mock_settlements_aggregate
        mock_db.settlements.aggregate.return_value = mock_aggregate_cursor

        # Mock pending settlements find
        mock_pending_cursor = AsyncMock()
        mock_pending_cursor.to_list.return_value = mock_pending_settlements_docs
        mock_db.settlements.find.return_value = (
            mock_pending_cursor  # This is the first .find() call
        )

        # Mock recent expenses find
        mock_expenses_cursor = AsyncMock()
        mock_expenses_cursor.to_list.return_value = mock_recent_expenses_docs
        # Ensure the second .find() call (for expenses) is correctly patched
        mock_db.expenses.find.return_value.sort.return_value.limit.return_value = (
            mock_expenses_cursor
        )

        result = await expense_service.get_user_balance_in_group(
            group_id, target_user_id_str, current_user_id
        )

        assert result is not None
        assert result["userId"] == target_user_id_str
        assert result["userName"] == "User B Target"
        assert result["totalPaid"] == 100.0
        assert result["totalOwed"] == 50.0
        assert result["netBalance"] == 50.0  # 100 - 50
        assert (
            result["owesYou"]
            is True
            # Net balance is positive, so target_user_id is owed money (by others in general)
        )

        assert len(result["pendingSettlements"]) == 1
        assert result["pendingSettlements"][0].amount == 100.0

        assert len(result["recentExpenses"]) == 1
        assert result["recentExpenses"][0]["description"] == "Lunch by B"
        assert result["recentExpenses"][0]["userShare"] == 75.0

        mock_db.groups.find_one.assert_called_once_with(
            {"_id": ObjectId(group_id), "members.userId": current_user_id}
        )
        mock_db.users.find_one.assert_called_once_with({"_id": target_user_id_obj})
        mock_db.settlements.aggregate.assert_called_once()

        # Check the two find calls to settlements and expenses collections
        settlements_find_call_args = mock_db.settlements.find.call_args[0][0]
        assert (
            settlements_find_call_args["payeeId"] == target_user_id_str
        )  # For pending settlements

        expenses_find_call_args = mock_db.expenses.find.call_args[0][0]
        assert "$or" in expenses_find_call_args  # For recent expenses


@pytest.mark.asyncio
async def test_get_user_balance_in_group_access_denied(expense_service):
    """Test get user balance when current user not in group"""
    group_id = str(ObjectId())
    # Use a valid ObjectId string for target
    target_user_id_str = str(ObjectId())
    current_user_id = "user_x"  # Not in group

    with patch("app.expenses.service.mongodb") as mock_mongodb:
        mock_db = MagicMock()
        mock_mongodb.database = mock_db
        mock_db.groups.find_one = AsyncMock(
            return_value=None
        )  # Current user not member

        """with pytest.raises(ValueError, match="Group not found or user not a member"):
            await expense_service.get_user_balance_in_group(group_id, target_user_id_str, current_user_id)"""
        # Updated after stricter exception handling (July 2025)
        with pytest.raises(HTTPException) as exc_info:
            await expense_service.get_user_balance_in_group(
                group_id, target_user_id_str, current_user_id
            )

        assert exc_info.value.status_code == 403
        assert exc_info.value.detail == "Group not found or user not a member"

        mock_db.users.find_one.assert_not_called()
        mock_db.settlements.aggregate.assert_not_called()
        mock_db.settlements.find.assert_not_called()
        mock_db.expenses.find.assert_not_called()


@pytest.mark.asyncio
async def test_get_friends_balance_summary_success(expense_service):
    """Test successful retrieval of friends balance summary"""
    user_id_obj = ObjectId()
    friend1_id_obj = ObjectId()
    friend2_id_obj = ObjectId()
    user_id_str = str(user_id_obj)
    friend1_id_str = str(friend1_id_obj)
    friend2_id_str = str(friend2_id_obj)

    # Remains as string, used for direct comparison in mock
    group1_id = str(ObjectId())
    group2_id = str(ObjectId())

    mock_user_main_doc = {"_id": user_id_obj, "name": "Main User"}
    mock_friend1_doc = {"_id": friend1_id_obj, "name": "Friend One"}
    mock_friend2_doc = {"_id": friend2_id_obj, "name": "Friend Two"}

    mock_groups_data = [
        {
            "_id": ObjectId(group1_id),
            "name": "Group Alpha",
            "members": [{"userId": user_id_str}, {"userId": friend1_id_str}],
        },
        {
            "_id": ObjectId(group2_id),
            "name": "Group Beta",
            "members": [
                {"userId": user_id_str},
                {"userId": friend1_id_str},
                {"userId": friend2_id_str},
            ],
        },
    ]

    # Mocking the OPTIMIZED settlement aggregation
    # The new optimized version makes ONE aggregation call that returns all friends' balances
    # Friend 1:
    #   Group Alpha: Main owes Friend1 50 (balance: -50 for Main)
    #   Group Beta: Friend1 owes Main 30 (balance: +30 for Main)
    #   Total for Friend1: -50 + 30 = -20 (Main owes Friend1 20)
    # Friend 2:
    #   Group Beta: Main owes Friend2 70 (balance: -70 for Main)
    #   Total for Friend2: -70 (Main owes Friend2 70)

    def sync_mock_settlements_aggregate_cursor_factory(
        _pipeline: Any, *_args: Any, **_kwargs: Any
    ) -> AsyncMock:
        # The optimized version returns aggregated results for all friends in one go
        mock_agg_cursor = AsyncMock()
        mock_agg_cursor.to_list.return_value = [
            {
                "_id": friend1_id_str,  # Friend 1
                "totalBalance": -20.0,  # Main owes Friend1 20 (net: -50 from G1, +30 from G2)
                "groups": [
                    {
                        "groupId": group1_id,
                        "balance": -50.0,
                    },  # Main owes 50 in Group Alpha
                    {
                        "groupId": group2_id,
                        "balance": 30.0,
                    },  # Friend1 owes 30 in Group Beta
                ],
            },
            {
                "_id": friend2_id_str,  # Friend 2
                "totalBalance": -70.0,  # Main owes Friend2 70
                "groups": [
                    {
                        "groupId": group2_id,
                        "balance": -70.0,
                    },  # Main owes 70 in Group Beta
                ],
            },
        ]
        return mock_agg_cursor

    with patch("app.expenses.service.mongodb") as mock_mongodb:
        mock_db = MagicMock()
        mock_mongodb.database = mock_db

        # Mock groups user belongs to
        mock_groups_cursor = AsyncMock()
        mock_groups_cursor.to_list.return_value = mock_groups_data
        mock_db.groups.find.return_value = mock_groups_cursor

        # Mock user name lookups
        # This side effect is for the users.find() call. It returns a cursor mock.
        def mock_user_find_cursor_side_effect(query, *args, **kwargs):
            ids_in_query = query["_id"][
                "$in"
            ]  # These are already ObjectIds from the service
            users_to_return = []
            if friend1_id_obj in ids_in_query:
                users_to_return.append(mock_friend1_doc)
            if friend2_id_obj in ids_in_query:
                users_to_return.append(mock_friend2_doc)

            cursor_mock = AsyncMock()
            cursor_mock.to_list = AsyncMock(return_value=users_to_return)
            return cursor_mock

        mock_db.users.find = MagicMock(side_effect=mock_user_find_cursor_side_effect)

        # Mock the optimized settlement aggregation logic
        # .aggregate() is sync, returns an async cursor.
        mock_db.settlements.aggregate = MagicMock(
            side_effect=sync_mock_settlements_aggregate_cursor_factory
        )

        result = await expense_service.get_friends_balance_summary(user_id_str)

        assert result is not None
        assert "friendsBalance" in result
        assert "summary" in result

        friends_balance = result["friendsBalance"]
        summary = result["summary"]

        assert len(friends_balance) == 2  # Friend1 and Friend2

        friend1_summary = next(
            f for f in friends_balance if f["userId"] == friend1_id_str
        )
        friend2_summary = next(
            f for f in friends_balance if f["userId"] == friend2_id_str
        )

        # Friend1: owes Main 30 (Group Beta), Main owes Friend1 50 (Group Alpha)
        # Net for Friend1: Friend1 owes Main (30 - 50) = -20. So Main is owed 20 by Friend1.
        # The service calculates from perspective of "user_id" (Main User)
        # So if friendOwes > userOwes, it means friend owes user_id.
        # Group Alpha: friendOwes (Friend1 to Main) = 0, userOwes (Main to Friend1) = 50. Balance = 0 - 50 = -50 (Main owes F1 50)
        # Group Beta: friendOwes (Friend1 to Main) = 30, userOwes (Main to Friend1) = 0. Balance = 30 - 0 = +30 (F1 owes Main 30)
        # Total for Friend1: Net Balance = -50 (from G1) + 30 (from G2) = -20. So Main User owes Friend1 20.
        assert friend1_summary["userName"] == "Friend One"
        assert (
            abs(friend1_summary["netBalance"] - (-20.0)) < 0.01
        )  # Main owes Friend1 20
        assert friend1_summary["owesYou"] is False
        assert len(friend1_summary["breakdown"]) == 2

        # Friend2: Main owes Friend2 70 (Group Beta)
        # Group Beta: friendOwes (Friend2 to Main) = 0, userOwes (Main to Friend2) = 70. Balance = 0 - 70 = -70
        # Total for Friend2: Net Balance = -70. So Main User owes Friend2 70.
        assert friend2_summary["userName"] == "Friend Two"
        assert (
            abs(friend2_summary["netBalance"] - (-70.0)) < 0.01
        )  # Main owes Friend2 70
        assert friend2_summary["owesYou"] is False
        assert len(friend2_summary["breakdown"]) == 1
        assert friend2_summary["breakdown"][0]["groupName"] == "Group Beta"
        assert abs(friend2_summary["breakdown"][0]["balance"] - (-70.0)) < 0.01

        # Summary: Main owes Friend1 20, Main owes Friend2 70.
        # totalOwedToYou = 0
        # totalYouOwe = 20 (to F1) + 70 (to F2) = 90
        assert abs(summary["totalOwedToYou"] - 0.0) < 0.01
        assert abs(summary["totalYouOwe"] - 90.0) < 0.01
        assert abs(summary["netBalance"] - (-90.0)) < 0.01
        assert summary["friendCount"] == 2
        assert summary["activeGroups"] == 2

        # Verify mocks - groups.find is called (exact query format may vary due to $or support)
        mock_db.groups.find.assert_called_once()
        # OPTIMIZED: settlements.aggregate is called ONCE (not per friend/group)
        # The optimized version uses a single aggregation pipeline to get all friends' balances
        assert mock_db.settlements.aggregate.call_count == 1


@pytest.mark.asyncio
async def test_get_friends_balance_summary_no_friends_or_groups(expense_service):
    """Test friends balance summary when user has no friends or no shared groups with balances"""
    user_id = "lonely_user"

    with patch("app.expenses.service.mongodb") as mock_mongodb:
        mock_db = MagicMock()
        mock_mongodb.database = mock_db

        # No groups for user
        mock_groups_cursor = AsyncMock()
        mock_groups_cursor.to_list.return_value = []
        mock_db.groups.find.return_value = mock_groups_cursor

        # If groups list is empty, users.find won't be called by the service method.
        # However, if it were called, it should return a proper cursor.
        mock_user_find_cursor = AsyncMock()
        mock_user_find_cursor.to_list = AsyncMock(return_value=[])
        mock_db.users.find = MagicMock(
            return_value=mock_user_find_cursor
        )  # find is sync, returns async cursor

        mock_db.settlements.aggregate = (
            AsyncMock()
        )  # Won't be called if no friends/groups

        result = await expense_service.get_friends_balance_summary(user_id)

        assert len(result["friendsBalance"]) == 0
        assert result["summary"]["totalOwedToYou"] == 0
        assert result["summary"]["totalYouOwe"] == 0
        assert result["summary"]["netBalance"] == 0
        assert result["summary"]["friendCount"] == 0
        assert result["summary"]["activeGroups"] == 0
        # mock_db.users.find will be called with an empty $in if friend_ids is empty,
        # so assert_not_called() is incorrect. If specific call verification is needed,
        # it would be mock_db.users.find.assert_called_once_with({'_id': {'$in': []}})
        # For now, removing the assertion is fine as the main check is the summary.


@pytest.mark.asyncio
async def test_get_overall_balance_summary_success(expense_service):
    """Test successful retrieval of overall balance summary for a user"""
    user_id = "user_test_overall"
    group1_id = str(ObjectId())
    group2_id = str(ObjectId())
    group3_id = str(ObjectId())  # Group with zero balance for the user

    mock_groups_data = [
        {
            "_id": ObjectId(group1_id),
            "name": "Group One",
            "members": [{"userId": user_id}],
        },
        {
            "_id": ObjectId(group2_id),
            "name": "Group Two",
            "members": [{"userId": user_id}],
        },
        {
            "_id": ObjectId(group3_id),
            "name": "Group Three",
            "members": [{"userId": user_id}],
        },
    ]

    # Mocking settlement aggregations for the user in each group
    # Group One: User paid 100, was owed 20. Net balance = +80 (owed 80 by group)
    # Group Two: User paid 50, was owed 150. Net balance = -100 (owes 100 to group)
    # Group Three: User paid 50, was owed 50. Net balance = 0

    # This side effect will be for the aggregate() call. It needs to return a cursor mock.
    def mock_aggregate_cursor_side_effect(pipeline, *args, **kwargs):
        group_id_pipeline = pipeline[0]["$match"]["groupId"]

        # Create a new AsyncMock for the cursor each time aggregate is called
        cursor_mock = AsyncMock()

        if group_id_pipeline == group1_id:
            cursor_mock.to_list = AsyncMock(
                return_value=[{"_id": None, "totalPaid": 100.0, "totalOwed": 20.0}]
            )
        elif group_id_pipeline == group2_id:
            cursor_mock.to_list = AsyncMock(
                return_value=[{"_id": None, "totalPaid": 50.0, "totalOwed": 150.0}]
            )
        elif group_id_pipeline == group3_id:  # Zero balance
            cursor_mock.to_list = AsyncMock(
                return_value=[{"_id": None, "totalPaid": 50.0, "totalOwed": 50.0}]
            )
        else:  # Should not happen in this test
            cursor_mock.to_list = AsyncMock(return_value=[])
        return cursor_mock

    with patch("app.expenses.service.mongodb") as mock_mongodb:
        mock_db = MagicMock()
        mock_mongodb.database = mock_db

        # Mock groups user belongs to
        mock_groups_cursor = AsyncMock()
        mock_groups_cursor.to_list.return_value = mock_groups_data
        mock_db.groups.find.return_value = mock_groups_cursor

        # Mock settlement aggregation
        # .aggregate() is a sync method returning an async cursor
        mock_db.settlements.aggregate = MagicMock(
            side_effect=mock_aggregate_cursor_side_effect
        )

        result = await expense_service.get_overall_balance_summary(user_id)

        assert result is not None
        # Group One: +80. Group Two: -100. Group Three: 0
        # Total Owed to You: 80 (from Group One)
        # Total You Owe: 100 (to Group Two)
        # Net Balance: 80 - 100 = -20
        assert abs(result["totalOwedToYou"] - 80.0) < 0.01
        assert abs(result["totalYouOwe"] - 100.0) < 0.01
        assert abs(result["netBalance"] - (-20.0)) < 0.01
        assert result["currency"] == "USD"

        assert "groupsSummary" in result
        # Group three had zero balance, so it should not be in groupsSummary
        assert len(result["groupsSummary"]) == 2

        group1_summary = next(
            g for g in result["groupsSummary"] if g["group_id"] == group1_id
        )
        group2_summary = next(
            g for g in result["groupsSummary"] if g["group_id"] == group2_id
        )

        assert group1_summary["group_name"] == "Group One"
        assert abs(group1_summary["yourBalanceInGroup"] - 80.0) < 0.01

        assert group2_summary["group_name"] == "Group Two"
        assert abs(group2_summary["yourBalanceInGroup"] - (-100.0)) < 0.01

        # Verify mocks
        mock_db.groups.find.assert_called_once_with({"members.userId": user_id})
        assert mock_db.settlements.aggregate.call_count == 3  # Called for each group


@pytest.mark.asyncio
async def test_get_overall_balance_summary_no_groups(expense_service):
    """Test overall balance summary when user is in no groups"""
    user_id = "user_no_groups"

    with patch("app.expenses.service.mongodb") as mock_mongodb:
        mock_db = MagicMock()
        mock_mongodb.database = mock_db

        mock_groups_cursor = AsyncMock()
        mock_groups_cursor.to_list.return_value = []  # No groups
        mock_db.groups.find.return_value = mock_groups_cursor

        mock_db.settlements.aggregate = AsyncMock()  # Should not be called

        result = await expense_service.get_overall_balance_summary(user_id)

        assert result["totalOwedToYou"] == 0
        assert result["totalYouOwe"] == 0
        assert result["netBalance"] == 0
        assert len(result["groupsSummary"]) == 0
        mock_db.settlements.aggregate.assert_not_called()


@pytest.mark.asyncio
async def test_get_group_analytics_success(expense_service, mock_group_data):
    """Test successful retrieval of group analytics"""
    group_id_str = str(mock_group_data["_id"])  # Changed variable name for clarity
    user_a_obj = ObjectId()  # This is the user making the request and also a member
    user_b_obj = ObjectId()
    user_c_obj = ObjectId()  # In group but no expenses
    user_a_str = str(user_a_obj)
    user_b_str = str(user_b_obj)
    user_c_str = str(user_c_obj)

    year = 2023
    month = 10

    # Update mock_group_data to use new string ObjectIds if this fixture is used by other tests that need it
    # For this test, we mainly care about the member IDs used in logic below
    # Let's assume mock_group_data uses string IDs that are fine for direct comparison but might need ObjectId conversion if used in DB queries
    # For this test, the service method `get_group_analytics` takes group_id_str and user_a_str

    # Mock expenses for the specified period
    expense1_date = datetime(year, month, 5, tzinfo=timezone.utc)
    expense2_date = datetime(year, month, 15, tzinfo=timezone.utc)
    mock_expenses_in_period = [
        {
            "_id": ObjectId(),
            "groupId": group_id_str,
            "createdBy": user_a_str,
            "description": "Groceries",
            "amount": 70.0,
            "tags": ["food", "household"],
            "splits": [
                {"userId": user_a_str, "amount": 35.0},
                {"userId": user_b_str, "amount": 35.0},
            ],
            "createdAt": expense1_date,
        },
        {
            "_id": ObjectId(),
            "groupId": group_id_str,
            "createdBy": user_b_str,
            "description": "Movies",
            "amount": 30.0,
            "tags": ["entertainment", "food"],
            "splits": [
                {"userId": user_a_str, "amount": 15.0},
                {"userId": user_b_str, "amount": 15.0},
            ],
            "createdAt": expense2_date,
        },
    ]

    # Mock user data for member contributions
    mock_user_a_doc_db = {"_id": user_a_obj, "name": "User A"}
    mock_user_b_doc_db = {"_id": user_b_obj, "name": "User B"}
    mock_user_c_doc_db = {"_id": user_c_obj, "name": "User C"}

    async def mock_users_find_one_side_effect(query, *args, **kwargs):
        user_id_query_obj = query["_id"]  # This should be an ObjectId
        if user_id_query_obj == user_a_obj:
            return mock_user_a_doc_db
        if user_id_query_obj == user_b_obj:
            return mock_user_b_doc_db
        if user_id_query_obj == user_c_obj:
            return mock_user_c_doc_db
        return None

    # Adjust mock_group_data to ensure its members list matches what the service method expects
    # The service method iterates group["members"] which comes from `groups_collection.find_one`
    # So `mock_group_data` needs to have the correct string user IDs for the service logic.
    # The `mock_group_data` fixture already has "user_a", "user_b", "user_c". We need to ensure these match the ObjectIds used.
    # Let's redefine mock_group_data for this specific test to ensure consistency.

    current_test_mock_group_data = {
        # Use the same ObjectId as in the service call
        "_id": ObjectId(group_id_str),
        "name": "Test Group Analytics",
        "members": [
            {"userId": user_a_str, "role": "admin"},
            {"userId": user_b_str, "role": "member"},
            {"userId": user_c_str, "role": "member"},
        ],
    }

    with patch("app.expenses.service.mongodb") as mock_mongodb:
        mock_db = MagicMock()
        mock_mongodb.database = mock_db

        # Mock group membership check
        mock_db.groups.find_one = AsyncMock(
            return_value=current_test_mock_group_data
        )  # Use the adjusted mock
        # Mock expenses find for the period
        mock_expenses_cursor = AsyncMock()
        mock_expenses_cursor.to_list.return_value = mock_expenses_in_period
        mock_db.expenses.find.return_value = mock_expenses_cursor
        # Mock user lookups for member names
        mock_db.users.find_one = AsyncMock(side_effect=mock_users_find_one_side_effect)

        result = await expense_service.get_group_analytics(
            group_id_str, user_a_str, period="month", year=year, month=month
        )

        assert result is not None
        assert result["period"] == f"{year}-{month:02d}"
        assert abs(result["totalExpenses"] - 100.0) < 0.01  # 70 + 30
        assert result["expenseCount"] == 2
        assert abs(result["avgExpenseAmount"] - 50.0) < 0.01

        assert "topCategories" in result
        top_categories = result["topCategories"]
        # food: 70 (Groceries) + 30 (Movies) = 100
        # household: 70
        # entertainment: 30
        food_cat = next(c for c in top_categories if c["tag"] == "food")
        household_cat = next(c for c in top_categories if c["tag"] == "household")
        entertainment_cat = next(
            c for c in top_categories if c["tag"] == "entertainment"
        )

        assert abs(food_cat["amount"] - 100.0) < 0.01 and food_cat["count"] == 2
        assert (
            abs(household_cat["amount"] - 70.0) < 0.01 and household_cat["count"] == 1
        )
        assert (
            abs(entertainment_cat["amount"] - 30.0) < 0.01
            and entertainment_cat["count"] == 1
        )

        assert "memberContributions" in result
        member_contribs = result["memberContributions"]
        assert len(member_contribs) == 3  # user_a_str, user_b_str, user_c_str

        user_a_contrib = next(m for m in member_contribs if m["userId"] == user_a_str)
        user_b_contrib = next(m for m in member_contribs if m["userId"] == user_b_str)
        user_c_contrib = next(m for m in member_contribs if m["userId"] == user_c_str)

        # User A: Paid 70 (Groceries). Owed 35 (Groceries) + 15 (Movies) = 50. Net = 70 - 50 = 20
        assert user_a_contrib["userName"] == "User A"
        assert abs(user_a_contrib["totalPaid"] - 70.0) < 0.01
        assert abs(user_a_contrib["totalOwed"] - 50.0) < 0.01
        assert abs(user_a_contrib["netContribution"] - 20.0) < 0.01

        # User B: Paid 30 (Movies). Owed 35 (Groceries) + 15 (Movies) = 50. Net = 30 - 50 = -20
        assert user_b_contrib["userName"] == "User B"
        assert abs(user_b_contrib["totalPaid"] - 30.0) < 0.01
        assert abs(user_b_contrib["totalOwed"] - 50.0) < 0.01
        assert abs(user_b_contrib["netContribution"] - (-20.0)) < 0.01

        # User C: Paid 0. Owed 0. Net = 0
        assert user_c_contrib["userName"] == "User C"
        assert user_c_contrib["totalPaid"] == 0
        assert user_c_contrib["totalOwed"] == 0
        assert user_c_contrib["netContribution"] == 0

        assert "expenseTrends" in result
        # Should have entries for each day in the month. Check a couple.
        assert len(result["expenseTrends"]) >= 28  # Days in Oct
        day5_trend = next(
            d for d in result["expenseTrends"] if d["date"] == f"{year}-{month:02d}-05"
        )
        assert abs(day5_trend["amount"] - 70.0) < 0.01 and day5_trend["count"] == 1
        day15_trend = next(
            d for d in result["expenseTrends"] if d["date"] == f"{year}-{month:02d}-15"
        )
        assert abs(day15_trend["amount"] - 30.0) < 0.01 and day15_trend["count"] == 1
        day10_trend = next(
            d for d in result["expenseTrends"] if d["date"] == f"{year}-{month:02d}-10"
        )  # No expense
        assert day10_trend["amount"] == 0 and day10_trend["count"] == 0

        # Verify mocks
        mock_db.groups.find_one.assert_called_once()
        mock_db.expenses.find.assert_called_once()
        # users.find_one called for each member in current_test_mock_group_data["members"]
        assert mock_db.users.find_one.call_count == len(
            current_test_mock_group_data["members"]
        )


@pytest.mark.asyncio
async def test_get_group_analytics_group_not_found(expense_service):
    """Test get group analytics when group not found or user not member"""
    group_id = str(ObjectId())  # Valid format
    user_id = "user_a"

    with patch("app.expenses.service.mongodb") as mock_mongodb:
        mock_db = MagicMock()
        mock_mongodb.database = mock_db
        mock_db.groups.find_one = AsyncMock(return_value=None)  # Group not found

        """with pytest.raises(ValueError, match="Group not found or user not a member"):
            await expense_service.get_group_analytics(group_id, user_id)"""
        # Updated after stricter exception handling (July 2025)
        with pytest.raises(HTTPException) as exc_info:
            await expense_service.get_group_analytics(group_id, user_id)

        assert exc_info.value.status_code == 403
        assert exc_info.value.detail == "Group not found or user not a member"

        mock_db.expenses.find.assert_not_called()
        mock_db.users.find_one.assert_not_called()


@pytest.mark.asyncio
async def test_get_friends_balance_summary_aggregation_error(expense_service):
    """Test friends balance summary when aggregation fails"""
    user_id_str = str(ObjectId())

    with patch("app.expenses.service.mongodb") as mock_mongodb:
        mock_db = MagicMock()
        mock_mongodb.database = mock_db

        # Mock groups
        mock_groups = [
            {
                "_id": ObjectId(),
                "name": "Test Group",
                "members": [{"userId": user_id_str}, {"userId": str(ObjectId())}],
            }
        ]
        mock_groups_cursor = AsyncMock()
        mock_groups_cursor.to_list.return_value = mock_groups
        mock_db.groups.find.return_value = mock_groups_cursor

        # Mock aggregation failure
        mock_agg_cursor = AsyncMock()
        mock_agg_cursor.to_list.side_effect = Exception("Aggregation failed")
        mock_db.settlements.aggregate.return_value = mock_agg_cursor

        result = await expense_service.get_friends_balance_summary(user_id_str)

        # Should return empty results on error
        assert len(result["friendsBalance"]) == 0
        assert result["summary"]["totalOwedToYou"] == 0
        assert result["summary"]["totalYouOwe"] == 0
        assert result["summary"]["friendCount"] == 0


@pytest.mark.asyncio
async def test_get_friends_balance_summary_user_fetch_error(expense_service):
    """Test friends balance summary when fetching user details fails"""
    user_id_str = str(ObjectId())
    friend_id_str = str(ObjectId())

    with patch("app.expenses.service.mongodb") as mock_mongodb:
        mock_db = MagicMock()
        mock_mongodb.database = mock_db

        # Mock groups
        mock_groups = [
            {
                "_id": ObjectId(),
                "name": "Test Group",
                "members": [{"userId": user_id_str}, {"userId": friend_id_str}],
            }
        ]
        mock_groups_cursor = AsyncMock()
        mock_groups_cursor.to_list.return_value = mock_groups
        mock_db.groups.find.return_value = mock_groups_cursor

        # Mock aggregation success
        mock_agg_cursor = AsyncMock()
        mock_agg_cursor.to_list.return_value = [
            {
                "_id": friend_id_str,
                "totalBalance": 50.0,
                "groups": [{"groupId": str(mock_groups[0]["_id"]), "balance": 50.0}],
            }
        ]
        mock_db.settlements.aggregate.return_value = mock_agg_cursor

        # Mock user fetch failure
        mock_users_cursor = AsyncMock()
        mock_users_cursor.to_list.side_effect = Exception("User fetch failed")
        mock_db.users.find.return_value = mock_users_cursor

        result = await expense_service.get_friends_balance_summary(user_id_str)

        # Should still return results but with "Unknown" for user names
        assert len(result["friendsBalance"]) == 1
        assert result["friendsBalance"][0]["userName"] == "Unknown"
        assert result["friendsBalance"][0]["netBalance"] == 50.0


@pytest.mark.asyncio
async def test_get_friends_balance_summary_zero_balance_filtering(expense_service):
    """Test that friends with zero balance are filtered out - covers line 1061"""
    user_id_str = str(ObjectId())

    with patch("app.expenses.service.mongodb") as mock_mongodb:
        mock_db = MagicMock()
        mock_mongodb.database = mock_db

        # Mock groups
        mock_groups = [
            {
                "_id": ObjectId(),
                "name": "Test Group",
                "members": [{"userId": user_id_str}],
            }
        ]
        mock_groups_cursor = AsyncMock()
        mock_groups_cursor.to_list.return_value = mock_groups
        mock_db.groups.find.return_value = mock_groups_cursor

        # Mock aggregation returns no results (all filtered by zero balance)
        mock_agg_cursor = AsyncMock()
        mock_agg_cursor.to_list.return_value = []
        mock_db.settlements.aggregate.return_value = mock_agg_cursor

        result = await expense_service.get_friends_balance_summary(user_id_str)

        # Should return empty friend balance
        assert len(result["friendsBalance"]) == 0
        assert result["summary"]["totalOwedToYou"] == 0
        assert result["summary"]["totalYouOwe"] == 0
        assert result["summary"]["friendCount"] == 0
        assert result["summary"]["activeGroups"] == 1


@pytest.mark.asyncio
async def test_get_friends_balance_summary_negative_balance(expense_service):
    """Test friends balance with negative balance (user owes) - covers line 1141"""
    user_id_str = str(ObjectId())
    friend_id_str = str(ObjectId())
    group_id = str(ObjectId())

    with patch("app.expenses.service.mongodb") as mock_mongodb:
        mock_db = MagicMock()
        mock_mongodb.database = mock_db

        # Mock groups
        mock_groups = [
            {
                "_id": ObjectId(group_id),
                "name": "Test Group",
                "members": [{"userId": user_id_str}, {"userId": friend_id_str}],
            }
        ]
        mock_groups_cursor = AsyncMock()
        mock_groups_cursor.to_list.return_value = mock_groups
        mock_db.groups.find.return_value = mock_groups_cursor

        # Mock aggregation with NEGATIVE balance (user owes friend)
        mock_agg_cursor = AsyncMock()
        mock_agg_cursor.to_list.return_value = [
            {
                "_id": friend_id_str,
                "totalBalance": -100.0,  # Negative = user owes friend
                "groups": [{"groupId": group_id, "balance": -100.0}],
            }
        ]
        mock_db.settlements.aggregate.return_value = mock_agg_cursor

        # Mock user fetch
        mock_users_cursor = AsyncMock()
        mock_users_cursor.to_list.return_value = [
            {"_id": ObjectId(friend_id_str), "name": "Friend", "imageUrl": None}
        ]
        mock_db.users.find.return_value = mock_users_cursor

        result = await expense_service.get_friends_balance_summary(user_id_str)

        # Should have totalYouOwe = 100 (covers line 1141 - else branch)
        assert result["summary"]["totalOwedToYou"] == 0
        assert result["summary"]["totalYouOwe"] == 100.0
        assert result["summary"]["netBalance"] == -100.0


if __name__ == "__main__":
    pytest.main([__file__])
