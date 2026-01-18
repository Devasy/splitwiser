from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from app.config import logger
from app.database import mongodb
from app.expenses.schemas import (
    ExpenseCreateRequest,
    ExpenseResponse,
    ExpenseUpdateRequest,
    OptimizedSettlement,
    Settlement,
    SettlementCreateRequest,
    SettlementStatus,
    SplitType,
)
from bson import ObjectId, errors
from fastapi import HTTPException


class ExpenseService:
    def __init__(self):
        pass

    @property
    def expenses_collection(self):
        return mongodb.database.expenses

    @property
    def settlements_collection(self):
        return mongodb.database.settlements

    @property
    def groups_collection(self):
        return mongodb.database.groups

    @property
    def users_collection(self):
        return mongodb.database.users

    async def create_expense(
        self, group_id: str, expense_data: ExpenseCreateRequest, user_id: str
    ) -> Dict[str, Any]:
        """Create a new expense and calculate settlements"""

        # Validate and convert group_id to ObjectId
        try:
            group_obj_id = ObjectId(group_id)
        except errors.InvalidId:  # Incorrect ObjectId format
            logger.warning(f"Invalid group ID format: {group_id}")
            raise HTTPException(status_code=400, detail="Invalid group ID")
        except Exception as e:
            logger.error(f"Unexpected error parsing groupId: {e}")
            raise HTTPException(status_code=500, detail="Failed to process group ID")

        # Verify user is member of the group
        # Query for both string and ObjectId userId formats for compatibility with imported groups
        try:
            user_obj_id = ObjectId(user_id)
        except:
            user_obj_id = user_id

        group = await self.groups_collection.find_one(
            {
                "_id": group_obj_id,
                "$or": [
                    {"members.userId": user_obj_id},
                    {"members.userId": user_id},
                    {"createdBy": user_obj_id},
                    {"createdBy": user_id},
                ],
            }
        )
        if not group:  # User not a member of the group
            raise HTTPException(
                status_code=403, detail="You are not a member of this group"
            )

        # Verify the payer is also a member of the group
        payer_is_member = any(
            member.get("userId") == expense_data.paidBy
            for member in group.get("members", [])
        )
        if not payer_is_member:
            raise HTTPException(
                status_code=400,
                detail="The selected payer is not a member of this group",
            )

        # Create expense document
        expense_doc = {
            "_id": ObjectId(),
            "groupId": group_id,
            "createdBy": user_id,
            "paidBy": expense_data.paidBy,
            "description": expense_data.description,
            "amount": expense_data.amount,
            "currency": expense_data.currency or group.get("currency", "USD"),
            "splits": [split.model_dump() for split in expense_data.splits],
            "splitType": expense_data.splitType,
            "tags": expense_data.tags or [],
            "receiptUrls": expense_data.receiptUrls or [],
            "comments": [],
            "history": [],
            "createdAt": datetime.utcnow(),
            "updatedAt": datetime.utcnow(),
        }

        # Insert expense
        await self.expenses_collection.insert_one(expense_doc)

        # Create settlements
        settlements = await self._create_settlements_for_expense(
            expense_doc, expense_data.paidBy
        )

        # Get optimized settlements for the group
        optimized_settlements = await self.calculate_optimized_settlements(group_id)

        # Update cached balances for the group
        await self._recalculate_group_balances(group_id)

        # Get group summary
        group_summary = await self._get_group_summary(group_id, optimized_settlements)

        # Convert expense to response format
        expense_response = await self._expense_doc_to_response(expense_doc)

        return {
            "expense": expense_response,
            "settlements": settlements,
            "groupSummary": group_summary,
        }

    async def _create_settlements_for_expense(
        self, expense_doc: Dict[str, Any], payer_id: str
    ) -> List[Settlement]:
        """Create settlement records for an expense"""
        settlements = []
        expense_id = str(expense_doc["_id"])
        group_id = expense_doc["groupId"]

        # Get user names for the settlements
        user_ids = [split["userId"] for split in expense_doc["splits"]] + [payer_id]
        users = await self.users_collection.find(
            {"_id": {"$in": [ObjectId(uid) for uid in user_ids]}}
        ).to_list(None)
        user_names = {str(user["_id"]): user.get("name", "Unknown") for user in users}

        for split in expense_doc["splits"]:
            # Skip if split user is the payer (they don't owe themselves)
            if split["userId"] == payer_id:
                continue

            settlement_doc = {
                "_id": ObjectId(),
                "expenseId": expense_id,
                "groupId": group_id,
                # IMPORTANT: payerId = debtor (person who OWES/will pay)
                #            payeeId = creditor (person who is OWED/paid the expense)
                # This matches: net_balances[payerId][payeeId] means payerId owes payeeId
                "payerId": split["userId"],  # The debtor (person who owes)
                "payeeId": payer_id,  # The creditor (person who paid)
                "amount": split["amount"],
                "currency": expense_doc.get("currency", "USD"),
                "payerName": user_names.get(split["userId"], "Unknown"),  # Debtor name
                "payeeName": user_names.get(payer_id, "Unknown"),  # Creditor name
                "status": "pending",
                "description": f"Share for {expense_doc['description']}",
                "createdAt": datetime.utcnow(),
            }

            await self.settlements_collection.insert_one(settlement_doc)

            # Convert to Settlement model
            settlement = Settlement(
                **{**settlement_doc, "_id": str(settlement_doc["_id"])}
            )
            settlements.append(settlement)

        return settlements

    async def list_group_expenses(
        self,
        group_id: str,
        user_id: str,
        page: int = 1,
        limit: int = 20,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        tags: Optional[List[str]] = None,
        search: Optional[str] = None,
    ) -> Dict[str, Any]:
        """List expenses for a group with pagination and filtering"""

        # Verify user access - handle both string and ObjectId userId formats
        try:
            user_obj_id = ObjectId(user_id)
        except:
            user_obj_id = user_id

        group = await self.groups_collection.find_one(
            {
                "_id": ObjectId(group_id),
                "$or": [
                    {"members.userId": user_obj_id},
                    {"members.userId": user_id},
                    {"createdBy": user_obj_id},
                    {"createdBy": user_id},
                ],
            }
        )
        if not group:
            raise ValueError("Group not found or user not a member")

        # Build query
        query = {"groupId": group_id}

        if from_date or to_date:
            date_filter = {}
            if from_date:
                date_filter["$gte"] = from_date
            if to_date:
                date_filter["$lte"] = to_date
            query["createdAt"] = date_filter

        if tags:
            query["tags"] = {"$in": tags}

        # Add search filter
        if search:
            query["$or"] = [
                {"description": {"$regex": search, "$options": "i"}},
                {"tags": {"$regex": search, "$options": "i"}},
            ]

        # Get total count for filtered results
        total = await self.expenses_collection.count_documents(query)

        # Get expenses with pagination
        skip = (page - 1) * limit
        expenses_cursor = (
            self.expenses_collection.find(query)
            .sort("createdAt", -1)
            .skip(skip)
            .limit(limit)
        )
        expenses_docs = await expenses_cursor.to_list(None)

        expenses = []
        for doc in expenses_docs:
            expense = await self._expense_doc_to_response(doc)
            expenses.append(expense)

        # Calculate filtered summary (for current query)
        pipeline = [
            {"$match": query},
            {
                "$group": {
                    "_id": None,
                    "totalAmount": {"$sum": "$amount"},
                    "expenseCount": {"$sum": 1},
                    "avgExpense": {"$avg": "$amount"},
                }
            },
        ]
        summary_result = await self.expenses_collection.aggregate(pipeline).to_list(
            None
        )
        filtered_summary = (
            summary_result[0]
            if summary_result
            else {"totalAmount": 0, "expenseCount": 0, "avgExpense": 0}
        )
        filtered_summary.pop("_id", None)

        # Calculate TOTAL group summary (all expenses, no filters)
        total_query = {"groupId": group_id}
        total_pipeline = [
            {"$match": total_query},
            {
                "$group": {
                    "_id": None,
                    "totalAmount": {"$sum": "$amount"},
                    "expenseCount": {"$sum": 1},
                    "avgExpense": {"$avg": "$amount"},
                }
            },
        ]
        total_summary_result = await self.expenses_collection.aggregate(
            total_pipeline
        ).to_list(None)
        total_summary = (
            total_summary_result[0]
            if total_summary_result
            else {"totalAmount": 0, "expenseCount": 0, "avgExpense": 0}
        )
        total_summary.pop("_id", None)

        return {
            "expenses": expenses,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "totalPages": (total + limit - 1) // limit,
                "hasNext": page * limit < total,
                "hasPrev": page > 1,
            },
            "summary": filtered_summary,  # Summary for filtered results
            "totalSummary": total_summary,  # Summary for ALL expenses in group
        }

    async def get_expense_by_id(
        self, group_id: str, expense_id: str, user_id: str
    ) -> Dict[str, Any]:
        """Get a single expense with details"""

        # Validate ObjectIds
        try:
            group_obj_id = ObjectId(group_id)
            expense_obj_id = ObjectId(expense_id)
        except errors.InvalidId:  # Incorrect ObjectId format for group_id or expense_id
            logger.warning(
                f"Invalid ObjectId(s): group_id={group_id}, expense_id={expense_id}"
            )
            raise HTTPException(
                status_code=400, detail="Invalid group ID or expense ID"
            )
        except Exception as e:
            logger.error(f"Unexpected error parsing IDs: {e}")
            raise HTTPException(status_code=500, detail="Unable to process IDs")

        # Verify user access - handle both string and ObjectId userId formats
        try:
            user_obj_id = ObjectId(user_id)
        except:
            user_obj_id = user_id

        group = await self.groups_collection.find_one(
            {
                "_id": group_obj_id,
                "$or": [
                    {"members.userId": user_obj_id},
                    {"members.userId": user_id},
                    {"createdBy": user_obj_id},
                    {"createdBy": user_id},
                ],
            }
        )
        if not group:  # Unauthorized access
            raise HTTPException(
                status_code=403, detail="You are not a member of this group"
            )

        expense_doc = await self.expenses_collection.find_one(
            {"_id": expense_obj_id, "groupId": group_id}
        )
        if not expense_doc:  # Expense not found
            raise HTTPException(status_code=404, detail="Expense not found")

        expense = await self._expense_doc_to_response(expense_doc)

        # Get related settlements
        settlements_docs = await self.settlements_collection.find(
            {"expenseId": expense_id}
        ).to_list(None)

        settlements = []
        for doc in settlements_docs:
            settlement = Settlement(**{**doc, "_id": str(doc["_id"])})
            settlements.append(settlement)

        return {"expense": expense, "relatedSettlements": settlements}

    async def update_expense(
        self,
        group_id: str,
        expense_id: str,
        updates: ExpenseUpdateRequest,
        user_id: str,
    ) -> ExpenseResponse:
        """Update an expense"""

        try:
            # Validate ObjectId format
            try:
                expense_obj_id = ObjectId(expense_id)
            except errors.InvalidId:
                logger.warning(f"Invalid expense ID format: {expense_id}")
                raise HTTPException(status_code=400, detail="Invalid expense ID format")

            # Verify user access and that they created the expense
            expense_doc = await self.expenses_collection.find_one(
                {"_id": expense_obj_id, "groupId": group_id, "createdBy": user_id}
            )
            if not expense_doc:  # Expense not found or user not authorized
                raise HTTPException(
                    status_code=403,
                    detail="Not authorized to update this expense or it does not exist",
                )

            # Validate splits against current or new amount if both are being updated
            if updates.splits is not None and updates.amount is not None:
                total_split = sum(split.amount for split in updates.splits)
                if abs(total_split - updates.amount) > 0.01:
                    raise HTTPException(
                        status_code=400,
                        detail="Split amounts must sum to total expense amount",
                    )

            # If only splits are being updated, validate against current amount
            elif updates.splits is not None:
                current_amount = expense_doc["amount"]
                total_split = sum(split.amount for split in updates.splits)
                if abs(total_split - current_amount) > 0.01:
                    raise HTTPException(
                        status_code=400,
                        detail="Split amounts must sum to total expense amount",
                    )

            # Store original data for history
            original_data = {
                "amount": expense_doc["amount"],
                "description": expense_doc["description"],
                "splits": expense_doc["splits"],
            }

            # Build update document
            update_doc = {"updatedAt": datetime.utcnow()}

            if updates.description is not None:
                update_doc["description"] = updates.description
            if updates.amount is not None:
                update_doc["amount"] = updates.amount
            if updates.splits is not None:
                update_doc["splits"] = [split.model_dump() for split in updates.splits]
            if updates.tags is not None:
                update_doc["tags"] = updates.tags
            if updates.receiptUrls is not None:
                update_doc["receiptUrls"] = updates.receiptUrls

            # Only add history if there are actual changes
            if len(update_doc) > 1:  # More than just updatedAt
                # Get user name
                try:
                    user = await self.users_collection.find_one(
                        {"_id": ObjectId(user_id)}
                    )
                    user_name = (
                        user.get("name", "Unknown User") if user else "Unknown User"
                    )
                except Exception as e:
                    logger.warning(f"Failed to fetch user for history: {e}")
                    user_name = "Unknown User"

                history_entry = {
                    "_id": ObjectId(),
                    "userId": user_id,
                    "userName": user_name,
                    "beforeData": original_data,
                    "editedAt": datetime.utcnow(),
                }

                # Update expense with both $set and $push operations
                result = await self.expenses_collection.update_one(
                    {"_id": expense_obj_id},
                    {"$set": update_doc, "$push": {"history": history_entry}},
                )

                if result.matched_count == 0:  # Expense not found during update
                    raise HTTPException(
                        status_code=404, detail="Expense not found during update"
                    )
            else:
                # No actual changes, just update the timestamp
                result = await self.expenses_collection.update_one(
                    {"_id": expense_obj_id}, {"$set": update_doc}
                )

                if result.matched_count == 0:
                    raise HTTPException(
                        status_code=404, detail="Expense not found during update"
                    )

            # If splits changed, recalculate settlements
            if updates.splits is not None or updates.amount is not None:
                try:
                    # Delete old settlements for this expense
                    await self.settlements_collection.delete_many(
                        {"expenseId": expense_id}
                    )

                    # Get updated expense
                    updated_expense = await self.expenses_collection.find_one(
                        {"_id": expense_obj_id}
                    )

                    if updated_expense:
                        # Create new settlements
                        await self._create_settlements_for_expense(
                            updated_expense, user_id
                        )
                except Exception:
                    logger.error(
                        f"Warning: Failed to recalculate settlements", exc_info=True
                    )
                    # Continue anyway, as the expense update succeeded

            # Return updated expense
            updated_expense = await self.expenses_collection.find_one(
                {"_id": expense_obj_id}
            )
            if not updated_expense:
                raise HTTPException(
                    status_code=500, detail="Failed to retrieve updated expense"
                )

            # Update cached balances for the group
            await self._recalculate_group_balances(group_id)

            return await self._expense_doc_to_response(updated_expense)

        # Allowing FastAPI exception to bubble up for proper handling
        except HTTPException:
            raise
        except ValueError as ve:
            raise HTTPException(status_code=400, detail=str(ve))
        except (
            Exception
        ) as e:  # logger.exception() will provide the entire traceback, so its safe to remove traceback
            logger.exception(
                f"Unhandled error in update_expense for expense {expense_id}: {e}"
            )
            import traceback

            traceback.print_exc()
            raise Exception(f"Database error during expense update: {str(e)}")

    async def delete_expense(
        self, group_id: str, expense_id: str, user_id: str
    ) -> bool:
        """Delete an expense"""

        # Verify user access and that they created the expense
        expense_doc = await self.expenses_collection.find_one(
            {"_id": ObjectId(expense_id), "groupId": group_id, "createdBy": user_id}
        )
        if not expense_doc:
            logger.warning(
                f"Unauthorized delete attempt or missing expense: {expense_id} by user {user_id}"
            )
            raise HTTPException(
                status_code=403,
                detail="Not authorized to delete this expense or it does not exist",
            )

        # Delete settlements for this expense
        await self.settlements_collection.delete_many({"expenseId": expense_id})

        # Delete the expense
        result = await self.expenses_collection.delete_one(
            {"_id": ObjectId(expense_id)}
        )

        # Update cached balances for the group
        if result.deleted_count > 0:
            await self._recalculate_group_balances(group_id)

        return result.deleted_count > 0

    async def calculate_optimized_settlements(
        self, group_id: str, algorithm: str = "advanced"
    ) -> List[OptimizedSettlement]:
        """Calculate optimized settlements using specified algorithm"""

        if algorithm == "normal":
            return await self._calculate_normal_settlements(group_id)
        else:
            return await self._calculate_advanced_settlements(group_id)

    async def _calculate_normal_settlements(
        self, group_id: str
    ) -> List[OptimizedSettlement]:
        """Normal splitting algorithm - simplifies only direct relationships"""

        # Get all settlements for the group regardless of status
        # We calculate net balances from ALL transactions to get true outstanding amounts
        settlements = await self.settlements_collection.find(
            {"groupId": group_id}
        ).to_list(None)

        # Calculate net balances between each pair of users
        net_balances = defaultdict(lambda: defaultdict(float))
        user_names = {}

        for settlement in settlements:
            payer = settlement["payerId"]
            payee = settlement["payeeId"]
            amount = settlement["amount"]

            user_names[payer] = settlement["payerName"]
            user_names[payee] = settlement["payeeName"]

            # Net amount that payer owes to payee
            net_balances[payer][payee] += amount

        # Simplify direct relationships only
        optimized = []
        for payer in net_balances:
            for payee in net_balances[payer]:
                payer_owes_payee = net_balances[payer][payee]
                payee_owes_payer = net_balances[payee][payer]

                net_amount = payer_owes_payee - payee_owes_payer

                if net_amount > 0.01:  # Payer owes payee
                    optimized.append(
                        OptimizedSettlement(
                            fromUserId=payer,
                            toUserId=payee,
                            fromUserName=user_names.get(payer, "Unknown"),
                            toUserName=user_names.get(payee, "Unknown"),
                            amount=round(net_amount, 2),
                        )
                    )
                elif net_amount < -0.01:  # Payee owes payer
                    optimized.append(
                        OptimizedSettlement(
                            fromUserId=payee,
                            toUserId=payer,
                            fromUserName=user_names.get(payee, "Unknown"),
                            toUserName=user_names.get(payer, "Unknown"),
                            amount=round(-net_amount, 2),
                        )
                    )

        return optimized

    async def _calculate_advanced_settlements(
        self, group_id: str
    ) -> List[OptimizedSettlement]:
        """Advanced settlement algorithm using graph optimization"""

        # Get all settlements for the group regardless of status
        # We calculate net balances from ALL transactions to get true outstanding amounts
        settlements = await self.settlements_collection.find(
            {"groupId": group_id}
        ).to_list(None)

        # Calculate net balance for each user (what they owe - what they are owed)
        user_balances = defaultdict(float)
        user_names = {}

        for settlement in settlements:
            payer = settlement["payerId"]
            payee = settlement["payeeId"]
            amount = settlement["amount"]

            user_names[payer] = settlement["payerName"]
            user_names[payee] = settlement["payeeName"]

            # In our settlement model:
            # payerId = debtor (person who OWES money)
            # payeeId = creditor (person who is OWED money)
            # So: payer owes payee the amount
            user_balances[payer] += amount  # Payer owes money (positive = debtor)
            user_balances[payee] -= amount  # Payee is owed money (negative = creditor)

        # Separate debtors (positive balance) and creditors (negative balance)
        debtors = []  # (user_id, amount_owed)
        creditors = []  # (user_id, amount_owed_to_them)

        for user_id, balance in user_balances.items():
            if balance > 0.01:
                debtors.append([user_id, balance])
            elif balance < -0.01:
                creditors.append([user_id, -balance])

        # Sort debtors by amount owed (descending)
        debtors.sort(key=lambda x: x[1], reverse=True)
        # Sort creditors by amount owed to them (descending)
        creditors.sort(key=lambda x: x[1], reverse=True)

        # Use two-pointer technique to minimize transactions
        optimized = []
        i, j = 0, 0

        while i < len(debtors) and j < len(creditors):
            debtor_id, debt_amount = debtors[i]
            creditor_id, credit_amount = creditors[j]

            # Settle the minimum of what debtor owes and what creditor is owed
            settlement_amount = min(debt_amount, credit_amount)

            if settlement_amount > 0.01:
                optimized.append(
                    OptimizedSettlement(
                        fromUserId=debtor_id,
                        toUserId=creditor_id,
                        fromUserName=user_names.get(debtor_id, "Unknown"),
                        toUserName=user_names.get(creditor_id, "Unknown"),
                        amount=round(settlement_amount, 2),
                    )
                )

            # Update remaining amounts
            debtors[i][1] -= settlement_amount
            creditors[j][1] -= settlement_amount

            # Move to next debtor if current one is settled
            if debtors[i][1] <= 0.01:
                i += 1

            # Move to next creditor if current one is settled
            if creditors[j][1] <= 0.01:
                j += 1

        return optimized

    async def _recalculate_group_balances(self, group_id: str) -> Dict[str, float]:
        """
        Recalculate and cache member balances for a group.

        Uses the optimized settlement algorithm to compute net balances,
        then stores them in the group document for fast reads.

        Returns:
            Dict mapping userId to their net balance (positive = owed, negative = owes)
        """
        # Get optimized settlements for this group
        optimized = await self._calculate_advanced_settlements(group_id)

        # Convert settlements to per-member net balances
        member_balances: Dict[str, float] = defaultdict(float)
        for settlement in optimized:
            # fromUserId owes money (negative balance)
            member_balances[settlement.fromUserId] -= settlement.amount
            # toUserId is owed money (positive balance)
            member_balances[settlement.toUserId] += settlement.amount

        # Update group document with cached balances
        await self.groups_collection.update_one(
            {"_id": ObjectId(group_id)},
            {
                "$set": {
                    "cachedBalances": dict(member_balances),
                    "balancesUpdatedAt": datetime.now(timezone.utc),
                }
            },
        )

        logger.debug(f"Updated cached balances for group {group_id}: {member_balances}")
        return dict(member_balances)

    async def _get_cached_balances(self, group_id: str) -> Dict[str, float]:
        """
        Get cached balances for a group, recalculating if missing.

        Returns:
            Dict mapping userId to their net balance
        """
        group = await self.groups_collection.find_one({"_id": ObjectId(group_id)})
        if not group:
            return {}

        cached = group.get("cachedBalances")
        if cached is not None:
            return cached

        # Cache miss - recalculate
        return await self._recalculate_group_balances(group_id)

    async def create_manual_settlement(
        self, group_id: str, settlement_data: SettlementCreateRequest, user_id: str
    ) -> Settlement:
        """Create a manual settlement record"""

        # Verify user access - handle both string and ObjectId userId formats
        try:
            user_obj_id = ObjectId(user_id)
        except:
            user_obj_id = user_id

        group = await self.groups_collection.find_one(
            {
                "_id": ObjectId(group_id),
                "$or": [
                    {"members.userId": user_obj_id},
                    {"members.userId": user_id},
                    {"createdBy": user_obj_id},
                    {"createdBy": user_id},
                ],
            }
        )
        if not group:
            logger.warning(
                f"Unauthorized access attempt to group {group_id} by user {user_id}"
            )
            raise HTTPException(
                status_code=403, detail="Group not found or user not a member"
            )

        # Get user names
        users = await self.users_collection.find(
            {
                "_id": {
                    "$in": [
                        ObjectId(settlement_data.payer_id),
                        ObjectId(settlement_data.payee_id),
                    ]
                }
            }
        ).to_list(None)
        user_names = {str(user["_id"]): user.get("name", "Unknown") for user in users}

        settlement_doc = {
            "_id": ObjectId(),
            "expenseId": None,  # Manual settlement
            "groupId": group_id,
            "payerId": settlement_data.payer_id,
            "payeeId": settlement_data.payee_id,
            "payerName": user_names.get(settlement_data.payer_id, "Unknown"),
            "payeeName": user_names.get(settlement_data.payee_id, "Unknown"),
            "amount": settlement_data.amount,
            "currency": group.get("currency", "USD"),
            "status": "completed",
            "description": settlement_data.description or "Manual settlement",
            "paidAt": settlement_data.paidAt or datetime.utcnow(),
            "createdAt": datetime.utcnow(),
        }

        await self.settlements_collection.insert_one(settlement_doc)

        # Update cached balances for the group
        await self._recalculate_group_balances(group_id)

        return Settlement(**{**settlement_doc, "_id": str(settlement_doc["_id"])})

    async def _expense_doc_to_response(self, doc: Dict[str, Any]) -> ExpenseResponse:
        """Convert expense document to response model"""
        return ExpenseResponse(**{**doc, "_id": str(doc["_id"])})

    async def _get_group_summary(
        self, group_id: str, optimized_settlements: List[OptimizedSettlement]
    ) -> Dict[str, Any]:
        """Get group summary statistics"""

        # Get total expenses
        pipeline = [
            {"$match": {"groupId": group_id}},
            {
                "$group": {
                    "_id": None,
                    "totalExpenses": {"$sum": "$amount"},
                    "expenseCount": {"$sum": 1},
                }
            },
        ]
        expense_result = await self.expenses_collection.aggregate(pipeline).to_list(
            None
        )
        expense_stats = (
            expense_result[0]
            if expense_result
            else {"totalExpenses": 0, "expenseCount": 0}
        )

        # Get total settlements count
        settlement_count = await self.settlements_collection.count_documents(
            {"groupId": group_id}
        )

        return {
            "totalExpenses": expense_stats["totalExpenses"],
            "totalSettlements": settlement_count,
            "optimizedSettlements": optimized_settlements,
        }

    async def get_group_settlements(
        self,
        group_id: str,
        user_id: str,
        status_filter: Optional[str] = None,
        page: int = 1,
        limit: int = 50,
    ) -> Dict[str, Any]:
        """Get settlements for a group with pagination"""

        # Verify user access - handle both string and ObjectId userId formats
        try:
            user_obj_id = ObjectId(user_id)
        except:
            user_obj_id = user_id

        group = await self.groups_collection.find_one(
            {
                "_id": ObjectId(group_id),
                "$or": [
                    {"members.userId": user_obj_id},
                    {"members.userId": user_id},
                    {"createdBy": user_obj_id},
                    {"createdBy": user_id},
                ],
            }
        )
        if not group:
            logger.warning(
                f"Unauthorized access attempt to group {group_id} by user {user_id}"
            )
            raise HTTPException(
                status_code=403, detail="Group not found or user not a member"
            )

        # Build query
        query = {"groupId": group_id}
        if status_filter:
            query["status"] = status_filter

        # Get total count
        total = await self.settlements_collection.count_documents(query)

        # Get settlements with pagination
        skip = (page - 1) * limit
        settlements_docs = (
            await self.settlements_collection.find(query)
            .sort("createdAt", -1)
            .skip(skip)
            .limit(limit)
            .to_list(None)
        )

        settlements = []
        for doc in settlements_docs:
            settlement = Settlement(**{**doc, "_id": str(doc["_id"])})
            settlements.append(settlement)

        return {
            "settlements": settlements,
            "total": total,
            "page": page,
            "limit": limit,
        }

    async def get_settlement_by_id(
        self, group_id: str, settlement_id: str, user_id: str
    ) -> Settlement:
        """Get a single settlement by ID"""

        # Verify user access - handle both string and ObjectId userId formats
        try:
            user_obj_id = ObjectId(user_id)
        except:
            user_obj_id = user_id

        group = await self.groups_collection.find_one(
            {
                "_id": ObjectId(group_id),
                "$or": [
                    {"members.userId": user_obj_id},
                    {"members.userId": user_id},
                    {"createdBy": user_obj_id},
                    {"createdBy": user_id},
                ],
            }
        )
        if not group:
            raise HTTPException(
                status_code=403, detail="Group not found or user not a member"
            )

        settlement_doc = await self.settlements_collection.find_one(
            {"_id": ObjectId(settlement_id), "groupId": group_id}
        )

        if not settlement_doc:
            raise HTTPException(status_code=404, detail="Settlement not found")

        return Settlement(**{**settlement_doc, "_id": str(settlement_doc["_id"])})

    async def update_settlement_status(
        self,
        group_id: str,
        settlement_id: str,
        status: SettlementStatus,
        paid_at: Optional[datetime] = None,
        user_id: str = None,
    ) -> Settlement:
        """Update settlement status"""

        update_doc = {"status": status.value, "updatedAt": datetime.utcnow()}

        if paid_at:
            update_doc["paidAt"] = paid_at

        result = await self.settlements_collection.update_one(
            {"_id": ObjectId(settlement_id), "groupId": group_id}, {"$set": update_doc}
        )

        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Settlement not found")

        # Get updated settlement
        settlement_doc = await self.settlements_collection.find_one(
            {"_id": ObjectId(settlement_id)}
        )

        # Update cached balances for the group
        await self._recalculate_group_balances(group_id)

        return Settlement(**{**settlement_doc, "_id": str(settlement_doc["_id"])})

    async def delete_settlement(
        self, group_id: str, settlement_id: str, user_id: str
    ) -> bool:
        """Delete a settlement"""

        # Verify user access
        group = await self.groups_collection.find_one(
            {"_id": ObjectId(group_id), "members.userId": user_id}
        )
        if not group:
            raise HTTPException(
                status_code=403, detail="Group not found or user not a member"
            )

        result = await self.settlements_collection.delete_one(
            {"_id": ObjectId(settlement_id), "groupId": group_id}
        )

        # Update cached balances for the group if deletion was successful
        if result.deleted_count > 0:
            await self._recalculate_group_balances(group_id)

        return result.deleted_count > 0

    async def get_user_balance_in_group(
        self, group_id: str, target_user_id: str, current_user_id: str
    ) -> Dict[str, Any]:
        """Get a user's balance within a specific group"""

        # Verify current user access
        group = await self.groups_collection.find_one(
            {"_id": ObjectId(group_id), "members.userId": current_user_id}
        )
        if not group:
            raise HTTPException(
                status_code=403, detail="Group not found or user not a member"
            )

        # Get user info
        user = await self.users_collection.find_one({"_id": ObjectId(target_user_id)})
        user_name = user.get("name", "Unknown") if user else "Unknown"

        # Calculate totals from settlements
        pipeline = [
            {
                "$match": {
                    "groupId": group_id,
                    "$or": [{"payerId": target_user_id}, {"payeeId": target_user_id}],
                }
            },
            {
                "$group": {
                    "_id": None,
                    "totalPaid": {
                        "$sum": {
                            "$cond": [
                                {"$eq": ["$payerId", target_user_id]},
                                "$amount",
                                0,
                            ]
                        }
                    },
                    "totalOwed": {
                        "$sum": {
                            "$cond": [
                                {"$eq": ["$payeeId", target_user_id]},
                                "$amount",
                                0,
                            ]
                        }
                    },
                }
            },
        ]

        result = await self.settlements_collection.aggregate(pipeline).to_list(None)
        balance_data = result[0] if result else {"totalPaid": 0, "totalOwed": 0}

        total_paid = balance_data["totalPaid"]
        total_owed = balance_data["totalOwed"]
        net_balance = total_paid - total_owed

        # Get pending settlements
        pending_settlements = await self.settlements_collection.find(
            {"groupId": group_id, "payeeId": target_user_id, "status": "pending"}
        ).to_list(None)

        pending_settlement_objects = []
        for doc in pending_settlements:
            settlement = Settlement(**{**doc, "_id": str(doc["_id"])})
            pending_settlement_objects.append(settlement)

        # Get recent expenses where user was involved
        recent_expenses = (
            await self.expenses_collection.find(
                {
                    "groupId": group_id,
                    "$or": [
                        {"createdBy": target_user_id},
                        {"splits.userId": target_user_id},
                    ],
                }
            )
            .sort("createdAt", -1)
            .limit(5)
            .to_list(None)
        )

        recent_expense_data = []
        for expense in recent_expenses:
            # Find user's share
            user_share = 0
            for split in expense["splits"]:
                if split["userId"] == target_user_id:
                    user_share = split["amount"]
                    break

            recent_expense_data.append(
                {
                    "expenseId": str(expense["_id"]),
                    "description": expense["description"],
                    "userShare": user_share,
                    "createdAt": expense["createdAt"],
                }
            )

        return {
            "userId": target_user_id,
            "userName": user_name,
            "totalPaid": total_paid,
            "totalOwed": total_owed,
            "netBalance": net_balance,
            "owesYou": net_balance > 0,
            "pendingSettlements": pending_settlement_objects,
            "recentExpenses": recent_expense_data,
        }

    async def get_friends_balance_summary(self, user_id: str) -> Dict[str, Any]:
        """
        Get cross-group friend balances using optimized settlements per group.

        This method now uses the same `calculate_optimized_settlements` algorithm
        used everywhere else, ensuring consistency across all balance calculations.

        Performance: N queries (one per group) for settlement calculation.
        The cached balances feature reduces repeated calculations.
        """

        # First, get all groups user belongs to
        try:
            user_object_id = ObjectId(user_id)
        except errors.InvalidId:
            user_object_id = None

        groups = await self.groups_collection.find(
            {
                "$or": [
                    {"members.userId": user_id},
                    (
                        {"members.userId": user_object_id}
                        if user_object_id
                        else {"_id": {"$exists": False}}
                    ),
                ]
            }
        ).to_list(length=500)

        if not groups:
            return {
                "friendsBalance": [],
                "summary": {
                    "totalOwedToYou": 0,
                    "totalYouOwe": 0,
                    "netBalance": 0,
                    "friendCount": 0,
                    "activeGroups": 0,
                },
            }

        # Build group map for name lookup
        groups_map = {str(g["_id"]): g.get("name", "Unknown Group") for g in groups}

        # Aggregate friend balances across all groups using optimized settlements
        # friend_id -> {"balance": float, "groups": [{"groupId", "groupName", "balance"}]}
        friend_balances: Dict[str, Dict[str, Any]] = defaultdict(
            lambda: {"balance": 0, "groups": []}
        )

        for group in groups:
            group_id = str(group["_id"])
            group_name = group.get("name", "Unknown Group")

            # Get optimized settlements for this group
            optimized = await self.calculate_optimized_settlements(group_id)

            for settlement in optimized:
                # Check if user is involved in this settlement
                if settlement.fromUserId == user_id:
                    # User owes friend (negative balance for user = friend owes nothing to user)
                    friend_id = settlement.toUserId
                    friend_balances[friend_id]["balance"] -= settlement.amount
                    friend_balances[friend_id]["groups"].append(
                        {
                            "groupId": group_id,
                            "groupName": group_name,
                            "balance": -settlement.amount,
                            "owesYou": False,
                        }
                    )
                elif settlement.toUserId == user_id:
                    # Friend owes user (positive balance = friend owes user)
                    friend_id = settlement.fromUserId
                    friend_balances[friend_id]["balance"] += settlement.amount
                    friend_balances[friend_id]["groups"].append(
                        {
                            "groupId": group_id,
                            "groupName": group_name,
                            "balance": settlement.amount,
                            "owesYou": True,
                        }
                    )

        # Filter out friends with zero balance
        friend_balances = {
            fid: data
            for fid, data in friend_balances.items()
            if abs(data["balance"]) > 0.01
        }

        if not friend_balances:
            return {
                "friendsBalance": [],
                "summary": {
                    "totalOwedToYou": 0,
                    "totalYouOwe": 0,
                    "netBalance": 0,
                    "friendCount": 0,
                    "activeGroups": len(groups),
                },
            }

        # Batch fetch all friend details
        friend_ids = list(friend_balances.keys())
        try:
            friends_cursor = self.users_collection.find(
                {
                    "_id": {
                        "$in": [
                            ObjectId(fid)
                            for fid in friend_ids
                            if ObjectId.is_valid(fid)
                        ]
                    }
                },
                {"_id": 1, "name": 1, "imageUrl": 1},
            )
            friends_list = await friends_cursor.to_list(length=500)
            friends_map = {str(f["_id"]): f for f in friends_list}
        except Exception as e:
            logger.error(f"Error batch fetching friend details: {e}")
            friends_map = {}

        # Build final response
        friends_balance_list = []
        user_totals = {"totalOwedToYou": 0, "totalYouOwe": 0}

        for friend_id, data in friend_balances.items():
            total_balance = data["balance"]
            friend_details = friends_map.get(friend_id)

            # Build friend balance object
            friend_data = {
                "userId": friend_id,
                "userName": (
                    friend_details.get("name", "Unknown")
                    if friend_details
                    else "Unknown"
                ),
                "userImageUrl": (
                    friend_details.get("imageUrl") if friend_details else None
                ),
                "netBalance": round(total_balance, 2),
                "owesYou": total_balance > 0,
                "breakdown": data["groups"],
                "lastActivity": datetime.now(
                    timezone.utc
                ),  # TODO: Calculate actual last activity
            }

            friends_balance_list.append(friend_data)

            # Update totals
            if total_balance > 0:
                user_totals["totalOwedToYou"] += total_balance
            else:
                user_totals["totalYouOwe"] += abs(total_balance)

        return {
            "friendsBalance": friends_balance_list,
            "summary": {
                "totalOwedToYou": round(user_totals["totalOwedToYou"], 2),
                "totalYouOwe": round(user_totals["totalYouOwe"], 2),
                "netBalance": round(
                    user_totals["totalOwedToYou"] - user_totals["totalYouOwe"], 2
                ),
                "friendCount": len(friends_balance_list),
                "activeGroups": len(groups),
            },
        }

    async def get_overall_balance_summary(self, user_id: str) -> Dict[str, Any]:
        """
        Get overall balance summary for a user using cached balances.

        Performance: O(1) read per group from cached balances vs O(N) aggregations.
        """

        # Get all groups user belongs to
        groups = await self.groups_collection.find({"members.userId": user_id}).to_list(
            None
        )

        total_owed_to_you = 0
        total_you_owe = 0
        groups_summary = []

        for group in groups:
            group_id = str(group["_id"])

            # Read from cached balances (will recalculate if missing)
            cached = group.get("cachedBalances")
            if cached is None:
                # Cache miss - recalculate
                cached = await self._recalculate_group_balances(group_id)

            # Get user's balance from cache
            user_balance = cached.get(user_id, 0)

            if abs(user_balance) > 0.01:  # Only include groups with significant balance
                groups_summary.append(
                    {
                        "group_id": group_id,
                        "group_name": group["name"],
                        "yourBalanceInGroup": user_balance,
                    }
                )

                if user_balance > 0:
                    total_owed_to_you += user_balance
                else:
                    total_you_owe += abs(user_balance)

        return {
            "totalOwedToYou": total_owed_to_you,
            "totalYouOwe": total_you_owe,
            "netBalance": total_owed_to_you - total_you_owe,
            "currency": "USD",
            "groupsSummary": groups_summary,
        }

    async def get_group_analytics(
        self,
        group_id: str,
        user_id: str,
        period: str = "month",
        year: int = None,
        month: int = None,
    ) -> Dict[str, Any]:
        """Get expense analytics for a group"""

        # Verify user access
        group = await self.groups_collection.find_one(
            {"_id": ObjectId(group_id), "members.userId": user_id}
        )
        if not group:
            raise HTTPException(
                status_code=403, detail="Group not found or user not a member"
            )

        # Build date range
        if period == "month" and year and month:
            start_date = datetime(year, month, 1)
            if month == 12:
                end_date = datetime(year + 1, 1, 1)
            else:
                end_date = datetime(year, month + 1, 1)
            period_str = f"{year}-{month:02d}"
        elif period == "6months":
            # Last 6 months from today
            now = datetime.utcnow()
            start_date = (now - timedelta(days=180)).replace(day=1)
            end_date = now
            period_str = f"Last 6 months"
        elif period == "year":
            # Use provided year or default to current year
            target_year = year if year else datetime.utcnow().year
            start_date = datetime(target_year, 1, 1)
            end_date = datetime(target_year + 1, 1, 1)
            period_str = str(target_year)
        else:
            # Default to current month
            now = datetime.utcnow()
            start_date = datetime(now.year, now.month, 1)
            if now.month == 12:
                end_date = datetime(now.year + 1, 1, 1)
            else:
                end_date = datetime(now.year, now.month + 1, 1)
            period_str = f"{now.year}-{now.month:02d}"

        # Get expenses in the period
        expenses = await self.expenses_collection.find(
            {"groupId": group_id, "createdAt": {"$gte": start_date, "$lt": end_date}}
        ).to_list(None)

        total_expenses = sum(expense["amount"] for expense in expenses)
        expense_count = len(expenses)
        avg_expense = total_expenses / expense_count if expense_count > 0 else 0

        # Analyze categories (tags)
        tag_stats = defaultdict(lambda: {"amount": 0, "count": 0})
        for expense in expenses:
            tags = expense.get("tags", [])
            if not tags:
                tags = ["uncategorized"]
            for tag in tags:
                tag_stats[tag]["amount"] += expense["amount"]
                tag_stats[tag]["count"] += 1

        top_categories = []
        for tag, stats in sorted(
            tag_stats.items(), key=lambda x: x[1]["amount"], reverse=True
        ):
            top_categories.append(
                {
                    "category": tag,  # Changed from 'tag' to 'category' for frontend consistency
                    "amount": stats["amount"],
                    "count": stats["count"],
                    "percentage": round(
                        (
                            (stats["amount"] / total_expenses * 100)
                            if total_expenses > 0
                            else 0
                        ),
                        1,
                    ),
                }
            )

        # Member contributions (aggregated)
        member_contributions = []
        group_members = {member["userId"]: member for member in group["members"]}

        for member_id in group_members:
            # Get user info
            user = await self.users_collection.find_one({"_id": ObjectId(member_id)})
            user_name = user.get("name", "Unknown") if user else "Unknown"

            # Calculate contributions
            total_paid = sum(
                expense["amount"]
                for expense in expenses
                if expense["paidBy"] == member_id
            )

            total_owed = 0
            for expense in expenses:
                for split in expense["splits"]:
                    if split["userId"] == member_id:
                        total_owed += split["amount"]

            member_contributions.append(
                {
                    "userId": member_id,
                    "userName": user_name,
                    "totalPaid": total_paid,
                    "totalOwed": total_owed,
                    "netContribution": total_paid - total_owed,
                }
            )

        # Member contribution timeline (cumulative by date)
        # Only generate data points for dates that have expenses
        contribution_timeline = []

        # Get unique expense dates, sorted
        expense_dates = sorted(set(e["createdAt"].date() for e in expenses))

        if expense_dates:
            # Pre-fetch all member names to avoid repeated DB queries
            member_names = {}
            for member_id in group_members:
                user = await self.users_collection.find_one(
                    {"_id": ObjectId(member_id)}
                )
                member_names[member_id] = (
                    user.get("name", "Unknown") if user else "Unknown"
                )

            # Generate timeline for each expense date
            for expense_date in expense_dates:
                day_data = {"date": expense_date.strftime("%Y-%m-%d")}

                # Get expenses up to and including this date (cumulative)
                cumulative_expenses = [
                    e for e in expenses if e["createdAt"].date() <= expense_date
                ]

                # Calculate total expenses up to this date
                total_expenses_cumulative = sum(
                    e["amount"] for e in cumulative_expenses
                )
                day_data["Total Expenses"] = total_expenses_cumulative

                # Calculate cumulative contributions for each member
                for member_id, user_name in member_names.items():
                    # Cumulative amount paid by this member
                    cumulative_paid = sum(
                        e["amount"]
                        for e in cumulative_expenses
                        if e["paidBy"] == member_id
                    )
                    day_data[user_name] = cumulative_paid

                contribution_timeline.append(day_data)

        # Expense trends (daily)
        expense_trends = []
        current_date = start_date
        while current_date < end_date:
            day_expenses = [
                e for e in expenses if e["createdAt"].date() == current_date.date()
            ]
            expense_trends.append(
                {
                    "date": current_date.strftime("%Y-%m-%d"),
                    "amount": sum(e["amount"] for e in day_expenses),
                    "count": len(day_expenses),
                }
            )
            current_date += timedelta(days=1)

        return {
            "period": period_str,
            "totalExpenses": total_expenses,
            "expenseCount": expense_count,
            "avgExpenseAmount": round(avg_expense, 2),
            "topCategories": top_categories[:10],  # Top 10 categories
            "memberContributions": member_contributions,
            "contributionTimeline": contribution_timeline,  # New timeline data
            "expenseTrends": expense_trends,
        }


# Create service instance
expense_service = ExpenseService()
