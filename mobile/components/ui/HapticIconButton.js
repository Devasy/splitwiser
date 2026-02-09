import { IconButton } from 'react-native-paper';
import { withHapticFeedback } from './hapticUtils';

const HapticIconButton = withHapticFeedback(IconButton);

export default HapticIconButton;
