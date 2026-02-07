import React from 'react';
import { List } from 'react-native-paper';
import * as Haptics from 'expo-haptics';

const HapticListItem = ({ onPress, ...props }) => {
  const handlePress = (e) => {
    if (onPress) {
      Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
      onPress(e);
    }
  };
  return <List.Item onPress={onPress ? handlePress : undefined} {...props} />;
};

const HapticListAccordion = ({ onPress, ...props }) => {
  const handlePress = (e) => {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    if (onPress) onPress(e);
  };

  return <List.Accordion onPress={handlePress} {...props} />;
};

export { HapticListItem, HapticListAccordion };
