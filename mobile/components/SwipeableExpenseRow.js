import React, { useRef } from 'react';
import { View, StyleSheet, Animated } from 'react-native';
import { Swipeable } from 'react-native-gesture-handler';
import { IconButton } from 'react-native-paper';

const SwipeableExpenseRow = ({ children, onDelete, style, deleteColor }) => {
  const swipeableRef = useRef(null);

  const renderRightActions = (progress, dragX) => {
    const scale = dragX.interpolate({
      inputRange: [-80, 0],
      outputRange: [1, 0],
      extrapolate: 'clamp',
    });

    return (
      <View
        style={[
          styles.rightActionContainer,
          { backgroundColor: deleteColor || "#ff5252" },
        ]}
      >
        <Animated.View style={[styles.deleteButton, { transform: [{ scale }] }]}>
          <IconButton
            icon="delete"
            iconColor="white"
            size={24}
            onPress={() => {
                swipeableRef.current?.close();
                onDelete();
            }}
            accessibilityLabel="Delete expense"
            accessibilityRole="button"
          />
        </Animated.View>
      </View>
    );
  };

  return (
    <Swipeable
      ref={swipeableRef}
      renderRightActions={renderRightActions}
      friction={2}
      rightThreshold={40}
      containerStyle={style}
    >
      {children}
    </Swipeable>
  );
};

const styles = StyleSheet.create({
  rightActionContainer: {
    width: 80,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#ff5252',
    borderTopRightRadius: 12,
    borderBottomRightRadius: 12,
  },
  deleteButton: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
});

export default SwipeableExpenseRow;
