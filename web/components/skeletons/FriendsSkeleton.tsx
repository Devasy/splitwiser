import { Card } from '../ui/Card';
import { Skeleton } from '../ui/Skeleton';

export const FriendsSkeleton = () => {
  return (
    <div className="p-4 md:p-6 max-w-7xl mx-auto space-y-8 min-h-screen">
      {/* Header Skeleton */}
      <div className="relative overflow-hidden rounded-3xl h-48 md:h-64 w-full">
        <Skeleton className="w-full h-full" />
      </div>

      {/* Summary Cards Skeleton */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {[1, 2].map((i) => (
          <Card key={i} className="flex items-center justify-between p-6 h-32">
            <div>
               <Skeleton className="w-32 h-4 mb-2" />
               <Skeleton className="w-24 h-8" />
            </div>
            <Skeleton className="w-12 h-12 rounded-full" />
          </Card>
        ))}
      </div>

      {/* Friends Grid Skeleton */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 items-start">
        {[1, 2, 3, 4, 5, 6].map((i) => (
          <Card key={i} className="flex flex-col p-6 h-64">
             <div className="flex justify-between items-start mb-4">
                <Skeleton className="w-14 h-14 rounded-full" />
                <Skeleton className="w-20 h-6 rounded-full" />
             </div>
             <Skeleton className="w-32 h-8 mb-2" />
             <Skeleton className="w-24 h-8" />
          </Card>
        ))}
      </div>
    </div>
  );
};
