import React from 'react';
import { View, StyleSheet } from 'react-native';
import { Card } from 'react-native-paper';
import Skeleton from '../ui/Skeleton';

const GroupListSkeleton = () => {
  // Create an array of 5 items to mimic a list
  const items = Array.from({ length: 5 }, (_, i) => i);

  return (
    <View style={styles.container}>
      {items.map((key) => (
        <Card key={key} style={styles.card}>
          <Card.Title
            title={<Skeleton width={150} height={20} />}
            left={() => <Skeleton width={40} height={40} borderRadius={20} />}
          />
          <Card.Content>
            <Skeleton width="100%" height={16} style={styles.subtitle} />
          </Card.Content>
        </Card>
      ))}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    padding: 16,
  },
  card: {
    marginBottom: 16,
  },
  subtitle: {
    marginTop: 4,
  },
});

export default GroupListSkeleton;
