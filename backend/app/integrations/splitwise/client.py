"""
Splitwise API client wrapper.

Handles authentication and API requests to Splitwise.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from splitwise import Splitwise


class SplitwiseClient:
    """Wrapper around Splitwise SDK for API operations."""

    def __init__(
        self, api_key: str = None, consumer_key: str = None, consumer_secret: str = None
    ):
        """
        Initialize Splitwise client.

        Args:
            api_key: Bearer token for API authentication
            consumer_key: OAuth consumer key
            consumer_secret: OAuth consumer secret
        """
        self.sObj = Splitwise(
            consumer_key=consumer_key, consumer_secret=consumer_secret, api_key=api_key
        )

    def get_current_user(self):
        """Get current authenticated user."""
        return self.sObj.getCurrentUser()

    def get_friends(self):
        """Get list of friends."""
        return self.sObj.getFriends()

    def get_groups(self):
        """Get list of groups."""
        return self.sObj.getGroups()

    def get_expenses(self, group_id: Optional[int] = None, limit: int = 1000):
        """
        Get expenses, optionally filtered by group.

        Args:
            group_id: Optional group ID to filter
            limit: Maximum number of expenses to fetch

        Returns:
            List of expense objects
        """
        if group_id:
            return self.sObj.getExpenses(group_id=group_id, limit=limit)
        return self.sObj.getExpenses(limit=limit)

    @staticmethod
    def transform_user(user) -> Dict[str, Any]:
        """Transform Splitwise user to Splitwiser format."""
        picture = user.getPicture() if hasattr(user, "getPicture") else None
        picture_url = (
            picture.getMedium() if picture and hasattr(picture, "getMedium") else None
        )

        return {
            "splitwiseId": str(user.getId()),
            "name": f"{user.getFirstName() or ''} {user.getLastName() or ''}".strip(),
            "email": user.getEmail() if hasattr(user, "getEmail") else None,
            "imageUrl": picture_url,
            "currency": (
                user.getDefaultCurrency()
                if hasattr(user, "getDefaultCurrency")
                else "USD"
            ),
            "importedFrom": "splitwise",
            "importedAt": datetime.now(timezone.utc).isoformat(),
        }

    @staticmethod
    def transform_friend(friend) -> Dict[str, Any]:
        """Transform Splitwise friend to Splitwiser user format."""
        picture = friend.getPicture() if hasattr(friend, "getPicture") else None
        picture_url = (
            picture.getMedium() if picture and hasattr(picture, "getMedium") else None
        )

        balances = []
        if hasattr(friend, "getBalances"):
            try:
                for balance in friend.getBalances() or []:
                    balances.append(
                        {
                            "currency": (
                                balance.getCurrencyCode()
                                if hasattr(balance, "getCurrencyCode")
                                else "USD"
                            ),
                            "amount": (
                                float(balance.getAmount())
                                if hasattr(balance, "getAmount")
                                else 0.0
                            ),
                        }
                    )
            except Exception:
                pass

        return {
            "splitwiseId": str(friend.getId()),
            "name": f"{friend.getFirstName() or ''} {friend.getLastName() or ''}".strip(),
            "email": friend.getEmail() if hasattr(friend, "getEmail") else None,
            "imageUrl": picture_url,
            "currency": None,
            "balances": balances,
            "importedFrom": "splitwise",
            "importedAt": datetime.now(timezone.utc).isoformat(),
        }

    @staticmethod
    def transform_group(group) -> Dict[str, Any]:
        """Transform Splitwise group to Splitwiser format."""
        members = []
        for member in group.getMembers() or []:
            members.append(
                {
                    "userId": str(member.getId()),
                    "splitwiseUserId": str(member.getId()),
                    "firstName": (
                        member.getFirstName() if hasattr(member, "getFirstName") else ""
                    ),
                    "lastName": (
                        member.getLastName() if hasattr(member, "getLastName") else ""
                    ),
                    "email": member.getEmail() if hasattr(member, "getEmail") else None,
                    "role": "member",
                    "joinedAt": datetime.now(timezone.utc).isoformat(),
                }
            )

        avatar = group.getAvatar() if hasattr(group, "getAvatar") else None
        avatar_url = (
            avatar.getMedium() if avatar and hasattr(avatar, "getMedium") else None
        )

        return {
            "splitwiseGroupId": str(group.getId()),
            "name": group.getName(),
            "currency": group.getCurrency() if hasattr(group, "getCurrency") else "USD",
            "imageUrl": avatar_url,
            "type": group.getType() if hasattr(group, "getType") else "general",
            "members": members,
            "importedFrom": "splitwise",
            "importedAt": datetime.now(timezone.utc).isoformat(),
        }

    @staticmethod
    def _safe_isoformat(date_value):
        """Safely convert date to ISO format string."""
        if date_value is None:
            return None
        if isinstance(date_value, str):
            return date_value
        return (
            date_value.isoformat()
            if hasattr(date_value, "isoformat")
            else str(date_value)
        )

    @staticmethod
    def transform_expense(expense) -> Dict[str, Any]:
        """Transform Splitwise expense to Splitwiser format."""
        # Determine who paid
        paid_by_user_id = None
        users = expense.getUsers() if hasattr(expense, "getUsers") else []
        for user in users or []:
            try:
                if float(user.getPaidShare()) > 0:
                    paid_by_user_id = str(user.getId())
                    break
            except Exception:
                continue

        # Transform splits
        splits = []
        for user in users or []:
            try:
                owed_amount = (
                    float(user.getOwedShare()) if hasattr(user, "getOwedShare") else 0
                )
                if owed_amount > 0:
                    splits.append(
                        {
                            "userId": str(user.getId()),
                            "splitwiseUserId": str(user.getId()),
                            "userName": f"{user.getFirstName() or ''} {user.getLastName() or ''}".strip(),
                            "amount": owed_amount,
                            "type": "equal",
                        }
                    )
            except Exception:
                continue

        # Extract tags/category
        tags = []
        if hasattr(expense, "getCategory"):
            try:
                category = expense.getCategory()
                if category and hasattr(category, "getName"):
                    tags.append(category.getName())
            except Exception:
                pass

        # Receipt URLs
        receipt_urls = []
        if hasattr(expense, "getReceipt"):
            try:
                receipt = expense.getReceipt()
                if receipt and hasattr(receipt, "getOriginal"):
                    receipt_urls.append(receipt.getOriginal())
            except Exception:
                pass

        # Safe attribute access
        group_id = (
            str(expense.getGroupId())
            if hasattr(expense, "getGroupId") and expense.getGroupId()
            else "0"
        )
        created_by = (
            expense.getCreatedBy() if hasattr(expense, "getCreatedBy") else None
        )
        created_by_id = (
            str(created_by.getId())
            if created_by and hasattr(created_by, "getId")
            else None
        )

        # Extract dates safely
        expense_date = expense.getDate() if hasattr(expense, "getDate") else None
        deleted_at = (
            expense.getDeletedAt() if hasattr(expense, "getDeletedAt") else None
        )
        created_at = (
            expense.getCreatedAt() if hasattr(expense, "getCreatedAt") else None
        )
        updated_at = (
            expense.getUpdatedAt() if hasattr(expense, "getUpdatedAt") else None
        )

        return {
            "splitwiseExpenseId": str(expense.getId()),
            "groupId": group_id,
            "description": (
                expense.getDescription() if hasattr(expense, "getDescription") else ""
            ),
            "amount": float(expense.getCost()) if hasattr(expense, "getCost") else 0.0,
            "currency": (
                expense.getCurrencyCode()
                if hasattr(expense, "getCurrencyCode")
                else "USD"
            ),
            "date": SplitwiseClient._safe_isoformat(expense_date),
            "paidBy": paid_by_user_id,
            "createdBy": created_by_id,
            "splits": splits,
            "splitType": "equal",
            "tags": tags,
            "receiptUrls": receipt_urls,
            "isDeleted": deleted_at is not None,
            "deletedAt": SplitwiseClient._safe_isoformat(deleted_at),
            "importedFrom": "splitwise",
            "importedAt": datetime.now(timezone.utc).isoformat(),
            "createdAt": SplitwiseClient._safe_isoformat(created_at),
            "updatedAt": SplitwiseClient._safe_isoformat(updated_at),
        }
