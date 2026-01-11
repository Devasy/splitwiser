# Splitwiser API Documentation

Welcome to the official API documentation for the Splitwiser backend. This document provides a comprehensive guide to understanding and interacting with our API.

---

## 1. Introduction

The Splitwiser API is a modern, RESTful service built with FastAPI that powers the Splitwiser application. It provides a complete set of endpoints for managing users, groups, expenses, and settlements, with a focus on security, performance, and ease of use.

This documentation is divided into several modules, each covering a distinct area of the API's functionality.

---

## 2. General Concepts

### **Authentication**

All API endpoints (with the exception of sign-up and login) are protected and require a valid **JSON Web Token (JWT)** to be included in the request.

* **Flow**: To access protected routes, you must first authenticate using one of the login endpoints to receive an `access_token`. This token must then be sent in the `Authorization` header of all subsequent requests with the `Bearer` scheme.
    ```
    Authorization: Bearer <your_access_token>
    ```
* **Token Expiry**: Access tokens are short-lived. When one expires, you must use the provided `refresh_token` to obtain a new one.

For a complete guide on how to register, log in, and manage tokens, please see the detailed **[Authentication API Documentation](./authentication.md)**.

---

## 3. API Reference

The API is organized into logical modules. For detailed information on the endpoints, request/response models, and business logic for each module, please refer to the documents below.

* **[Authentication](./authentication.md)**: User sign-up, login (email & Google), and token management.
* **[Users](./users.md)**: Managing user profiles.
* **[Groups](./groups.md)**: Creating groups, managing membership, and handling roles.
* **[Expenses](./expenses.md)**: Creating, splitting, and managing expenses within groups.
* **[Settlements](./settlements.md)**: Managing debts, recording payments, and using the debt optimization engine.

---

## 4. Examples & Tools

To help you get started quickly, we provide practical examples and tools.

* **[cURL Examples](./examples/curl_examples.md)**: A collection of copy-pasteable `cURL` commands for interacting with the API from your terminal.
* **[Postman Collection](./examples/postman_collection.json)**: A comprehensive Postman collection that you can import to immediately start making requests to all available endpoints.
