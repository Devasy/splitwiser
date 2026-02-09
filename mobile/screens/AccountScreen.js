import { useContext } from "react";
import { Alert, StyleSheet, View } from "react-native";
import { Appbar, Avatar, Divider, List, Switch, Text } from "react-native-paper";
import { HapticListItem } from '../components/ui/HapticList';
import { AuthContext } from "../context/AuthContext";

const AccountScreen = ({ navigation }) => {
  const {
    user,
    logout,
    isBiometricSupported,
    isBiometricEnabled,
    enableBiometrics,
    disableBiometrics
  } = useContext(AuthContext);

  const handleLogout = () => {
    logout();
  };

  const handleComingSoon = () => {
    Alert.alert("Coming Soon", "This feature is not yet implemented.");
  };

  const toggleBiometric = async (value) => {
    if (value) {
      const success = await enableBiometrics();
      if (!success) {
        Alert.alert("Error", "Failed to enable biometric authentication.");
      }
    } else {
      const success = await disableBiometrics();
      if (!success) {
        Alert.alert("Error", "Failed to disable biometric authentication.");
      }
    }
  };

  return (
    <View style={styles.container}>
      <Appbar.Header>
        <Appbar.Content title="Account" />
      </Appbar.Header>
      <View style={styles.content}>
        <View style={styles.profileSection}>
          {user?.imageUrl && /^(https?:|data:image)/.test(user.imageUrl) ? (
            <Avatar.Image size={80} source={{ uri: user.imageUrl }} />
          ) : (
            <Avatar.Text size={80} label={user?.name?.charAt(0) || "A"} />
          )}
          <Text variant="headlineSmall" style={styles.name}>
            {user?.name}
          </Text>
          <Text variant="bodyLarge" style={styles.email}>
            {user?.email}
          </Text>
        </View>

        <List.Section>
          <HapticListItem
            title="Edit Profile"
            left={() => <List.Icon icon="account-edit" />}
            onPress={() => navigation.navigate("EditProfile")}
            accessibilityLabel="Edit Profile"
            accessibilityRole="button"
          />
          <Divider />
          <HapticListItem
            title="Email Settings"
            left={() => <List.Icon icon="email-edit-outline" />}
            onPress={handleComingSoon}
            accessibilityLabel="Email Settings"
            accessibilityRole="button"
          />
          <Divider />

          {isBiometricSupported && (
            <>
              <HapticListItem
                title="Biometric Login"
                description="Use FaceID/TouchID to login"
                left={() => <List.Icon icon="face-recognition" />}
                right={() => (
                  <Switch
                    value={isBiometricEnabled}
                    onValueChange={toggleBiometric}
                  />
                )}
                onPress={() => toggleBiometric(!isBiometricEnabled)}
                accessibilityLabel="Enable Biometric Login"
                accessibilityRole="switch"
                accessibilityState={{ checked: isBiometricEnabled }}
              />
              <Divider />
            </>
          )}

          <HapticListItem
            title="Send Feedback"
            left={() => <List.Icon icon="message-alert-outline" />}
            onPress={handleComingSoon}
            accessibilityLabel="Send Feedback"
            accessibilityRole="button"
          />
          <Divider />
          <HapticListItem
            title="Import from Splitwise"
            left={() => <List.Icon icon="import" />}
            onPress={() => navigation.navigate("SplitwiseImport")}
            accessibilityLabel="Import from Splitwise"
            accessibilityRole="button"
          />
          <Divider />
          <HapticListItem
            title="Logout"
            left={() => <List.Icon icon="logout" />}
            onPress={handleLogout}
            accessibilityLabel="Logout"
            accessibilityRole="button"
            accessibilityHint="Logs you out of the application"
          />
        </List.Section>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  content: {
    padding: 16,
  },
  profileSection: {
    alignItems: "center",
    marginBottom: 24,
  },
  name: {
    marginTop: 16,
  },
  email: {
    marginTop: 4,
    color: "gray",
  },
});

export default AccountScreen;
