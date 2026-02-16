import React from 'react';
import { StyleSheet } from 'react-native';
import { Card } from 'react-native-paper';
import Skeleton from '../ui/Skeleton';

const GroupCardSkeleton = ({ index = 0 }) => {
  // Deterministic random-looking widths based on index
  const titleWidth = 100 + ((index * 37) % 60); // 100 - 159
  const subtitleWidth = 140 + ((index * 53) % 90); // 140 - 229

  return (
    <Card style={styles.card}>
      <Card.Title
        title={<Skeleton width={titleWidth} height={20} />}
        left={() => <Skeleton width={40} height={40} borderRadius={20} />}
      />
      <Card.Content>
        <Skeleton width={subtitleWidth} height={16} style={styles.subtitle} />
      </Card.Content>
    </Card>
  );
};

const styles = StyleSheet.create({
  card: {
    marginBottom: 16,
  },
  subtitle: {
    marginTop: 4,
  },
});

export default GroupCardSkeleton;
