import React, { useEffect, useRef } from 'react';
import { Animated } from 'react-native';
import { useTheme } from 'react-native-paper';

const Skeleton = ({ width, height, borderRadius = 4, style }) => {
  const theme = useTheme();
  const opacity = useRef(new Animated.Value(0.5)).current;

  useEffect(() => {
    Animated.loop(
      Animated.sequence([
        Animated.timing(opacity, {
          toValue: 1,
          duration: 1000,
          useNativeDriver: true,
        }),
        Animated.timing(opacity, {
          toValue: 0.5,
          duration: 1000,
          useNativeDriver: true,
        }),
      ])
    ).start();
  }, [opacity]);

  return (
    <Animated.View
      style={[
        {
          width,
          height,
          borderRadius,
          backgroundColor: theme.colors.surfaceVariant,
          opacity,
        },
        style,
      ]}
      accessibilityRole="progressbar"
      accessibilityLabel="Loading..."
    />
  );
};

export default Skeleton;
