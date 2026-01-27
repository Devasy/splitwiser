"""
Fix Member userId Format and Missing Fields Migration
======================================================

This script:
1. Converts members.userId from ObjectId to string format
2. Converts createdBy from ObjectId to string format
3. Adds missing joinedAt field to members

Run this script once to update existing groups:
    python -m migrations.004_fix_member_userid_format

Expected runtime: < 10 seconds for small databases
"""

import asyncio
import sys
from datetime import datetime, timezone
from pathlib import Path

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import logger, settings  # noqa: E402


async def fix_member_userid_format():
    """Convert members.userId from ObjectId to string and add missing fields"""
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

        # Process groups in batches
        updated_count = 0
        cursor = groups_collection.find({})

        async for group in cursor:
            needs_update = False
            updated_members = []

            # Check if createdBy needs conversion
            created_by = group.get("createdBy")
            new_created_by = created_by
            if isinstance(created_by, ObjectId):
                new_created_by = str(created_by)
                needs_update = True

            # Check each member for ObjectId userId or missing joinedAt
            for member in group.get("members", []):
                user_id = member.get("userId")
                joined_at = member.get("joinedAt")

                # Convert ObjectId to string
                if isinstance(user_id, ObjectId):
                    user_id = str(user_id)
                    needs_update = True

                # Add joinedAt if missing
                if joined_at is None:
                    joined_at = group.get("createdAt", datetime.now(timezone.utc))
                    needs_update = True

                # Preserve all existing member fields, only override normalized ones
                updated_member = dict(member)  # Shallow copy to preserve all fields
                updated_member["userId"] = user_id
                updated_member["joinedAt"] = joined_at
                updated_members.append(updated_member)

            # Update if needed
            if needs_update:
                update_doc = {"members": updated_members}
                if new_created_by != created_by:
                    update_doc["createdBy"] = new_created_by

                await groups_collection.update_one(
                    {"_id": group["_id"]}, {"$set": update_doc}
                )
                updated_count += 1
                logger.info(
                    f"Updated group: {group.get('name', 'Unknown')} (ID: {group['_id']})"
                )

        logger.info(f"✅ Successfully updated {updated_count} groups")
        logger.info(
            f"✅ {total_groups - updated_count} groups already had correct format"
        )

    except Exception as e:
        logger.error(f"❌ Migration failed: {str(e)}")
        raise
    finally:
        if client:
            client.close()
            logger.info("Database connection closed")


async def verify_migration():
    """Verify that all groups now have string userId format"""
    client = None
    try:
        client = AsyncIOMotorClient(settings.mongodb_url)
        db = client[settings.database_name]
        groups_collection = db["groups"]

        # Count total groups
        total_groups = await groups_collection.count_documents({})

        # Check for any remaining ObjectId format
        groups_with_objectid = 0
        cursor = groups_collection.find({})

        async for group in cursor:
            for member in group.get("members", []):
                if isinstance(member.get("userId"), ObjectId):
                    groups_with_objectid += 1
                    logger.warning(
                        f"⚠️  Group still has ObjectId: {group.get('name')} (ID: {group['_id']})"
                    )
                    break

        logger.info(f"\n📊 Verification Results:")
        logger.info(f"   Total groups: {total_groups}")
        logger.info(f"   Groups with ObjectId format: {groups_with_objectid}")
        logger.info(
            f"   Groups with string format: {total_groups - groups_with_objectid}"
        )

        if groups_with_objectid == 0:
            logger.info("✅ All groups have correct string userId format!")
        else:
            logger.warning(
                f"⚠️  {groups_with_objectid} groups still have ObjectId format"
            )

    except Exception as e:
        logger.error(f"❌ Verification failed: {str(e)}")
        raise
    finally:
        if client:
            client.close()


async def main():
    """Run migration and verification"""
    logger.info("=" * 60)
    logger.info("Starting Member userId Format Migration")
    logger.info("=" * 60)

    await fix_member_userid_format()
    await verify_migration()

    logger.info("=" * 60)
    logger.info("Migration Complete!")
    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
