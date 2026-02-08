import { Appbar } from 'react-native-paper';
import { withHapticFeedback } from './hapticUtils';

const HapticAppbarAction = withHapticFeedback(Appbar.Action);
const HapticAppbarBackAction = withHapticFeedback(Appbar.BackAction);

export { HapticAppbarAction, HapticAppbarBackAction };
