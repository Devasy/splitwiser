from typing import Any, Dict

from app.auth.security import get_current_user
from app.config import logger
from app.services.schemas import ImageUploadResponse
from app.services.storage import storage_service
from app.user.schemas import (
    DeleteUserResponse,
    UserProfileResponse,
    UserProfileUpdateRequest,
)
from app.user.service import user_service
from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    HTTPException,
    UploadFile,
    status,
)

router = APIRouter(prefix="/users", tags=["User"])


@router.get("/me", response_model=UserProfileResponse)
async def get_current_user_profile(
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    user = await user_service.get_user_by_id(current_user["_id"])
    if not user:
        raise HTTPException(
            status_code=404, detail={"error": "NotFound", "message": "User not found"}
        )
    return user


@router.patch("/me", response_model=Dict[str, Any])
async def update_user_profile(
    updates: UserProfileUpdateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    update_data = updates.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(
            status_code=400,
            detail={"error": "InvalidInput", "message": "No update fields provided."},
        )
    updated_user = await user_service.update_user_profile(
        current_user["_id"], update_data
    )
    if not updated_user:
        raise HTTPException(
            status_code=404, detail={"error": "NotFound", "message": "User not found"}
        )
    return {"user": updated_user}


@router.delete("/me", response_model=DeleteUserResponse)
async def delete_user_account(current_user: Dict[str, Any] = Depends(get_current_user)):
    deleted = await user_service.delete_user(current_user["_id"])
    if not deleted:
        raise HTTPException(
            status_code=404, detail={"error": "NotFound", "message": "User not found"}
        )
    return DeleteUserResponse(
        success=True, message="User account scheduled for deletion."
    )


@router.post("/me/avatar", response_model=ImageUploadResponse)
async def upload_user_avatar(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_user: dict = Depends(get_current_user),
):
    user_id = str(current_user["_id"])

    try:
        # Validate, process, upload
        urls = await storage_service.upload_image_workflow(
            file=file, folder="users", entity_id=user_id
        )
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Storage location not found.")
    except Exception as e:
        logger.exception(f"Unexpected error during avatar upload for user {user_id}")
        raise HTTPException(
            status_code=500, detail="Image upload failed due to an internal error."
        )

    # Update DB in background
    background_tasks.add_task(
        user_service.update_user_avatar_url, user_id, urls.get("full")
    )

    return ImageUploadResponse(
        success=True, urls=urls, message="Avatar uploaded successfully."
    )


@router.delete("/me/avatar", response_model=DeleteUserResponse)
async def delete_user_avatar(
    current_user: dict = Depends(get_current_user),
    background_tasks: BackgroundTasks = BackgroundTasks(),
):

    user_id = str(current_user["_id"])

    user = await user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    image_url = user.get("imageUrl")

    if not image_url:
        raise HTTPException(status_code=404, detail="User avatar not found")

    file_path = storage_service.extract_path_from_url(image_url)
    if not await storage_service.delete_image(file_path):
        raise HTTPException(status_code=500, detail="Failed to delete image")

    background_tasks.add_task(user_service.update_user_avatar_url, user_id, None)

    return DeleteUserResponse(success=True, message="User avatar deleted successfully.")
