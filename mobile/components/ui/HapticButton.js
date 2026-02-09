import { Button } from 'react-native-paper';
import { withHapticFeedback } from './hapticUtils';

const HapticButton = withHapticFeedback(Button);

export default HapticButton;
