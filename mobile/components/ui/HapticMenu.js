import React from 'react';
import { Menu } from 'react-native-paper';
import { withHapticFeedback } from './hapticUtils';

const HapticMenuItem = withHapticFeedback(Menu.Item);

const HapticMenu = React.forwardRef(({ children, ...props }, ref) => {
  return <Menu ref={ref} {...props}>{children}</Menu>;
});
HapticMenu.displayName = 'HapticMenu';

HapticMenu.Item = HapticMenuItem;

export default HapticMenu;
