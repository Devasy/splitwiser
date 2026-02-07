import React from 'react';
import { Appbar } from 'react-native-paper';
import * as Haptics from 'expo-haptics';

const HapticAppbarAction = ({ onPress, ...props }) => {
  const handlePress = (e) => {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    if (onPress) onPress(e);
  };
  return <Appbar.Action onPress={handlePress} {...props} />;
};

const HapticAppbarBackAction = ({ onPress, ...props }) => {
  const handlePress = (e) => {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    if (onPress) onPress(e);
  };
  return <Appbar.BackAction onPress={handlePress} {...props} />;
};

export { HapticAppbarAction, HapticAppbarBackAction };
