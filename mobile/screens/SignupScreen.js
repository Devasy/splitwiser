import React, { useState, useContext } from 'react';
import { View, StyleSheet, Alert } from 'react-native';
import { Text, TextInput } from 'react-native-paper';
import HapticButton from '../components/ui/HapticButton';
import { AuthContext } from '../context/AuthContext';

const SignupScreen = ({ navigation }) => {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const { signup } = useContext(AuthContext);

  const handleSignup = async () => {
    if (!name || !email || !password || !confirmPassword) {
      Alert.alert('Error', 'Please fill in all fields.');
      return;
    }
    if (password !== confirmPassword) {
      Alert.alert('Error', "Passwords don't match!");
      return;
    }
    setIsLoading(true);
    const success = await signup(name, email, password);
    setIsLoading(false);
    if (success) {
      Alert.alert(
        'Success',
        'Your account has been created successfully. Please log in.',
        [{ text: 'OK', onPress: () => navigation.navigate('Login') }]
      );
    } else {
      Alert.alert('Signup Failed', 'An error occurred. Please try again.');
    }
  };

  return (
    <View style={styles.container}>
      <Text variant="headlineMedium" style={styles.title}>Create Account</Text>
      <TextInput
        label="Name"
        value={name}
        onChangeText={setName}
        style={styles.input}
        autoCapitalize="words"
        accessibilityLabel="Full Name"
      />
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
      <TextInput
        label="Confirm Password"
        value={confirmPassword}
        onChangeText={setConfirmPassword}
        style={styles.input}
        secureTextEntry
        accessibilityLabel="Confirm Password"
      />
      <HapticButton
        mode="contained"
        onPress={handleSignup}
        style={styles.button}
        loading={isLoading}
        disabled={isLoading}
        accessibilityLabel="Create account"
        accessibilityRole="button"
      >
        Sign Up
      </HapticButton>
      <HapticButton
        onPress={() => navigation.navigate("Login")}
        style={styles.button}
        disabled={isLoading}
        accessibilityLabel="Go to login screen"
        accessibilityRole="button"
        accessibilityHint="Navigates to the login screen"
      >
        Already have an account? Log In
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

export default SignupScreen;
