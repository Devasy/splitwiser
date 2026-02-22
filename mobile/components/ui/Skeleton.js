import React, { useEffect, useRef } from 'react';
import { Animated, View } from 'react-native';
import { useTheme } from 'react-native-paper';

const Skeleton = ({ width, height, borderRadius, style }) => {
  const theme = useTheme();
  const opacity = useRef(new Animated.Value(0.3)).current;

  useEffect(() => {
    const animation = Animated.loop(
      Animated.sequence([
        Animated.timing(opacity, {
          toValue: 1,
          duration: 800,
          useNativeDriver: true,
        }),
        Animated.timing(opacity, {
          toValue: 0.3,
          duration: 800,
          useNativeDriver: true,
        }),
      ])
    );
    animation.start();

    return () => animation.stop();
  }, [opacity]);

  return (
    <Animated.View
      style={[
        {
          width,
          height,
          borderRadius: borderRadius || 4,
          backgroundColor: theme.colors.surfaceVariant,
          opacity,
        },
        style,
      ]}
    />
  );
};

export default Skeleton;
