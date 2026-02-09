import { useContext, useEffect, useState } from "react";
import { Alert, FlatList, RefreshControl, StyleSheet, View } from "react-native";
import {
  ActivityIndicator,
  Appbar,
  Avatar,
  Modal,
  Portal,
  Text,
  TextInput,
  useTheme,
} from "react-native-paper";
import HapticButton from '../components/ui/HapticButton';
import HapticCard from '../components/ui/HapticCard';
import { HapticAppbarAction } from '../components/ui/HapticAppbar';
import * as Haptics from "expo-haptics";
import { createGroup, getGroups, getOptimizedSettlements } from "../api/groups";
import { AuthContext } from "../context/AuthContext";
import { formatCurrency, getCurrencySymbol } from "../utils/currency";

const HomeScreen = ({ navigation }) => {
  const { token, logout, user } = useContext(AuthContext);
  const theme = useTheme();
  const [groups, setGroups] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [groupSettlements, setGroupSettlements] = useState({}); // Track settlement status for each group

  // State for the Create Group modal
  const [modalVisible, setModalVisible] = useState(false);
  const [newGroupName, setNewGroupName] = useState("");
  const [isCreatingGroup, setIsCreatingGroup] = useState(false);

  const showModal = () => setModalVisible(true);
  const hideModal = () => setModalVisible(false);

  // Calculate settlement status for a group
  const calculateSettlementStatus = async (groupId, userId) => {
    try {
      const response = await getOptimizedSettlements(groupId);
      const settlements = response.data.optimizedSettlements || [];

      // Check if user has any pending settlements
      const userOwes = settlements.filter((s) => s.fromUserId === userId);
      const userIsOwed = settlements.filter((s) => s.toUserId === userId);

      const totalOwed = userOwes.reduce((sum, s) => sum + (s.amount || 0), 0);
      const totalToReceive = userIsOwed.reduce(
        (sum, s) => sum + (s.amount || 0),
        0
      );

      return {
        isSettled: totalOwed === 0 && totalToReceive === 0,
        owesAmount: totalOwed,
        owedAmount: totalToReceive,
        netBalance: totalToReceive - totalOwed,
      };
    } catch (error) {
      console.error(
        "Failed to fetch settlement status for group:",
        groupId,
        error
      );
      return {
        isSettled: true,
        owesAmount: 0,
        owedAmount: 0,
        netBalance: 0,
      };
    }
  };

  const fetchGroups = async (showLoading = true) => {
    try {
      if (showLoading) setIsLoading(true);
      const response = await getGroups();
      const groupsList = response.data.groups;
      setGroups(groupsList);

      // Fetch settlement status for each group
      if (user?._id) {
        const settlementPromises = groupsList.map(async (group) => {
          const status = await calculateSettlementStatus(group._id, user._id);
          return { groupId: group._id, status };
        });

        const settlementResults = await Promise.all(settlementPromises);
        const settlementMap = {};
        settlementResults.forEach(({ groupId, status }) => {
          settlementMap[groupId] = status;
        });
        setGroupSettlements(settlementMap);
      }
    } catch (error) {
      console.error("Failed to fetch groups:", error);
      Alert.alert("Error", "Failed to fetch groups.");
    } finally {
      if (showLoading) setIsLoading(false);
    }
  };

  const onRefresh = async () => {
    setIsRefreshing(true);
    await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    await fetchGroups(false);
    setIsRefreshing(false);
  };

  useEffect(() => {
    if (token) {
      fetchGroups();
    }
  }, [token]);

  const handleCreateGroup = async () => {
    if (!newGroupName) {
      Alert.alert("Error", "Please enter a group name.");
      return;
    }
    setIsCreatingGroup(true);
    try {
      await createGroup(newGroupName);
      hideModal();
      setNewGroupName("");
      await fetchGroups(); // Refresh the groups list
    } catch (error) {
      console.error("Failed to create group:", error);
      Alert.alert("Error", "Failed to create group.");
    } finally {
      setIsCreatingGroup(false);
    }
  };

  const currencySymbol = getCurrencySymbol();

  const renderGroup = ({ item }) => {
    const settlementStatus = groupSettlements[item._id];

    // Generate settlement status text
    const getSettlementStatusText = () => {
      if (!settlementStatus) {
        return "Calculating balances...";
      }

      if (settlementStatus.isSettled) {
        return "✓ You are settled up.";
      }

      if (settlementStatus.netBalance > 0) {
        return `You are owed ${formatCurrency(settlementStatus.netBalance)}.`;
      } else if (settlementStatus.netBalance < 0) {
        return `You owe ${formatCurrency(
          Math.abs(settlementStatus.netBalance)
        )}.`;
      }

      return "You are settled up.";
    };

    // Get text color based on settlement status
    const getStatusColor = () => {
      if (!settlementStatus || settlementStatus.isSettled) {
        return "#4CAF50"; // Green for settled
      }

      if (settlementStatus.netBalance > 0) {
        return "#4CAF50"; // Green for being owed money
      } else if (settlementStatus.netBalance < 0) {
        return "#F44336"; // Red for owing money
      }

      return "#4CAF50"; // Default green
    };

    const isImage =
      item.imageUrl && /^(https?:|data:image)/.test(item.imageUrl);
    const groupIcon = item.imageUrl || item.name?.charAt(0) || "?";
    return (
      <HapticCard
        style={styles.card}
        onPress={() =>
          navigation.navigate("GroupDetails", {
            groupId: item._id,
            groupName: item.name,
            groupIcon,
          })
        }
        accessibilityRole="button"
        accessibilityLabel={`Group ${item.name}. ${getSettlementStatusText()}`}
        accessibilityHint="Double tap to view group details"
      >
        <HapticCard.Title
          title={item.name}
          left={(props) =>
            isImage ? (
              <Avatar.Image {...props} source={{ uri: item.imageUrl }} />
            ) : (
              <Avatar.Text {...props} label={groupIcon} />
            )
          }
        />
        <HapticCard.Content>
          <Text style={[styles.settlementStatus, { color: getStatusColor() }]}>
            {getSettlementStatusText()}
          </Text>
        </HapticCard.Content>
      </HapticCard>
    );
  };

  return (
    <View style={styles.container}>
      <Portal>
        <Modal
          visible={modalVisible}
          onDismiss={hideModal}
          contentContainerStyle={styles.modalContainer}
        >
          <Text style={styles.modalTitle}>Create a New Group</Text>
          <TextInput
            label="Group Name"
            value={newGroupName}
            onChangeText={setNewGroupName}
            style={styles.input}
            accessibilityLabel="New group name"
          />
          <HapticButton
            mode="contained"
            onPress={handleCreateGroup}
            loading={isCreatingGroup}
            disabled={isCreatingGroup}
            accessibilityLabel="Create Group"
            accessibilityRole="button"
          >
            Create
          </HapticButton>
        </Modal>
      </Portal>

      <Appbar.Header>
        <Appbar.Content title="Your Groups" />
        <HapticAppbarAction
          icon="plus"
          onPress={showModal}
          accessibilityLabel="Create new group"
          accessibilityRole="button"
        />
        <HapticAppbarAction
          icon="account-plus"
          onPress={() =>
            navigation.navigate("JoinGroup", { onGroupJoined: fetchGroups })
          }
          accessibilityLabel="Join a group"
          accessibilityRole="button"
        />
      </Appbar.Header>

      {isLoading ? (
        <View style={styles.loaderContainer}>
          <ActivityIndicator size="large" />
        </View>
      ) : (
        <FlatList
          data={groups}
          renderItem={renderGroup}
          keyExtractor={(item) => item._id}
          contentContainerStyle={styles.list}
          ListEmptyComponent={
            <Text style={styles.emptyText}>
              No groups found. Create or join one!
            </Text>
          }
          refreshControl={
            <RefreshControl
              refreshing={isRefreshing}
              onRefresh={onRefresh}
              colors={[theme.colors.primary]}
              tintColor={theme.colors.primary}
            />
          }
        />
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  loaderContainer: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
  },
  list: {
    padding: 16,
  },
  card: {
    marginBottom: 16,
  },
  settlementStatus: {
    fontWeight: "500",
    marginTop: 4,
  },
  emptyText: {
    textAlign: "center",
    marginTop: 20,
  },
  modalContainer: {
    backgroundColor: "white",
    padding: 20,
    margin: 20,
    borderRadius: 8,
  },
  modalTitle: {
    fontSize: 20,
    marginBottom: 20,
    textAlign: "center",
  },
  input: {
    marginBottom: 20,
  },
});

export default HomeScreen;
