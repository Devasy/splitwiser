import { Card } from 'react-native-paper';
import { withHapticFeedback } from './hapticUtils';

const HapticCard = withHapticFeedback(Card, { onlyWhenHandler: true });

// Attach subcomponents
HapticCard.Content = Card.Content;
HapticCard.Actions = Card.Actions;
HapticCard.Cover = Card.Cover;
HapticCard.Title = Card.Title;

export default HapticCard;
