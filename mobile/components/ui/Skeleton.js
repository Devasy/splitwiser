import React, { useEffect, useRef } from 'react';
import { Animated, StyleSheet } from 'react-native';
import { Surface, useTheme } from 'react-native-paper';

const Skeleton = ({ width, height, borderRadius = 4, style }) => {
  const theme = useTheme();
  const opacity = useRef(new Animated.Value(0.3)).current;

  useEffect(() => {
    const animation = Animated.loop(
      Animated.sequence([
        Animated.timing(opacity, {
          toValue: 1,
          duration: 1000,
          useNativeDriver: true,
        }),
        Animated.timing(opacity, {
          toValue: 0.3,
          duration: 1000,
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
        { opacity },
        style,
      ]}
      accessibilityRole="progressbar"
      accessibilityLabel="Loading..."
    >
      <Surface
        style={[
          styles.skeleton,
          {
            width,
            height,
            borderRadius,
            backgroundColor: theme.colors.surfaceVariant,
          },
        ]}
        elevation={0}
      />
    </Animated.View>
  );
};

const styles = StyleSheet.create({
  skeleton: {
    overflow: 'hidden',
  },
});

export default Skeleton;
