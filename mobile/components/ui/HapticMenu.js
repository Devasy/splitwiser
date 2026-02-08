import React from 'react';
import { Menu } from 'react-native-paper';
import { withHapticFeedback } from './hapticUtils';

const HapticMenuItem = withHapticFeedback(Menu.Item);

const HapticMenu = ({ children, ...props }) => {
  return <Menu {...props}>{children}</Menu>;
};

HapticMenu.Item = HapticMenuItem;

export default HapticMenu;
