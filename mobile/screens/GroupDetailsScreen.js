import { useContext, useEffect, useState } from "react";
import { Alert, FlatList, StyleSheet, Text, View } from "react-native";
import * as Haptics from "expo-haptics";
import {
  ActivityIndicator,
  Card,
  FAB,
  IconButton,
  Paragraph,
  Title,
} from "react-native-paper";
import {
  getGroupExpenses,
  getGroupMembers,
  getOptimizedSettlements,
} from "../api/groups";
import { AuthContext } from "../context/AuthContext";

const GroupDetailsScreen = ({ route, navigation }) => {
  const { groupId, groupName } = route.params;
  const { token, user } = useContext(AuthContext);
  const [members, setMembers] = useState([]);
  const [expenses, setExpenses] = useState([]);
  const [settlements, setSettlements] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);

  // Currency configuration - can be made configurable later
  const currency = "₹"; // Default to INR, can be changed to '$' for USD

  // Helper function to format currency amounts
  const formatCurrency = (amount) => `${currency}${amount.toFixed(2)}`;

  const fetchData = async (refresh = false) => {
    try {
      if (refresh) {
        setIsRefreshing(true);
        Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
      } else {
        setIsLoading(true);
      }
      // Fetch members, expenses, and settlements in parallel
      const [membersResponse, expensesResponse, settlementsResponse] =
        await Promise.all([
          getGroupMembers(groupId),
          getGroupExpenses(groupId),
          getOptimizedSettlements(groupId),
        ]);
      setMembers(membersResponse.data);
      setExpenses(expensesResponse.data.expenses);
      setSettlements(settlementsResponse.data.optimizedSettlements || []);
    } catch (error) {
      console.error("Failed to fetch group details:", error);
      Alert.alert("Error", "Failed to fetch group details.");
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  };

  useEffect(() => {
    navigation.setOptions({
      title: groupName,
      headerRight: () => (
        <IconButton
          icon="cog"
          onPress={() => navigation.navigate("GroupSettings", { groupId })}
        />
      ),
    });
    if (token && groupId) {
      fetchData(false);
    }
  }, [token, groupId]);

  const getMemberName = (userId) => {
    const member = members.find((m) => m.userId === userId);
    return member ? member.user.name : "Unknown";
  };

  const renderExpense = ({ item }) => {
    const userSplit = item.splits.find((s) => s.userId === user._id);
    const userShare = userSplit ? userSplit.amount : 0;
    const paidByMe = (item.paidBy || item.createdBy) === user._id;
    const net = paidByMe ? item.amount - userShare : -userShare;

    let balanceText;
    let balanceColor = "black";

    if (net > 0) {
      balanceText = `You are owed ${formatCurrency(net)}`;
      balanceColor = "green";
    } else if (net < 0) {
      balanceText = `You borrowed ${formatCurrency(Math.abs(net))}`;
      balanceColor = "red";
    } else {
      balanceText = "You are settled for this expense.";
    }

    return (
      <Card style={styles.card}>
        <Card.Content>
          <Title>{item.description}</Title>
          <Paragraph>Amount: {formatCurrency(item.amount)}</Paragraph>
          <Paragraph>
            Paid by: {getMemberName(item.paidBy || item.createdBy)}
          </Paragraph>
          <Paragraph style={{ color: balanceColor }}>{balanceText}</Paragraph>
        </Card.Content>
      </Card>
    );
  };

  const renderSettlementSummary = () => {
    const userOwes = settlements.filter((s) => s.fromUserId === user._id);
    const userIsOwed = settlements.filter((s) => s.toUserId === user._id);
    const totalOwed = userOwes.reduce((sum, s) => sum + s.amount, 0);
    const totalToReceive = userIsOwed.reduce((sum, s) => sum + s.amount, 0);

    // If user is all settled up
    if (userOwes.length === 0 && userIsOwed.length === 0) {
      return (
        <View style={styles.settledContainer}>
          <Text style={styles.settledText}>✓ You are all settled up!</Text>
        </View>
      );
    }

    return (
      <View style={styles.settlementContainer}>
        {/* You owe section - only show if totalOwed > 0 */}
        {totalOwed > 0 && (
          <View style={styles.owedSection}>
            <Text style={styles.sectionTitle}>
              You need to pay:{" "}
              <Text style={styles.amountOwed}>{formatCurrency(totalOwed)}</Text>
            </Text>
            {userOwes.map((s, index) => (
              <View key={`owes-${index}`} style={styles.settlementItem}>
                <View style={styles.personInfo}>
                  <Text style={styles.personName}>
                    {getMemberName(s.toUserId)}
                  </Text>
                  <Text style={styles.settlementAmount}>
                    {formatCurrency(s.amount)}
                  </Text>
                </View>
              </View>
            ))}
          </View>
        )}

        {/* You receive section - only show if totalToReceive > 0 */}
        {totalToReceive > 0 && (
          <View style={styles.receiveSection}>
            <Text style={styles.sectionTitle}>
              You will receive:{" "}
              <Text style={styles.amountReceive}>
                {formatCurrency(totalToReceive)}
              </Text>
            </Text>
            {userIsOwed.map((s, index) => (
              <View key={`is-owed-${index}`} style={styles.settlementItem}>
                <View style={styles.personInfo}>
                  <Text style={styles.personName}>
                    {getMemberName(s.fromUserId)}
                  </Text>
                  <Text style={styles.settlementAmount}>
                    {formatCurrency(s.amount)}
                  </Text>
                </View>
              </View>
            ))}
          </View>
        )}
      </View>
    );
  };

  if (isLoading) {
    return (
      <View style={styles.loaderContainer}>
        <ActivityIndicator size="large" />
      </View>
    );
  }

  const renderHeader = () => (
    <>
      <Card style={styles.card}>
        <Card.Content>
          <Title>Settlement Summary</Title>
          {renderSettlementSummary()}
        </Card.Content>
      </Card>

      <Title style={styles.expensesTitle}>Expenses</Title>
    </>
  );

  return (
    <View style={styles.container}>
      <FlatList
        style={styles.contentContainer}
        data={expenses}
        renderItem={renderExpense}
        keyExtractor={(item) => item._id}
        ListHeaderComponent={renderHeader}
        ListEmptyComponent={
          <Text style={styles.emptyText}>No expenses recorded yet.</Text>
        }
        contentContainerStyle={{ paddingBottom: 80 }} // To avoid FAB overlap
        onRefresh={() => fetchData(true)}
        refreshing={isRefreshing}
      />

      <FAB
        style={styles.fab}
        icon="plus"
        onPress={() => navigation.navigate("AddExpense", { groupId: groupId })}
      />
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  contentContainer: {
    flex: 1,
    padding: 16,
  },
  loaderContainer: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
  },
  card: {
    marginBottom: 16,
  },
  expensesTitle: {
    marginTop: 16,
    marginBottom: 8,
    fontSize: 20,
    fontWeight: "bold",
  },
  memberText: {
    fontSize: 16,
    lineHeight: 24,
  },
  fab: {
    position: "absolute",
    margin: 16,
    right: 0,
    bottom: 0,
  },
  // Settlement Summary Styles
  settlementContainer: {
    marginBottom: 16,
  },
  settledContainer: {
    alignItems: "center",
    paddingVertical: 12,
  },
  settledText: {
    fontSize: 16,
    color: "#2e7d32",
    fontWeight: "500",
  },
  owedSection: {
    backgroundColor: "#ffebee",
    borderRadius: 8,
    padding: 12,
    borderLeftWidth: 4,
    borderLeftColor: "#d32f2f",
  },
  receiveSection: {
    backgroundColor: "#e8f5e8",
    borderRadius: 8,
    padding: 12,
    borderLeftWidth: 4,
    borderLeftColor: "#2e7d32",
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: "600",
    marginBottom: 8,
    color: "#333",
  },
  amountOwed: {
    color: "#d32f2f",
    fontWeight: "bold",
  },
  amountReceive: {
    color: "#2e7d32",
    fontWeight: "bold",
  },
  settlementItem: {
    marginVertical: 4,
  },
  personInfo: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingVertical: 4,
  },
  personName: {
    fontSize: 14,
    color: "#555",
    flex: 1,
  },
  settlementAmount: {
    fontSize: 14,
    fontWeight: "600",
    color: "#333",
  },
  emptyText: {
    fontSize: 14,
    color: "#666",
    paddingVertical: 8,
  },
});

export default GroupDetailsScreen;
