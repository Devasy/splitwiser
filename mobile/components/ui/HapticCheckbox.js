import React from 'react';
import { Checkbox } from 'react-native-paper';
import * as Haptics from 'expo-haptics';

const HapticCheckboxItem = ({ onPress, ...props }) => {
  const handlePress = (e) => {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    if (onPress) onPress(e);
  };
  return <Checkbox.Item onPress={handlePress} {...props} />;
};

export default HapticCheckboxItem;
