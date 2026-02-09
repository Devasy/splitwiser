import { useContext, useState } from "react";
import { Alert, StyleSheet, View } from "react-native";
import { Appbar, TextInput, Title } from "react-native-paper";
import HapticButton from '../components/ui/HapticButton';
import { HapticAppbarBackAction } from '../components/ui/HapticAppbar';
import { joinGroup } from "../api/groups";
import { AuthContext } from "../context/AuthContext";

const JoinGroupScreen = ({ navigation, route }) => {
  const { token } = useContext(AuthContext);
  const [joinCode, setJoinCode] = useState("");
  const [isJoining, setIsJoining] = useState(false);
  const { onGroupJoined } = route.params;

  const handleJoinGroup = async () => {
    if (!joinCode) {
      Alert.alert("Error", "Please enter a join code.");
      return;
    }
    setIsJoining(true);
    try {
      await joinGroup(joinCode);
      Alert.alert("Success", "Successfully joined the group.");
      onGroupJoined(); // Call the callback to refresh the groups list
      navigation.goBack();
    } catch (error) {
      console.error("Failed to join group:", error);
      Alert.alert(
        "Error",
        "Failed to join group. Please check the code and try again."
      );
    } finally {
      setIsJoining(false);
    }
  };

  return (
    <View style={styles.container}>
      <Appbar.Header>
        <HapticAppbarBackAction onPress={() => navigation.goBack()} />
        <Appbar.Content title="Join a Group" />
      </Appbar.Header>
      <View style={styles.content}>
        <Title>Enter Group Code</Title>
        <TextInput
          label="Join Code"
          value={joinCode}
          onChangeText={setJoinCode}
          style={styles.input}
          autoCapitalize="characters"
          accessibilityLabel="Group Join Code"
        />
        <HapticButton
          mode="contained"
          onPress={handleJoinGroup}
          loading={isJoining}
          disabled={isJoining}
          style={styles.button}
          accessibilityLabel="Join Group"
          accessibilityRole="button"
        >
          Join Group
        </HapticButton>
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
  input: {
    marginBottom: 16,
  },
  button: {
    marginTop: 8,
  },
});

export default JoinGroupScreen;
