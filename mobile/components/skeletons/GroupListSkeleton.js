import React from 'react';
import { View, StyleSheet } from 'react-native';
import { Card } from 'react-native-paper';
import Skeleton from '../ui/Skeleton';

const GroupListSkeleton = () => {
  return (
    <View
      style={styles.container}
      accessible={true}
      accessibilityLabel="Loading groups"
      accessibilityRole="progressbar"
    >
      {[...Array(6)].map((_, index) => (
        <Card key={index} style={styles.card}>
          <Card.Title
            title={
              <Skeleton width="60%" height={20} borderRadius={4} />
            }
            left={(props) => (
              <Skeleton
                width={props.size}
                height={props.size}
                borderRadius={props.size / 2}
              />
            )}
          />
          <Card.Content>
            <Skeleton
              width="80%"
              height={16}
              borderRadius={4}
              style={styles.status}
            />
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
  status: {
    marginTop: 4,
  },
});

export default GroupListSkeleton;
