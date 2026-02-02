import React, { useEffect, useRef } from "react";
import { View, StyleSheet, Animated } from "react-native";
import { Card, useTheme } from "react-native-paper";

const SkeletonGroupCard = () => {
  const theme = useTheme();
  const opacity = useRef(new Animated.Value(0.3)).current;

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
  }, []);

  const styles = StyleSheet.create({
    card: {
      marginBottom: 16,
      backgroundColor: theme.colors.surface,
    },
    row: {
      flexDirection: "row",
      alignItems: "center",
      padding: 16,
    },
    avatarPlaceholder: {
      width: 40,
      height: 40,
      borderRadius: 20,
      backgroundColor: theme.colors.surfaceVariant,
      marginRight: 16,
    },
    textContainer: {
      flex: 1,
      justifyContent: "center",
    },
    titlePlaceholder: {
      height: 20,
      width: "60%",
      backgroundColor: theme.colors.surfaceVariant,
      borderRadius: 4,
    },
    cardContent: {
      paddingHorizontal: 16,
      paddingBottom: 16,
    },
    statusPlaceholder: {
      height: 14,
      width: "40%",
      backgroundColor: theme.colors.surfaceVariant,
      borderRadius: 4,
    },
  });

  return (
    <Card
      style={styles.card}
      accessible={true}
      accessibilityRole="progressbar"
      accessibilityLabel="Loading group"
    >
      <Animated.View style={{ opacity }}>
        <View style={styles.row}>
          <View style={styles.avatarPlaceholder} />
          <View style={styles.textContainer}>
            <View style={styles.titlePlaceholder} />
          </View>
        </View>
        <View style={styles.cardContent}>
          <View style={styles.statusPlaceholder} />
        </View>
      </Animated.View>
    </Card>
  );
};

export default SkeletonGroupCard;
