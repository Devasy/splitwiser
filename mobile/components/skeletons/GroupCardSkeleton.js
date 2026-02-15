import React from 'react';
import { StyleSheet } from 'react-native';
import { Card } from 'react-native-paper';
import Skeleton from '../ui/Skeleton';

const GroupCardSkeleton = () => {
  return (
    <Card style={styles.card}>
      <Card.Title
        title={<Skeleton width={120} height={20} />}
        left={() => <Skeleton width={40} height={40} borderRadius={20} />}
      />
      <Card.Content>
        <Skeleton width={200} height={16} style={styles.subtitle} />
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
