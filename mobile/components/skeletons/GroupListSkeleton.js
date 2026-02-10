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
      {[...Array(5)].map((_, index) => (
        <Card key={index} style={styles.card}>
          <Card.Title
            title={<Skeleton width={120} height={20} />}
            left={(props) => (
              <Skeleton
                width={props.size}
                height={props.size}
                borderRadius={props.size / 2}
              />
            )}
          />
          <Card.Content>
            <Skeleton width={200} height={16} style={styles.subtitle} />
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
