from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, validator


class SplitType(str, Enum):
    EQUAL = "equal"
    UNEQUAL = "unequal"
    PERCENTAGE = "percentage"


class SettlementStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Currency(str, Enum):
    USD = "USD"
    INR = "INR"
    EUR = "EUR"


class ExpenseSplit(BaseModel):
    userId: str
    amount: float = Field(..., gt=0)
    type: SplitType = SplitType.EQUAL


class ExpenseCreateRequest(BaseModel):
    description: str = Field(..., min_length=1, max_length=500)
    amount: float = Field(..., gt=0)
    splits: List[ExpenseSplit]
    splitType: SplitType = SplitType.EQUAL
    paidBy: str = Field(..., description="User ID of who paid for the expense")
    currency: Optional[Currency] = None
    tags: Optional[List[str]] = []
    receiptUrls: Optional[List[str]] = []

    @validator("splits")
    def validate_splits_sum(cls, v, values):
        if "amount" in values:
            total_split = sum(split.amount for split in v)
            if (
                abs(total_split - values["amount"]) > 0.01
            ):  # Allow small floating point differences
                raise ValueError("Split amounts must sum to total expense amount")
        return v


class ExpenseUpdateRequest(BaseModel):
    description: Optional[str] = Field(None, min_length=1, max_length=500)
    amount: Optional[float] = Field(None, gt=0)
    splits: Optional[List[ExpenseSplit]] = None
    tags: Optional[List[str]] = None
    receiptUrls: Optional[List[str]] = None

    @validator("splits")
    def validate_splits_sum(cls, v, values):
        # Only validate if both splits and amount are provided in the update
        if v is not None and "amount" in values and values["amount"] is not None:
            total_split = sum(split.amount for split in v)
            if abs(total_split - values["amount"]) > 0.01:
                raise ValueError("Split amounts must sum to total expense amount")
        return v

    class Config:
        # Allow validation to work with partial updates
        validate_assignment = True


class ExpenseComment(BaseModel):
    id: str = Field(alias="_id")
    userId: str
    userName: str
    content: str
    createdAt: datetime

    model_config = ConfigDict(
        populate_by_name=True, str_strip_whitespace=True, validate_assignment=True
    )


class ExpenseHistoryEntry(BaseModel):
    id: str = Field(alias="_id")
    userId: str
    userName: str
    beforeData: Dict[str, Any]
    editedAt: datetime

    model_config = ConfigDict(populate_by_name=True)


class ExpenseResponse(BaseModel):
    id: str = Field(alias="_id")
    groupId: str
    createdBy: str
    paidBy: str
    description: str
    amount: float
    splits: List[ExpenseSplit]
    splitType: SplitType
    currency: Currency = Currency.USD
    tags: List[str] = []
    receiptUrls: List[str] = []
    comments: Optional[List[ExpenseComment]] = []
    history: Optional[List[ExpenseHistoryEntry]] = []
    createdAt: datetime
    updatedAt: datetime

    model_config = ConfigDict(populate_by_name=True)


class Settlement(BaseModel):
    id: str = Field(alias="_id")
    expenseId: Optional[str] = None  # None for manual settlements
    groupId: str
    payerId: str
    payeeId: str
    payerName: str
    payeeName: str
    amount: float
    currency: Currency = Currency.USD
    status: SettlementStatus
    description: Optional[str] = None
    paidAt: Optional[datetime] = None
    createdAt: datetime

    model_config = ConfigDict(populate_by_name=True)


class OptimizedSettlement(BaseModel):
    fromUserId: str
    toUserId: str
    fromUserName: str
    toUserName: str
    amount: float
    consolidatedExpenses: Optional[List[str]] = []


class GroupSummary(BaseModel):
    totalExpenses: float
    totalSettlements: int
    optimizedSettlements: List[OptimizedSettlement]


class ExpenseCreateResponse(BaseModel):
    expense: ExpenseResponse
    settlements: List[Settlement]
    groupSummary: GroupSummary


class ExpenseListResponse(BaseModel):
    expenses: List[ExpenseResponse]
    pagination: Dict[str, Any]
    summary: Dict[str, Any]


class SettlementCreateRequest(BaseModel):
    payer_id: str
    payee_id: str
    amount: float = Field(..., gt=0)
    description: Optional[str] = None
    paidAt: Optional[datetime] = None


class SettlementUpdateRequest(BaseModel):
    status: SettlementStatus
    paidAt: Optional[datetime] = None


class SettlementListResponse(BaseModel):
    settlements: List[Settlement]
    optimizedSettlements: List[OptimizedSettlement]
    summary: Dict[str, Any]
    pagination: Dict[str, Any]


class UserBalance(BaseModel):
    userId: str
    userName: str
    totalPaid: float
    totalOwed: float
    netBalance: float
    owesYou: bool
    pendingSettlements: List[Settlement] = []
    recentExpenses: List[Dict[str, Any]] = []


class FriendBalanceBreakdown(BaseModel):
    groupId: str
    groupName: str
    balance: float
    owesYou: bool


class FriendBalance(BaseModel):
    userId: str
    userName: str
    userImageUrl: Optional[str] = None
    netBalance: float
    owesYou: bool
    breakdown: List[FriendBalanceBreakdown]
    lastActivity: datetime


class FriendsBalanceResponse(BaseModel):
    friendsBalance: List[FriendBalance]
    summary: Dict[str, Any]


class BalanceSummaryResponse(BaseModel):
    totalOwedToYou: float
    totalYouOwe: float
    netBalance: float
    currency: str = "USD"
    groupsSummary: List[Dict[str, Any]]


class ExpenseAnalytics(BaseModel):
    period: str
    totalExpenses: float
    expenseCount: int
    avgExpenseAmount: float
    topCategories: List[Dict[str, Any]]
    memberContributions: List[Dict[str, Any]]
    contributionTimeline: List[Dict[str, Any]] = []
    expenseTrends: List[Dict[str, Any]]


class AttachmentUploadResponse(BaseModel):
    attachment_key: str
    url: str


class OptimizedSettlementsResponse(BaseModel):
    optimizedSettlements: List[OptimizedSettlement]
    savings: Dict[str, Any]
