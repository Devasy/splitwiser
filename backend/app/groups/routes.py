from typing import Any, Dict, List

from app.auth.security import get_current_user
from app.groups.schemas import (
    DeleteGroupResponse,
    GroupCreateRequest,
    GroupListResponse,
    GroupMemberWithDetails,
    GroupResponse,
    GroupUpdateRequest,
    JoinGroupRequest,
    JoinGroupResponse,
    LeaveGroupResponse,
    MemberRoleUpdateRequest,
    RemoveMemberResponse,
)
from app.groups.service import group_service
from app.services.schemas import ImageUploadResponse
from app.services.storage import storage_service
from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    HTTPException,
    UploadFile,
    status,
)

router = APIRouter(prefix="/groups", tags=["Groups"])


@router.post("", response_model=GroupResponse, status_code=status.HTTP_201_CREATED)
async def create_group(
    group_data: GroupCreateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Create a new group"""
    group = await group_service.create_group(
        group_data.model_dump(exclude_unset=True), current_user["_id"]
    )
    if not group:
        raise HTTPException(status_code=500, detail="Failed to create group")
    return group


@router.get("", response_model=GroupListResponse)
async def list_user_groups(current_user: Dict[str, Any] = Depends(get_current_user)):
    """List all groups the current user belongs to"""
    groups = await group_service.get_user_groups(current_user["_id"])
    return {"groups": groups}


@router.get("/{group_id}", response_model=GroupResponse)
async def get_group_details(
    group_id: str, current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get group details including members"""
    group = await group_service.get_group_by_id(group_id, current_user["_id"])
    if not group:
        raise HTTPException(status_code=404, detail="Group not found or access denied")
    return group


@router.patch("/{group_id}", response_model=GroupResponse)
async def update_group_metadata(
    group_id: str,
    updates: GroupUpdateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Update group metadata (admin only)"""
    update_data = updates.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="No update fields provided")

    updated_group = await group_service.update_group(
        group_id, update_data, current_user["_id"]
    )
    if not updated_group:
        raise HTTPException(status_code=404, detail="Group not found or access denied")
    return updated_group


@router.delete("/{group_id}", response_model=DeleteGroupResponse)
async def delete_group(
    group_id: str, current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Delete a group (admin only)"""
    deleted = await group_service.delete_group(group_id, current_user["_id"])
    if not deleted:
        raise HTTPException(status_code=404, detail="Group not found or access denied")
    return DeleteGroupResponse(success=True, message="Group deleted successfully")


@router.post("/join", response_model=JoinGroupResponse)
async def join_group_by_code(
    join_data: JoinGroupRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Join a group using a join code"""
    group = await group_service.join_group_by_code(
        join_data.joinCode, current_user["_id"]
    )
    if not group:
        raise HTTPException(status_code=404, detail="Invalid join code")
    return {"group": group}


@router.post("/{group_id}/leave", response_model=LeaveGroupResponse)
async def leave_group(
    group_id: str, current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Leave a group (only if no outstanding balances)"""
    left = await group_service.leave_group(group_id, current_user["_id"])
    if not left:
        raise HTTPException(status_code=400, detail="Failed to leave group")
    return LeaveGroupResponse(success=True, message="Successfully left the group")


@router.get("/{group_id}/members", response_model=List[GroupMemberWithDetails])
async def get_group_members(
    group_id: str, current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get list of group members with detailed user information"""
    members = await group_service.get_group_members(group_id, current_user["_id"])
    return members


@router.patch("/{group_id}/members/{member_id}", response_model=Dict[str, str])
async def update_member_role(
    group_id: str,
    member_id: str,
    role_update: MemberRoleUpdateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Change member role (admin only)"""
    updated = await group_service.update_member_role(
        group_id, member_id, role_update.role, current_user["_id"]
    )
    if not updated:
        raise HTTPException(status_code=400, detail="Failed to update member role")
    return {"message": f"Member role updated to {role_update.role}"}


@router.delete("/{group_id}/members/{member_id}", response_model=RemoveMemberResponse)
async def remove_group_member(
    group_id: str,
    member_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Remove a member from the group (admin only)"""
    removed = await group_service.remove_member(
        group_id, member_id, current_user["_id"]
    )
    if not removed:
        raise HTTPException(status_code=400, detail="Failed to remove member")
    return RemoveMemberResponse(success=True, message="Member removed successfully")


@router.post("/{group_id}/image", response_model=ImageUploadResponse)
async def upload_group_image(
    group_id: str,
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_user: dict = Depends(get_current_user),
):

    await group_service.ensure_user_in_group(group_id, current_user["_id"])

    try:
        urls = await storage_service.upload_image_workflow(
            file=file, folder="groups", entity_id=group_id
        )

    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception:
        raise HTTPException(status_code=500, detail="Group image upload failed")

    background_tasks.add_task(
        group_service.update_group_image_url, group_id, urls.get("full")
    )

    return ImageUploadResponse(
        success=True, urls=urls, message="Group image uploaded successfully."
    )


@router.delete("/{group_id}/image", response_model=DeleteGroupResponse)
async def delete_group_avatar(
    group_id: str,
    current_user: dict = Depends(get_current_user),
    background_tasks: BackgroundTasks = BackgroundTasks(),
):
    group = await group_service.get_group_by_id(group_id, current_user["_id"])
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    await group_service.ensure_user_in_group(group_id, current_user["_id"])

    image_url = group.get("imageUrl")
    if not image_url:
        raise HTTPException(status_code=404, detail="Group avatar not found")

    try:
        file_path = storage_service.extract_path_from_url(image_url)
        deleted = await storage_service.delete_image(file_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to delete group avatar")

    if not deleted:
        raise HTTPException(status_code=500, detail="Failed to delete group avatar")

    background_tasks.add_task(group_service.update_group_image_url, group_id, None)

    return DeleteGroupResponse(
        success=True, message="Group image deleted successfully."
    )
