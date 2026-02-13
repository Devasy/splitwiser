import React, { useEffect, useRef } from 'react';
import { Animated } from 'react-native';
import { useTheme } from 'react-native-paper';

const Skeleton = ({ width, height, borderRadius = 4, style }) => {
  const theme = useTheme();
  const opacity = useRef(new Animated.Value(0.3)).current;

  useEffect(() => {
    const pulse = Animated.loop(
      Animated.sequence([
        Animated.timing(opacity, {
          toValue: 0.7,
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
    pulse.start();

    return () => pulse.stop();
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
    />
  );
};

export default Skeleton;
