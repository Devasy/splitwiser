"""
Pydantic schemas for import operations.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field, model_validator


class ImportProvider(str, Enum):
    """Supported import providers."""

    SPLITWISE = "splitwise"


class ImportStatus(str, Enum):
    """Import job status."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class ImportStage(str, Enum):
    """Import stages."""

    USER = "user"
    FRIENDS = "friends"
    GROUPS = "groups"
    EXPENSES = "expenses"
    SETTLEMENTS = "settlements"


class ImportCheckpoint(BaseModel):
    """Progress checkpoint for import stages."""

    completed: int = 0
    total: int = 0
    currentItem: Optional[str] = None


class ImportError(BaseModel):
    """Import error record."""

    stage: str
    message: str
    details: Optional[dict[str, Any]] = None
    timestamp: datetime


class ImportOptions(BaseModel):
    """Options for import configuration."""

    importReceipts: bool = True
    importComments: bool = True
    importArchivedExpenses: bool = False
    selectedGroupIds: list[str] = []  # Splitwise group IDs to import


class ImportPreviewRequest(BaseModel):
    """Request to preview import data."""

    provider: ImportProvider = ImportProvider.SPLITWISE


class ImportPreviewGroup(BaseModel):
    """Group information for preview."""

    splitwiseId: str
    name: str
    currency: str
    memberCount: int
    expenseCount: int
    totalAmount: float
    imageUrl: Optional[str] = None


class ImportPreviewWarning(BaseModel):
    """Warning about potential import issues."""

    type: str
    message: str
    resolution: Optional[str] = None
    blocking: bool = False  # If True, import should not proceed without acknowledgment


class ImportPreviewResponse(BaseModel):
    """Response with import preview information."""

    splitwiseUser: Optional[dict[str, Any]] = None
    groups: list[ImportPreviewGroup] = []
    summary: dict[str, Any]
    warnings: list[ImportPreviewWarning] = []
    estimatedDuration: str


class StartImportRequest(BaseModel):
    """Request to start import."""

    provider: ImportProvider = ImportProvider.SPLITWISE
    options: ImportOptions = ImportOptions()


class StartImportResponse(BaseModel):
    """Response when import is started."""

    importJobId: str
    status: ImportStatus
    estimatedCompletion: Optional[datetime] = None


class ImportStatusCheckpoint(BaseModel):
    """Checkpoint status for a stage."""

    user: str = "pending"
    friends: str = "pending"
    groups: str = "pending"
    expenses: str = "pending"
    settlements: str = "pending"


class ImportStatusResponse(BaseModel):
    """Response with current import status."""

    importJobId: str
    status: ImportStatus
    progress: Optional[dict[str, Any]] = None
    errors: list[ImportError] = []
    startedAt: Optional[datetime] = None
    completedAt: Optional[datetime] = None
    estimatedCompletion: Optional[datetime] = None


class ImportSummary(BaseModel):
    """Summary of completed import."""

    usersCreated: int = 0
    groupsCreated: int = 0
    expensesCreated: int = 0
    commentsImported: int = 0
    settlementsCreated: int = 0
    receiptsMigrated: int = 0


class ImportJobResponse(BaseModel):
    """Detailed import job information."""

    importJobId: str
    userId: str
    provider: ImportProvider
    status: ImportStatus
    summary: ImportSummary
    startedAt: datetime
    completedAt: Optional[datetime] = None


class ImportHistoryResponse(BaseModel):
    """List of import jobs."""

    imports: list[ImportJobResponse]


class RollbackImportResponse(BaseModel):
    """Response after rolling back an import."""

    success: bool
    message: str
    deletedRecords: dict[str, int]


class OAuthInitiateResponse(BaseModel):
    """Response to initiate OAuth flow."""

    authUrl: str
    state: str


class OAuthCallbackResponse(BaseModel):
    """Response after OAuth callback."""

    success: bool
    message: str
    canProceed: bool


class OAuthCallbackRequest(BaseModel):
    """Request body for OAuth callback."""

    code: Optional[str] = None
    state: Optional[str] = None
    accessToken: Optional[str] = None  # Used when returning from group selection
    options: Optional[ImportOptions] = None

    @model_validator(mode="after")
    def check_required_fields(self) -> "OAuthCallbackRequest":
        """Validate that either (code and state) or accessToken is provided."""
        has_oauth = self.code is not None and self.state is not None
        has_token = self.accessToken is not None
        if not has_oauth and not has_token:
            raise ValueError(
                "Either both code and state must be provided (OAuth flow) or accessToken must be provided (token flow)"
            )
        return self
