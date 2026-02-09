import { SegmentedButtons } from 'react-native-paper';
import { withHapticFeedback } from './hapticUtils';

const HapticSegmentedButtons = withHapticFeedback(SegmentedButtons, {
  pressProp: 'onValueChange',
});

export default HapticSegmentedButtons;
