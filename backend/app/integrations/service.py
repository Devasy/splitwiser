"""
Import service for managing data imports from external providers.
"""

import asyncio
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

            # Count expenses (without fetching all)
            sample_expenses = client.get_expenses(limit=10)

            # Transform user data
            splitwise_user = SplitwiseClient.transform_user(current_user)

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
            total_items = (
                len(friends) + len(groups) + (len(sample_expenses) * 10)
            )  # Rough estimate
            estimated_minutes = max(3, int(total_items / 100))

            return {
                "splitwiseUser": splitwise_user,
                "summary": {
                    "groups": len(groups),
                    "expenses": len(sample_expenses) * 10,  # Rough estimate
                    "friends": len(friends),
                    "estimatedDuration": f"{estimated_minutes}-{estimated_minutes + 2} minutes",
                },
                "warnings": warnings,
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

            # Step 2: Import friends
            logger.info(f"Importing friends for job {import_job_id}")
            friends = client.get_friends()
            await self._import_friends(import_job_id, user_id, friends)
            await self._update_checkpoint(import_job_id, "friendsImported", True)

            # Step 3: Import groups
            logger.info(f"Importing groups for job {import_job_id}")
            groups = client.get_groups()
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
        """Import groups."""
        for group in groups:
            try:
                group_data = SplitwiseClient.transform_group(group)

                # Map member IDs to Splitwiser user IDs
                mapped_members = []
                for member in group_data["members"]:
                    mapping = await self.id_mappings.find_one(
                        {
                            "importJobId": ObjectId(import_job_id),
                            "entityType": "user",
                            "splitwiseId": member["splitwiseUserId"],
                        }
                    )

                    if mapping:
                        mapped_members.append(
                            {
                                "userId": ObjectId(mapping["splitwiserId"]),
                                "role": (
                                    "admin" if member["userId"] == user_id else "member"
                                ),
                                "joinedAt": datetime.now(timezone.utc),
                            }
                        )

                # Create group
                new_group = {
                    "_id": ObjectId(),
                    "name": group_data["name"],
                    "currency": group_data["currency"],
                    "imageUrl": group_data["imageUrl"],
                    "createdBy": ObjectId(user_id),
                    "members": mapped_members,
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
                    "groupId": ObjectId(group_mapping["splitwiserId"]),
                    "createdBy": ObjectId(user_id),
                    "paidBy": (
                        paid_by_mapping["splitwiserId"] if paid_by_mapping else user_id
                    ),
                    "description": expense_data["description"],
                    "amount": expense_data["amount"],
                    "splits": mapped_splits,
                    "splitType": expense_data["splitType"],
                    "tags": expense_data["tags"],
                    "receiptUrls": (
                        expense_data["receiptUrls"] if options.importReceipts else []
                    ),
                    "comments": [],
                    "history": [],
                    "splitwiseExpenseId": expense_data["splitwiseExpenseId"],
                    "importedFrom": "splitwise",
                    "importedAt": datetime.now(timezone.utc),
                    "createdAt": (
                        datetime.fromisoformat(expense_data["createdAt"])
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

            except Exception as e:
                await self._record_error(import_job_id, "expense_import", str(e))

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
