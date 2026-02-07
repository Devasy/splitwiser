import React from 'react';
import { IconButton } from 'react-native-paper';
import * as Haptics from 'expo-haptics';

const HapticIconButton = ({ onPress, ...props }) => {
  const handlePress = (e) => {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    if (onPress) onPress(e);
  };

  return <IconButton onPress={handlePress} {...props} />;
};

export default HapticIconButton;
