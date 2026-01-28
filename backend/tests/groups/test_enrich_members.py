"""Tests for the optimized _enrich_members_with_user_details function"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from app.groups.service import GroupService
from bson import ObjectId


class TestEnrichMembersOptimized:
    """Test cases for _enrich_members_with_user_details optimized function"""

    def setup_method(self):
        """Setup for each test method"""
        self.service = GroupService()

    @pytest.mark.asyncio
    async def test_enrich_members_with_user_details_success(self):
        """Test successful enrichment of members with user details"""
        user_id_1 = str(ObjectId())
        user_id_2 = str(ObjectId())
        user_id_3 = str(ObjectId())

        members = [
            {"userId": user_id_1, "role": "admin", "joinedAt": "2023-01-01"},
            {"userId": user_id_2, "role": "member", "joinedAt": "2023-01-02"},
            {"userId": user_id_3, "role": "member", "joinedAt": "2023-01-03"},
        ]

        mock_users = [
            {"_id": ObjectId(user_id_1), "name": "Admin User", "imageUrl": "admin.jpg"},
            {
                "_id": ObjectId(user_id_2),
                "name": "Member One",
                "imageUrl": "member1.jpg",
            },
            {"_id": ObjectId(user_id_3), "name": "Member Two", "imageUrl": None},
        ]

        mock_db = MagicMock()
        mock_users_collection = MagicMock()
        mock_db.users = mock_users_collection

        # Mock the find operation
        mock_cursor = AsyncMock()
        mock_cursor.to_list.return_value = mock_users
        mock_users_collection.find.return_value = mock_cursor

        with patch.object(self.service, "get_db", return_value=mock_db):
            enriched = await self.service._enrich_members_with_user_details(members)

        assert len(enriched) == 3
        assert enriched[0]["userId"] == user_id_1
        assert enriched[0]["user"]["name"] == "Admin User"
        assert enriched[0]["user"]["imageUrl"] == "admin.jpg"
        assert enriched[0]["role"] == "admin"

        assert enriched[1]["userId"] == user_id_2
        assert enriched[1]["user"]["name"] == "Member One"
        assert enriched[1]["user"]["imageUrl"] == "member1.jpg"

        assert enriched[2]["userId"] == user_id_3
        assert enriched[2]["user"]["name"] == "Member Two"
        assert enriched[2]["user"]["imageUrl"] is None

        # Verify the query was made correctly with $in operator
        mock_users_collection.find.assert_called_once()
        call_args = mock_users_collection.find.call_args
        assert "_id" in call_args[0][0]
        assert "$in" in call_args[0][0]["_id"]

    @pytest.mark.asyncio
    async def test_enrich_members_empty_list(self):
        """Test enrichment with empty members list - covers line 35"""
        mock_db = MagicMock()

        with patch.object(self.service, "get_db", return_value=mock_db):
            enriched = await self.service._enrich_members_with_user_details([])

        assert enriched == []
        # Verify no database call was made
        mock_db.users.find.assert_not_called()

    @pytest.mark.asyncio
    async def test_enrich_members_invalid_object_ids(self):
        """Test enrichment with invalid ObjectIds - covers lines 47, 52, 108-109"""
        members = [
            {"userId": "invalid_id_123", "role": "admin", "joinedAt": "2023-01-01"},
            {"userId": "also_invalid", "role": "member", "joinedAt": "2023-01-02"},
        ]

        mock_db = MagicMock()

        with patch.object(self.service, "get_db", return_value=mock_db):
            # Patch logger to verify warning is called (covers line 47)
            with patch("app.groups.service.logger") as mock_logger:
                enriched = await self.service._enrich_members_with_user_details(members)
                # Verify logger.warning was called for invalid ObjectIds (line 47)
                assert mock_logger.warning.call_count == 2

        # Should return fallback members since no valid ObjectIds (line 52)
        assert len(enriched) == 2
        # Verify _create_fallback_member output (lines 108-109)
        assert enriched[0]["userId"] == "invalid_id_123"
        assert "User" in enriched[0]["user"]["name"]
        assert enriched[0]["role"] == "admin"
        assert enriched[0]["user"]["email"] == "invalid_id_123@example.com"
        assert enriched[0]["joinedAt"] == "2023-01-01"

    @pytest.mark.asyncio
    async def test_enrich_members_member_without_userId(self):
        """Test enrichment when member has no userId - covers line 99"""
        user_id_1 = str(ObjectId())

        members = [
            {"userId": user_id_1, "role": "admin", "joinedAt": "2023-01-01"},
            {"role": "member", "joinedAt": "2023-01-02"},  # No userId
        ]

        mock_users = [
            {"_id": ObjectId(user_id_1), "name": "Admin User", "imageUrl": "admin.jpg"},
        ]

        mock_db = MagicMock()
        mock_users_collection = MagicMock()
        mock_db.users = mock_users_collection

        mock_cursor = AsyncMock()
        mock_cursor.to_list.return_value = mock_users
        mock_users_collection.find.return_value = mock_cursor

        with patch.object(self.service, "get_db", return_value=mock_db):
            enriched = await self.service._enrich_members_with_user_details(members)

        assert len(enriched) == 2
        assert enriched[0]["user"]["name"] == "Admin User"
        # Second member should be returned as-is since no userId
        assert enriched[1]["role"] == "member"
        assert "user" not in enriched[1] or enriched[1] == members[1]

    @pytest.mark.asyncio
    async def test_enrich_members_missing_user_data(self):
        """Test enrichment when some users are not found in database"""
        user_id_1 = str(ObjectId())
        user_id_2 = str(ObjectId())

        members = [
            {"userId": user_id_1, "role": "admin", "joinedAt": "2023-01-01"},
            {"userId": user_id_2, "role": "member", "joinedAt": "2023-01-02"},
        ]

        # Only return data for user_id_1, not user_id_2
        mock_users = [
            {"_id": ObjectId(user_id_1), "name": "Admin User", "imageUrl": "admin.jpg"},
        ]

        mock_db = MagicMock()
        mock_users_collection = MagicMock()
        mock_db.users = mock_users_collection

        mock_cursor = AsyncMock()
        mock_cursor.to_list.return_value = mock_users
        mock_users_collection.find.return_value = mock_cursor

        with patch.object(self.service, "get_db", return_value=mock_db):
            enriched = await self.service._enrich_members_with_user_details(members)

        assert len(enriched) == 2
        assert enriched[0]["user"]["name"] == "Admin User"
        # Missing user should have fallback name
        assert "User" in enriched[1]["user"]["name"]  # Will be "User <last4digits>"

    @pytest.mark.asyncio
    async def test_enrich_members_database_error(self):
        """Test enrichment when database query fails"""
        user_id_1 = str(ObjectId())

        members = [
            {"userId": user_id_1, "role": "admin", "joinedAt": "2023-01-01"},
        ]

        mock_db = MagicMock()
        mock_users_collection = MagicMock()
        mock_db.users = mock_users_collection

        # Simulate database error
        mock_cursor = AsyncMock()
        mock_cursor.to_list.side_effect = Exception("Database connection error")
        mock_users_collection.find.return_value = mock_cursor

        with patch.object(self.service, "get_db", return_value=mock_db):
            enriched = await self.service._enrich_members_with_user_details(members)

        # Should still return members with fallback user data
        assert len(enriched) == 1
        assert "User" in enriched[0]["user"]["name"]  # Fallback name
        assert enriched[0]["user"]["imageUrl"] is None

    @pytest.mark.asyncio
    async def test_enrich_members_preserves_member_fields(self):
        """Test that enrichment preserves all original member fields"""
        user_id_1 = str(ObjectId())

        members = [
            {
                "userId": user_id_1,
                "role": "admin",
                "joinedAt": "2023-01-01",
                "customField": "custom_value",
            },
        ]

        mock_users = [
            {"_id": ObjectId(user_id_1), "name": "Admin User", "imageUrl": "admin.jpg"},
        ]

        mock_db = MagicMock()
        mock_users_collection = MagicMock()
        mock_db.users = mock_users_collection

        mock_cursor = AsyncMock()
        mock_cursor.to_list.return_value = mock_users
        mock_users_collection.find.return_value = mock_cursor

        with patch.object(self.service, "get_db", return_value=mock_db):
            enriched = await self.service._enrich_members_with_user_details(members)

        # Verify all fields are preserved
        assert enriched[0]["userId"] == user_id_1
        assert enriched[0]["role"] == "admin"
        assert enriched[0]["joinedAt"] == "2023-01-01"
        # Note: customField won't be in the output as the function creates a new structure
        # It only preserves userId, role, and joinedAt
        assert enriched[0]["user"]["name"] == "Admin User"
        assert enriched[0]["user"]["imageUrl"] == "admin.jpg"

    @pytest.mark.asyncio
    async def test_enrich_members_batch_query_optimization(self):
        """Test that the function uses a single batch query instead of N queries"""
        # Create 10 members
        members = []
        user_ids = []
        for i in range(10):
            user_id = str(ObjectId())
            user_ids.append(user_id)
            members.append(
                {
                    "userId": user_id,
                    "role": "member",
                    "joinedAt": f"2023-01-{i + 1:02d}",
                }
            )

        mock_users = [
            {"_id": ObjectId(uid), "name": f"User {i}", "imageUrl": None}
            for i, uid in enumerate(user_ids)
        ]

        mock_db = MagicMock()
        mock_users_collection = MagicMock()
        mock_db.users = mock_users_collection

        mock_cursor = AsyncMock()
        mock_cursor.to_list.return_value = mock_users
        mock_users_collection.find.return_value = mock_cursor

        with patch.object(self.service, "get_db", return_value=mock_db):
            enriched = await self.service._enrich_members_with_user_details(members)

        # Verify only ONE database call was made (batch query)
        assert mock_users_collection.find.call_count == 1

        # Verify all 10 members were enriched
        assert len(enriched) == 10
        for i, member in enumerate(enriched):
            assert member["user"]["name"] == f"User {i}"

    def test_create_fallback_member_short_user_id(self):
        """Test _create_fallback_member with short user ID - covers lines 108-109"""
        member = {"userId": "ab", "role": "member", "joinedAt": "2023-01-01"}

        result = self.service._create_fallback_member(member)

        # Verify fallback member structure (lines 108-109)
        assert result["userId"] == "ab"
        assert result["role"] == "member"
        assert result["joinedAt"] == "2023-01-01"
        assert result["user"]["name"] == "User ab"  # Uses the short ID since len < 4
        assert result["user"]["email"] == "ab@example.com"
        assert result["user"]["imageUrl"] is None

    def test_create_fallback_member_long_user_id(self):
        """Test _create_fallback_member with long user ID - covers lines 108-109"""
        long_id = "abcdefghijklmnop"
        member = {"userId": long_id, "role": "admin", "joinedAt": "2023-01-01"}

        result = self.service._create_fallback_member(member)

        # Verify fallback member structure with last 4 chars
        assert result["userId"] == long_id
        assert result["role"] == "admin"
        assert result["user"]["name"] == "User mnop"  # Uses last 4 chars
        assert result["user"]["email"] == "abcdefghijklmnop@example.com"
        assert result["user"]["imageUrl"] is None

    def test_create_fallback_member_no_user_id(self):
        """Test _create_fallback_member when userId is missing"""
        member = {"role": "member", "joinedAt": "2023-01-01"}  # No userId

        result = self.service._create_fallback_member(member)

        # Should use "unknown" as fallback
        assert result["userId"] == "unknown"
        assert result["user"]["name"] == "User nown"  # Last 4 chars of "unknown"
