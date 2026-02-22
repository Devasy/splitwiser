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
          <Card.Title
            title={<Skeleton width={150} height={20} />}
            left={(props) => (
              <Skeleton width={40} height={40} borderRadius={20} />
            )}
          />
          <Card.Content>
            <Skeleton width={220} height={16} style={{ marginTop: 4 }} />
          </Card.Content>
        </Card>
      ))}
    </View>
  );
};

export default GroupListSkeleton;
