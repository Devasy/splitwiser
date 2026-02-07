import React from 'react';
import { Menu } from 'react-native-paper';
import * as Haptics from 'expo-haptics';

const HapticMenuItem = ({ onPress, ...props }) => {
  const handlePress = (e) => {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    if (onPress) onPress(e);
  };
  return <Menu.Item onPress={handlePress} {...props} />;
};

const HapticMenu = ({ children, ...props }) => {
  return <Menu {...props}>{children}</Menu>;
};

HapticMenu.Item = HapticMenuItem;

export default HapticMenu;
