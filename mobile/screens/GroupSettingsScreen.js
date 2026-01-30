import * as ImagePicker from "expo-image-picker";
import {
  useContext,
  useEffect,
  useLayoutEffect,
  useMemo,
  useState,
} from "react";
import {
  Alert,
  Image,
  ScrollView,
  Share,
  StyleSheet,
  View,
} from "react-native";
import {
  ActivityIndicator,
  Avatar,
  Button,
  Card,
  IconButton,
  List,
  Text,
  TextInput,
} from "react-native-paper";
import {
  deleteGroup as apiDeleteGroup,
  leaveGroup as apiLeaveGroup,
  removeMember as apiRemoveMember,
  updateGroup as apiUpdateGroup,
  getGroupById,
  getGroupMembers,
  getOptimizedSettlements,
} from "../api/groups";
import { AuthContext } from "../context/AuthContext";

const ICON_CHOICES = ["👥", "🏠", "🎉", "🧳", "🍽️", "🚗", "🏖️", "🎮", "💼"];

const GroupSettingsScreen = ({ route, navigation }) => {
  const { groupId } = route.params;
  const { token, user } = useContext(AuthContext);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [members, setMembers] = useState([]);
  const [group, setGroup] = useState(null);
  const [name, setName] = useState("");
  const [icon, setIcon] = useState("");
  const [pickedImage, setPickedImage] = useState(null); // { uri, base64 }

  const isAdmin = useMemo(() => {
    const me = members.find((m) => m.userId === user?._id);
    return me?.role === "admin";
  }, [members, user?._id]);

  const load = async () => {
    try {
      setLoading(true);
      const [gRes, mRes] = await Promise.all([
        getGroupById(groupId),
        getGroupMembers(groupId),
      ]);
      setGroup(gRes.data);
      setName(gRes.data.name);
      setIcon(gRes.data.imageUrl || gRes.data.icon || "");
      setMembers(mRes.data);
    } catch (e) {
      console.error("Failed to load group settings", e);
      Alert.alert("Error", "Failed to load group settings.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (token && groupId) load();
  }, [token, groupId]);

  useLayoutEffect(() => {
    navigation.setOptions({ title: "Group Settings" });
  }, [navigation]);

  const onSave = async () => {
    if (!isAdmin) return;
    const updates = {};
    if (name && name !== group?.name) updates.name = name;

    // Handle different icon types
    if (pickedImage?.base64) {
      // If user picked an image, use it as imageUrl
      updates.imageUrl = `data:image/jpeg;base64,${pickedImage.base64}`;
    } else if (icon && icon !== (group?.imageUrl || group?.icon || "")) {
      // If user selected an emoji and it's different from current
      // Check if it's an emoji (not a URL)
      const isEmoji = ICON_CHOICES.includes(icon);
      if (isEmoji) {
        updates.imageUrl = icon; // Store emoji as imageUrl for now
      } else {
        updates.imageUrl = icon; // Store other text/URL as imageUrl
      }
    }

    if (Object.keys(updates).length === 0)
      return Alert.alert("Nothing to update");
    try {
      setSaving(true);
      const res = await apiUpdateGroup(groupId, updates);
      setGroup(res.data);
      if (pickedImage) setPickedImage(null);
      Alert.alert("Updated", "Group updated successfully.");
    } catch (e) {
      console.error("Update failed", e);
      Alert.alert(
        "Error",
        e.response?.data?.detail || "Failed to update group"
      );
    } finally {
      setSaving(false);
    }
  };

  const pickImage = async () => {
    if (!isAdmin) return;
    // Ask permissions
    const { status } = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (status !== "granted") {
      Alert.alert(
        "Permission required",
        "We need media library permission to select an image."
      );
      return;
    }
    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      base64: true,
      allowsEditing: true,
      aspect: [1, 1],
      quality: 0.8,
    });
    if (!result.canceled && result.assets && result.assets.length > 0) {
      const asset = result.assets[0];
      setPickedImage({ uri: asset.uri, base64: asset.base64 });
    }
  };

  const onShareInvite = async () => {
    try {
      const code = group?.joinCode;
      if (!code) return;
      await Share.share({
        message: `Join my group on Splitwiser! Use code ${code}`,
      });
    } catch (e) {
      console.error("Share failed", e);
    }
  };

  const onKick = (memberId, name) => {
    if (!isAdmin) return;
    if (memberId === user?._id) return; // safeguard
    Alert.alert("Remove member", `Are you sure you want to remove ${name}?`, [
      { text: "Cancel", style: "cancel" },
      {
        text: "Remove",
        style: "destructive",
        onPress: async () => {
          try {
            // Pre-check balances using optimized settlements
            const settlementsRes = await getOptimizedSettlements(groupId);
            const settlements =
              settlementsRes?.data?.optimizedSettlements || [];
            const hasUnsettled = settlements.some(
              (s) =>
                (s.fromUserId === memberId || s.toUserId === memberId) &&
                (s.amount || 0) > 0
            );
            if (hasUnsettled) {
              Alert.alert(
                "Cannot remove",
                "This member has unsettled balances in the group."
              );
              return;
            }
            await apiRemoveMember(groupId, memberId);
            await load();
          } catch (e) {
            console.error("Remove failed", e);
            Alert.alert(
              "Error",
              e.response?.data?.detail || "Failed to remove member"
            );
          }
        },
      },
    ]);
  };

  const onLeave = () => {
    Alert.alert(
      "Leave group",
      "You can leave only when your balances are settled. Continue?",
      [
        { text: "Cancel", style: "cancel" },
        {
          text: "Leave",
          style: "destructive",
          onPress: async () => {
            try {
              await apiLeaveGroup(groupId);
              Alert.alert("Left group");
              navigation.popToTop();
            } catch (e) {
              console.error("Leave failed", e);
              Alert.alert(
                "Cannot leave",
                e.response?.data?.detail || "Please settle balances first"
              );
            }
          },
        },
      ]
    );
  };

  const onDeleteGroup = () => {
    if (!isAdmin) return;
    // Only allow delete if no other members present
    const others = members.filter((m) => m.userId !== user?._id);
    if (others.length > 0) {
      Alert.alert(
        "Cannot delete",
        "Remove all members first, or transfer admin."
      );
      return;
    }
    Alert.alert(
      "Delete group",
      "This will permanently delete the group. Continue?",
      [
        { text: "Cancel", style: "cancel" },
        {
          text: "Delete",
          style: "destructive",
          onPress: async () => {
            try {
              await apiDeleteGroup(groupId);
              Alert.alert("Group deleted");
              navigation.popToTop();
            } catch (e) {
              console.error("Delete failed", e);
              Alert.alert(
                "Error",
                e.response?.data?.detail || "Failed to delete group"
              );
            }
          },
        },
      ]
    );
  };

  const renderMemberItem = (m) => {
    const isSelf = m.userId === user?._id;
    const displayName = m.user?.name || "Unknown";
    const imageUrl = m.user?.imageUrl;
    return (
      <List.Item
        key={m.userId}
        title={displayName}
        description={m.role === "admin" ? "Admin" : undefined}
        left={() =>
          imageUrl ? (
            <Avatar.Image size={40} source={{ uri: imageUrl }} />
          ) : (
            <Avatar.Text size={40} label={(displayName || "?").charAt(0)} />
          )
        }
        right={() =>
          isAdmin && !isSelf ? (
            <IconButton
              icon="account-remove"
              onPress={() => onKick(m.userId, displayName)}
              accessibilityLabel={`Remove ${displayName} from group`}
              accessibilityRole="button"
            />
          ) : null
        }
      />
    );
  };

  if (loading) {
    return (
      <View style={styles.loaderContainer}>
        <ActivityIndicator />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <ScrollView contentContainerStyle={styles.scrollContent}>
        <Card style={styles.card}>
          <Card.Title title="Group Info" />
          <Card.Content>
            <TextInput
              label="Group Name"
              value={name}
              onChangeText={setName}
              editable={!!isAdmin}
              style={{ marginBottom: 12 }}
              accessibilityLabel="Group Name"
            />
            <Text style={{ marginBottom: 8 }}>Icon</Text>
            <View style={styles.iconRow}>
              {ICON_CHOICES.map((i) => (
                <Button
                  key={i}
                  mode={icon === i ? "contained" : "outlined"}
                  style={styles.iconBtn}
                  onPress={() => setIcon(i)}
                  disabled={!isAdmin}
                  accessibilityLabel={`Select icon ${i}`}
                  accessibilityRole="button"
                >
                  {i}
                </Button>
              ))}
            </View>
            <View style={{ flexDirection: "row", alignItems: "center" }}>
              <Button
                mode="outlined"
                onPress={pickImage}
                disabled={!isAdmin}
                icon="image"
                style={{ marginRight: 12 }}
                accessibilityLabel="Change group image"
                accessibilityRole="button"
              >
                {pickedImage ? "Change Image" : "Upload Image"}
              </Button>
              {pickedImage?.uri ? (
                <Image
                  source={{ uri: pickedImage.uri }}
                  style={{ width: 48, height: 48, borderRadius: 24 }}
                />
              ) : group?.imageUrl &&
                /^(https?:|data:image)/.test(group.imageUrl) ? (
                <Image
                  source={{ uri: group.imageUrl }}
                  style={{ width: 48, height: 48, borderRadius: 24 }}
                />
              ) : group?.imageUrl ? (
                <Text style={{ fontSize: 32 }}>{group.imageUrl}</Text>
              ) : null}
            </View>
            {isAdmin && (
              <Button
                mode="contained"
                style={{ marginTop: 12 }}
                loading={saving}
                disabled={saving}
                onPress={onSave}
                accessibilityLabel="Save Changes"
                accessibilityRole="button"
              >
                Save Changes
              </Button>
            )}
          </Card.Content>
        </Card>

        <Card style={styles.card}>
          <Card.Title title="Members" />
          <Card.Content>{members.map(renderMemberItem)}</Card.Content>
        </Card>

        <Card style={styles.card}>
          <Card.Title title="Invite" />
          <Card.Content>
            <Text style={{ marginBottom: 8 }}>
              Join Code: {group?.joinCode}
            </Text>
            <Button
              mode="outlined"
              onPress={onShareInvite}
              icon="share-variant"
              accessibilityLabel="Share invite code"
              accessibilityRole="button"
            >
              Share invite
            </Button>
          </Card.Content>
        </Card>

        <Card style={styles.card}>
          <Card.Title title="Danger Zone" />
          <Card.Content>
            <View>
              <Button
                mode="outlined"
                buttonColor="#fff"
                textColor="#d32f2f"
                onPress={onLeave}
                icon="logout-variant"
                accessibilityLabel="Leave Group"
                accessibilityRole="button"
                accessibilityHint="You must settle balances before leaving"
              >
                Leave Group
              </Button>
              {isAdmin && (
                <Button
                  mode="contained"
                  buttonColor="#d32f2f"
                  onPress={onDeleteGroup}
                  icon="delete"
                  style={{ marginTop: 8 }}
                  accessibilityLabel="Delete Group"
                  accessibilityRole="button"
                  accessibilityHint="Permanently deletes the group and all data"
                >
                  Delete Group
                </Button>
              )}
            </View>
          </Card.Content>
        </Card>
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1 },
  scrollContent: { padding: 16 },
  loaderContainer: { flex: 1, justifyContent: "center", alignItems: "center" },
  card: { marginBottom: 16 },
  iconRow: { flexDirection: "row", flexWrap: "wrap", marginBottom: 8 },
  iconBtn: { marginRight: 8, marginBottom: 8 },
});

export default GroupSettingsScreen;
