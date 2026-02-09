import { useState } from "react";
import { Alert, Linking, ScrollView, StyleSheet, View } from "react-native";
import {
    Appbar,
    Card,
    IconButton,
    List,
    Text,
} from "react-native-paper";
import HapticButton from '../components/ui/HapticButton';
import { HapticAppbarBackAction } from '../components/ui/HapticAppbar';
import { getSplitwiseAuthUrl } from "../api/client";

const SplitwiseImportScreen = ({ navigation }) => {
  const [loading, setLoading] = useState(false);

  const handleOAuthImport = async () => {
    setLoading(true);
    try {
      const response = await getSplitwiseAuthUrl();
      const { authorization_url } = response.data;

      // Open Splitwise OAuth in browser
      const supported = await Linking.canOpenURL(authorization_url);
      if (supported) {
        await Linking.openURL(authorization_url);
        Alert.alert(
          "Authorization Started",
          "Please complete the authorization in your browser. Once done, the import will start automatically.",
          [{ text: "OK", onPress: () => navigation.goBack() }]
        );
      } else {
        Alert.alert("Error", "Unable to open authorization link");
        setLoading(false);
      }
    } catch (error) {
      console.error("OAuth error:", error);
      Alert.alert(
        "Error",
        error.response?.data?.detail || "Failed to initiate authorization"
      );
      setLoading(false);
    }
  };

  return (
    <View style={styles.container}>
      <Appbar.Header>
        <HapticAppbarBackAction onPress={() => navigation.goBack()} />
        <Appbar.Content title="Import from Splitwise" />
      </Appbar.Header>

      <ScrollView style={styles.content}>
        <Card style={styles.card}>
          <Card.Content>
            <Text variant="headlineSmall" style={styles.title}>
              Import Your Splitwise Data
            </Text>
            <Text variant="bodyMedium" style={styles.subtitle}>
              Import all your friends, groups, and expenses with one click
            </Text>

            <HapticButton
              mode="contained"
              onPress={handleOAuthImport}
              disabled={loading}
              style={styles.button}
              icon={loading ? undefined : "login"}
              loading={loading}
              accessibilityLabel="Connect with Splitwise"
              accessibilityRole="button"
              accessibilityHint="Opens Splitwise in your browser to authorize access"
            >
              {loading ? "Connecting..." : "Connect with Splitwise"}
            </HapticButton>

            <Text variant="bodySmall" style={styles.helperText}>
              You'll be redirected to Splitwise to authorize access
            </Text>
          </Card.Content>
        </Card>

        <Card style={styles.infoCard}>
          <Card.Title
            title="What will be imported?"
            left={(props) => <IconButton {...props} icon="information" />}
          />
          <Card.Content>
            <List.Item
              title="All your friends and their details"
              left={(props) => <List.Icon {...props} icon="account-group" />}
            />
            <List.Item
              title="All your groups with members"
              left={(props) => <List.Icon {...props} icon="account-multiple" />}
            />
            <List.Item
              title="All expenses with split details"
              left={(props) => <List.Icon {...props} icon="currency-usd" />}
            />
            <List.Item
              title="All balances and settlements"
              left={(props) => <List.Icon {...props} icon="scale-balance" />}
            />
          </Card.Content>
        </Card>

        <Card style={styles.warningCard}>
          <Card.Title
            title="Important Note"
            left={(props) => <IconButton {...props} icon="alert" />}
          />
          <Card.Content>
            <Text variant="bodySmall" style={styles.warningText}>
              After authorizing in your browser, please return to the app.
            </Text>
            <Text variant="bodySmall" style={styles.warningText}>
              The import will start automatically and may take a few minutes.
            </Text>
          </Card.Content>
        </Card>
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  content: {
    flex: 1,
    padding: 16,
  },
  card: {
    marginBottom: 16,
  },
  title: {
    marginBottom: 8,
    textAlign: "center",
  },
  subtitle: {
    marginBottom: 24,
    textAlign: "center",
    opacity: 0.7,
  },
  input: {
    marginBottom: 8,
  },
  helperText: {
    marginBottom: 24,
    opacity: 0.7,
  },
  link: {
    color: "#2196F3",
  },
  progressContainer: {
    marginBottom: 24,
  },
  progressHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    marginBottom: 8,
  },
  progressText: {
    fontWeight: "bold",
  },
  progressBar: {
    height: 8,
    borderRadius: 4,
  },
  button: {
    paddingVertical: 8,
  },
  infoCard: {
    marginBottom: 16,
    backgroundColor: "#E3F2FD",
  },
  warningCard: {
    marginBottom: 16,
    backgroundColor: "#FFF3E0",
  },
  warningText: {
    marginBottom: 4,
  },
});

export default SplitwiseImportScreen;
