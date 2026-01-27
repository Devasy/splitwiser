"""
Import service for managing data imports from external providers.
"""

import asyncio
import secrets
import string
from datetime import datetime, timezone
from typing import Dict, List, Optional

from app.config import logger
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

            # Check if email already exists
            existing_user = await self.users.find_one(
                {"email": splitwise_user["email"]}
            )
            if existing_user and str(existing_user["_id"]) != user_id:
                warnings.append(
                    {
                        "type": "email_conflict",
                        "message": f"Email {splitwise_user['email']} already exists",
                        "resolution": "Will link to existing account",
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

            # Create ID mapping for the importing user so they can be found during expense import
            # This is critical - without this mapping, expenses paid by the importing user won't be imported
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

            await self._import_groups(
                import_job_id, user_id, user_data["splitwiseId"], groups
            )

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

    async def _import_groups(
        self, import_job_id: str, user_id: str, user_splitwise_id: str, groups: List
    ):
        """Import groups with all members including unregistered ones.

        Args:
            import_job_id: The import job ID
            user_id: The Splitwiser user ID (MongoDB ObjectId as string)
            user_splitwise_id: The importing user's Splitwise ID
            groups: List of Splitwise group objects
        """
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
                        # Check if this is the importing user by comparing Splitwise IDs
                        is_importing_user = str(member["splitwiseUserId"]) == str(
                            user_splitwise_id
                        )
                        mapped_members.append(
                            {
                                "userId": mapping[
                                    "splitwiserId"
                                ],  # Already a string from mapping
                                "role": "admin" if is_importing_user else "member",
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
                                    "userId": existing_user_id,  # String format
                                    "role": "member",
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
                                    "userId": str(
                                        placeholder_id
                                    ),  # Convert ObjectId to string
                                    "role": "member",
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
        logger.info(
            f"Fetched {len(all_expenses)} expenses from Splitwise for job {import_job_id}"
        )

        await self._update_checkpoint(
            import_job_id, "expensesImported.total", len(all_expenses)
        )

        imported_count = 0
        skipped_count = 0
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
                    skipped_count += 1
                    logger.debug(
                        f"Skipping expense {expense_data.get('splitwiseExpenseId')} - no group mapping for group {expense_data.get('groupId')}"
                    )
                    continue  # Skip if group not found

                # Map user IDs in splits
                mapped_splits = []
                for split in expense_data["splits"]:
                    user_mapping = await self.id_mappings.find_one(
                        {
                            "importJobId": ObjectId(import_job_id),
                            "entityType": "user",
                            "splitwiseId": split["splitwiseUserId"],
                        }
                    )

                    if user_mapping:
                        mapped_splits.append(
                            {
                                "userId": user_mapping["splitwiserId"],
                                "amount": split["amount"],
                                "type": split["type"],
                            }
                        )

                # Map paidBy user ID
                paid_by_mapping = await self.id_mappings.find_one(
                    {
                        "importJobId": ObjectId(import_job_id),
                        "entityType": "user",
                        "splitwiseId": expense_data["paidBy"],
                    }
                )

                # Create expense
                new_expense = {
                    "_id": ObjectId(),
                    "groupId": group_mapping[
                        "splitwiserId"
                    ],  # String format for consistency
                    "createdBy": user_id,  # String format
                    "paidBy": (
                        paid_by_mapping["splitwiserId"] if paid_by_mapping else user_id
                    ),
                    "description": expense_data["description"],
                    "amount": expense_data["amount"],
                    "currency": expense_data.get("currency", "USD"),
                    "splits": mapped_splits,
                    "splitType": expense_data["splitType"],
                    "tags": expense_data.get("tags") or [],
                    "receiptUrls": (
                        expense_data.get("receiptUrls") or []
                        if options.importReceipts
                        else []
                    ),
                    "comments": [],
                    "history": [],
                    "splitwiseExpenseId": expense_data["splitwiseExpenseId"],
                    "importedFrom": "splitwise",
                    "importedAt": datetime.now(timezone.utc),
                    "createdAt": (
                        datetime.fromisoformat(
                            expense_data["createdAt"].replace("Z", "+00:00")
                        )
                        if expense_data.get("createdAt")
                        else datetime.now(timezone.utc)
                    ),
                    "updatedAt": datetime.now(timezone.utc),
                }

                await self.expenses.insert_one(new_expense)

                # Store mapping
                await self.id_mappings.insert_one(
                    {
                        "importJobId": ObjectId(import_job_id),
                        "entityType": "expense",
                        "splitwiseId": expense_data["splitwiseExpenseId"],
                        "splitwiserId": str(new_expense["_id"]),
                        "createdAt": datetime.now(timezone.utc),
                    }
                )

                await self._increment_summary(import_job_id, "expensesCreated")
                await self._update_checkpoint(
                    import_job_id, "expensesImported.completed", 1, increment=True
                )

                imported_count += 1

            except Exception as e:
                logger.error(f"Error importing expense: {e}")
                await self._record_error(import_job_id, "expense_import", str(e))

        logger.info(
            f"Import completed: {imported_count} expenses imported, {skipped_count} skipped for job {import_job_id}"
        )

    async def _update_checkpoint(
        self, import_job_id: str, field: str, value, increment: bool = False
    ):
        """Update import checkpoint."""
        if increment:
            await self.import_jobs.update_one(
                {"_id": ObjectId(import_job_id)},
                {"$inc": {f"checkpoints.{field}": value}},
            )
        else:
            await self.import_jobs.update_one(
                {"_id": ObjectId(import_job_id)},
                {"$set": {f"checkpoints.{field}": value}},
            )

    async def _increment_summary(self, import_job_id: str, field: str):
        """Increment summary counter."""
        await self.import_jobs.update_one(
            {"_id": ObjectId(import_job_id)}, {"$inc": {f"summary.{field}": 1}}
        )

    async def _record_error(self, import_job_id: str, stage: str, message: str):
        """Record an import error."""
        error = {
            "stage": stage,
            "message": message,
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
