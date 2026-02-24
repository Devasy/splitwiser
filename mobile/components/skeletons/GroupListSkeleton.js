import React from 'react';
import { View, StyleSheet } from 'react-native';
import { Card } from 'react-native-paper';
import Skeleton from '../ui/Skeleton';

const GroupListSkeleton = () => {
  // Render 5 items to fill the screen
  const items = Array.from({ length: 5 }, (_, i) => i);

  return (
    <View style={styles.container} accessible={true} accessibilityLabel="Loading groups">
      {items.map((key) => (
        <Card key={key} style={styles.card}>
          <Card.Title
            title={<Skeleton width={150} height={20} />}
            left={(props) => (
              <Skeleton width={40} height={40} borderRadius={20} />
            )}
          />
          <Card.Content>
            <Skeleton width={200} height={16} style={{ marginTop: 4 }} />
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
});

export default GroupListSkeleton;
