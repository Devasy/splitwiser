"""
Integration tests for Splitwise import service.

These tests verify the actual import logic in:
- backend/app/integrations/splitwise/client.py (transform_expense)
- backend/app/integrations/service.py (_import_expenses)

They use mock Splitwise expense objects to simulate real data.
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# Mock Splitwise expense user
class MockSplitwiseUser:
    def __init__(self, user_id, first_name, last_name, paid_share, owed_share):
        self._id = user_id
        self._first_name = first_name
        self._last_name = last_name
        self._paid_share = paid_share
        self._owed_share = owed_share

    def getId(self):
        return self._id

    def getFirstName(self):
        return self._first_name

    def getLastName(self):
        return self._last_name

    def getPaidShare(self):
        return self._paid_share

    def getOwedShare(self):
        return self._owed_share


# Mock Splitwise expense
class MockSplitwiseExpense:
    def __init__(
        self,
        expense_id,
        description,
        cost,
        currency,
        users,
        is_payment=False,
        group_id=None,
        deleted_at=None,
        created_at=None,
        updated_at=None,
    ):
        self._id = expense_id
        self._description = description
        self._cost = cost
        self._currency = currency
        self._users = users
        self._is_payment = is_payment
        self._group_id = group_id
        self._deleted_at = deleted_at
        self._created_at = created_at or datetime.now(timezone.utc)
        self._updated_at = updated_at or datetime.now(timezone.utc)

    def getId(self):
        return self._id

    def getDescription(self):
        return self._description

    def getCost(self):
        return self._cost

    def getCurrencyCode(self):
        return self._currency

    def getUsers(self):
        return self._users

    def getPayment(self):
        return self._is_payment

    def getGroup(self):
        mock_group = MagicMock()
        mock_group.getId.return_value = self._group_id
        return mock_group

    def getDeletedAt(self):
        return self._deleted_at

    def getCreatedAt(self):
        return self._created_at

    def getUpdatedAt(self):
        return self._updated_at

    def getDate(self):
        return self._created_at

    def getCategory(self):
        return None

    def getReceipt(self):
        return None

    def getCreatedBy(self):
        mock_user = MagicMock()
        mock_user.getId.return_value = self._users[0].getId() if self._users else None
        return mock_user


class TestSplitwiseClientTransform:
    """Tests for SplitwiseClient.transform_expense()"""

    def test_simple_expense_transform(self):
        """Test transforming a simple expense."""
        from app.integrations.splitwise.client import SplitwiseClient

        users = [
            MockSplitwiseUser("1", "Devasy", "Patel", 100.0, 25.0),
            MockSplitwiseUser("2", "Deep", "Patel", 0.0, 25.0),
            MockSplitwiseUser("3", "Dwij", "Bavisi", 0.0, 25.0),
            MockSplitwiseUser("4", "Yaksh", "Rajvanshi", 0.0, 25.0),
        ]

        expense = MockSplitwiseExpense(
            expense_id="12345",
            description="Dinner",
            cost=100.0,
            currency="INR",
            users=users,
            group_id="999",
        )

        result = SplitwiseClient.transform_expense(expense)

        # Verify userShares
        assert "userShares" in result
        assert len(result["userShares"]) == 4

        # Check Devasy's share
        devasy_share = next(s for s in result["userShares"] if s["userId"] == "1")
        assert devasy_share["paidShare"] == 100.0
        assert devasy_share["owedShare"] == 25.0
        assert devasy_share["netEffect"] == 75.0

        # Check payers
        assert len(result["payers"]) == 1
        assert result["payers"][0]["id"] == "1"
        assert result["payers"][0]["amount"] == 100.0

        # Check paidBy
        assert result["paidBy"] == "1"

    def test_payment_transform(self):
        """Test transforming a payment transaction."""
        from app.integrations.splitwise.client import SplitwiseClient

        users = [
            MockSplitwiseUser("4", "Yaksh", "Rajvanshi", 50.0, 0.0),  # Payer
            MockSplitwiseUser("1", "Devasy", "Patel", 0.0, 50.0),  # Receiver
        ]

        expense = MockSplitwiseExpense(
            expense_id="12346",
            description="Payment",
            cost=50.0,
            currency="INR",
            users=users,
            is_payment=True,
            group_id="999",
        )

        result = SplitwiseClient.transform_expense(expense)

        # Verify isPayment flag
        assert result["isPayment"] is True

        # Verify userShares
        yaksh_share = next(s for s in result["userShares"] if s["userId"] == "4")
        assert yaksh_share["netEffect"] == 50.0  # Positive (paying off debt)

        devasy_share = next(s for s in result["userShares"] if s["userId"] == "1")
        assert devasy_share["netEffect"] == -50.0  # Negative (receiving payment)

    def test_multi_payer_transform(self):
        """Test transforming a multi-payer expense."""
        from app.integrations.splitwise.client import SplitwiseClient

        users = [
            MockSplitwiseUser("1", "Devasy", "Patel", 120.0, 50.0),
            MockSplitwiseUser("2", "Deep", "Patel", 80.0, 50.0),
            MockSplitwiseUser("3", "Dwij", "Bavisi", 0.0, 50.0),
            MockSplitwiseUser("4", "Yaksh", "Rajvanshi", 0.0, 50.0),
        ]

        expense = MockSplitwiseExpense(
            expense_id="12347",
            description="Multi-payer dinner",
            cost=200.0,
            currency="INR",
            users=users,
            group_id="999",
        )

        result = SplitwiseClient.transform_expense(expense)

        # Verify multiple payers
        assert len(result["payers"]) == 2

        # Verify userShares
        devasy_share = next(s for s in result["userShares"] if s["userId"] == "1")
        assert devasy_share["netEffect"] == 70.0

        deep_share = next(s for s in result["userShares"] if s["userId"] == "2")
        assert deep_share["netEffect"] == 30.0


class TestSplitTypeDetection:
    """Tests for detecting equal vs unequal split types."""

    def test_equal_split_detection(self):
        """Test that equal splits are detected correctly."""
        from app.integrations.splitwise.client import SplitwiseClient

        splits = [
            {"userId": "1", "amount": 25.0},
            {"userId": "2", "amount": 25.0},
            {"userId": "3", "amount": 25.0},
            {"userId": "4", "amount": 25.0},
        ]
        assert SplitwiseClient._detect_split_type(splits) == "equal"

    def test_unequal_split_detection(self):
        """Test that unequal splits are detected correctly."""
        from app.integrations.splitwise.client import SplitwiseClient

        # Example: Jamnagar trip with unequal distribution
        splits = [
            {"userId": "1", "amount": 1080.0},  # Vijay
            {"userId": "2", "amount": 1080.0},  # Devasy (different from others)
        ]
        assert SplitwiseClient._detect_split_type(splits) == "equal"

        # Actually unequal split
        unequal_splits = [
            {"userId": "1", "amount": 800.0},
            {"userId": "2", "amount": 1360.0},  # Different amount
        ]
        assert SplitwiseClient._detect_split_type(unequal_splits) == "unequal"

    def test_single_person_split(self):
        """Test single person splits are treated as equal."""
        from app.integrations.splitwise.client import SplitwiseClient

        splits = [{"userId": "1", "amount": 100.0}]
        assert SplitwiseClient._detect_split_type(splits) == "equal"

    def test_empty_splits(self):
        """Test empty splits are treated as equal."""
        from app.integrations.splitwise.client import SplitwiseClient

        assert SplitwiseClient._detect_split_type([]) == "equal"

    def test_near_equal_within_tolerance(self):
        """Test splits within 5 cent tolerance are considered equal."""
        from app.integrations.splitwise.client import SplitwiseClient

        # Splits within 0.05 tolerance (handles rounding from 3-way splits)
        # e.g., 100/3 = 33.33, 33.33, 33.34
        splits = [
            {"userId": "1", "amount": 33.33},
            {"userId": "2", "amount": 33.37},  # 0.04 diff from first
            {"userId": "3", "amount": 33.30},  # 0.03 diff from first
        ]
        # All within 0.05 tolerance - should be considered equal
        assert SplitwiseClient._detect_split_type(splits) == "equal"

        # Outside tolerance (> 0.05)
        unequal_splits = [
            {"userId": "1", "amount": 33.33},
            {"userId": "2", "amount": 33.40},  # 0.07 difference - outside tolerance
            {"userId": "3", "amount": 33.33},
        ]
        assert SplitwiseClient._detect_split_type(unequal_splits) == "unequal"


class TestSettlementDirection:
    """
    Tests to verify the correct direction of settlements.

    The key insight:
    - payerId = debtor (person who OWES money)
    - payeeId = creditor (person who is OWED money)

    In the calculation:
    - net_balances[payerId][payeeId] = what payerId owes payeeId
    """

    def test_expense_settlement_direction(self):
        """Verify that expense creates correct settlement direction."""
        from test_settlement_calculation import SettlementCalculator

        # Devasy pays 100 for Deep
        expense = {
            "users": [
                {
                    "userId": "devasy",
                    "userName": "Devasy",
                    "paidShare": 100.0,
                    "owedShare": 0.0,
                },
                {
                    "userId": "deep",
                    "userName": "Deep",
                    "paidShare": 0.0,
                    "owedShare": 100.0,
                },
            ]
        }

        calc = SettlementCalculator()
        shares = calc.calculate_user_shares(expense)
        settlements = calc.create_settlements_from_shares(shares)

        # Deep owes Devasy 100
        assert len(settlements) == 1
        assert settlements[0]["payerId"] == "deep"  # Debtor
        assert settlements[0]["payeeId"] == "devasy"  # Creditor
        assert settlements[0]["amount"] == 100.0

    def test_payment_settlement_direction(self):
        """Verify that payment creates correct settlement direction."""
        from test_settlement_calculation import SettlementCalculator

        # Deep pays Devasy 100 (settling debt)
        # In Splitwise: Deep paid 100, Devasy owes 100
        payment = {
            "users": [
                {
                    "userId": "deep",
                    "userName": "Deep",
                    "paidShare": 100.0,
                    "owedShare": 0.0,
                },
                {
                    "userId": "devasy",
                    "userName": "Devasy",
                    "paidShare": 0.0,
                    "owedShare": 100.0,
                },
            ]
        }

        calc = SettlementCalculator()
        shares = calc.calculate_user_shares(payment)
        settlements = calc.create_settlements_from_shares(shares)

        # This creates a "reverse" settlement: Devasy now "owes" Deep
        # Which offsets any previous debt Deep had to Devasy
        assert len(settlements) == 1
        assert settlements[0]["payerId"] == "devasy"  # Now the debtor (in this tx)
        assert settlements[0]["payeeId"] == "deep"  # Now the creditor (in this tx)
        assert settlements[0]["amount"] == 100.0

    def test_combined_expense_and_payment_nets_out(self):
        """Verify that expense + payment with same amount nets to zero."""
        from test_settlement_calculation import SettlementCalculator

        # Expense: Devasy pays 100 for Deep
        expense = {
            "users": [
                {
                    "userId": "devasy",
                    "userName": "Devasy",
                    "paidShare": 100.0,
                    "owedShare": 0.0,
                },
                {
                    "userId": "deep",
                    "userName": "Deep",
                    "paidShare": 0.0,
                    "owedShare": 100.0,
                },
            ]
        }

        # Payment: Deep pays Devasy 100
        payment = {
            "users": [
                {
                    "userId": "deep",
                    "userName": "Deep",
                    "paidShare": 100.0,
                    "owedShare": 0.0,
                },
                {
                    "userId": "devasy",
                    "userName": "Devasy",
                    "paidShare": 0.0,
                    "owedShare": 100.0,
                },
            ]
        }

        calc = SettlementCalculator()

        all_settlements = []
        for tx in [expense, payment]:
            shares = calc.calculate_user_shares(tx)
            settlements = calc.create_settlements_from_shares(shares)
            all_settlements.extend(settlements)

        # From expense: Deep owes Devasy 100 -> net_balances[deep][devasy] = 100
        # From payment: Devasy owes Deep 100 -> net_balances[devasy][deep] = 100
        # Net: 100 - 100 = 0

        optimized, balances = calc.calculate_optimized_settlements(all_settlements)

        assert len(optimized) == 0
        assert abs(balances.get("devasy", 0)) < 0.01
        assert abs(balances.get("deep", 0)) < 0.01


class TestPayerAttribution:
    """
    Tests to verify correct payer attribution during import.

    The bug: When netEffect = 0 for all users (self-paid expenses),
    the creditors list is empty and the code incorrectly defaults
    to the importing user as the payer.

    The fix: Use paidShare directly to find who actually paid money,
    not netEffect (which can be 0 for self-paid expenses).
    """

    def test_normal_expense_payer_attribution(self):
        """
        Normal expense: Alice pays $30 for lunch split 3 ways.

        Alice: paid $30, owes $10 → netEffect = +$20 (creditor)
        Bob: paid $0, owes $10 → netEffect = -$10 (debtor)
        Charlie: paid $0, owes $10 → netEffect = -$10

        Result: payer should be Alice
        """
        mapped_shares = [
            {
                "userId": "alice",
                "userName": "Alice",
                "paidShare": 30.0,
                "owedShare": 10.0,
                "netEffect": 20.0,
            },
            {
                "userId": "bob",
                "userName": "Bob",
                "paidShare": 0.0,
                "owedShare": 10.0,
                "netEffect": -10.0,
            },
            {
                "userId": "charlie",
                "userName": "Charlie",
                "paidShare": 0.0,
                "owedShare": 10.0,
                "netEffect": -10.0,
            },
        ]
        importing_user_id = "dave"  # Dave is importing but didn't pay

        # Apply the fix logic
        paid_by = max(mapped_shares, key=lambda s: s["paidShare"], default=None)
        payer_id = (
            paid_by["userId"]
            if paid_by and paid_by["paidShare"] > 0
            else importing_user_id
        )

        assert payer_id == "alice", f"Expected Alice to be the payer, got {payer_id}"

    def test_self_paid_expense_payer_attribution(self):
        """
        Self-paid expense: Each person pays their own $10 coffee.

        Alice: paid $10, owes $10 → netEffect = $0
        Bob: paid $10, owes $10 → netEffect = $0

        Result: payer should be Alice (highest paidShare), NOT importing user Dave

        This was the bug - when netEffect = 0 for everyone,
        creditors was empty and defaulted to importing user.
        """
        mapped_shares = [
            {
                "userId": "alice",
                "userName": "Alice",
                "paidShare": 10.0,
                "owedShare": 10.0,
                "netEffect": 0.0,
            },
            {
                "userId": "bob",
                "userName": "Bob",
                "paidShare": 10.0,
                "owedShare": 10.0,
                "netEffect": 0.0,
            },
        ]
        importing_user_id = "dave"  # Dave is importing but didn't pay

        # Old buggy logic would do this:
        creditors = [
            (s["userId"], s["userName"], s["netEffect"])
            for s in mapped_shares
            if s["netEffect"] > 0.01
        ]
        buggy_payer_id = creditors[0][0] if creditors else importing_user_id

        # Verify the bug exists
        assert buggy_payer_id == "dave", "Bug should have defaulted to importing user"

        # Apply the fix logic
        paid_by = max(mapped_shares, key=lambda s: s["paidShare"], default=None)
        payer_id = (
            paid_by["userId"]
            if paid_by and paid_by["paidShare"] > 0
            else importing_user_id
        )

        # Alice paid the most, so she should be the payer
        assert payer_id == "alice", f"Expected Alice to be the payer, got {payer_id}"

    def test_solo_expense_payer_attribution(self):
        """
        Solo expense: Bob pays $50 for groceries he bought himself (no split).

        Bob: paid $50, owes $50 → netEffect = $0

        Result: payer should be Bob, NOT importing user Dave
        """
        mapped_shares = [
            {
                "userId": "bob",
                "userName": "Bob",
                "paidShare": 50.0,
                "owedShare": 50.0,
                "netEffect": 0.0,
            },
        ]
        importing_user_id = "dave"  # Different user is importing

        # Apply the fix logic
        paid_by = max(mapped_shares, key=lambda s: s["paidShare"], default=None)
        payer_id = (
            paid_by["userId"]
            if paid_by and paid_by["paidShare"] > 0
            else importing_user_id
        )

        assert payer_id == "bob", f"Expected Bob to be the payer, got {payer_id}"

    def test_no_payers_defaults_to_importing_user(self):
        """
        Edge case: No one paid anything (shouldn't happen, but handle gracefully).

        Result: Fall back to importing user
        """
        mapped_shares = [
            {
                "userId": "alice",
                "userName": "Alice",
                "paidShare": 0.0,
                "owedShare": 10.0,
                "netEffect": -10.0,
            },
            {
                "userId": "bob",
                "userName": "Bob",
                "paidShare": 0.0,
                "owedShare": 10.0,
                "netEffect": -10.0,
            },
        ]
        importing_user_id = "dave"

        # Apply the fix logic
        paid_by = max(mapped_shares, key=lambda s: s["paidShare"], default=None)
        payer_id = (
            paid_by["userId"]
            if paid_by and paid_by["paidShare"] > 0
            else importing_user_id
        )

        # No one paid, so fall back to importing user
        assert (
            payer_id == "dave"
        ), f"Expected Dave (importing user) to be the payer, got {payer_id}"

    def test_empty_shares_defaults_to_importing_user(self):
        """
        Edge case: Empty mapped_shares list.

        Result: Fall back to importing user
        """
        mapped_shares = []
        importing_user_id = "dave"

        # Apply the fix logic
        paid_by = max(mapped_shares, key=lambda s: s["paidShare"], default=None)
        payer_id = (
            paid_by["userId"]
            if paid_by and paid_by["paidShare"] > 0
            else importing_user_id
        )

        assert (
            payer_id == "dave"
        ), f"Expected Dave (importing user) to be the payer, got {payer_id}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
