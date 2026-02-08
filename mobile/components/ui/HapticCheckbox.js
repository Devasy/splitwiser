import { Checkbox } from 'react-native-paper';
import { withHapticFeedback } from './hapticUtils';

const HapticCheckboxItem = withHapticFeedback(Checkbox.Item);

export default HapticCheckboxItem;
