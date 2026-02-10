import React, { useEffect, useRef } from "react";
import { View, StyleSheet, Animated } from "react-native";
import { Card, useTheme } from "react-native-paper";

const SkeletonItem = () => {
  const theme = useTheme();
  const opacity = useRef(new Animated.Value(0.3)).current;

  // Use surfaceVariant for a neutral placeholder color that adapts to dark/light mode
  const skeletonColor = theme.colors.surfaceVariant || "#E0E0E0";

  useEffect(() => {
    Animated.loop(
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
    ).start();
  }, [opacity]);

  return (
    <Card style={styles.card}>
      <Card.Content style={styles.content}>
        <View style={styles.row}>
          {/* Avatar Skeleton */}
          <Animated.View
            style={[
              styles.avatar,
              { opacity, backgroundColor: skeletonColor }
            ]}
          />

          <View style={styles.textContainer}>
            {/* Title Skeleton */}
            <Animated.View
              style={[
                styles.title,
                { opacity, backgroundColor: skeletonColor }
              ]}
            />
            {/* Subtitle/Status Skeleton */}
            <Animated.View
              style={[
                styles.subtitle,
                { opacity, backgroundColor: skeletonColor }
              ]}
            />
          </View>
        </View>
      </Card.Content>
    </Card>
  );
};

const GroupSkeleton = () => {
  return (
    <View style={styles.container}>
      {[1, 2, 3, 4, 5].map((key) => (
        <SkeletonItem key={key} />
      ))}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    padding: 16,
  },
  card: {
    marginBottom: 16,
  },
  content: {
    paddingVertical: 8,
  },
  row: {
    flexDirection: "row",
    alignItems: "center",
  },
  avatar: {
    width: 40,
    height: 40,
    borderRadius: 20,
    marginRight: 16,
  },
  textContainer: {
    flex: 1,
    justifyContent: "center",
  },
  title: {
    width: "60%",
    height: 16,
    borderRadius: 4,
    marginBottom: 8,
  },
  subtitle: {
    width: "40%",
    height: 12,
    borderRadius: 4,
  },
});

export default GroupSkeleton;
