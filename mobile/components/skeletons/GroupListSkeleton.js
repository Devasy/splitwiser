import React from 'react';
import { View, StyleSheet, FlatList } from 'react-native';
import { Card } from 'react-native-paper';
import Skeleton from '../ui/Skeleton';

const GroupListSkeleton = () => {
  const dummyData = [1, 2, 3, 4, 5]; // Render 5 skeleton items

  const renderItem = () => (
    <Card style={styles.card} mode="elevated">
      <Card.Title
        title={<Skeleton width={150} height={20} style={styles.skeletonTitle} />}
        subtitle={<Skeleton width={100} height={16} style={styles.skeletonSubtitle} />}
        left={(props) => (
          <Skeleton
            width={props.size}
            height={props.size}
            borderRadius={props.size / 2}
            style={styles.skeletonAvatar}
          />
        )}
      />
      <Card.Content>
         <Skeleton width={120} height={16} style={styles.skeletonStatus} />
      </Card.Content>
    </Card>
  );

  return (
    <View style={styles.container} accessible={true} accessibilityLabel="Loading groups">
      <FlatList
        data={dummyData}
        renderItem={renderItem}
        keyExtractor={(item) => item.toString()}
        contentContainerStyle={styles.list}
        scrollEnabled={false} // Disable scrolling for skeleton state
      />
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  list: {
    padding: 16,
  },
  card: {
    marginBottom: 16,
  },
  skeletonTitle: {
    marginTop: 4,
    marginBottom: 4,
  },
  skeletonSubtitle: {
    marginTop: 4,
  },
  skeletonAvatar: {
    marginRight: 8,
  },
  skeletonStatus: {
    marginTop: 8,
  }
});

export default GroupListSkeleton;
