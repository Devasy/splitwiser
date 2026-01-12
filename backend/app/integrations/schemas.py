"""
Pydantic schemas for import operations.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


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
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime


class ImportOptions(BaseModel):
    """Options for import configuration."""

    importReceipts: bool = True
    importComments: bool = True
    importArchivedExpenses: bool = False
    confirmWarnings: bool = False


class ImportPreviewRequest(BaseModel):
    """Request to preview import data."""

    provider: ImportProvider = ImportProvider.SPLITWISE


class ImportPreviewWarning(BaseModel):
    """Warning about potential import issues."""

    type: str
    message: str
    resolution: Optional[str] = None


class ImportPreviewResponse(BaseModel):
    """Response with import preview information."""

    splitwiseUser: Optional[Dict[str, Any]] = None
    summary: Dict[str, Any]
    warnings: List[ImportPreviewWarning] = []
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
    progress: Optional[Dict[str, Any]] = None
    errors: List[ImportError] = []
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

    imports: List[ImportJobResponse]


class RollbackImportResponse(BaseModel):
    """Response after rolling back an import."""

    success: bool
    message: str
    deletedRecords: Dict[str, int]


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

    code: str
    state: Optional[str] = None
