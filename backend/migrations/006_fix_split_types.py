"""
Fix Split Types Migration
==========================

This script recalculates the splitType field for all existing expenses.
Many imported expenses were incorrectly marked as "equal" when they were actually "unequal".

Run this script to fix split types:
    python -m migrations.006_fix_split_types

Expected runtime: Depends on number of expenses
"""

import asyncio
import sys
from pathlib import Path

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import logger, settings  # noqa: E402


def detect_split_type(splits: list) -> str:
    """
    Detect whether the expense split is equal or unequal.

    Args:
        splits: List of split dicts with 'amount' (owedShare) for each user

    Returns:
        'equal' if all amounts are the same (within 5 cent tolerance)
        'unequal' otherwise
    """
    if not splits or len(splits) <= 1:
        return "equal"

    amounts = [s.get("amount", 0) for s in splits]
    first_amount = amounts[0]

    # Check if all amounts are equal (within 5 cent tolerance for floating-point precision)
    # This handles rounding issues from 3-way splits like 100/3 = 33.33, 33.33, 33.34
    for amount in amounts[1:]:
        if abs(amount - first_amount) > 0.05:
            return "unequal"

    return "equal"


async def fix_split_types():
    """Fix split types for all existing expenses."""
    client = None
    try:
        # Connect to MongoDB
        logger.info(f"Connecting to MongoDB at {settings.mongodb_url}")
        client = AsyncIOMotorClient(settings.mongodb_url)
        db = client[settings.database_name]
        expenses_collection = db["expenses"]

        # Find all expenses
        total_expenses = await expenses_collection.count_documents({})
        logger.info(f"Found {total_expenses} total expenses")

        # Process expenses
        updated_count = 0
        correct_count = 0
        error_count = 0
        cursor = expenses_collection.find({})

        async for expense in cursor:
            expense_id = str(expense["_id"])
            description = expense.get("description", "Unknown")
            current_split_type = expense.get("splitType", "equal")
            splits = expense.get("splits", [])

            try:
                # Detect correct split type
                correct_split_type = detect_split_type(splits)

                if current_split_type != correct_split_type:
                    # Update expense with correct split type
                    await expenses_collection.update_one(
                        {"_id": expense["_id"]},
                        {"$set": {"splitType": correct_split_type}},
                    )

                    logger.info(
                        f"Updated '{description}' ({expense_id}): "
                        f"{current_split_type} -> {correct_split_type}"
                    )
                    updated_count += 1
                else:
                    correct_count += 1

            except Exception as e:
                logger.error(f"Failed to process expense {description}: {e}")
                error_count += 1
                continue

        logger.info("=" * 60)
        logger.info("Migration Summary:")
        logger.info(f"  Total expenses: {total_expenses}")
        logger.info(f"  Already correct: {correct_count}")
        logger.info(f"  Updated: {updated_count}")
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
    """Verify that split types are now correct."""
    client = None
    try:
        client = AsyncIOMotorClient(settings.mongodb_url)
        db = client[settings.database_name]
        expenses_collection = db["expenses"]

        # Count total expenses
        total_expenses = await expenses_collection.count_documents({})

        # Sample a few to verify
        sample_expenses = await expenses_collection.find({}).limit(10).to_list(None)

        logger.info(f"\n📊 Verification Results:")
        logger.info(f"   Total expenses: {total_expenses}")
        logger.info(f"\n   Sample verification:")

        for expense in sample_expenses:
            splits = expense.get("splits", [])
            current_type = expense.get("splitType", "equal")
            expected_type = detect_split_type(splits)
            match = "✓" if current_type == expected_type else "✗"

            logger.info(
                f"   {match} {expense.get('description')[:30]:30} | "
                f"Type: {current_type:10} | Expected: {expected_type}"
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
    logger.info("Starting Split Type Fix Migration")
    logger.info("=" * 60)

    await fix_split_types()
    await verify_migration()

    logger.info("=" * 60)
    logger.info("Migration Complete!")
    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
