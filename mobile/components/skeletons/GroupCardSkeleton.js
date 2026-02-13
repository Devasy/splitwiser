import React from 'react';
import { Card } from 'react-native-paper';
import Skeleton from '../ui/Skeleton';

const GroupCardSkeleton = () => {
  return (
    <Card style={{ marginBottom: 16 }}>
      <Card.Title
        title={<Skeleton width={120} height={20} />}
        left={(props) => <Skeleton width={40} height={40} borderRadius={20} />}
      />
      <Card.Content>
        <Skeleton width={200} height={16} style={{ marginTop: 4 }} />
      </Card.Content>
    </Card>
  );
};

export default GroupCardSkeleton;
