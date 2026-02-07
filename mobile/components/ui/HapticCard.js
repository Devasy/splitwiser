import React from 'react';
import { Card } from 'react-native-paper';
import * as Haptics from 'expo-haptics';

const HapticCard = ({ onPress, ...props }) => {
  const handlePress = (e) => {
    if (onPress) {
      Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
      onPress(e);
    }
  };

  return <Card onPress={onPress ? handlePress : undefined} {...props} />;
};

// Attach subcomponents
HapticCard.Content = Card.Content;
HapticCard.Actions = Card.Actions;
HapticCard.Cover = Card.Cover;
HapticCard.Title = Card.Title;

export default HapticCard;
