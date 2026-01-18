import io
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from app.auth.security import get_current_user
from app.config import logger
from app.expenses.schemas import (
    AttachmentUploadResponse,
    BalanceSummaryResponse,
    ExpenseAnalytics,
    ExpenseCreateRequest,
    ExpenseCreateResponse,
    ExpenseListResponse,
    ExpenseResponse,
    ExpenseUpdateRequest,
    FriendsBalanceResponse,
    OptimizedSettlementsResponse,
    Settlement,
    SettlementCreateRequest,
    SettlementListResponse,
    SettlementUpdateRequest,
    UserBalance,
)
from app.expenses.service import expense_service
from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Query,
    Response,
    UploadFile,
    status,
)
from fastapi.responses import StreamingResponse

router = APIRouter(prefix="/groups/{group_id}", tags=["Expenses"])

# Expense CRUD Operations


@router.post(
    "/expenses",
    response_model=ExpenseCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_expense(
    group_id: str,
    expense_data: ExpenseCreateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Create a new expense within a group"""
    try:
        result = await expense_service.create_expense(
            group_id, expense_data, current_user["_id"]
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to create expense")


@router.get("/expenses", response_model=ExpenseListResponse)
async def list_group_expenses(
    group_id: str,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    from_date: Optional[datetime] = Query(None, alias="from"),
    to_date: Optional[datetime] = Query(None, alias="to"),
    tags: Optional[str] = Query(None),
    search: Optional[str] = Query(None, description="Search in description or tags"),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """List all expenses for a group with pagination and filtering"""
    try:
        tag_list = tags.split(",") if tags else None
        result = await expense_service.list_group_expenses(
            group_id,
            current_user["_id"],
            page,
            limit,
            from_date,
            to_date,
            tag_list,
            search,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to fetch expenses")


@router.get("/expenses/{expense_id}")
async def get_single_expense(
    group_id: str,
    expense_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Retrieve details for a single expense"""
    try:
        result = await expense_service.get_expense_by_id(
            group_id, expense_id, current_user["_id"]
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to fetch expense")


@router.patch("/expenses/{expense_id}", response_model=ExpenseResponse)
async def update_expense(
    group_id: str,
    expense_id: str,
    updates: ExpenseUpdateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Update an existing expense"""
    try:
        result = await expense_service.update_expense(
            group_id, expense_id, updates, current_user["_id"]
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating expense: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to update expense: {str(e)}"
        )


@router.delete("/expenses/{expense_id}")
async def delete_expense(
    group_id: str,
    expense_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Delete an expense"""
    try:
        success = await expense_service.delete_expense(
            group_id, expense_id, current_user["_id"]
        )
        if not success:
            raise HTTPException(status_code=404, detail="Expense not found")
        return {"success": True}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to delete expense")


# Attachment Handling


@router.post(
    "/expenses/{expense_id}/attachments",
    response_model=AttachmentUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_attachment_for_expense(
    group_id: str,
    expense_id: str,
    file: UploadFile = File(...),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Upload attachment for an expense"""
    try:
        # Verify user has access to the expense
        await expense_service.get_expense_by_id(
            group_id, expense_id, current_user["_id"]
        )

        # Generate unique key for the attachment
        file_extension = file.filename.split(".")[-1] if "." in file.filename else ""
        attachment_key = f"{expense_id}_{uuid.uuid4().hex}.{file_extension}"

        # In a real implementation, you would upload to cloud storage (S3, etc.)
        # For now, we'll simulate this
        file_content = await file.read()

        # Store file metadata (in practice, store the actual file and return the URL)
        url = f"https://storage.example.com/attachments/{attachment_key}"

        return AttachmentUploadResponse(attachment_key=attachment_key, url=url)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to upload attachment")


@router.get("/expenses/{expense_id}/attachments/{key}")
async def get_attachment(
    group_id: str,
    expense_id: str,
    key: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Get/download an attachment"""
    try:
        # Verify user has access to the expense
        await expense_service.get_expense_by_id(
            group_id, expense_id, current_user["_id"]
        )

        # In a real implementation, you would fetch from cloud storage
        # For now, we'll return a placeholder response
        raise HTTPException(
            status_code=501, detail="Attachment download not implemented"
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to get attachment")


# Settlement Management


@router.post(
    "/settlements", response_model=Settlement, status_code=status.HTTP_201_CREATED
)
async def manually_record_payment(
    group_id: str,
    settlement_data: SettlementCreateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Manually record a payment settlement between users in a group"""
    try:
        result = await expense_service.create_manual_settlement(
            group_id, settlement_data, current_user["_id"]
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to record settlement")


@router.get("/settlements", response_model=SettlementListResponse)
async def get_group_settlements(
    group_id: str,
    status_filter: Optional[str] = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    algorithm: str = Query(
        "advanced", description="Settlement algorithm: 'normal' or 'advanced'"
    ),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Retrieve pending and optimized settlements for a group"""
    try:
        # Get settlements using service
        settlements_result = await expense_service.get_group_settlements(
            group_id, current_user["_id"], status_filter, page, limit
        )

        # Get optimized settlements
        optimized_settlements = await expense_service.calculate_optimized_settlements(
            group_id, algorithm
        )

        # Calculate summary
        from app.database import mongodb

        total_pending_result = await mongodb.database.settlements.aggregate(
            [
                {"$match": {"groupId": group_id, "status": "pending"}},
                {"$group": {"_id": None, "totalPending": {"$sum": "$amount"}}},
            ]
        ).to_list(None)

        total_pending = (
            total_pending_result[0]["totalPending"] if total_pending_result else 0
        )

        return SettlementListResponse(
            settlements=settlements_result["settlements"],
            optimizedSettlements=optimized_settlements,
            summary={
                "totalPending": total_pending,
                "transactionCount": len(settlements_result["settlements"]),
                "optimizedCount": len(optimized_settlements),
            },
            pagination={
                "currentPage": page,
                "totalPages": (settlements_result["total"] + limit - 1) // limit,
                "totalItems": settlements_result["total"],
                "limit": limit,
            },
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to fetch settlements")


@router.get("/settlements/{settlement_id}", response_model=Settlement)
async def get_single_settlement(
    group_id: str,
    settlement_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Retrieve details for a single settlement"""
    try:
        settlement = await expense_service.get_settlement_by_id(
            group_id, settlement_id, current_user["_id"]
        )
        return settlement
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to fetch settlement")


@router.patch("/settlements/{settlement_id}", response_model=Settlement)
async def mark_settlement_as_paid(
    group_id: str,
    settlement_id: str,
    updates: SettlementUpdateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Mark a settlement as paid"""
    try:
        settlement = await expense_service.update_settlement_status(
            group_id, settlement_id, updates.status, updates.paidAt, current_user["_id"]
        )
        return settlement
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to update settlement")


@router.delete("/settlements/{settlement_id}")
async def delete_settlement(
    group_id: str,
    settlement_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Delete/undo a recorded settlement"""
    try:
        success = await expense_service.delete_settlement(
            group_id, settlement_id, current_user["_id"]
        )
        if not success:
            raise HTTPException(status_code=404, detail="Settlement not found")

        return {"success": True, "message": "Settlement record deleted successfully."}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to delete settlement")


@router.post("/settlements/optimize", response_model=OptimizedSettlementsResponse)
async def calculate_optimized_settlements(
    group_id: str,
    algorithm: str = Query(
        "advanced", description="Settlement algorithm: 'normal' or 'advanced'"
    ),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Calculate and return optimized (simplified) settlements for a group"""
    try:
        optimized_settlements = await expense_service.calculate_optimized_settlements(
            group_id, algorithm
        )

        # Calculate savings
        from app.database import mongodb

        total_settlements = await mongodb.database.settlements.count_documents(
            {"groupId": group_id, "status": "pending"}
        )

        optimized_count = len(optimized_settlements)
        reduction_percentage = (
            ((total_settlements - optimized_count) / total_settlements * 100)
            if total_settlements > 0
            else 0
        )

        return OptimizedSettlementsResponse(
            optimizedSettlements=optimized_settlements,
            savings={
                "originalTransactions": total_settlements,
                "optimizedTransactions": optimized_count,
                "reductionPercentage": round(reduction_percentage, 1),
            },
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail="Failed to calculate optimized settlements"
        )


# User Balance Endpoints

# These endpoints are defined at the root level in a separate router
balance_router = APIRouter(prefix="/users/me", tags=["User Balance"])


@balance_router.get("/friends-balance", response_model=FriendsBalanceResponse)
async def get_cross_group_friend_balances(
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Retrieve the current user's aggregated balances with all friends"""
    try:
        result = await expense_service.get_friends_balance_summary(current_user["_id"])
        return FriendsBalanceResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to fetch friends balance")


@balance_router.get("/balance-summary", response_model=BalanceSummaryResponse)
async def get_overall_user_balance_summary(
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Retrieve an overall balance summary for the current user"""
    try:
        result = await expense_service.get_overall_balance_summary(current_user["_id"])
        return BalanceSummaryResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to fetch balance summary")


# Group-specific user balance
@router.get("/users/{user_id}/balance", response_model=UserBalance)
async def get_user_balance_in_specific_group(
    group_id: str,
    user_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Get a specific user's balance within a particular group"""
    try:
        result = await expense_service.get_user_balance_in_group(
            group_id, user_id, current_user["_id"]
        )
        return UserBalance(**result)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to fetch user balance")


# Analytics
@router.get("/analytics", response_model=ExpenseAnalytics)
async def group_expense_analytics(
    group_id: str,
    period: str = Query(
        "month", description="Analytics period: 'month', '6months', 'year'"
    ),
    year: Optional[int] = Query(None),
    month: Optional[int] = Query(None),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Provide expense analytics for a group"""
    try:
        result = await expense_service.get_group_analytics(
            group_id, current_user["_id"], period, year, month
        )
        return ExpenseAnalytics(**result)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to fetch analytics")
