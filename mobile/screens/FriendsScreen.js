import { useIsFocused } from "@react-navigation/native";
import { useContext, useEffect, useRef, useState } from "react";
import { Alert, Animated, FlatList, RefreshControl, StyleSheet, View } from "react-native";
import {
  Appbar,
  Avatar,
  Divider,
  List,
  Text,
  useTheme,
} from "react-native-paper";
import HapticIconButton from '../components/ui/HapticIconButton';
import { HapticListAccordion } from '../components/ui/HapticList';
import * as Haptics from "expo-haptics";
import { getFriendsBalance, getGroups } from "../api/groups";
import { AuthContext } from "../context/AuthContext";
import { formatCurrency } from "../utils/currency";

const FriendsScreen = () => {
  const { token, user } = useContext(AuthContext);
  const theme = useTheme();
  const [friends, setFriends] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [showTooltip, setShowTooltip] = useState(true);
  const isFocused = useIsFocused();

  const fetchData = async (showLoading = true) => {
    if (showLoading) setIsLoading(true);
    try {
      // Fetch friends balance + groups concurrently for group icons
      const friendsResponse = await getFriendsBalance();
      const friendsData = friendsResponse.data.friendsBalance || [];
      const groupsResponse = await getGroups();
      const groups = groupsResponse?.data?.groups || [];
      const groupMeta = new Map(
        groups.map((g) => [g._id, { name: g.name, imageUrl: g.imageUrl }])
      );

      const transformedFriends = friendsData.map((friend) => ({
        id: friend.userId,
        name: friend.userName,
        imageUrl: friend.userImageUrl || null,
        netBalance: friend.netBalance,
        groups: (friend.breakdown || []).map((group) => ({
          id: group.groupId,
          name: group.groupName,
          balance: group.balance,
          imageUrl: groupMeta.get(group.groupId)?.imageUrl || null,
        })),
      }));

      setFriends(transformedFriends);
    } catch (error) {
      console.error("Failed to fetch friends balance data:", error);
      Alert.alert("Error", "Failed to load friends balance data.");
    } finally {
      if (showLoading) setIsLoading(false);
    }
  };

  const onRefresh = async () => {
    setIsRefreshing(true);
    await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    await fetchData(false);
    setIsRefreshing(false);
  };

  useEffect(() => {
    if (token && isFocused) {
      fetchData();
    }
  }, [token, isFocused]);

  const renderFriend = ({ item }) => {
    const balanceColor = item.netBalance < 0 ? "red" : "green";
    const balanceText =
      item.netBalance < 0
        ? `You owe ${formatCurrency(Math.abs(item.netBalance))}`
        : `Owes you ${formatCurrency(item.netBalance)}`;

    // Determine if we have an image URL or a base64 payload
    const hasImage = !!item.imageUrl;
    let imageUri = null;
    if (hasImage) {
      // If it's a raw base64 string without prefix, add a default MIME prefix
      if (
        /^data:image/.test(item.imageUrl) ||
        /^https?:\/\//.test(item.imageUrl)
      ) {
        imageUri = item.imageUrl;
      } else if (/^[A-Za-z0-9+/=]+$/.test(item.imageUrl.substring(0, 50))) {
        imageUri = `data:image/jpeg;base64,${item.imageUrl}`;
      }
    }

    return (
      <HapticListAccordion
        title={item.name}
        description={item.netBalance !== 0 ? balanceText : "Settled up"}
        descriptionStyle={{
          color: item.netBalance !== 0 ? balanceColor : "gray",
        }}
        accessibilityRole="button"
        accessibilityLabel={`Friend ${item.name}. ${
          item.netBalance !== 0 ? balanceText : "Settled up"
        }`}
        accessibilityHint="Double tap to see balance breakdown"
        left={(props) =>
          imageUri ? (
            <Avatar.Image {...props} size={40} source={{ uri: imageUri }} />
          ) : (
            <Avatar.Text
              {...props}
              size={40}
              label={(item.name || "?").charAt(0)}
            />
          )
        }
      >
        {item.groups.map((group) => {
          const groupBalanceColor = group.balance < 0 ? "red" : "green";
          const groupBalanceText =
            group.balance < 0
              ? `You owe ${formatCurrency(Math.abs(group.balance))}`
              : `Owes you ${formatCurrency(group.balance)}`;
          // Prepare group icon (imageUrl may be base64 or URL)
          let groupImageUri = null;
          if (group.imageUrl) {
            if (
              /^data:image/.test(group.imageUrl) ||
              /^https?:\/\//.test(group.imageUrl)
            ) {
              groupImageUri = group.imageUrl;
            } else if (
              /^[A-Za-z0-9+/=]+$/.test(group.imageUrl.substring(0, 50))
            ) {
              groupImageUri = `data:image/jpeg;base64,${group.imageUrl}`;
            }
          }

          return (
            <List.Item
              key={group.id}
              title={group.name}
              description={groupBalanceText}
              descriptionStyle={{ color: groupBalanceColor }}
              left={(props) =>
                groupImageUri ? (
                  <Avatar.Image
                    {...props}
                    size={36}
                    source={{ uri: groupImageUri }}
                  />
                ) : (
                  <Avatar.Text
                    {...props}
                    size={36}
                    label={(group.name || "?").charAt(0)}
                  />
                )
              }
            />
          );
        })}
      </HapticListAccordion>
    );
  };

  // Shimmer skeleton components
  const opacityAnim = useRef(new Animated.Value(0.3)).current;
  useEffect(() => {
    const loop = Animated.loop(
      Animated.sequence([
        Animated.timing(opacityAnim, {
          toValue: 1,
          duration: 700,
          useNativeDriver: true,
        }),
        Animated.timing(opacityAnim, {
          toValue: 0.3,
          duration: 700,
          useNativeDriver: true,
        }),
      ])
    );
    loop.start();
    return () => loop.stop();
  }, [opacityAnim]);

  const SkeletonRow = () => (
    <View style={styles.skeletonRow}>
      <Animated.View
        style={[styles.skeletonAvatar, { opacity: opacityAnim }]}
      />
      <View style={{ flex: 1, marginLeft: 12 }}>
        <Animated.View
          style={[styles.skeletonLine, { width: "60%", opacity: opacityAnim }]}
        />
        <Animated.View
          style={[
            styles.skeletonLineSmall,
            { width: "40%", opacity: opacityAnim },
          ]}
        />
      </View>
    </View>
  );

  if (isLoading) {
    return (
      <View style={styles.container}>
        <Appbar.Header>
          <Appbar.Content title="Friends" />
        </Appbar.Header>
        <View
          style={styles.skeletonContainer}
          accessibilityLabel="Loading friends list"
          accessibilityRole="progressbar"
        >
          {Array.from({ length: 5 }).map((_, i) => (
            <SkeletonRow key={i} />
          ))}
        </View>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <Appbar.Header>
        <Appbar.Content title="Friends" />
      </Appbar.Header>
      {showTooltip && (
        <View style={styles.explanationContainer}>
          <View style={styles.explanationContent}>
            <Text style={styles.explanationText}>
              💡 These amounts show your direct balance with each friend across
              all shared groups. Check individual group details for optimized
              settlement suggestions.
            </Text>
            <HapticIconButton
              icon="close"
              size={16}
              onPress={() => setShowTooltip(false)}
              style={styles.closeButton}
              accessibilityLabel="Close tooltip"
              accessibilityRole="button"
            />
          </View>
        </View>
      )}
      <FlatList
        data={friends}
        renderItem={renderFriend}
        keyExtractor={(item) => item.id}
        ItemSeparatorComponent={Divider}
        ListEmptyComponent={
          <Text style={styles.emptyText}>No balances with friends yet.</Text>
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
  explanationContainer: {
    backgroundColor: "#f0f8ff",
    margin: 8,
    borderRadius: 8,
    borderLeftWidth: 4,
    borderLeftColor: "#2196f3",
  },
  explanationContent: {
    flexDirection: "row",
    alignItems: "flex-start",
    padding: 12,
  },
  explanationText: {
    fontSize: 12,
    color: "#555",
    lineHeight: 16,
    flex: 1,
    paddingRight: 8,
  },
  closeButton: {
    margin: 0,
    marginTop: -4,
  },
  emptyText: {
    textAlign: "center",
    marginTop: 20,
  },
  skeletonContainer: {
    padding: 16,
  },
  skeletonRow: {
    flexDirection: "row",
    alignItems: "center",
    marginBottom: 14,
  },
  skeletonAvatar: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: "#e0e0e0",
  },
  skeletonLine: {
    height: 14,
    backgroundColor: "#e0e0e0",
    borderRadius: 6,
    marginBottom: 6,
  },
  skeletonLineSmall: {
    height: 12,
    backgroundColor: "#e0e0e0",
    borderRadius: 6,
  },
});

export default FriendsScreen;
