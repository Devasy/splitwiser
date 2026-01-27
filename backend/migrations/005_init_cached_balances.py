"""
Initialize Cached Balances Migration
=====================================

This script initializes the cachedBalances field for all existing groups.
It calculates the current balances using the optimized settlement algorithm
and stores them in the group document.

Run this script once to initialize caching:
    python -m migrations.005_init_cached_balances

Expected runtime: Depends on number of groups and settlements
"""

import asyncio
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import logger, settings  # noqa: E402


async def calculate_group_balances(db, group_id: str) -> dict:
    """
    Calculate optimized settlements and convert to per-member balances.

    This is a self-contained version that doesn't rely on ExpenseService.
    """
    settlements_collection = db["settlements"]

    # Get all settlements for the group
    settlements = await settlements_collection.find({"groupId": group_id}).to_list(None)

    if not settlements:
        return {}

    # Calculate net balance for each user (what they owe - what they are owed)
    user_balances = defaultdict(float)
    user_names = {}

    for settlement in settlements:
        payer = settlement["payerId"]
        payee = settlement["payeeId"]
        amount = settlement["amount"]

        user_names[payer] = settlement.get("payerName", payer)
        user_names[payee] = settlement.get("payeeName", payee)

        # payerId = debtor (person who OWES money)
        # payeeId = creditor (person who is OWED money)
        user_balances[payer] += amount  # Payer owes money (positive = debtor)
        user_balances[payee] -= amount  # Payee is owed money (negative = creditor)

    # Separate debtors and creditors
    debtors = []  # (user_id, amount_owed)
    creditors = []  # (user_id, amount_owed_to_them)

    for user_id, balance in user_balances.items():
        if balance > 0.01:
            debtors.append([user_id, balance])
        elif balance < -0.01:
            creditors.append([user_id, -balance])

    # Sort debtors and creditors by amount (descending)
    debtors.sort(key=lambda x: x[1], reverse=True)
    creditors.sort(key=lambda x: x[1], reverse=True)

    # Use two-pointer technique to minimize transactions
    optimized = []
    i, j = 0, 0

    while i < len(debtors) and j < len(creditors):
        debtor_id, debt_amount = debtors[i]
        creditor_id, credit_amount = creditors[j]

        # Settle the minimum
        settlement_amount = min(debt_amount, credit_amount)

        if settlement_amount > 0.01:
            optimized.append(
                {
                    "fromUserId": debtor_id,
                    "toUserId": creditor_id,
                    "amount": round(settlement_amount, 2),
                }
            )

        # Update remaining amounts
        debtors[i][1] -= settlement_amount
        creditors[j][1] -= settlement_amount

        if debtors[i][1] <= 0.01:
            i += 1
        if creditors[j][1] <= 0.01:
            j += 1

    # Convert optimized settlements to per-member balances
    member_balances = defaultdict(float)
    for settlement in optimized:
        # fromUserId owes money (negative balance)
        member_balances[settlement["fromUserId"]] -= settlement["amount"]
        # toUserId is owed money (positive balance)
        member_balances[settlement["toUserId"]] += settlement["amount"]

    return dict(member_balances)


async def init_cached_balances():
    """Initialize cachedBalances for all existing groups."""
    client = None
    try:
        # Connect to MongoDB (URL redacted for security)
        logger.info("Connecting to MongoDB...")
        client = AsyncIOMotorClient(settings.mongodb_url)
        db = client[settings.database_name]
        groups_collection = db["groups"]

        # Find all groups
        total_groups = await groups_collection.count_documents({})
        logger.info(f"Found {total_groups} total groups")

        # Process groups
        updated_count = 0
        skipped_count = 0
        error_count = 0
        cursor = groups_collection.find({})

        async for group in cursor:
            group_id = str(group["_id"])
            group_name = group.get("name", "Unknown")

            try:
                # Check if already has cached balances
                if group.get("cachedBalances") is not None:
                    logger.debug(f"Skipping group {group_name} - already has cache")
                    skipped_count += 1
                    continue

                # Calculate balances
                logger.info(f"Calculating balances for group: {group_name}")
                balances = await calculate_group_balances(db, group_id)

                # Update group document with cached balances
                await groups_collection.update_one(
                    {"_id": group["_id"]},
                    {
                        "$set": {
                            "cachedBalances": balances,
                            "balancesUpdatedAt": datetime.now(timezone.utc),
                        }
                    },
                )

                logger.info(f"  -> Cached {len(balances)} member balances")
                updated_count += 1

            except Exception as e:
                logger.error(f"Failed to process group {group_name}: {e}")
                import traceback

                traceback.print_exc()
                error_count += 1
                continue

        logger.info("=" * 60)
        logger.info("Migration Summary:")
        logger.info(f"  Total groups: {total_groups}")
        logger.info(f"  Updated: {updated_count}")
        logger.info(f"  Skipped (already cached): {skipped_count}")
        logger.info(f"  Errors: {error_count}")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"❌ Migration failed: {str(e)}")
        raise
    finally:
        if client:
            client.close()
            logger.info("Database connection closed")


async def verify_migration():
    """Verify that all groups now have cachedBalances."""
    client = None
    try:
        client = AsyncIOMotorClient(settings.mongodb_url)
        db = client[settings.database_name]
        groups_collection = db["groups"]

        # Count total groups
        total_groups = await groups_collection.count_documents({})

        # Count groups with cachedBalances
        groups_with_cache = await groups_collection.count_documents(
            {"cachedBalances": {"$exists": True, "$ne": None}}
        )

        logger.info(f"\n📊 Verification Results:")
        logger.info(f"   Total groups: {total_groups}")
        logger.info(f"   Groups with cached balances: {groups_with_cache}")

        if total_groups == groups_with_cache:
            logger.info("✅ All groups have cached balances!")
        else:
            logger.warning(
                f"⚠️  {total_groups - groups_with_cache} groups still missing cache"
            )

    except Exception as e:
        logger.error(f"❌ Verification failed: {str(e)}")
        raise
    finally:
        if client:
            client.close()


async def main():
    """Run migration and verification."""
    logger.info("=" * 60)
    logger.info("Starting Cached Balances Migration")
    logger.info("=" * 60)

    await init_cached_balances()
    await verify_migration()

    logger.info("=" * 60)
    logger.info("Migration Complete!")
    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
