import { List } from 'react-native-paper';
import { withHapticFeedback } from './hapticUtils';

const HapticListItem = withHapticFeedback(List.Item, { onlyWhenHandler: true });
const HapticListAccordion = withHapticFeedback(List.Accordion, { onlyWhenHandler: true });

export { HapticListItem, HapticListAccordion };
