from datetime import datetime
from typing import List, Optional

from app.expenses.schemas import Currency
from pydantic import BaseModel, ConfigDict, Field


class GroupMember(BaseModel):
    userId: str
    role: str = "member"  # "admin" or "member"
    joinedAt: datetime


class GroupMemberWithDetails(BaseModel):
    userId: str
    role: str = "member"  # "admin" or "member"
    joinedAt: datetime
    user: Optional[dict] = None  # Contains user details like name, email


class GroupCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    currency: Optional[Currency] = Currency.USD
    imageUrl: Optional[str] = None


class GroupUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    imageUrl: Optional[str] = None
    currency: Optional[Currency] = None


class GroupResponse(BaseModel):
    id: str = Field(alias="_id")
    name: str
    currency: str
    joinCode: str
    createdBy: str
    createdAt: datetime
    imageUrl: Optional[str] = None
    members: Optional[List[GroupMemberWithDetails]] = []

    model_config = ConfigDict(populate_by_name=True)


class GroupListResponse(BaseModel):
    groups: List[GroupResponse]


class JoinGroupRequest(BaseModel):
    joinCode: str = Field(..., min_length=1)


class JoinGroupResponse(BaseModel):
    group: GroupResponse


class MemberRoleUpdateRequest(BaseModel):
    role: str = Field(..., pattern="^(admin|member)$")


class LeaveGroupResponse(BaseModel):
    success: bool
    message: str


class DeleteGroupResponse(BaseModel):
    success: bool
    message: str


class RemoveMemberResponse(BaseModel):
    success: bool
    message: str
