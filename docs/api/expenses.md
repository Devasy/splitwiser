# Expenses API Documentation

This document provides a detailed specification for the API endpoints related to managing expenses, attachments, balances, and analytics within groups. All endpoints require authentication and proper group membership.

*For details on how debts are calculated, simplified, and paid, please see the **Settlements.md**

---

## 1. Core Concepts & Business Logic

### **Core Concept: Expenses**

* An **Expense** is a single financial event, like "Dinner for $100," that details who paid and how the cost is split among members.
* When an expense is created, the system automatically calculates the resulting debts for each member. These debts are recorded as **Settlements**.

### **Database Collections**

* **`expenses`**: Stores all expense documents, including descriptions, amounts, splits, and a history of edits.
* **`groups`** & **`users`**: Used to verify user membership, permissions, and retrieve user details.
* **`settlements`**: This collection is used to record the individual debts that result from expenses.

---

## 2. Expense Management

These endpoints handle the creation, retrieval, updating, and deletion of expenses. All endpoints are prefixed with `/groups/{group_id}`.

### **`POST /expenses`**

Creates a new expense within a specified group.

* **Server-Side Logic**:
    1.  Verifies the user is a member of the group.
    2.  Creates the expense document in the `expenses` collection.
    3.  Automatically calculates and records the resulting debts (settlements).
    4.  Returns the new expense object, the calculated settlements, and a group summary.
* **Request Body** (`ExpenseCreateRequest`):
    ```json
    {
      "description": "Team Dinner",
      "amount": 150.75,
      "splits": [
        { "userId": "user_id_1", "amount": 50.25, "type": "equal" },
        { "userId": "user_id_2", "amount": 100.50, "type": "unequal" }
      ],
      "splitType": "unequal",
      "paidBy": "user_id_2",
      "tags": ["food", "social"]
    }
    ```
* **Response** (`ExpenseCreateResponse`):
    ```json
    {
      "expense": { /* ... ExpenseResponse object ... */ },
      "settlements": [ /* ... list of Settlement objects ... */ ],
      "groupSummary": { /* ... GroupSummary object ... */ }
    }
    ```

### **`GET /expenses`**

Lists all expenses for a group with support for pagination and filtering.

* **Query Parameters**:
    * `page`, `limit`, `from`, `to`, `tags`.
* **Response** (`ExpenseListResponse`):
    ```json
    {
      "expenses": [ /* ... list of ExpenseResponse objects ... */ ],
      "pagination": { /* ... pagination details ... */ },
      "summary": { "totalAmount": 1234.56, "expenseCount": 50, "avgExpense": 24.69 }
    }
    ```

### **`GET /expenses/{expense_id}`**

Retrieves the details for a single expense and its related settlements.

* **Response**: A dictionary containing the `ExpenseResponse` object and a list of all `Settlement` objects associated with it.

### **`PATCH /expenses/{expense_id}`**

Updates an existing expense.

* **Server-Side Logic**:
    1.  Verifies that the user attempting the update is the one who originally created the expense.
    2.  Creates a history entry to log the changes.
    3.  If the amount or splits are modified, it automatically recalculates the associated settlements.
* **Request Body** (`ExpenseUpdateRequest`):
    ```json
    {
      "description": "Updated description for groceries",
      "tags": ["household", "urgent"]
    }
    ```
* **Response** (`ExpenseResponse`): Returns the complete, updated expense object.

### **`DELETE /expenses/{expense_id}`**

Deletes an expense.

* **Server-Side Logic**:
    1.  Verifies the user is the creator of the expense.
    2.  Deletes all associated settlement records.
    3.  Deletes the expense document itself.
* **Successful Response**: `{"success": True}`

---

## 3. Balance & Analytics Endpoints

### **User-Centric Balances (prefixed with `/users/me`)**

* **`GET /friends-balance`**: Retrieves the current user's aggregated net balance with every friend across all shared groups.
* **`GET /balance-summary`**: Retrieves the user's overall financial summary: total amount owed to them, total amount they owe, and a breakdown of their balance in each group.

### **Group-Specific Balances & Analytics (prefixed with `/groups/{group_id}`)**

* **`GET /users/{user_id}/balance`**: Gets a specific user's detailed balance within one particular group.
* **`GET /analytics`**: Provides detailed expense analytics for the group over a specified period (`week`, `month`, `year`), including total spend, top categories, member contributions, and daily spending trends.

---

## 4. Expense Attachments

* **`POST /expenses/{expense_id}/attachments`**: Uploads a file (e.g., a receipt) for an expense.
