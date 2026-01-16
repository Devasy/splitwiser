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
        self._created_at = created_at or datetime.now()
        self._updated_at = updated_at or datetime.now()

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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
