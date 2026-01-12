"""
API router for import operations.
"""

from app.auth.security import get_current_user
from app.config import settings
from app.database import get_database
from app.integrations.schemas import (
    ImportPreviewResponse,
    ImportStatusResponse,
    OAuthCallbackRequest,
    RollbackImportResponse,
    StartImportRequest,
    StartImportResponse,
)
from app.integrations.service import ImportService
from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from splitwise import Splitwise

router = APIRouter(prefix="/import", tags=["import"])


@router.get("/splitwise/authorize")
async def get_splitwise_oauth_url(current_user=Depends(get_current_user)):
    """
    Get Splitwise OAuth 2.0 authorization URL.

    Returns the URL where user should be redirected to authorize Splitwiser
    to access their Splitwise data.
    """
    if not all([settings.splitwise_consumer_key, settings.splitwise_consumer_secret]):
        raise HTTPException(
            status_code=500,
            detail="Splitwise OAuth not configured. Please contact administrator.",
        )

    # Initialize Splitwise SDK with OAuth credentials
    sObj = Splitwise(
        consumer_key=settings.splitwise_consumer_key,
        consumer_secret=settings.splitwise_consumer_secret,
    )

    # Get OAuth authorization URL
    # User will be redirected back to: {FRONTEND_URL}/import/splitwise/callback
    auth_url, secret = sObj.getOAuth2AuthorizeURL(
        redirect_uri=f"{settings.frontend_url}/import/splitwise/callback"
    )

    # Store the secret temporarily (you may want to use Redis/cache instead)
    # For now, we'll include it in the response for the callback to use
    return {
        "authorization_url": auth_url,
        "state": secret,  # This will be needed in the callback
    }


@router.post("/splitwise/callback")
async def splitwise_oauth_callback(
    request: OAuthCallbackRequest, current_user=Depends(get_current_user)
):
    """
    Handle OAuth 2.0 callback from Splitwise.

    After user authorizes, Splitwise redirects to frontend with code.
    Frontend sends code here to exchange for access token and start import.
    """
    if not all([settings.splitwise_consumer_key, settings.splitwise_consumer_secret]):
        raise HTTPException(status_code=500, detail="Splitwise OAuth not configured")

    # Initialize Splitwise SDK
    sObj = Splitwise(
        consumer_key=settings.splitwise_consumer_key,
        consumer_secret=settings.splitwise_consumer_secret,
    )

    try:
        # Exchange authorization code for access token
        access_token = sObj.getOAuth2AccessToken(
            code=request.code,
            redirect_uri=f"{settings.frontend_url}/import/splitwise/callback",
        )

        # Start import with the access token
        service = ImportService()
        import_job_id = await service.start_import(
            user_id=current_user["_id"],
            provider="splitwise",
            api_key=access_token["access_token"],  # Use access token
        )

        return StartImportResponse(
            importJobId=str(import_job_id),
            status="started",
            message="Import started successfully with OAuth",
        )

    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Failed to exchange OAuth code: {str(e)}"
        )


@router.post("/splitwise/start", response_model=StartImportResponse)
async def start_splitwise_import(
    request: StartImportRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Start importing data from Splitwise with a single button click.

    This endpoint will:
    1. Fetch all your Splitwise data (friends, groups, expenses)
    2. Transform it to Splitwiser format
    3. Import everything into your account
    4. Handle ID mapping automatically

    All you need is your Splitwise API key!
    """
    # Get API credentials from environment or request
    # In production, users would authenticate via OAuth
    # For now, using API key from config
    from app.config import settings

    api_key = getattr(settings, "splitwise_api_key", None)
    consumer_key = getattr(settings, "splitwise_consumer_key", None)
    consumer_secret = getattr(settings, "splitwise_consumer_secret", None)

    if not api_key or not consumer_key or not consumer_secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Splitwise API credentials not configured. Please add them to your environment variables.",
        )

    service = ImportService(db)

    try:
        import_job_id = await service.start_import(
            user_id=str(current_user["_id"]),
            provider=request.provider,
            api_key=api_key,
            consumer_key=consumer_key,
            consumer_secret=consumer_secret,
            options=request.options,
        )

        return StartImportResponse(
            importJobId=import_job_id, status="in_progress", estimatedCompletion=None
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start import: {str(e)}",
        )


@router.get("/status/{import_job_id}", response_model=ImportStatusResponse)
async def get_import_status(
    import_job_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Check the status of an ongoing import.

    Returns progress information, errors, and completion status.
    """
    service = ImportService(db)

    job = await service.get_import_status(import_job_id)

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Import job not found"
        )

    # Verify user owns this import
    if str(job["userId"]) != str(current_user["_id"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this import job",
        )

    # Calculate progress
    checkpoints = job.get("checkpoints", {})
    groups_progress = checkpoints.get("groupsImported", {})
    expenses_progress = checkpoints.get("expensesImported", {})

    total_items = groups_progress.get("total", 0) + expenses_progress.get("total", 0)
    completed_items = groups_progress.get("completed", 0) + expenses_progress.get(
        "completed", 0
    )

    progress_percentage = 0
    if total_items > 0:
        progress_percentage = int((completed_items / total_items) * 100)

    # Determine current stage
    current_stage = "Starting..."
    if not checkpoints.get("userImported"):
        current_stage = "Importing your profile"
    elif not checkpoints.get("friendsImported"):
        current_stage = "Importing friends"
    elif groups_progress.get("completed", 0) < groups_progress.get("total", 0):
        current_stage = f"Importing groups ({groups_progress.get('completed', 0)}/{groups_progress.get('total', 0)})"
    elif expenses_progress.get("completed", 0) < expenses_progress.get("total", 0):
        current_stage = f"Importing expenses ({expenses_progress.get('completed', 0)}/{expenses_progress.get('total', 0)})"
    elif job["status"] == "completed":
        current_stage = "Completed!"

    return ImportStatusResponse(
        importJobId=import_job_id,
        status=job["status"],
        progress={
            "current": completed_items,
            "total": total_items,
            "percentage": progress_percentage,
            "currentStage": current_stage,
            "stages": {
                "user": "completed" if checkpoints.get("userImported") else "pending",
                "friends": (
                    "completed" if checkpoints.get("friendsImported") else "pending"
                ),
                "groups": (
                    "completed"
                    if groups_progress.get("completed", 0)
                    >= groups_progress.get("total", 1)
                    else "in_progress"
                ),
                "expenses": (
                    "completed"
                    if expenses_progress.get("completed", 0)
                    >= expenses_progress.get("total", 1)
                    else "in_progress"
                ),
            },
        },
        errors=job.get("errors", []),
        startedAt=job.get("startedAt"),
        completedAt=job.get("completedAt"),
        estimatedCompletion=None,
    )


@router.post("/rollback/{import_job_id}", response_model=RollbackImportResponse)
async def rollback_import(
    import_job_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Rollback an import by deleting all imported data.

    This will remove all groups, expenses, and users that were created
    during this import.
    """
    service = ImportService(db)

    # Verify user owns this import
    job = await service.get_import_status(import_job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Import job not found"
        )

    if str(job["userId"]) != str(current_user["_id"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to rollback this import",
        )

    result = await service.rollback_import(import_job_id)

    return RollbackImportResponse(**result)
