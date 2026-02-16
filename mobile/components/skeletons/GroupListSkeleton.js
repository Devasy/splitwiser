import React from 'react';
import { View, StyleSheet } from 'react-native';
import { Card } from 'react-native-paper';
import Skeleton from '../ui/Skeleton';

const GroupListSkeleton = () => {
  return (
    <View
      style={styles.list}
      accessibilityRole="progressbar"
      accessibilityLabel="Loading groups list"
    >
      {[1, 2, 3, 4, 5].map((key) => (
        <Card key={key} style={styles.card}>
          <Card.Title
            title={<Skeleton width={120} height={20} />}
            left={(props) => (
              <Skeleton width={40} height={40} borderRadius={20} style={props.style} />
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
  list: {
    padding: 16,
  },
  card: {
    marginBottom: 16,
  },
});

export default GroupListSkeleton;
