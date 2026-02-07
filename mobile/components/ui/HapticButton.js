import React from 'react';
import { Button } from 'react-native-paper';
import * as Haptics from 'expo-haptics';

const HapticButton = ({ onPress, ...props }) => {
  const handlePress = (e) => {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    if (onPress) onPress(e);
  };

  return <Button onPress={handlePress} {...props} />;
};

export default HapticButton;
