import React from 'react';
import { SegmentedButtons } from 'react-native-paper';
import * as Haptics from 'expo-haptics';

const HapticSegmentedButtons = ({ onValueChange, ...props }) => {
  const handleChange = (value) => {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    if (onValueChange) onValueChange(value);
  };
  return <SegmentedButtons onValueChange={handleChange} {...props} />;
};

export default HapticSegmentedButtons;
