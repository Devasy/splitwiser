"""
Import service for managing data imports from external providers.
"""

import asyncio
import secrets
import string
from datetime import datetime, timezone
from typing import Dict, List, Optional

from app.config import logger
from app.database import get_database, mongodb
from app.expenses.service import expense_service
from app.integrations.schemas import (
    ImportError,
    ImportOptions,
    ImportProvider,
    ImportStatus,
    ImportSummary,
)
from app.integrations.splitwise.client import SplitwiseClient
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase


class ImportService:
    """Service for handling import operations."""

    def __init__(self, db: AsyncIOMotorDatabase):
        """Initialize import service with database connection."""
        self.db = db
        self.import_jobs = db["import_jobs"]
        self.id_mappings = db["splitwise_id_mappings"]
        self.oauth_tokens = db["oauth_tokens"]
        self.users = db["users"]
        self.groups = db["groups"]
        self.expenses = db["expenses"]

    def _generate_join_code(self, length: int = 6) -> str:
        """Generate a random alphanumeric join code for imported groups"""
        characters = string.ascii_uppercase + string.digits
        return "".join(secrets.choice(characters) for _ in range(length))

    def _ensure_string_id(self, id_value) -> str:
        """Convert ObjectId or any ID to string format for consistency."""
        if id_value is None:
            return None
        if isinstance(id_value, ObjectId):
            return str(id_value)
        return str(id_value)

    async def preview_splitwise_import(
        self, user_id: str, api_key: str, consumer_key: str, consumer_secret: str
    ) -> Dict:
        """
        Generate a preview of what will be imported from Splitwise.

        Args:
            user_id: Current Splitwiser user ID
            api_key: Splitwise API key
            consumer_key: Splitwise consumer key
            consumer_secret: Splitwise consumer secret

        Returns:
            Dict with preview information
        """
        try:
            client = SplitwiseClient(
                api_key=api_key,
                consumer_key=consumer_key,
                consumer_secret=consumer_secret,
            )

            # Fetch data for preview
            current_user = client.get_current_user()
            friends = client.get_friends()
            groups = client.get_groups()

            # Transform user data
            splitwise_user = SplitwiseClient.transform_user(current_user)

            # Build detailed group preview list
            group_previews = []
            total_expenses = 0

            for group in groups:
                # Get expenses for this group to count them
                group_expenses = client.get_expenses(group_id=group.getId(), limit=1000)
                expense_count = len(group_expenses)
                total_expenses += expense_count

                # Calculate total amount for the group
                total_amount = sum(float(exp.getCost() or 0) for exp in group_expenses)

                # Get currency from first expense, or default to USD
                currency = "USD"
                if group_expenses:
                    currency = (
                        group_expenses[0].getCurrencyCode()
                        if hasattr(group_expenses[0], "getCurrencyCode")
                        else "USD"
                    )

                group_previews.append(
                    {
                        "splitwiseId": str(group.getId()),
                        "name": group.getName(),
                        "currency": currency,
                        "memberCount": (
                            len(group.getMembers()) if group.getMembers() else 0
                        ),
                        "expenseCount": expense_count,
                        "totalAmount": total_amount,
                        "imageUrl": (
                            getattr(group, "avatar", {}).get("large")
                            if hasattr(group, "avatar")
                            else None
                        ),
                    }
                )

            # Check for warnings
            warnings = []

            # Check if Splitwise account email matches logged-in user (critical validation)
            current_splitwiser_user = await self.users.find_one(
                {"_id": ObjectId(user_id)}
            )
            if current_splitwiser_user:
                logged_in_email = (
                    (current_splitwiser_user.get("email") or "").lower().strip()
                )
                splitwise_email = (splitwise_user.get("email") or "").lower().strip()

                if (
                    logged_in_email
                    and splitwise_email
                    and logged_in_email != splitwise_email
                ):
                    warnings.append(
                        {
                            "type": "email_mismatch",
                            "message": f"Splitwise account ({splitwise_email}) does not match your Splitwiser account ({logged_in_email})",
                            "resolution": "Sign in with the matching account to import your data, or link your accounts first.",
                            "blocking": True,
                        }
                    )

            # Check if email already exists (different user)
            existing_user = await self.users.find_one(
                {"email": splitwise_user["email"]}
            )
            if existing_user and str(existing_user["_id"]) != user_id:
                warnings.append(
                    {
                        "type": "email_conflict",
                        "message": f"Email {splitwise_user['email']} already exists in another account",
                        "resolution": "Will link to existing account if it's yours",
                        "blocking": False,
                    }
                )

            # Estimate duration based on data size
            total_items = len(friends) + len(groups) + total_expenses
            estimated_minutes = max(3, int(total_items / 50))

            return {
                "splitwiseUser": splitwise_user,
                "groups": group_previews,
                "summary": {
                    "groups": len(groups),
                    "expenses": total_expenses,
                    "friends": len(friends),
                },
                "warnings": warnings,
                "estimatedDuration": f"{estimated_minutes}-{estimated_minutes + 2} minutes",
            }
        except Exception as e:
            logger.error(f"Error previewing Splitwise import: {e}")
            raise

    async def start_import(
        self,
        user_id: str,
        provider: ImportProvider,
        api_key: str,
        consumer_key: str,
        consumer_secret: str,
        options: ImportOptions,
    ) -> str:
        """
        Start an import job.

        Args:
            user_id: Current Splitwiser user ID
            provider: Import provider
            api_key: API key
            consumer_key: Consumer key
            consumer_secret: Consumer secret
            options: Import options

        Returns:
            Import job ID
        """
        # Create import job
        import_job = {
            "userId": ObjectId(user_id),
            "provider": provider.value,
            "status": ImportStatus.PENDING.value,
            "options": options.dict(),
            "startedAt": datetime.now(timezone.utc),
            "completedAt": None,
            "checkpoints": {
                "userImported": False,
                "friendsImported": False,
                "groupsImported": {"completed": 0, "total": 0},
                "expensesImported": {"completed": 0, "total": 0},
            },
            "errors": [],
            "summary": {
                "usersCreated": 0,
                "groupsCreated": 0,
                "expensesCreated": 0,
                "commentsImported": 0,
                "settlementsCreated": 0,
                "receiptsMigrated": 0,
            },
        }

        result = await self.import_jobs.insert_one(import_job)
        import_job_id = str(result.inserted_id)

        # Store OAuth token (encrypted in production)
        await self.oauth_tokens.insert_one(
            {
                "userId": ObjectId(user_id),
                "provider": provider.value,
                "apiKey": api_key,  # Should be encrypted
                "consumerKey": consumer_key,
                "consumerSecret": consumer_secret,
                "importJobId": ObjectId(import_job_id),
                "createdAt": datetime.now(timezone.utc),
            }
        )

        # Start import in background (use Celery in production)
        asyncio.create_task(
            self._perform_import(
                import_job_id, user_id, api_key, consumer_key, consumer_secret, options
            )
        )

        return import_job_id

    async def _perform_import(
        self,
        import_job_id: str,
        user_id: str,
        api_key: str,
        consumer_key: str,
        consumer_secret: str,
        options: ImportOptions,
    ):
        """Perform the actual import operation."""
        try:
            # Update status to in progress
            await self.import_jobs.update_one(
                {"_id": ObjectId(import_job_id)},
                {"$set": {"status": ImportStatus.IN_PROGRESS.value}},
            )

            client = SplitwiseClient(api_key, consumer_key, consumer_secret)

            # Step 1: Import current user
            logger.info(f"Importing user for job {import_job_id}")
            current_user = client.get_current_user()
            user_data = SplitwiseClient.transform_user(current_user)
            # Update existing user with Splitwise ID
            await self.users.update_one(
                {"_id": ObjectId(user_id)},
                {
                    "$set": {
                        "splitwiseId": user_data["splitwiseId"],
                        "importedFrom": "splitwise",
                        "importedAt": datetime.now(timezone.utc),
                    }
                },
            )
            await self._update_checkpoint(import_job_id, "userImported", True)

            # Merge any existing placeholders for this Splitwise ID
            splitwise_id = user_data["splitwiseId"]
            placeholders = (
                await self.db["users"]
                .find(
                    {
                        "splitwiseId": splitwise_id,
                        "isPlaceholder": True,
                        "_id": {"$ne": ObjectId(user_id)},
                    }
                )
                .to_list(None)
            )

            if placeholders:
                logger.info(
                    f"Merging {len(placeholders)} placeholders for Splitwise ID {splitwise_id} into user {user_id}"
                )
                for p in placeholders:
                    p_id_str = str(p["_id"])

                    # Update groups where placeholder is a member
                    await self.db["groups"].update_many(
                        {"members.userId": p_id_str},
                        {
                            "$set": {
                                "members.$.userId": user_id,
                                "members.$.isPlaceholder": False,
                            }
                        },
                    )

                    # Update groups created by placeholder
                    await self.db["groups"].update_many(
                        {"createdBy": p_id_str}, {"$set": {"createdBy": user_id}}
                    )

                    # Update expenses created by placeholder
                    await self.db["expenses"].update_many(
                        {"createdBy": p_id_str}, {"$set": {"createdBy": user_id}}
                    )

                    # Update expenses paid by placeholder
                    await self.db["expenses"].update_many(
                        {"paidBy": p_id_str}, {"$set": {"paidBy": user_id}}
                    )

                    # Update expense splits for placeholder
                    await self.db["expenses"].update_many(
                        {"splits.userId": p_id_str},
                        {"$set": {"splits.$.userId": user_id}},
                    )

                    # Update settlements where placeholder is payer or payee
                    await self.db["settlements"].update_many(
                        {"payerId": p_id_str}, {"$set": {"payerId": user_id}}
                    )
                    await self.db["settlements"].update_many(
                        {"payeeId": p_id_str}, {"$set": {"payeeId": user_id}}
                    )

                    # Delete the placeholder user
                    await self.db["users"].delete_one({"_id": p["_id"]})

            # Create ID mapping for the importing user so they can be found during group import
            await self.id_mappings.insert_one(
                {
                    "importJobId": ObjectId(import_job_id),
                    "entityType": "user",
                    "splitwiseId": user_data["splitwiseId"],
                    "splitwiserId": user_id,  # The current user's ID (already a string)
                    "createdAt": datetime.now(timezone.utc),
                }
            )

            # Step 2: Import friends
            logger.info(f"Importing friends for job {import_job_id}")
            friends = client.get_friends()
            await self._import_friends(import_job_id, user_id, friends)
            await self._update_checkpoint(import_job_id, "friendsImported", True)

            # Step 3: Import groups
            logger.info(f"Importing groups for job {import_job_id}")
            groups = client.get_groups()

            # Filter groups if specific ones were selected
            if options.selectedGroupIds:
                selected_ids = set(options.selectedGroupIds)
                groups = [g for g in groups if str(g.getId()) in selected_ids]
                logger.info(f"Filtered to {len(groups)} selected groups")

            await self._import_groups(import_job_id, user_id, groups)

            # Step 4: Import expenses
            logger.info(f"Importing expenses for job {import_job_id}")
            await self._import_expenses(import_job_id, user_id, client, options)

            # Mark as completed
            await self.import_jobs.update_one(
                {"_id": ObjectId(import_job_id)},
                {
                    "$set": {
                        "status": ImportStatus.COMPLETED.value,
                        "completedAt": datetime.now(timezone.utc),
                    }
                },
            )

            logger.info(f"Import job {import_job_id} completed successfully")

        except Exception as e:
            logger.error(f"Error in import job {import_job_id}: {e}")
            await self._record_error(import_job_id, "import_failed", str(e))
            await self.import_jobs.update_one(
                {"_id": ObjectId(import_job_id)},
                {"$set": {"status": ImportStatus.FAILED.value}},
            )

    async def _import_friends(self, import_job_id: str, user_id: str, friends: List):
        """Import friends as users."""
        for friend in friends:
            try:
                friend_data = SplitwiseClient.transform_friend(friend)

                # Check if user already exists
                existing = await self.users.find_one({"email": friend_data["email"]})

                if not existing:
                    # Create new user
                    friend_data["_id"] = ObjectId()
                    friend_data["passwordHash"] = None  # No password for imported users
                    await self.users.insert_one(friend_data)

                    # Store mapping
                    await self.id_mappings.insert_one(
                        {
                            "importJobId": ObjectId(import_job_id),
                            "entityType": "user",
                            "splitwiseId": friend_data["splitwiseId"],
                            "splitwiserId": str(friend_data["_id"]),
                            "createdAt": datetime.now(timezone.utc),
                        }
                    )

                    await self._increment_summary(import_job_id, "usersCreated")
                else:
                    # Update existing with Splitwise ID
                    await self.users.update_one(
                        {"_id": existing["_id"]},
                        {"$set": {"splitwiseId": friend_data["splitwiseId"]}},
                    )

                    # Store mapping
                    await self.id_mappings.insert_one(
                        {
                            "importJobId": ObjectId(import_job_id),
                            "entityType": "user",
                            "splitwiseId": friend_data["splitwiseId"],
                            "splitwiserId": str(existing["_id"]),
                            "createdAt": datetime.now(timezone.utc),
                        }
                    )

            except Exception as e:
                await self._record_error(import_job_id, "friend_import", str(e))

    async def _import_groups(self, import_job_id: str, user_id: str, groups: List):
        """Import groups with all members including unregistered ones."""
        for group in groups:
            try:
                group_data = SplitwiseClient.transform_group(group)

                # Map member IDs - include ALL members (registered and unregistered)
                mapped_members = []
                for member in group_data["members"]:
                    # Check if member is already mapped (friend that was imported)
                    mapping = await self.id_mappings.find_one(
                        {
                            "importJobId": ObjectId(import_job_id),
                            "entityType": "user",
                            "splitwiseId": member["splitwiseUserId"],
                        }
                    )

                    if mapping:
                        # Registered user - use their Splitwiser ID as string
                        # All members are admins since Splitwise has no member/admin roles
                        mapped_members.append(
                            {
                                "userId": self._ensure_string_id(
                                    mapping["splitwiserId"]
                                ),
                                "role": "admin",  # All Splitwise members are admins
                                "joinedAt": datetime.now(timezone.utc),
                                "isPlaceholder": False,
                            }
                        )
                    else:
                        # Unregistered user - check if they already exist by email or Splitwise ID
                        existing_user = None

                        # First check by email (if available)
                        if member.get("email"):
                            existing_user = await self.users.find_one(
                                {"email": member["email"]}
                            )

                        # If not found by email, check by Splitwise ID
                        if not existing_user:
                            existing_user = await self.users.find_one(
                                {"splitwiseId": member["splitwiseUserId"]}
                            )

                        if existing_user:
                            # User exists - create mapping and use their ID as string
                            existing_user_id = str(existing_user["_id"])

                            # Create mapping
                            await self.id_mappings.insert_one(
                                {
                                    "importJobId": ObjectId(import_job_id),
                                    "entityType": "user",
                                    "splitwiseId": member["splitwiseUserId"],
                                    "splitwiserId": existing_user_id,
                                    "createdAt": datetime.now(timezone.utc),
                                }
                            )

                            mapped_members.append(
                                {
                                    "userId": self._ensure_string_id(existing_user_id),
                                    "role": "admin",  # All Splitwise members are admins
                                    "joinedAt": datetime.now(timezone.utc),
                                    "isPlaceholder": existing_user.get(
                                        "isPlaceholder", False
                                    ),
                                }
                            )
                        else:
                            # Create placeholder user
                            placeholder_id = ObjectId()
                            placeholder_user = {
                                "_id": placeholder_id,
                                "name": member.get("name", "Unknown User"),
                                "email": member.get(
                                    "email"
                                ),  # Email for future mapping
                                "imageUrl": member.get("imageUrl"),
                                "splitwiseId": member["splitwiseUserId"],
                                "isPlaceholder": True,  # Mark as placeholder
                                "passwordHash": None,
                                "createdAt": datetime.now(timezone.utc),
                                "importedFrom": "splitwise",
                                "importedAt": datetime.now(timezone.utc),
                            }

                            # Insert placeholder user
                            await self.users.insert_one(placeholder_user)

                            # Create mapping for placeholder
                            await self.id_mappings.insert_one(
                                {
                                    "importJobId": ObjectId(import_job_id),
                                    "entityType": "user",
                                    "splitwiseId": member["splitwiseUserId"],
                                    "splitwiserId": str(placeholder_id),
                                    "createdAt": datetime.now(timezone.utc),
                                }
                            )

                            mapped_members.append(
                                {
                                    "userId": self._ensure_string_id(placeholder_id),
                                    "role": "admin",  # All Splitwise members are admins
                                    "joinedAt": datetime.now(timezone.utc),
                                    "isPlaceholder": True,
                                }
                            )

                # Ensure the importing user is always in the members array as admin
                importing_user_ids = [m["userId"] for m in mapped_members]
                if user_id not in importing_user_ids:
                    # Add importing user as admin if not already in members
                    mapped_members.insert(
                        0,
                        {
                            "userId": user_id,
                            "role": "admin",
                            "joinedAt": datetime.now(timezone.utc),
                            "isPlaceholder": False,
                        },
                    )

                # Check if group already exists for this user (imported previously)
                existing_group = await self.groups.find_one(
                    {
                        "splitwiseGroupId": group_data["splitwiseGroupId"],
                        "members.userId": user_id,
                    }
                )

                if existing_group:
                    logger.info(
                        f"Group {group_data['name']} already imported as {existing_group['_id']}, reusing."
                    )
                    # Store mapping for this job so expenses can be linked
                    await self.id_mappings.insert_one(
                        {
                            "importJobId": ObjectId(import_job_id),
                            "entityType": "group",
                            "splitwiseId": group_data["splitwiseGroupId"],
                            "splitwiserId": str(existing_group["_id"]),
                            "createdAt": datetime.now(timezone.utc),
                        }
                    )

                    # Update existing group metadata (e.g. currency if it changed/was default)
                    await self.groups.update_one(
                        {"_id": existing_group["_id"]},
                        {
                            "$set": {
                                "currency": group_data["currency"],
                                "isDeleted": False,  # Reactivate group if it was deleted
                                "archived": False,  # Unarchive if it was archived
                                "updatedAt": datetime.now(timezone.utc),
                            }
                        },
                    )

                    await self._increment_summary(import_job_id, "groupsCreated")
                    await self._update_checkpoint(
                        import_job_id, "groupsImported.completed", 1, increment=True
                    )
                    continue

                # Create group
                # Generate join code for imported group
                join_code = self._generate_join_code()

                new_group = {
                    "_id": ObjectId(),
                    "name": group_data["name"],
                    "currency": group_data["currency"],
                    "imageUrl": group_data["imageUrl"],
                    "createdBy": user_id,  # Use string format for consistency
                    "members": mapped_members,
                    "joinCode": join_code,
                    "splitwiseGroupId": group_data["splitwiseGroupId"],
                    "importedFrom": "splitwise",
                    "importedAt": datetime.now(timezone.utc),
                    "createdAt": datetime.now(timezone.utc),
                    "updatedAt": datetime.now(timezone.utc),
                }

                await self.groups.insert_one(new_group)

                # Store mapping
                await self.id_mappings.insert_one(
                    {
                        "importJobId": ObjectId(import_job_id),
                        "entityType": "group",
                        "splitwiseId": group_data["splitwiseGroupId"],
                        "splitwiserId": str(new_group["_id"]),
                        "createdAt": datetime.now(timezone.utc),
                    }
                )

                await self._increment_summary(import_job_id, "groupsCreated")
                await self._update_checkpoint(
                    import_job_id, "groupsImported.completed", 1, increment=True
                )

            except Exception as e:
                await self._record_error(import_job_id, "group_import", str(e))

    async def _import_expenses(
        self,
        import_job_id: str,
        user_id: str,
        client: SplitwiseClient,
        options: ImportOptions,
    ):
        """Import expenses."""
        # Get all expenses
        all_expenses = client.get_expenses(limit=1000)

        await self._update_checkpoint(
            import_job_id, "expensesImported.total", len(all_expenses)
        )

        for expense in all_expenses:
            try:
                # Skip deleted expenses if option is set
                if not options.importArchivedExpenses:
                    deleted_at = (
                        expense.getDeletedAt()
                        if hasattr(expense, "getDeletedAt")
                        else None
                    )
                    if deleted_at:
                        continue

                expense_data = SplitwiseClient.transform_expense(expense)

                # Map group ID
                group_mapping = await self.id_mappings.find_one(
                    {
                        "importJobId": ObjectId(import_job_id),
                        "entityType": "group",
                        "splitwiseId": expense_data["groupId"],
                    }
                )

                if not group_mapping:
                    continue  # Skip if group not found

                # Check if expense already exists in Splitwiser
                existing_expense = await self.expenses.find_one(
                    {
                        "splitwiseExpenseId": expense_data["splitwiseExpenseId"],
                        "groupId": group_mapping["splitwiserId"],
                    }
                )

                if existing_expense:
                    # Store mapping for this job so dependent entities (if any) can be linked
                    await self.id_mappings.insert_one(
                        {
                            "importJobId": ObjectId(import_job_id),
                            "entityType": "expense",
                            "splitwiseId": expense_data["splitwiseExpenseId"],
                            "splitwiserId": str(existing_expense["_id"]),
                            "createdAt": datetime.now(timezone.utc),
                        }
                    )

                    # Update existing expense currency if needed
                    await self.expenses.update_one(
                        {"_id": existing_expense["_id"]},
                        {
                            "$set": {
                                "currency": expense_data.get("currency", "USD"),
                                "updatedAt": datetime.now(timezone.utc),
                            }
                        },
                    )

                    # We still increment summary to show progress
                    await self._increment_summary(import_job_id, "expensesCreated")
                    continue

                # UNIFIED APPROACH: Use userShares to create settlements
                # For EVERY expense (including payments), each user has:
                #   netEffect = paidShare - owedShare
                #   Positive = they are owed money (creditor)
                #   Negative = they owe money (debtor)

                user_shares = expense_data.get("userShares", [])

                if not user_shares:
                    # Fallback: skip if no user shares data
                    logger.warning(
                        f"Expense {expense_data['splitwiseExpenseId']} has no userShares, skipping"
                    )
                    await self._update_checkpoint(
                        import_job_id, "expensesImported.completed", 1, increment=True
                    )
                    continue

                # Map Splitwise user IDs to Splitwiser user IDs
                mapped_shares = []
                for share in user_shares:
                    sw_user_id = share["userId"]
                    mapping = await self.id_mappings.find_one(
                        {
                            "importJobId": ObjectId(import_job_id),
                            "entityType": "user",
                            "splitwiseId": sw_user_id,
                        }
                    )
                    if mapping:
                        mapped_shares.append(
                            {
                                "userId": mapping["splitwiserId"],
                                "userName": share["userName"],
                                "paidShare": share["paidShare"],
                                "owedShare": share["owedShare"],
                                "netEffect": share["netEffect"],
                            }
                        )

                # Separate into creditors (positive netEffect) and debtors (negative netEffect)
                creditors = [
                    (s["userId"], s["userName"], s["netEffect"])
                    for s in mapped_shares
                    if s["netEffect"] > 0.01
                ]
                debtors = [
                    (s["userId"], s["userName"], -s["netEffect"])
                    for s in mapped_shares
                    if s["netEffect"] < -0.01
                ]

                # Create expense record
                payer_id = creditors[0][0] if creditors else user_id
                new_expense = {
                    "_id": ObjectId(),
                    "groupId": group_mapping["splitwiserId"],
                    "createdBy": user_id,
                    "paidBy": payer_id,
                    "description": expense_data["description"],
                    "amount": expense_data["amount"],
                    "splits": [
                        {
                            "userId": s["userId"],
                            "amount": s["owedShare"],
                            "userName": s["userName"],
                        }
                        for s in mapped_shares
                        if s["owedShare"] > 0
                    ],
                    "splitType": expense_data["splitType"],
                    "tags": [
                        t for t in (expense_data.get("tags") or []) if t is not None
                    ],
                    "receiptUrls": (
                        [
                            r
                            for r in (expense_data.get("receiptUrls") or [])
                            if r is not None
                        ]
                        if options.importReceipts
                        else []
                    ),
                    "comments": [],
                    "history": [],
                    "currency": expense_data.get("currency", "USD"),
                    "splitwiseExpenseId": expense_data["splitwiseExpenseId"],
                    "isPayment": expense_data.get("isPayment", False),
                    "importedFrom": "splitwise",
                    "importedAt": datetime.now(timezone.utc),
                    "updatedAt": datetime.now(timezone.utc),
                    "createdAt": (
                        datetime.fromisoformat(
                            expense_data["date"].replace("Z", "+00:00")
                        )
                        if expense_data.get("date")
                        else datetime.now(timezone.utc)
                    ),
                }

                await self.expenses.insert_one(new_expense)

                # Create settlements: each debtor owes each creditor proportionally
                # For simplicity, we match debtors to creditors in order (greedy approach)
                creditor_idx = 0
                remaining_credit = list(creditors)  # Make mutable copy

                for debtor_id, debtor_name, debt_amount in debtors:
                    remaining_debt = debt_amount

                    while remaining_debt > 0.01 and creditor_idx < len(
                        remaining_credit
                    ):
                        creditor_id, creditor_name, credit = remaining_credit[
                            creditor_idx
                        ]

                        # Match the minimum of debt and credit
                        settlement_amount = min(remaining_debt, credit)

                        if settlement_amount > 0.01:
                            settlement_doc = {
                                "_id": ObjectId(),
                                "expenseId": str(new_expense["_id"]),
                                "groupId": group_mapping["splitwiserId"],
                                # payerId = debtor (person who OWES), payeeId = creditor (person OWED)
                                "payerId": debtor_id,
                                "payeeId": creditor_id,
                                "amount": round(settlement_amount, 2),
                                "currency": expense_data.get("currency", "USD"),
                                "payerName": debtor_name,
                                "payeeName": creditor_name,
                                "status": "pending",
                                "description": f"Share for {expense_data['description']}",
                                "createdAt": datetime.now(timezone.utc),
                                "importedFrom": "splitwise",
                                "importedAt": datetime.now(timezone.utc),
                            }

                            await self.db["settlements"].insert_one(settlement_doc)
                            await self._increment_summary(
                                import_job_id, "settlementsCreated"
                            )

                        remaining_debt -= settlement_amount
                        remaining_credit[creditor_idx] = (
                            creditor_id,
                            creditor_name,
                            credit - settlement_amount,
                        )

                        if remaining_credit[creditor_idx][2] < 0.01:
                            creditor_idx += 1

                await self._increment_summary(import_job_id, "expensesCreated")
                await self._update_checkpoint(
                    import_job_id, "expensesImported.completed", 1, increment=True
                )

            except Exception as e:
                await self._record_error(import_job_id, "expense_import", str(e))

    async def _update_checkpoint(
        self, import_job_id: str, field: str, value, increment: bool = False
    ):
        """Update checkpoint status."""
        update = {}
        if increment:
            update = {"$inc": {f"checkpoints.{field}": value}}
        else:
            update = {"$set": {f"checkpoints.{field}": value}}

        await self.import_jobs.update_one({"_id": ObjectId(import_job_id)}, update)

    async def _increment_summary(
        self, import_job_id: str, field: str, increment_by: int = 1
    ):
        """Increment summary counter."""
        await self.import_jobs.update_one(
            {"_id": ObjectId(import_job_id)},
            {"$inc": {f"summary.{field}": increment_by}},
        )

    async def _record_error(
        self, import_job_id: str, error_type: str, message: str, blocking: bool = False
    ):
        """Record an error that occurred during import."""
        error = {
            "stage": error_type,  # Using 'stage' to match schema
            "message": message,
            "blocking": blocking,
            "timestamp": datetime.now(timezone.utc),
        }

        await self.import_jobs.update_one(
            {"_id": ObjectId(import_job_id)}, {"$push": {"errors": error}}
        )

    async def get_import_status(self, import_job_id: str) -> Optional[Dict]:
        """Get status of an import job."""
        job = await self.import_jobs.find_one({"_id": ObjectId(import_job_id)})
        if job:
            job["_id"] = str(job["_id"])
            job["userId"] = str(job["userId"])
        return job

    async def rollback_import(self, import_job_id: str) -> Dict:
        """Rollback an import by deleting all imported data."""
        try:
            # Get all mappings
            mappings = await self.id_mappings.find(
                {"importJobId": ObjectId(import_job_id)}
            ).to_list(None)

            deleted_counts = {"users": 0, "groups": 0, "expenses": 0}

            # Delete in reverse order
            for mapping in mappings:
                entity_id = ObjectId(mapping["splitwiserId"])

                if mapping["entityType"] == "expense":
                    await self.expenses.delete_one({"_id": entity_id})
                    deleted_counts["expenses"] += 1
                elif mapping["entityType"] == "group":
                    await self.groups.delete_one({"_id": entity_id})
                    deleted_counts["groups"] += 1
                elif mapping["entityType"] == "user":
                    await self.users.delete_one({"_id": entity_id})
                    deleted_counts["users"] += 1

            # Delete mappings
            await self.id_mappings.delete_many({"importJobId": ObjectId(import_job_id)})

            # Update job status
            await self.import_jobs.update_one(
                {"_id": ObjectId(import_job_id)},
                {"$set": {"status": ImportStatus.ROLLED_BACK.value}},
            )

            return {
                "success": True,
                "message": "Import rolled back successfully",
                "deletedRecords": deleted_counts,
            }

        except Exception as e:
            logger.error(f"Error rolling back import {import_job_id}: {e}")
            return {
                "success": False,
                "message": f"Rollback failed: {str(e)}",
                "deletedRecords": {},
            }
