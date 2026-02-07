import React from 'react';
import { FAB } from 'react-native-paper';
import * as Haptics from 'expo-haptics';

const HapticFAB = ({ onPress, ...props }) => {
  const handlePress = (e) => {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    if (onPress) onPress(e);
  };

  return <FAB onPress={handlePress} {...props} />;
};

export default HapticFAB;
