import React, { useRef } from 'react';
import { StyleSheet, View } from 'react-native';
import ReanimatedSwipeable from 'react-native-gesture-handler/ReanimatedSwipeable';
import Reanimated, { useAnimatedStyle, interpolate, Extrapolation } from 'react-native-reanimated';
import { IconButton } from 'react-native-paper';

const SwipeableExpenseRow = ({ children, onSwipeableOpen }) => {
  const swipeableRef = useRef(null);

  const renderRightActions = (progress, drag) => {
    const style = useAnimatedStyle(() => {
      const scale = interpolate(
        drag.value,
        [-80, 0],
        [1, 0],
        Extrapolation.CLAMP
      );
      return {
        transform: [{ scale }],
      };
    });

    return (
      <View style={styles.rightActionContainer}>
        <Reanimated.View style={[styles.rightAction, style]}>
          <IconButton
            icon="delete"
            iconColor="white"
            size={24}
            onPress={() => {
              swipeableRef.current?.close();
              onSwipeableOpen();
            }}
          />
        </Reanimated.View>
      </View>
    );
  };

  return (
    <ReanimatedSwipeable
      ref={swipeableRef}
      renderRightActions={renderRightActions}
      onSwipeableOpen={onSwipeableOpen}
      rightThreshold={40}
    >
      {children}
    </ReanimatedSwipeable>
  );
};

const styles = StyleSheet.create({
  rightActionContainer: {
    width: 80,
    backgroundColor: '#dd2c00',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 16, // Matches the card margin in GroupDetailsScreen
    borderTopRightRadius: 12, // Approximate card radius
    borderBottomRightRadius: 12,
  },
  rightAction: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
});

export default SwipeableExpenseRow;
