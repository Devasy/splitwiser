import React, { useState, useContext } from 'react';
import { View, StyleSheet, Alert } from 'react-native';
import { Text, TextInput } from 'react-native-paper';
import HapticButton from '../components/ui/HapticButton';
import { AuthContext } from '../context/AuthContext';

const LoginScreen = ({ navigation }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const { login, loginWithBiometrics, isBiometricEnabled, isBiometricSupported } = useContext(AuthContext);

  const handleLogin = async () => {
    if (!email || !password) {
      Alert.alert('Error', 'Please enter both email and password.');
      return;
    }
    setIsLoading(true);
    const success = await login(email, password);
    setIsLoading(false);
    if (!success) {
      Alert.alert('Login Failed', 'Invalid email or password. Please try again.');
    }
  };

  const handleBiometricLogin = async () => {
    setIsLoading(true);
    const success = await loginWithBiometrics();
    if (success) {
      return;
    }
    setIsLoading(false);
    Alert.alert('Biometric Login Failed', 'Please try again or use your password.');
  };

  return (
    <View style={styles.container}>
      <Text variant="headlineMedium" style={styles.title}>Welcome Back!</Text>
      <TextInput
        label="Email"
        value={email}
        onChangeText={setEmail}
        style={styles.input}
        keyboardType="email-address"
        autoCapitalize="none"
        accessibilityLabel="Email address"
      />
      <TextInput
        label="Password"
        value={password}
        onChangeText={setPassword}
        style={styles.input}
        secureTextEntry
        accessibilityLabel="Password"
      />
      <HapticButton
        mode="contained"
        onPress={handleLogin}
        style={styles.button}
        loading={isLoading}
        disabled={isLoading}
        accessibilityLabel="Login to your account"
        accessibilityRole="button"
      >
        Login
      </HapticButton>

      {isBiometricEnabled && isBiometricSupported && (
        <HapticButton
          mode="outlined"
          onPress={handleBiometricLogin}
          style={styles.button}
          icon="face-recognition"
          loading={isLoading}
          disabled={isLoading}
          accessibilityLabel="Login with Biometrics"
          accessibilityRole="button"
          accessibilityHint="Uses FaceID or TouchID to log in"
        >
          Login with FaceID/TouchID
        </HapticButton>
      )}

      <HapticButton
        onPress={() => navigation.navigate("Signup")}
        style={styles.button}
        accessibilityLabel="Go to sign up screen"
        accessibilityRole="button"
        accessibilityHint="Navigates to the account creation screen"
      >
        Don't have an account? Sign Up
      </HapticButton>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    padding: 16,
  },
  title: {
    textAlign: 'center',
    marginBottom: 24,
  },
  input: {
    marginBottom: 16,
  },
  button: {
    marginTop: 8,
  },
});

export default LoginScreen;
