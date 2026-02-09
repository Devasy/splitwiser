import { useContext, useEffect, useState } from "react";
import {
  Alert,
  KeyboardAvoidingView,
  Platform,
  StyleSheet,
  View,
} from "react-native";
import {
  ActivityIndicator,
  Paragraph,
  Text,
  TextInput,
  Title,
} from "react-native-paper";
import HapticButton from '../components/ui/HapticButton';
import HapticCheckboxItem from '../components/ui/HapticCheckbox';
import HapticMenu from '../components/ui/HapticMenu';
import HapticSegmentedButtons from '../components/ui/HapticSegmentedButtons';
import { createExpense, getGroupMembers } from "../api/groups";
import { AuthContext } from "../context/AuthContext";

const AddExpenseScreen = ({ route, navigation }) => {
  const { groupId } = route.params;
  const { token, user } = useContext(AuthContext);
  const [description, setDescription] = useState("");
  const [amount, setAmount] = useState("");
  const [members, setMembers] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [splitMethod, setSplitMethod] = useState("equal");
  const [payerId, setPayerId] = useState(null); // Initialize as null until members are loaded
  const [menuVisible, setMenuVisible] = useState(false);

  // State for different split methods
  const [percentages, setPercentages] = useState({});
  const [shares, setShares] = useState({});
  const [exactAmounts, setExactAmounts] = useState({});
  const [selectedMembers, setSelectedMembers] = useState({}); // For equal split

  useEffect(() => {
    const fetchMembers = async () => {
      try {
        const response = await getGroupMembers(groupId);
        setMembers(response.data);
        // Initialize split states
        const initialShares = {};
        const initialPercentages = {};
        const initialExactAmounts = {};
        const initialSelectedMembers = {};
        const numMembers = response.data.length;

        // Calculate percentages using integer math to avoid floating-point errors
        const basePercentage = Math.floor(100 / numMembers);
        const remainder = 100 - basePercentage * numMembers;

        response.data.forEach((member, index) => {
          initialShares[member.userId] = "1";

          // Distribute percentages using integer math
          let memberPercentage = basePercentage;
          // Distribute remainder to first members (could also be last, but first is simpler)
          if (index < remainder) {
            memberPercentage += 1;
          }
          initialPercentages[member.userId] = memberPercentage.toString();

          initialExactAmounts[member.userId] = "0.00";
          initialSelectedMembers[member.userId] = true; // Select all by default
        });
        setShares(initialShares);
        setPercentages(initialPercentages);
        setExactAmounts(initialExactAmounts);
        setSelectedMembers(initialSelectedMembers);

        // Set default payer to current user if they're a member
        const currentUserMember = response.data.find(
          (member) => member.userId === user._id
        );
        if (currentUserMember) {
          setPayerId(user._id);
        } else if (response.data.length > 0) {
          setPayerId(response.data[0].userId);
        }
      } catch (error) {
        console.error("Failed to fetch members:", error);
        Alert.alert("Error", "Failed to fetch group members.");
      } finally {
        setIsLoading(false);
      }
    };
    if (token && groupId) {
      fetchMembers();
    }
  }, [token, groupId]);

  const handleAddExpense = async () => {
    if (!description || !amount) {
      Alert.alert("Error", "Please fill in all fields.");
      return;
    }
    if (!payerId) {
      Alert.alert("Error", "Please select who paid for this expense.");
      return;
    }
    const numericAmount = parseFloat(amount);
    if (isNaN(numericAmount) || numericAmount <= 0) {
      Alert.alert("Error", "Please enter a valid amount.");
      return;
    }

    setIsSubmitting(true);
    let expenseData;

    try {
      let splits = [];
      let splitType = splitMethod;

      if (splitMethod === "equal") {
        const includedMembers = Object.keys(selectedMembers).filter(
          (userId) => selectedMembers[userId]
        );
        if (includedMembers.length === 0) {
          throw new Error("You must select at least one member for the split.");
        }
        const splitAmount =
          Math.round((numericAmount / includedMembers.length) * 100) / 100;
        // Calculate remainder to handle rounding
        const totalSplitAmount = splitAmount * includedMembers.length;
        const remainder =
          Math.round((numericAmount - totalSplitAmount) * 100) / 100;

        splits = includedMembers.map((userId, index) => ({
          userId,
          amount: index === 0 ? splitAmount + remainder : splitAmount, // Add remainder to first member
          type: "equal",
        }));
        splitType = "equal";
      } else if (splitMethod === "exact") {
        const total = Object.values(exactAmounts).reduce(
          (sum, val) => sum + parseFloat(val || "0"),
          0
        );
        if (Math.abs(total - numericAmount) > 0.01) {
          throw new Error(
            `The exact amounts must add up to ${numericAmount.toFixed(
              2
            )}. Current total: ${total.toFixed(2)}`
          );
        }
        splits = Object.entries(exactAmounts)
          .filter(([userId, value]) => parseFloat(value || "0") > 0)
          .map(([userId, value]) => ({
            userId,
            amount: Math.round(parseFloat(value) * 100) / 100,
            type: "unequal",
          }));
        splitType = "unequal"; // Backend uses 'unequal' for exact amounts
      } else if (splitMethod === "percentage") {
        const total = Object.values(percentages).reduce(
          (sum, val) => sum + parseFloat(val || "0"),
          0
        );
        if (Math.abs(total - 100) > 0.01) {
          throw new Error(
            `Percentages must add up to 100%. Current total: ${total.toFixed(
              2
            )}%`
          );
        }
        splits = Object.entries(percentages)
          .filter(([userId, value]) => parseFloat(value || "0") > 0)
          .map(([userId, value]) => ({
            userId,
            amount:
              Math.round(numericAmount * (parseFloat(value) / 100) * 100) / 100,
            type: "percentage",
          }));
        splitType = "percentage";
      } else if (splitMethod === "shares") {
        const nonZeroShares = Object.entries(shares).filter(
          ([userId, value]) => parseInt(value || "0", 10) > 0
        );
        const totalShares = nonZeroShares.reduce(
          (sum, [, value]) => sum + parseInt(value || "0", 10),
          0
        );

        if (totalShares === 0) {
          throw new Error("Total shares cannot be zero.");
        }

        // Calculate amounts with proper rounding
        const amounts = nonZeroShares.map(([userId, value]) => {
          const shareRatio = parseInt(value, 10) / totalShares;
          return {
            userId,
            amount: Math.round(numericAmount * shareRatio * 100) / 100,
            type: "unequal",
          };
        });

        // Adjust for rounding errors
        const totalCalculated = amounts.reduce(
          (sum, item) => sum + item.amount,
          0
        );
        const difference =
          Math.round((numericAmount - totalCalculated) * 100) / 100;

        if (Math.abs(difference) > 0) {
          amounts[0].amount =
            Math.round((amounts[0].amount + difference) * 100) / 100;
        }

        splits = amounts;
        splitType = "unequal"; // Backend uses 'unequal' for shares
      }

      expenseData = {
        description,
        amount: numericAmount,
        paidBy: payerId, // Use the selected payer
        splitType,
        splits,
        tags: [],
      };

      await createExpense(groupId, expenseData);
      Alert.alert("Success", "Expense added successfully.");
      navigation.goBack();
    } catch (error) {
      Alert.alert("Error", error.message || "Failed to create expense.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleMemberSelect = (userId) => {
    setSelectedMembers((prev) => ({ ...prev, [userId]: !prev[userId] }));
  };

  // Helper function to auto-balance percentages
  const balancePercentages = (updatedPercentages) => {
    const total = Object.values(updatedPercentages).reduce(
      (sum, val) => sum + parseFloat(val || "0"),
      0
    );
    const memberIds = Object.keys(updatedPercentages);

    if (total !== 100 && memberIds.length > 1) {
      // Find the last non-zero percentage to adjust
      const lastMemberId = memberIds[memberIds.length - 1];
      const otherTotal = Object.entries(updatedPercentages)
        .filter(([id]) => id !== lastMemberId)
        .reduce((sum, [, val]) => sum + parseFloat(val || "0"), 0);

      const newValue = Math.max(0, 100 - otherTotal);
      updatedPercentages[lastMemberId] = newValue.toFixed(2);
    }

    return updatedPercentages;
  };

  const renderSplitInputs = () => {
    const handleSplitChange = (setter, userId, value) => {
      if (setter === setPercentages) {
        // Auto-balance percentages when one changes
        const updatedPercentages = { ...percentages, [userId]: value };
        const balanced = balancePercentages(updatedPercentages);
        setter(balanced);
      } else {
        setter((prev) => ({ ...prev, [userId]: value }));
      }
    };

    switch (splitMethod) {
      case "equal":
        return members.map((member) => (
          <HapticCheckboxItem
            key={member.userId}
            label={member.user.name}
            status={selectedMembers[member.userId] ? "checked" : "unchecked"}
            onPress={() => handleMemberSelect(member.userId)}
            accessibilityLabel={`Select ${member.user.name}`}
            accessibilityRole="checkbox"
            accessibilityState={{
              checked: !!selectedMembers[member.userId],
            }}
          />
        ));
      case "exact":
        return members.map((member) => (
          <TextInput
            key={member.userId}
            label={`${member.user.name}'s exact amount`}
            value={exactAmounts[member.userId]}
            onChangeText={(text) =>
              handleSplitChange(setExactAmounts, member.userId, text)
            }
            keyboardType="numeric"
            style={styles.splitInput}
            accessibilityLabel={`${member.user.name}'s exact amount`}
          />
        ));
      case "percentage":
        return members.map((member) => (
          <TextInput
            key={member.userId}
            label={`${member.user.name}'s percentage`}
            value={percentages[member.userId]}
            onChangeText={(text) =>
              handleSplitChange(setPercentages, member.userId, text)
            }
            keyboardType="numeric"
            style={styles.splitInput}
            accessibilityLabel={`${member.user.name}'s percentage`}
          />
        ));
      case "shares":
        return members.map((member) => (
          <TextInput
            key={member.userId}
            label={`${member.user.name}'s shares`}
            value={shares[member.userId]}
            onChangeText={(text) =>
              handleSplitChange(setShares, member.userId, text)
            }
            keyboardType="numeric"
            style={styles.splitInput}
            accessibilityLabel={`${member.user.name}'s shares`}
          />
        ));
      default:
        return null;
    }
  };

  if (isLoading) {
    return (
      <View style={styles.loaderContainer}>
        <ActivityIndicator size="large" />
      </View>
    );
  }

  const selectedPayerName = payerId
    ? members.find((m) => m.userId === payerId)?.user.name || "Select Payer"
    : "Select Payer";

  return (
    <KeyboardAvoidingView
      behavior={Platform.OS === "ios" ? "padding" : "height"}
      style={styles.container}
    >
      <View style={styles.content}>
        <TextInput
          label="Description"
          value={description}
          onChangeText={setDescription}
          style={styles.input}
          accessibilityLabel="Expense Description"
        />
        <TextInput
          label="Amount"
          value={amount}
          onChangeText={setAmount}
          style={styles.input}
          keyboardType="numeric"
          accessibilityLabel="Expense Amount"
        />

        <HapticMenu
          visible={menuVisible}
          onDismiss={() => setMenuVisible(false)}
          anchor={
            <HapticButton
              onPress={() => setMenuVisible(true)}
              accessibilityLabel={`Paid by ${selectedPayerName}`}
              accessibilityRole="button"
              accessibilityHint="Double tap to change payer"
            >
              Paid by: {selectedPayerName}
            </HapticButton>
          }
        >
          {members.map((member) => (
            <HapticMenu.Item
              key={member.userId}
              onPress={() => {
                setPayerId(member.userId);
                setMenuVisible(false);
              }}
              title={member.user.name}
            />
          ))}
        </HapticMenu>

        <Title style={styles.splitTitle}>Split Method</Title>
        <HapticSegmentedButtons
          value={splitMethod}
          onValueChange={setSplitMethod}
          buttons={[
            { value: "equal", label: "Equally" },
            { value: "exact", label: "Exact" },
            { value: "percentage", label: "%" },
            { value: "shares", label: "Shares" },
          ]}
          style={styles.input}
        />

        {splitMethod === "equal" && (
          <Paragraph style={styles.helperText}>
            Select members to split the expense equally among them.
          </Paragraph>
        )}
        {splitMethod === "exact" && (
          <Paragraph style={styles.helperText}>
            Enter exact amounts for each member. Total must equal $
            {amount || "0"}.
            {amount && (
              <Text style={styles.totalText}>
                {" "}
                Current total: $
                {Object.values(exactAmounts)
                  .reduce((sum, val) => sum + parseFloat(val || "0"), 0)
                  .toFixed(2)}
              </Text>
            )}
          </Paragraph>
        )}
        {splitMethod === "percentage" && (
          <Paragraph style={styles.helperText}>
            Enter percentages for each member. Total must equal 100%.
            <Text style={styles.totalText}>
              {" "}
              Current total:{" "}
              {Object.values(percentages)
                .reduce((sum, val) => sum + parseFloat(val || "0"), 0)
                .toFixed(2)}
              %
            </Text>
          </Paragraph>
        )}
        {splitMethod === "shares" && (
          <Paragraph style={styles.helperText}>
            Enter shares for each member. Higher shares = larger portion of the
            expense.
          </Paragraph>
        )}

        <View style={styles.splitInputsContainer}>{renderSplitInputs()}</View>

        <HapticButton
          mode="contained"
          onPress={handleAddExpense}
          style={styles.button}
          loading={isSubmitting}
          disabled={isSubmitting}
          accessibilityLabel="Add Expense"
          accessibilityRole="button"
        >
          Add Expense
        </HapticButton>
      </View>
    </KeyboardAvoidingView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  content: {
    flex: 1,
    padding: 16,
    paddingBottom: 32,
  },
  loaderContainer: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
  },
  input: {
    marginBottom: 16,
  },
  button: {
    marginTop: 24,
  },
  splitTitle: {
    marginTop: 16,
    marginBottom: 8,
  },
  splitInputsContainer: {
    marginTop: 8,
  },
  splitInput: {
    marginBottom: 8,
  },
  helperText: {
    fontSize: 12,
    marginBottom: 8,
    opacity: 0.7,
  },
  totalText: {
    fontWeight: "bold",
    opacity: 1,
  },
});

export default AddExpenseScreen;
