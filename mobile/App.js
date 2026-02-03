import React from 'react';
import { GestureHandlerRootView } from 'react-native-gesture-handler';
import AppNavigator from './navigation/AppNavigator';
import { PaperProvider } from 'react-native-paper';
import { AuthProvider } from './context/AuthContext';

export default function App() {
  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <AuthProvider>
        <PaperProvider>
          <AppNavigator />
        </PaperProvider>
      </AuthProvider>
    </GestureHandlerRootView>
  );
}
