import * as ImagePicker from "expo-image-picker";
import { useContext, useState } from "react";
import { Alert, StyleSheet, View } from "react-native";
import { Appbar, Avatar, Button, TextInput, Title } from "react-native-paper";
import { updateUser } from "../api/auth";
import { AuthContext } from "../context/AuthContext";

const EditProfileScreen = ({ navigation }) => {
  const { user, token, updateUserInContext } = useContext(AuthContext);
  const [name, setName] = useState(user?.name || "");
  const [pickedImage, setPickedImage] = useState(null); // { uri, base64 }
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleUpdateProfile = async () => {
    if (!name) {
      Alert.alert("Error", "Name cannot be empty.");
      return;
    }
    setIsSubmitting(true);
    try {
      const updates = { name };

      // Add image if picked
      if (pickedImage?.base64) {
        // Dynamically determine MIME type from picker metadata
        const mime =
          pickedImage.mimeType && /image\//.test(pickedImage.mimeType)
            ? pickedImage.mimeType
            : "image/jpeg"; // fallback
        updates.imageUrl = `data:${mime};base64,${pickedImage.base64}`;
      }

      const response = await updateUser(updates);
      updateUserInContext(response.data);
      Alert.alert("Success", "Profile updated successfully.");
      navigation.goBack();
    } catch (error) {
      console.error("Failed to update profile:", error);
      Alert.alert("Error", "Failed to update profile.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const pickImage = async () => {
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
      // Capture mimeType (expo-image-picker provides mimeType on iOS/Android SDK 49+)
      let mimeType = asset.mimeType || asset.type; // expo sometimes supplies type like 'image'
      if (mimeType && !/image\//.test(mimeType)) {
        // if it's just 'image', normalize
        if (mimeType === 'image') mimeType = 'image/jpeg';
      }
      if (!mimeType || !/image\//.test(mimeType)) {
        // Attempt to infer from file extension as a lightweight fallback
        const ext = (asset.uri || "").split(".").pop()?.toLowerCase();
        if (ext === "png") mimeType = "image/png";
        else if (ext === "webp") mimeType = "image/webp";
        else if (ext === "gif") mimeType = "image/gif";
        else if (ext === "jpg" || ext === "jpeg") mimeType = "image/jpeg";
        else mimeType = "image/jpeg"; // safe default
      }
      setPickedImage({ uri: asset.uri, base64: asset.base64, mimeType });
    }
  };

  return (
    <View style={styles.container}>
      <Appbar.Header>
        <Appbar.BackAction onPress={() => navigation.goBack()} />
        <Appbar.Content title="Edit Profile" />
      </Appbar.Header>
      <View style={styles.content}>
        <Title>Edit Your Details</Title>

        {/* Profile Picture Section */}
        <View style={styles.profilePictureSection}>
          {pickedImage?.uri ? (
            <Avatar.Image size={100} source={{ uri: pickedImage.uri }} />
          ) : user?.imageUrl && /^(https?:|data:image)/.test(user.imageUrl) ? (
            <Avatar.Image size={100} source={{ uri: user.imageUrl }} />
          ) : (
            <Avatar.Text size={100} label={(user?.name || "?").charAt(0)} />
          )}
          <Button
            mode="outlined"
            onPress={pickImage}
            icon="camera"
            style={styles.imageButton}
            accessibilityLabel="Change profile picture"
            accessibilityRole="button"
            accessibilityHint="Opens your media library to select a new photo"
          >
            {pickedImage ? "Change Photo" : "Add Photo"}
          </Button>
        </View>

        <TextInput
          label="Name"
          value={name}
          onChangeText={setName}
          style={styles.input}
          accessibilityLabel="Full Name"
        />
        <Button
          mode="contained"
          onPress={handleUpdateProfile}
          loading={isSubmitting}
          disabled={isSubmitting}
          style={styles.button}
          accessibilityLabel="Save Changes"
          accessibilityRole="button"
        >
          Save Changes
        </Button>
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
  profilePictureSection: {
    alignItems: "center",
    marginBottom: 24,
  },
  imageButton: {
    marginTop: 12,
  },
  input: {
    marginBottom: 16,
  },
  button: {
    marginTop: 8,
  },
});

export default EditProfileScreen;
