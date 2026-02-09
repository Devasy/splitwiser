import React, { forwardRef, useCallback } from 'react';
import * as Haptics from 'expo-haptics';

/**
 * Higher-Order Component to add haptic feedback to pressable components.
 *
 * @param {React.Component} WrappedComponent - The component to wrap.
 * @param {Object} options - Configuration options.
 * @param {string} options.pressProp - The name of the prop that handles the press event (default: 'onPress').
 * @param {boolean} options.onlyWhenHandler - If true, haptics only trigger if the handler prop is provided.
 * @returns {React.Component} - The wrapped component with haptic feedback.
 */
export const withHapticFeedback = (WrappedComponent, options = {}) => {
  const { pressProp = 'onPress', onlyWhenHandler = false } = options;

  const WithHaptic = forwardRef((props, ref) => {
    const originalHandler = props[pressProp];

    const handlePress = useCallback(
      (...args) => {
        if (!onlyWhenHandler || originalHandler) {
          Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
        }
        if (originalHandler) {
          originalHandler(...args);
        }
      },
      [originalHandler]
    );

    // Only pass the intercepted handler if we're not in "onlyWhenHandler" mode OR if the handler exists.
    // However, some components might expect the handler prop to always be present or undefined.
    // If onlyWhenHandler is true and originalHandler is missing, we pass undefined to avoid attaching a no-op handler that might make the component look interactive.
    const handlerProps = {};
    if (onlyWhenHandler && !originalHandler) {
        // Do not attach our handler
        handlerProps[pressProp] = undefined;
    } else {
        handlerProps[pressProp] = handlePress;
    }

    return <WrappedComponent ref={ref} {...props} {...handlerProps} />;
  });

  const displayName = WrappedComponent.displayName || WrappedComponent.name || 'Component';
  WithHaptic.displayName = `WithHaptic(${displayName})`;

  return WithHaptic;
};

/**
 * Triggers a light haptic feedback for pull-to-refresh actions.
 */
export const triggerPullRefreshHaptic = async () => {
  await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
};
