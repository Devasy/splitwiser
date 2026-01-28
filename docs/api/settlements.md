# Settlements API Documentation

This document provides a complete and definitive specification for the API endpoints related to managing, optimizing, and recording settlements (debts) within groups. All endpoints require authentication.

---

## 1. Core Concepts & Business Logic

### **What is a Settlement?**

A Settlement records an obligation between two users. For auto-generated settlements (from an Expense): payerId is the original expense payer (the creditor — the person who paid the expense and is owed money) and payeeId is the member who owes that share (the debtor). For manual settlements (user-recorded repayments): payer_id is the member making the payment now and payee_id is the recipient.

* **Automatic Settlements**: When an expense is created, the system automatically generates a `pending` settlement record for each person who owes a share of the cost.
* **Manual Settlements**: Users can manually record a `completed` settlement to track a payment made outside the application (e.g., paying someone back in cash).

### **Debt Optimization Algorithms**

The system's most powerful feature is its ability to simplify all the individual debts in a group into the minimum number of payments required to clear all balances. This is handled by two distinct algorithms:

* **Normal (`algorithm=normal`)**: A basic simplification that only nets out direct, two-way debts. For example, if Alice owes Bob $20 from one expense and Bob owes Alice $15 from another, this algorithm simplifies it to a single settlement: "Alice pays Bob $5."
* **Advanced (`algorithm=advanced`)**: A more powerful graph-based algorithm that minimizes the total number of transactions for the      entire group. 
    * **Logic**:
        1.  It calculates the net balance of every member (total paid - total owed).
        2.  It separates all members into two lists: "debtors" (who owe money) and "creditors" (who are owed money).
        3.  Using a two-pointer approach, it matches the person who owes the most with the person who is owed the most, creating a single payment to clear as much debt as possible.
        4.  This process continues until all debts are consolidated into the fewest possible transactions.

---

## 2. Settlement Management Endpoints

These endpoints are for recording and managing payments between group members to settle debts. All endpoints are prefixed with `/groups/{group_id}`.

### **`POST /settlements`**

Manually records a payment settlement between two users. This is for tracking payments made outside the app.

* **Server-Side Logic**:
    1.  Verifies the current user is a member of the group.
    2.  Creates a new settlement document in the `settlements` collection with a status of `completed`.
* **Request Body** (`SettlementCreateRequest`):
    ```json
    {
        "payer_id": "user_id_1",
        "payee_id": "user_id_2",
        "amount": 25.00,
        "description": "Paid back for coffee",
        "paidAt": "2025-08-14T10:00:00Z"
    }
    ```
* **Response** (`Settlement`): Returns the newly created `completed` settlement object.

### **`GET /settlements`**

Retrieves a list of both pending and optimized settlements for a group.

* **Query Parameters**:
    * `status`: Optional filter for settlement status (e.g., "pending").
    * `page` & `limit`: For paginating through the list of raw settlements.
    * `algorithm`: The settlement algorithm to use (`normal` or `advanced`).
* **Response** (`SettlementListResponse`):
    ```json
    {
      "settlements": [ /* ... list of raw Settlement objects ... */ ],
      "optimizedSettlements": [ /* ... list of OptimizedSettlement objects ... */ ],
      "summary": { /* ... summary dictionary ... */ },
      "pagination": { /* ... pagination details ... */ }
    }
    ```

### **`GET /settlements/{settlement_id}`**

Retrieves the details for a single settlement.

* **Response** (`Settlement`):
    ```json
    {
      "id": "settlement_id_string",
      "expenseId": "expense_id_string_or_null",
      "groupId": "group_id_string",
      "payerId": "user_id_1",
      "payeeId": "user_id_2",
      "payerName": "Alice",
      "payeeName": "Bob",
      "amount": 50.25,
      "status": "pending",
      "description": "Share for Team Dinner",
      "paidAt": null,
      "createdAt": "2025-08-13T12:00:00Z"
    }
    ```

### **`PATCH /settlements/{settlement_id}`**

Updates the status of a settlement, typically to mark it as paid.

* **Request Body** (`SettlementUpdateRequest`):
    ```json
    {
        "status": "completed",
        "paidAt": "2025-08-14T14:00:00Z"
    }
    ```
* **Response** (`Settlement`): Returns the updated settlement object.

### **`DELETE /settlements/{settlement_id}`**

Deletes or undoes a recorded settlement.

* **Successful Response**: `{"success": true, "message": "Settlement record deleted successfully."}`

### **`POST /settlements/optimize`**

Calculates and returns the most efficient way to settle all debts in a group.

* **Query Parameters**:
    * `algorithm`: `normal` or `advanced` (default).
* **Response** (`OptimizedSettlementsResponse`):
    ```json
    {
      "optimizedSettlements": [
        {
          "fromUserId": "user_id_A",
          "toUserId": "user_id_B",
          "fromUserName": "Charlie",
          "toUserName": "David",
          "amount": 75.50,
          "consolidatedExpenses": []
        }
      ],
      "savings": {
        "originalTransactions": 15,
        "optimizedTransactions": 4,
        "reductionPercentage": 73.3
      }
    }
    