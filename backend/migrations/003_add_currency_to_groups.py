"""
Add Currency to Groups Migration
=================================

This script adds a currency field to all existing groups that don't have one.
The default currency is set to USD, which can be updated later by users.

Run this script once to update existing groups:
    python -m migrations.003_add_currency_to_groups

Expected runtime: < 10 seconds for small databases
"""

import asyncio
import sys
from pathlib import Path

from motor.motor_asyncio import AsyncIOMotorClient

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import logger, settings  # noqa: E402


async def add_currency_to_groups():
    """Add currency field to all existing groups without one"""
    client = None
    try:
        # Connect to MongoDB (URL redacted for security)
        logger.info("Connecting to MongoDB...")
        client = AsyncIOMotorClient(settings.mongodb_url)
        db = client[settings.database_name]
        groups_collection = db["groups"]

        # Find groups without currency field or with null currency
        groups_without_currency = await groups_collection.count_documents(
            {"$or": [{"currency": {"$exists": False}}, {"currency": None}]}
        )

        if groups_without_currency == 0:
            logger.info("✅ All groups already have a currency field")
            return

        logger.info(f"Found {groups_without_currency} groups without currency field")
        logger.info("Adding default currency (USD) to these groups...")

        # Update all groups without currency
        result = await groups_collection.update_many(
            {"$or": [{"currency": {"$exists": False}}, {"currency": None}]},
            {"$set": {"currency": "USD"}},
        )

        logger.info(f"✅ Successfully updated {result.modified_count} groups")
        logger.info("Groups now have default currency set to USD")
        logger.info("Users can update their group currencies from the group settings")

    except Exception as e:
        logger.error(f"❌ Migration failed: {str(e)}")
        raise
    finally:
        if client:
            client.close()
            logger.info("Database connection closed")


async def verify_migration():
    """Verify that all groups now have a currency field"""
    client = None
    try:
        client = AsyncIOMotorClient(settings.mongodb_url)
        db = client[settings.database_name]
        groups_collection = db["groups"]

        # Count total groups
        total_groups = await groups_collection.count_documents({})

        # Count groups with currency
        groups_with_currency = await groups_collection.count_documents(
            {"currency": {"$exists": True, "$ne": None}}
        )

        logger.info(f"\n📊 Verification Results:")
        logger.info(f"   Total groups: {total_groups}")
        logger.info(f"   Groups with currency: {groups_with_currency}")

        if total_groups == groups_with_currency:
            logger.info("✅ All groups have currency field!")
        else:
            logger.warning(
                f"⚠️  {total_groups - groups_with_currency} groups still missing currency"
            )

    except Exception as e:
        logger.error(f"❌ Verification failed: {str(e)}")
        raise
    finally:
        if client:
            client.close()


if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("Starting currency migration for groups...")
    logger.info("=" * 60)

    asyncio.run(add_currency_to_groups())

    logger.info("\n" + "=" * 60)
    logger.info("Verifying migration...")
    logger.info("=" * 60)

    asyncio.run(verify_migration())

    logger.info("\n" + "=" * 60)
    logger.info("Migration complete!")
    logger.info("=" * 60)
