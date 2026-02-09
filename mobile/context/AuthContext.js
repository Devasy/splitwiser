import AsyncStorage from "@react-native-async-storage/async-storage";
import { createContext, useEffect, useState } from "react";
import * as authApi from "../api/auth";
import * as LocalAuthentication from "expo-local-authentication";
import * as SecureStore from "expo-secure-store";
import {
  clearAuthTokens,
  setAuthTokens,
  setTokenUpdateListener,
} from "../api/client";

export const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);
  const [refresh, setRefresh] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isBiometricSupported, setIsBiometricSupported] = useState(false);
  const [isBiometricEnabled, setIsBiometricEnabled] = useState(false);

  // Load token and user data from AsyncStorage on app start
  useEffect(() => {
    const loadStoredAuth = async () => {
      try {
        const storedToken = await AsyncStorage.getItem("auth_token");
        const storedRefresh = await AsyncStorage.getItem("refresh_token");
        const storedUser = await AsyncStorage.getItem("user_data");
        const biometricEnabled = await AsyncStorage.getItem("biometric_enabled");

        if (biometricEnabled === 'true') {
          setIsBiometricEnabled(true);
        }

        // Check biometric support
        const hasHardware = await LocalAuthentication.hasHardwareAsync();
        const isEnrolled = await LocalAuthentication.isEnrolledAsync();
        setIsBiometricSupported(hasHardware && isEnrolled);

        if (storedToken && storedUser) {
          setToken(storedToken);
          setRefresh(storedRefresh);
          await setAuthTokens({
            newAccessToken: storedToken,
            newRefreshToken: storedRefresh,
          });
          // Normalize user id shape: ensure `_id` exists even if API stored `id`
          const parsed = JSON.parse(storedUser);
          const normalized = parsed?._id
            ? parsed
            : parsed?.id
            ? { ...parsed, _id: parsed.id }
            : parsed;
          setUser(normalized);
        }
      } catch (error) {
        console.error("Failed to load stored authentication:", error);
      } finally {
        setIsLoading(false);
      }
    };

    loadStoredAuth();
  }, []);

  // Subscribe to token updates from the api client (refresh flow)
  useEffect(() => {
    setTokenUpdateListener(async ({ accessToken, refreshToken }) => {
      if (accessToken && accessToken !== token) setToken(accessToken);
      if (refreshToken && refreshToken !== refresh) setRefresh(refreshToken);
    });
  }, [token, refresh]);

  // Save tokens to AsyncStorage whenever they change
  useEffect(() => {
    const saveToken = async () => {
      try {
        if (token) {
          await AsyncStorage.setItem("auth_token", token);
        } else {
          await AsyncStorage.removeItem("auth_token");
        }
      } catch (error) {
        console.error("Failed to save token to storage:", error);
      }
    };

    saveToken();
  }, [token]);

  useEffect(() => {
    const saveRefresh = async () => {
      try {
        if (refresh) {
          await AsyncStorage.setItem("refresh_token", refresh);
        } else {
          await AsyncStorage.removeItem("refresh_token");
        }
      } catch (error) {
        console.error("Failed to save refresh token to storage:", error);
      }
    };
    saveRefresh();
  }, [refresh]);

  // Save user data to AsyncStorage whenever it changes
  useEffect(() => {
    const saveUser = async () => {
      try {
        if (user) {
          await AsyncStorage.setItem("user_data", JSON.stringify(user));
        } else {
          await AsyncStorage.removeItem("user_data");
        }
      } catch (error) {
        console.error("Failed to save user data to storage:", error);
      }
    };

    saveUser();
  }, [user]);

  const login = async (email, password) => {
    try {
      const response = await authApi.login(email, password);
      const { access_token, refresh_token, user: userData } = response.data;
      setToken(access_token);
      setRefresh(refresh_token);
      await setAuthTokens({
        newAccessToken: access_token,
        newRefreshToken: refresh_token,
      });
      // Normalize user id shape: ensure `_id` exists even if backend returns `id`
      const normalizedUser = userData?._id
        ? userData
        : userData?.id
        ? { ...userData, _id: userData.id }
        : userData;
      setUser(normalizedUser);

      // If biometric is enabled, check if we are logging in as a different user
      if (isBiometricEnabled) {
        const storedUserData = await SecureStore.getItemAsync("secure_user_data");
        const storedUser = storedUserData ? JSON.parse(storedUserData) : null;

        // If there is a stored user and it doesn't match the new user, disable biometrics
        // to prevent account crossover/confusion.
        if (storedUser && storedUser._id !== normalizedUser._id) {
          await disableBiometrics();
        }
        // If same user (or no stored user), the useEffect will handle syncing the new tokens
      }

      return true;
    } catch (error) {
      console.error(
        "Login failed:",
        error.response?.data?.detail || error.message
      );
      return false;
    }
  };

  const signup = async (name, email, password) => {
    try {
      await authApi.signup(name, email, password);
      return true;
    } catch (error) {
      console.error(
        "Signup failed:",
        error.response?.data?.detail || error.message
      );
      return false;
    }
  };

  const logout = async () => {
    try {
      // Clear stored authentication data from AsyncStorage
      await AsyncStorage.removeItem("auth_token");
      await AsyncStorage.removeItem("refresh_token");
      await AsyncStorage.removeItem("user_data");

      // NOTE: We deliberately do NOT clear SecureStore if biometric is enabled
      // This allows "Login with FaceID" to work after logout
      if (!isBiometricEnabled) {
         await SecureStore.deleteItemAsync("secure_auth_token");
         await SecureStore.deleteItemAsync("secure_refresh_token");
         await SecureStore.deleteItemAsync("secure_user_data");
      }

    } catch (error) {
      console.error("Failed to clear stored authentication:", error);
    }

    setToken(null);
    setRefresh(null);
    setUser(null);
    await clearAuthTokens();
  };

  const enableBiometrics = async () => {
    try {
      const result = await LocalAuthentication.authenticateAsync({
        promptMessage: "Authenticate to enable biometric login",
      });

      if (result.success) {
        if (token && refresh && user) {
          await SecureStore.setItemAsync("secure_auth_token", token);
          await SecureStore.setItemAsync("secure_refresh_token", refresh);
          await SecureStore.setItemAsync("secure_user_data", JSON.stringify(user));
          await AsyncStorage.setItem("biometric_enabled", "true");
          setIsBiometricEnabled(true);
          return true;
        }
      }
      return false;
    } catch (error) {
      console.error("Failed to enable biometrics:", error);
      return false;
    }
  };

  const disableBiometrics = async () => {
    try {
      await SecureStore.deleteItemAsync("secure_auth_token");
      await SecureStore.deleteItemAsync("secure_refresh_token");
      await SecureStore.deleteItemAsync("secure_user_data");
      await AsyncStorage.setItem("biometric_enabled", "false");
      setIsBiometricEnabled(false);
      return true;
    } catch (error) {
      console.error("Failed to disable biometrics:", error);
      return false;
    }
  };

  const loginWithBiometrics = async () => {
    try {
      const result = await LocalAuthentication.authenticateAsync({
        promptMessage: "Login with biometrics",
      });

      if (result.success) {
        const storedToken = await SecureStore.getItemAsync("secure_auth_token");
        const storedRefresh = await SecureStore.getItemAsync("secure_refresh_token");
        const storedUser = await SecureStore.getItemAsync("secure_user_data");

        if (storedToken && storedUser) {
          setToken(storedToken);
          setRefresh(storedRefresh);
          await setAuthTokens({
            newAccessToken: storedToken,
            newRefreshToken: storedRefresh || storedToken, // Fallback if refresh missing
          });

          const parsed = JSON.parse(storedUser);
          const normalized = parsed?._id
            ? parsed
            : parsed?.id
            ? { ...parsed, _id: parsed.id }
            : parsed;
          setUser(normalized);
          return true;
        }
      }
      return false;
    } catch (error) {
      console.error("Biometric login failed:", error);
      return false;
    }
  };

  // Sync tokens and user data to SecureStore whenever they change, if biometrics is enabled
  useEffect(() => {
    const syncSecureStore = async () => {
      if (isBiometricEnabled && token && refresh && user) {
        try {
          await SecureStore.setItemAsync("secure_auth_token", token);
          await SecureStore.setItemAsync("secure_refresh_token", refresh);
          await SecureStore.setItemAsync("secure_user_data", JSON.stringify(user));
        } catch (error) {
          console.error("Failed to sync secure store:", error);
        }
      }
    };
    syncSecureStore();
  }, [token, refresh, user, isBiometricEnabled]);

  const updateUserInContext = (updatedUser) => {
    // Normalize on updates too
    const normalizedUser = updatedUser?._id
      ? updatedUser
      : updatedUser?.id
      ? { ...updatedUser, _id: updatedUser.id }
      : updatedUser;
    setUser(normalizedUser);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isLoading,
        isBiometricSupported,
        isBiometricEnabled,
        login,
        signup,
        logout,
        updateUserInContext,
        enableBiometrics,
        disableBiometrics,
        loginWithBiometrics
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};
