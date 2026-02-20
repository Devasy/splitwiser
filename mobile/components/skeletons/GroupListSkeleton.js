import React from 'react';
import { View, StyleSheet } from 'react-native';
import { Card } from 'react-native-paper';
import Skeleton from '../ui/Skeleton';

const GroupListSkeleton = () => {
  // Render 6 skeleton items to fill the screen
  return (
    <View
      style={styles.container}
      accessible={true}
      accessibilityRole="progressbar"
      accessibilityLabel="Loading groups"
    >
      {[...Array(6)].map((_, index) => (
        <Card key={index} style={styles.card}>
          <View style={styles.header}>
            {/* Avatar Skeleton */}
            <Skeleton width={40} height={40} borderRadius={20} />

            {/* Title Skeleton */}
            <View style={styles.titleContainer}>
              <Skeleton width={120} height={20} borderRadius={4} />
            </View>
          </View>

          <Card.Content>
            {/* Status Skeleton */}
            <Skeleton width={200} height={16} borderRadius={4} style={styles.status} />
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
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16, // Mimics Card.Title padding
  },
  titleContainer: {
    marginLeft: 16,
    flex: 1,
    justifyContent: 'center',
  },
  status: {
    marginTop: 4,
  }
});

export default GroupListSkeleton;
