# cURL API Examples

This document provides practical `cURL` examples for interacting with the Splitwiser API.

## 1. Prerequisites

Before running these commands, you'll need to set some environment variables in your terminal. This will make the examples easier to use.

```bash
export API_URL="http://localhost:8000"

export ACCESS_TOKEN="your_jwt_access_token_here"
export GROUP_ID="your_group_id_here"
export EXPENSE_ID="your_expense_id_here"
export SETTLEMENT_ID="your_settlement_id_here"
export MEMBER_ID="a_group_member_id_here"
```

## 2. Authentication (`/auth`)

### **Sign up with Email**
```bash
curl -X POST "$API_URL/auth/signup/email" \
-H "Content-Type: application/json" \
-d '{
  "email": "testuser@example.com",
  "password": "strongpassword123",
  "name": "Test User"
}'
```

### **Login with Email**
```bash
curl -X POST "$API_URL/auth/login/email" \
-H "Content-Type: application/json" \
-d '{
  "email": "testuser@example.com",
  "password": "strongpassword123"
}'
```

### **Refresh Token**
```bash
curl -X POST "$API_URL/auth/refresh" \
-H "Content-Type: application/json" \
-d '{
  "refresh_token": "your_refresh_token_here"
}'
```

### **Verify Token**
```bash
curl -X POST "$API_URL/auth/token/verify" \
-H "Content-Type: application/json" \
-d '{
  "access_token": "'"$ACCESS_TOKEN"'"
}'
```

### **Request Password Reset**
```bash
curl -X POST "$API_URL/auth/password/reset/request" \
-H "Content-Type: application/json" \
-d '{
  "email": "testuser@example.com"
}'
```

### **Confirm Password Reset**
```bash
curl -X POST "$API_URL/auth/password/reset/confirm" \
-H "Content-Type: application/json" \
-d '{
  "reset_token": "token_from_email_link",
  "new_password": "newstrongpassword456"
}'
```

## 3. User Profile (`/users`)

### **Get Current User Profile**
```bash
curl -X GET "$API_URL/users/me" \
-H "Authorization: Bearer $ACCESS_TOKEN"
```

### **Update User Profile**
```bash
curl -X PATCH "$API_URL/users/me" \
-H "Authorization: Bearer $ACCESS_TOKEN" \
-H "Content-Type: application/json" \
-d '{
  "name": "Updated Test User",
  "currency": "EUR"
}'
```

### **Delete User Account**
```bash
curl -X DELETE "$API_URL/users/me" \
-H "Authorization: Bearer $ACCESS_TOKEN"
```

## 4. Groups (`/groups`)

### **Create a Group**
```bash
curl -X POST "$API_URL/groups" \
-H "Authorization: Bearer $ACCESS_TOKEN" \
-H "Content-Type: application/json" \
-d '{
  "name": "Vacation Crew",
  "currency": "USD"
}'
```

### **List User's Groups**
```bash
curl -X GET "$API_URL/groups" \
-H "Authorization: Bearer $ACCESS_TOKEN"
```

### **Get Group Details**
```bash
curl -X GET "$API_URL/groups/$GROUP_ID" \
-H "Authorization: Bearer $ACCESS_TOKEN"
```

### **Join a Group**
```bash
curl -X POST "$API_URL/groups/join" \
-H "Authorization: Bearer $ACCESS_TOKEN" \
-H "Content-Type: application/json" \
-d '{
  "joinCode": "A1B2C3"
}'
```

### **Leave a Group**
```bash
curl -X POST "$API_URL/groups/$GROUP_ID/leave" \
-H "Authorization: Bearer $ACCESS_TOKEN"
```

### **Remove a Member (Admin Only)**
```bash
curl -X DELETE "$API_URL/groups/$GROUP_ID/members/$MEMBER_ID" \
-H "Authorization: Bearer $ACCESS_TOKEN"
```

## 5. Expenses (`/groups/{group_id}/expenses`)

### **Create an Expense**
```bash
curl -X POST "$API_URL/groups/$GROUP_ID/expenses" \
-H "Authorization: Bearer $ACCESS_TOKEN" \
-H "Content-Type: application/json" \
-d '{
  "description": "Dinner",
  "amount": 120.00,
  "paidBy": "user_id_who_paid",
  "splitType": "equal",
  "splits": [
    {"userId": "user_id_who_paid", "amount": 40.00},
    {"userId": "another_user_id", "amount": 40.00},
    {"userId": "third_user_id", "amount": 40.00}
  ]
}'
```

### **List Group Expenses**
```bash
curl -X GET "$API_URL/groups/$GROUP_ID/expenses?page=1&limit=10" \
-H "Authorization: Bearer $ACCESS_TOKEN"
```

### **Update an Expense**
```bash
curl -X PATCH "$API_URL/groups/$GROUP_ID/expenses/$EXPENSE_ID" \
-H "Authorization: Bearer $ACCESS_TOKEN" \
-H "Content-Type: application/json" \
-d '{
  "description": "Dinner at the fancy place"
}'
```

## 6. Settlements (`/groups/{group_id}/settlements`)

### **Manually Record a Payment**
```bash
curl -X POST "$API_URL/groups/$GROUP_ID/settlements" \
-H "Authorization: Bearer $ACCESS_TOKEN" \
-H "Content-Type: application/json" \
-d '{
  "payer_id": "user_id_who_paid_back",
  "payee_id": "user_id_who_received",
  "amount": 50.00,
  "description": "Cash payment for groceries"
}'
```

### **Get Group Settlements**
```bash
curl -X GET "$API_URL/groups/$GROUP_ID/settlements?status=pending" \
-H "Authorization: Bearer $ACCESS_TOKEN"
```

### **Mark a Settlement as Paid**
```bash
curl -X PATCH "$API_URL/groups/$GROUP_ID/settlements/$SETTLEMENT_ID" \
-H "Authorization: Bearer $ACCESS_TOKEN" \
-H "Content-Type: application/json" \
-d '{
  "status": "completed"
}'
```


### **Optimize Settlements**
```bash
curl -X POST "$API_URL/groups/$GROUP_ID/settlements/optimize?algorithm=advanced" \
-H "Authorization: Bearer $ACCESS_TOKEN"
```