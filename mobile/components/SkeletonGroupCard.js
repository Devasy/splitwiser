import React, { useEffect, useRef } from 'react';
import { Animated, StyleSheet, View } from 'react-native';
import { Card, useTheme } from 'react-native-paper';

const SkeletonGroupCard = () => {
  const theme = useTheme();
  const opacity = useRef(new Animated.Value(0.3)).current;

  useEffect(() => {
    const animation = Animated.loop(
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
    animation.start();

    return () => animation.stop();
  }, [opacity]);

  const skeletonColor = theme.colors.surfaceVariant;

  return (
    <Card
      style={styles.card}
      accessibilityRole="progressbar"
      accessibilityLabel="Loading group..."
    >
      {/* Simulate Card.Title */}
      <View style={styles.titleContainer}>
        {/* Avatar */}
        <Animated.View
          style={[
            styles.avatar,
            { backgroundColor: skeletonColor, opacity },
          ]}
        />
        {/* Title Text */}
        <Animated.View
          style={[
            styles.title,
            { backgroundColor: skeletonColor, opacity },
          ]}
        />
      </View>

      {/* Simulate Card.Content */}
      <View style={styles.contentContainer}>
        {/* Status Text */}
        <Animated.View
          style={[
            styles.status,
            { backgroundColor: skeletonColor, opacity },
          ]}
        />
      </View>
    </Card>
  );
};

const styles = StyleSheet.create({
  card: {
    marginBottom: 16,
  },
  titleContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingLeft: 16,
    paddingRight: 16,
    paddingTop: 16,
    paddingBottom: 0, // Adjusted to match visual flow better with content below
    minHeight: 72,
  },
  avatar: {
    width: 40,
    height: 40,
    borderRadius: 20,
    marginRight: 16,
  },
  title: {
    width: 140,
    height: 20,
    borderRadius: 4,
  },
  contentContainer: {
    padding: 16,
  },
  status: {
    width: '70%',
    height: 16,
    borderRadius: 4,
  },
});

export default SkeletonGroupCard;
