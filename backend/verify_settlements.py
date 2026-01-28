"""
Verification script for settlement calculations.

Scenario:
- Friends: A, B, C, D, E, F
- Group 1: A, B, C, D
- Group 2: B, C, E, F

Expenses:
Group 1:
  1. A pays $100 for dinner, split equally (each owes $25)
  2. B pays $80 for groceries, split equally (each owes $20)

Group 2:
  3. E pays $120 for concert, split equally (each owes $30)
  4. C pays $40 for taxi, split equally (each owes $10)

Expected Balances:
- A: +$55 (Group1: $75 owed - $20 owes)
- B: -$5 (Group1: +$35, Group2: -$40)
- C: -$45 (Group1: -$45, Group2: $0)
- D: -$45 (Group1: -$45)
- E: +$80 (Group2: +$80)
- F: -$40 (Group2: -$40)
"""

import asyncio
from typing import Any, Dict, List

import httpx

# API Configuration
API_URL = "http://localhost:8000"  # Adjust if needed

# Test users
USERS = {
    "A": {"email": "user.a@test.com", "password": "password123", "name": "User A"},
    "B": {"email": "user.b@test.com", "password": "password123", "name": "User B"},
    "C": {"email": "user.c@test.com", "password": "password123", "name": "User C"},
    "D": {"email": "user.d@test.com", "password": "password123", "name": "User D"},
    "E": {"email": "user.e@test.com", "password": "password123", "name": "User E"},
    "F": {"email": "user.f@test.com", "password": "password123", "name": "User F"},
}


