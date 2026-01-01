import { Card } from '../ui/Card';
import { Skeleton } from '../ui/Skeleton';

export const DashboardSkeleton = () => {
  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* Summary Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {[1, 2, 3].map((i) => (
          <Card key={i} className="flex flex-col items-center justify-center text-center h-[200px]">
            {/* Icon placeholder */}
            <Skeleton className="w-16 h-16 rounded-full mb-4" />
            {/* Label placeholder */}
            <Skeleton className="w-24 h-4 mb-2" />
            {/* Value placeholder */}
            <Skeleton className="w-32 h-8" />
          </Card>
        ))}
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Chart Section */}
        <Card title="Balance Overview">
          <div className="mt-4 space-y-4">
             {/* Chart bars placeholder */}
             <div className="flex items-end justify-between h-[250px] px-4 space-x-4">
                <Skeleton className="w-full h-[40%]" />
                <Skeleton className="w-full h-[70%]" />
                <Skeleton className="w-full h-[50%]" />
                <Skeleton className="w-full h-[80%]" />
             </div>
          </div>
        </Card>

        {/* Recent Activity Section */}
        <Card title="Recent Activity">
          <div className="mt-4 space-y-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="flex items-center space-x-4">
                <Skeleton className="w-10 h-10 rounded-full" />
                <div className="flex-1 space-y-2">
                  <Skeleton className="w-3/4 h-4" />
                  <Skeleton className="w-1/2 h-3" />
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
};
