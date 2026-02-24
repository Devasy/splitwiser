import React from 'react';
import { View } from 'react-native';
import { Card } from 'react-native-paper';
import Skeleton from '../ui/Skeleton';

const GroupListSkeleton = () => {
  // Render 4 skeleton items to fill the screen
  return (
    <View style={{ padding: 16 }} accessibilityLabel="Loading groups">
      {[1, 2, 3, 4].map((i) => (
        <Card key={i} style={{ marginBottom: 16 }}>
        <View style={{ flexDirection: 'row', alignItems: 'center', padding: 16 }}>
          <Skeleton width={40} height={40} borderRadius={20} style={{ marginRight: 16 }} />
          <Skeleton width={150} height={20} />
        </View>
          <Card.Content>
            <Skeleton width={220} height={16} style={{ marginTop: 4 }} />
          </Card.Content>
        </Card>
      ))}
    </View>
  );
};

export default GroupListSkeleton;