class SettlementVerifier:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.tokens: Dict[str, str] = {}
        self.user_ids: Dict[str, str] = {}
        self.groups: Dict[str, str] = {}

    async def signup_user(self, client: httpx.AsyncClient, user_key: str):
        """Sign up a new user"""
        user_data = USERS[user_key]
        print(f"📝 Signing up {user_key} ({user_data['name']})...")

        try:
            response = await client.post(
                f"{self.base_url}/auth/signup/email",
                json={
                    "email": user_data["email"],
                    "password": user_data["password"],
                    "name": user_data["name"],
                },
            )

            if response.status_code in [200, 201]:
                data = response.json()
                self.tokens[user_key] = data["access_token"]
                self.user_ids[user_key] = data["user"]["_id"]
                print(
                    f"  ✅ {user_key} signed up successfully (ID: {self.user_ids[user_key][:8]}...)"
                )
            elif response.status_code == 400:
                # User might already exist, try login
                print(f"  ⚠️  User exists, trying login...")
                await self.login_user(client, user_key)
            else:
                print(f"  ❌ Signup failed: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"  ❌ Error: {e}")

    async def login_user(self, client: httpx.AsyncClient, user_key: str):
        """Login an existing user"""
        user_data = USERS[user_key]

        response = await client.post(
            f"{self.base_url}/auth/login/email",
            json={
                "email": user_data["email"],
                "password": user_data["password"],
            },
        )

        if response.status_code == 200:
            data = response.json()
            self.tokens[user_key] = data["access_token"]
            self.user_ids[user_key] = data["user"]["_id"]
            print(f"  ✅ {user_key} logged in successfully")
        else:
            print(f"  ❌ Login failed: {response.status_code}")

    async def create_group(
        self, client: httpx.AsyncClient, creator: str, name: str, members: List[str]
    ) -> str:
        """Create a group and add members"""
        print(f"\n👥 Creating group '{name}' by {creator}...")

        headers = {"Authorization": f"Bearer {self.tokens[creator]}"}

        # Create group
        response = await client.post(
            f"{self.base_url}/groups",
            json={"name": name, "currency": "USD"},
            headers=headers,
        )

        if response.status_code != 201:
            print(
                f"  ❌ Failed to create group: {response.status_code} - {response.text}"
            )
            return None

        group_data = response.json()
        group_id = group_data["_id"]
        join_code = group_data["joinCode"]

        print(f"  ✅ Group created (ID: {group_id[:8]}..., Code: {join_code})")

        # Add other members
        for member in members:
            if member != creator:
                member_headers = {"Authorization": f"Bearer {self.tokens[member]}"}
                join_response = await client.post(
                    f"{self.base_url}/groups/join",
                    json={"joinCode": join_code},
                    headers=member_headers,
                )
                if join_response.status_code == 200:
                    print(f"  ✅ {member} joined the group")
                else:
                    print(f"  ❌ {member} failed to join: {join_response.text}")

        return group_id

    async def create_expense(
        self,
        client: httpx.AsyncClient,
        group_id: str,
        payer: str,
        description: str,
        amount: float,
        members: List[str],
    ):
        """Create an expense split equally among members"""
        print(f"\n💸 Creating expense: {payer} pays ${amount} for '{description}'")

        headers = {"Authorization": f"Bearer {self.tokens[payer]}"}

        # Calculate equal splits
        split_amount = round(amount / len(members), 2)
        splits = [
            {"userId": self.user_ids[member], "amount": split_amount}
            for member in members
        ]

        response = await client.post(
            f"{self.base_url}/groups/{group_id}/expenses",
            json={
                "description": description,
                "amount": amount,
                "paidBy": self.user_ids[payer],
                "splitType": "equal",
                "splits": splits,
            },
            headers=headers,
        )

        if response.status_code == 201:
            print(f"  ✅ Expense created")
        else:
            print(f"  ❌ Failed: {response.status_code} - {response.text}")

    async def get_balance_summary(self, client: httpx.AsyncClient, user: str) -> Dict:
        """Get user's overall balance summary"""
        headers = {"Authorization": f"Bearer {self.tokens[user]}"}

        response = await client.get(
            f"{self.base_url}/users/me/balance-summary",
            headers=headers,
        )

        if response.status_code == 200:
            return response.json()
        else:
            print(f"  ❌ Failed to get balance for {user}: {response.text}")
            return {}

    async def create_settlement(
        self,
        client: httpx.AsyncClient,
        group_id: str,
        payer: str,
        receiver: str,
        amount: float,
        description: str = "Settlement",
    ):
        """Create a settlement between two users"""
        print(
            f"\n💰 Creating settlement: {payer} pays {receiver} ${amount} - {description}"
        )

        headers = {"Authorization": f"Bearer {self.tokens[payer]}"}

        response = await client.post(
            f"{self.base_url}/groups/{group_id}/settlements",
            json={
                "amount": amount,
                "payer_id": self.user_ids[payer],
                "payee_id": self.user_ids[receiver],
                "description": description,
            },
            headers=headers,
        )

        if response.status_code == 201:
            settlement_data = response.json()
            print(
                f"  ✅ Settlement created (Status: {settlement_data.get('status', 'unknown')})"
            )
            return settlement_data
        else:
            print(f"  ❌ Settlement failed: {response.status_code} - {response.text}")
            return None

    async def get_friends_balance(self, client: httpx.AsyncClient, user: str) -> Dict:
        """Get user's friends balance"""
        headers = {"Authorization": f"Bearer {self.tokens[user]}"}

        response = await client.get(
            f"{self.base_url}/users/me/friends-balance",
            headers=headers,
        )

        if response.status_code == 200:
            return response.json()
        else:
            print(f"  ❌ Failed to get friends balance for {user}: {response.text}")
            return {}

    async def get_optimized_settlements(
        self, client: httpx.AsyncClient, user: str, group_id: str
    ) -> List[Dict]:
        """Get optimized settlements for a group"""
        headers = {"Authorization": f"Bearer {self.tokens[user]}"}

        response = await client.post(
            f"{self.base_url}/groups/{group_id}/settlements/optimize",
            headers=headers,
        )

        if response.status_code == 200:
            return response.json().get("optimizedSettlements", [])
        else:
            print(f"  ❌ Failed to get settlements: {response.text}")
            return []

    async def verify_balances(self, client: httpx.AsyncClient):
        """Verify all user balances match expectations"""
        print("\n" + "=" * 60)
        print("📊 VERIFYING BALANCES")
        print("=" * 60)

        # Updated expected values after adding:
        # - C pays $40 for movie tickets in Group 2 (so C is owed $30 more, B owes $10 more)
        # - D settles $45 with A in Group 1 (marked as completed, so still shows in pending balances)
        # NOTE: Completed settlements don't affect balances - they just mark debt as satisfied
        expected = {
            "A": {
                "total": 55.0,
                "group1": 55.0,
            },  # Still +55 (D's payment is completed, not pending)
            "B": {
                "total": -15.0,
                "group1": 35.0,
                "group2": -50.0,
            },  # Group2: -40-10 = -50
            "C": {
                "total": -15.0,
                "group1": -45.0,
                "group2": 30.0,
            },  # Group2: 0+30 = +30
            "D": {
                "total": -45.0,
                "group1": -45.0,
            },  # Still -45 (payment is completed, not pending)
            "E": {"total": 70.0, "group2": 70.0},  # Group2: 80-10 = 70
            "F": {"total": -50.0, "group2": -50.0},  # Group2: -40-10 = -50
        }

        all_correct = True

        # First verify friends balance summary (Priority 2 optimization)
        print("\n🤝 Verifying Friends Balance Summary (with imageUrl):")
        print("-" * 60)

        for user_key in ["A", "B", "C", "D", "E", "F"]:
            headers = {"Authorization": f"Bearer {self.tokens[user_key]}"}
            response = await client.get(
                f"{self.base_url}/users/me/friends-balance",
                headers=headers,
            )

            if response.status_code == 200:
                friends_data = response.json()
                summary = friends_data.get("summary", {})
                print(f"\n👤 User {user_key}:")
                print(f"  Net Balance: ${summary.get('netBalance', 0):.2f}")
                print(
                    f"  Friends: {summary.get('friendCount', 0)}, Groups: {summary.get('activeGroups', 0)}"
                )

                friends_balance = friends_data.get("friendsBalance", [])
                if friends_balance:
                    print(f"  Friend balances:")
                    for friend in friends_balance:
                        balance = friend["netBalance"]
                        balance_type = "owes you" if balance > 0 else "you owe"

                        # Verify breakdown has imageUrl (Priority 2 optimization)
                        has_imageurl = False
                        for detail in friend.get("breakdown", []):
                            if "imageUrl" in detail:
                                has_imageurl = True
                                break

                        symbol = "✅" if has_imageurl else "❌"
                        print(
                            f"    {symbol} {friend['userName']}: ${abs(balance):.2f} ({balance_type}) [imageUrl in breakdown: {'✓' if has_imageurl else 'MISSING'}]"
                        )

                        if not has_imageurl:
                            all_correct = False
                else:
                    print("  No friends with balances")
            else:
                print(f"  ❌ Failed to fetch friends balance: {response.status_code}")
                all_correct = False

        # Now verify group balance summary
        print("\n")
        print("-" * 60)
        print("📊 Verifying Group Balance Summary:")
        print("-" * 60)

        for user in ["A", "B", "C", "D", "E", "F"]:
            print(f"\n👤 User {user}:")
            balance_data = await self.get_balance_summary(client, user)

            actual_total = balance_data.get("netBalance", 0)
            expected_total = expected[user]["total"]

            match = abs(actual_total - expected_total) < 0.01
            symbol = "✅" if match else "❌"

            print(
                f"  {symbol} Total Balance: ${actual_total:.2f} (expected: ${expected_total:.2f})"
            )

            if not match:
                all_correct = False

            # Check group balances
            groups_summary = balance_data.get("groupsSummary", [])
            for group_sum in groups_summary:
                group_id = group_sum["groupId"]
                group_name = group_sum["groupName"]
                actual_amount = group_sum["amount"]

                # Determine expected group balance
                if "group1" in expected[user] and group_id == self.groups.get("group1"):
                    expected_amount = expected[user]["group1"]
                elif "group2" in expected[user] and group_id == self.groups.get(
                    "group2"
                ):
                    expected_amount = expected[user]["group2"]
                else:
                    continue

                match = abs(actual_amount - expected_amount) < 0.01
                symbol = "✅" if match else "❌"
                print(
                    f"  {symbol} {group_name}: ${actual_amount:.2f} (expected: ${expected_amount:.2f})"
                )

                if not match:
                    all_correct = False

        print("\n" + "=" * 60)
        if all_correct:
            print("🎉 ALL BALANCES CORRECT!")
        else:
            print("⚠️  SOME BALANCES INCORRECT!")
        print("=" * 60)

        return all_correct

    async def show_settlements(self, client: httpx.AsyncClient):
        """Show optimized settlements for both groups"""
        print("\n" + "=" * 60)
        print("💰 OPTIMIZED SETTLEMENTS")
        print("=" * 60)

        for group_name, group_id in self.groups.items():
            print(f"\n📋 {group_name.upper()}:")
            settlements = await self.get_optimized_settlements(client, "A", group_id)

            if settlements:
                for settlement in settlements:
                    from_name = settlement["fromUserName"]
                    to_name = settlement["toUserName"]
                    amount = settlement["amount"]
                    print(f"  💵 {from_name} → {to_name}: ${amount:.2f}")
            else:
                print("  ✅ All settled!")

    async def cleanup_test_data(self, client: httpx.AsyncClient):
        """Delete all groups for test users to start fresh"""
        print("🧹 Cleaning up previous test data...")

        deleted_count = 0
        for user_key in ["A", "B", "C", "D", "E", "F"]:
            if user_key not in self.tokens:
                continue

            headers = {"Authorization": f"Bearer {self.tokens[user_key]}"}

            # Get all groups for this user
            response = await client.get(f"{self.base_url}/groups", headers=headers)
            if response.status_code == 200:
                data = response.json()
                groups = data if isinstance(data, list) else data.get("groups", [])

                for group in groups:
                    group_id = group.get("_id") or group.get("id")
                    group_name = group.get("name", "Unknown")

                    if not group_id:
                        continue

                    # Delete each group
                    delete_response = await client.delete(
                        f"{self.base_url}/groups/{group_id}", headers=headers
                    )
                    if delete_response.status_code in [200, 204]:
                        deleted_count += 1

        if deleted_count > 0:
            print(f"  ✅ Deleted {deleted_count} groups")
        else:
            print(f"  ℹ️  No groups to delete")
        print("")

    async def run_verification(self):
        """Run the complete verification scenario"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            print("🚀 Starting Settlement Verification\n")

            # Step 1: Sign up all users
            print("=" * 60)
            print("STEP 1: Creating Users")
            print("=" * 60)
            for user_key in ["A", "B", "C", "D", "E", "F"]:
                await self.signup_user(client, user_key)

            # Step 1.5: Clean up existing data
            print("\n" + "=" * 60)
            print("STEP 1.5: Cleaning Up Old Test Data")
            print("=" * 60)
            await self.cleanup_test_data(client)

            # Step 2: Create groups
            print("\n" + "=" * 60)
            print("STEP 2: Creating Groups")
            print("=" * 60)
            self.groups["group1"] = await self.create_group(
                client, "A", "Group 1 - ABCD", ["A", "B", "C", "D"]
            )
            self.groups["group2"] = await self.create_group(
                client, "B", "Group 2 - BCEF", ["B", "C", "E", "F"]
            )

            # Step 3: Create expenses
            print("\n" + "=" * 60)
            print("STEP 3: Creating Expenses")
            print("=" * 60)

            # Group 1 expenses
            await self.create_expense(
                client,
                self.groups["group1"],
                "A",
                "Dinner",
                100.0,
                ["A", "B", "C", "D"],
            )
            await self.create_expense(
                client,
                self.groups["group1"],
                "B",
                "Groceries",
                80.0,
                ["A", "B", "C", "D"],
            )

            # Group 2 expenses
            await self.create_expense(
                client,
                self.groups["group2"],
                "E",
                "Concert Tickets",
                120.0,
                ["B", "C", "E", "F"],
            )
            await self.create_expense(
                client, self.groups["group2"], "C", "Taxi", 40.0, ["B", "C", "E", "F"]
            )

            # Additional expense in Group 2: C pays, so B owes C (cross-group complexity)
            await self.create_expense(
                client,
                self.groups["group2"],
                "C",
                "Movie Tickets",
                40.0,
                ["B", "C", "E", "F"],
            )

            # Step 4: Create settlements
            print("\n" + "=" * 60)
            print("STEP 4: Creating Settlements")
            print("=" * 60)

            # D pays A $45 in Group 1 (settling their debt)
            await self.create_settlement(
                client,
                self.groups["group1"],
                "D",
                "A",
                45.0,
                "Settling Dinner & Groceries debt",
            )

            # Step 4: Verify balances
            await asyncio.sleep(1)  # Give DB time to update
            all_correct = await self.verify_balances(client)

            # Step 5: Show settlements
            await self.show_settlements(client)

            return all_correct


async def main():
    verifier = SettlementVerifier(API_URL)
    try:
        result = await verifier.run_verification()
        if result:
            print("\n✅ VERIFICATION PASSED!")
            return 0
        else:
            print("\n❌ VERIFICATION FAILED!")
            return 1
    except Exception as e:
        print(f"\n💥 Error during verification: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
