import React from 'react';
import { View, StyleSheet, FlatList } from 'react-native';
import { Card } from 'react-native-paper';
import Skeleton from '../ui/Skeleton';

const GroupListSkeleton = () => {
  // Create 6 dummy items to fill the screen
  const dummyData = Array(6).fill(null);

  const renderItem = () => (
    <Card style={styles.card}>
      {/* Header Area (Avatar + Title) */}
      <View style={styles.header}>
        <Skeleton width={40} height={40} borderRadius={20} />
        <View style={styles.titleContainer}>
          <Skeleton width="50%" height={20} borderRadius={4} />
        </View>
      </View>

      {/* Content Area (Status Text) */}
      <View style={styles.content}>
        <Skeleton width="75%" height={16} borderRadius={4} />
      </View>
    </Card>
  );

  return (
    <View style={styles.container} accessible={true} accessibilityLabel="Loading groups">
      <FlatList
        data={dummyData}
        renderItem={renderItem}
        keyExtractor={(_, index) => index.toString()}
        contentContainerStyle={styles.list}
        scrollEnabled={false}
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
    // Card has default elevation and background color from theme
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16, // Match Card.Title padding
  },
  titleContainer: {
    marginLeft: 16,
    flex: 1,
  },
  content: {
    paddingHorizontal: 16,
    paddingBottom: 16, // Match Card.Content padding
  },
});

export default GroupListSkeleton;
