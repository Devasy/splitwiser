import { ArrowRight, DollarSign, PieChart as PieChartIcon, TrendingDown, TrendingUp, Users } from 'lucide-react';
import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Bar,
  BarChart,
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from 'recharts';
import { DashboardSkeleton } from '../components/skeletons/DashboardSkeleton';
import { Card } from '../components/ui/Card';
import { THEMES } from '../constants';
import { useTheme } from '../contexts/ThemeContext';
import { getBalanceSummary, getFriendsBalance, getGroups } from '../services/api';
import { BalanceSummary, FriendBalance, Group } from '../types';

// Color palette for charts
const CHART_COLORS = [
  '#10b981', // emerald
  '#3b82f6', // blue
  '#f59e0b', // amber
  '#ef4444', // red
  '#8b5cf6', // violet
  '#ec4899', // pink
  '#06b6d4', // cyan
  '#84cc16', // lime
];

interface GroupWithBalance extends Group {
  userBalance?: number;
}

export const Dashboard = () => {
  const [summary, setSummary] = useState<BalanceSummary | null>(null);
  const [friends, setFriends] = useState<FriendBalance[]>([]);
  const [groups, setGroups] = useState<GroupWithBalance[]>([]);
  const [loading, setLoading] = useState(true);
  const { style, mode } = useTheme();
  const navigate = useNavigate();

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [summaryRes, friendsRes, groupsRes] = await Promise.all([
          getBalanceSummary(),
          getFriendsBalance(),
          getGroups()
        ]);
        setSummary(summaryRes.data);
        setFriends(friendsRes.data.friendsBalance || []);

        // Merge groups with their balance from summary
        const groupsWithBalance = (groupsRes.data.groups || []).map((group: Group) => {
          const groupBalance = summaryRes.data.groupsSummary?.find(
            (g: any) => g.group_id === group._id
          );
          return {
            ...group,
            userBalance: groupBalance?.yourBalanceInGroup || 0
          };
        });
        setGroups(groupsWithBalance);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  if (loading) return <DashboardSkeleton />;

  // Prepare data for charts
  const balanceChartData = [
    { name: 'Owed To You', value: summary?.totalOwedToYou || 0, color: '#10b981' },
    { name: 'You Owe', value: summary?.totalYouOwe || 0, color: '#ef4444' },
  ];

  // Group balances for pie chart (only groups with non-zero balance)
  const groupBalanceData = groups
    .filter(g => Math.abs(g.userBalance || 0) > 0.01)
    .map((group, index) => ({
      name: group.name,
      value: Math.abs(group.userBalance || 0),
      isPositive: (group.userBalance || 0) >= 0,
      color: CHART_COLORS[index % CHART_COLORS.length],
    }));

  // Friends balance distribution
  const friendsBalanceData = friends
    .filter(f => Math.abs(f.netBalance) > 0.01)
    .slice(0, 8)
    .map((friend, index) => ({
      name: friend.userName,
      value: Math.abs(friend.netBalance),
      isPositive: friend.netBalance > 0,
      color: friend.netBalance > 0 ? '#10b981' : '#ef4444',
    }));

  // Custom tooltip for pie charts
  const CustomPieTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className={`p-3 shadow-lg ${style === THEMES.GLASSMORPHISM ? 'bg-white/90 backdrop-blur-sm rounded-lg' : 'bg-white border-2 border-black'}`}>
          <p className="font-bold">{data.name}</p>
          <p className={data.isPositive ? 'text-emerald-500' : 'text-red-500'}>
            {data.isPositive ? '+' : '-'}${data.value.toFixed(2)}
          </p>
        </div>
      );
    }
    return null;
  };

  const cardClasses = style === THEMES.NEOBRUTALISM
    ? 'border-2 border-black shadow-[4px_4px_0px_0px_rgba(0,0,0,1)]'
    : '';

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card className="flex flex-col items-center justify-center text-center">
          <div className={`p-4 mb-4 ${style === THEMES.NEOBRUTALISM ? 'bg-emerald-100 text-black border-2 border-black rounded-none' : 'bg-emerald-100 text-emerald-600 rounded-full'}`}>
            <TrendingUp size={32} />
          </div>
          <p className="opacity-70 font-medium">Owed to You</p>
          <h2 className={`text-3xl font-extrabold ${style === THEMES.NEOBRUTALISM ? 'text-black' : 'text-emerald-500'}`}>
            ${(summary?.totalOwedToYou ?? 0).toFixed(2)}
          </h2>
        </Card>

        <Card className="flex flex-col items-center justify-center text-center">
          <div className={`p-4 mb-4 ${style === THEMES.NEOBRUTALISM ? 'bg-red-100 text-black border-2 border-black rounded-none' : 'bg-red-100 text-red-600 rounded-full'}`}>
            <TrendingDown size={32} />
          </div>
          <p className="opacity-70 font-medium">You Owe</p>
          <h2 className={`text-3xl font-extrabold ${style === THEMES.NEOBRUTALISM ? 'text-black' : 'text-red-500'}`}>
            ${(summary?.totalYouOwe ?? 0).toFixed(2)}
          </h2>
        </Card>

        <Card className="flex flex-col items-center justify-center text-center">
          <div className={`p-4 mb-4 ${style === THEMES.NEOBRUTALISM ? 'bg-blue-100 text-black border-2 border-black rounded-none' : 'bg-blue-100 text-blue-600 rounded-full'}`}>
            <DollarSign size={32} />
          </div>
          <p className="opacity-70 font-medium">Net Balance</p>
          <h2 className={`text-3xl font-extrabold ${summary && summary.netBalance >= 0 ? (style === THEMES.NEOBRUTALISM ? 'text-black' : 'text-emerald-500') : (style === THEMES.NEOBRUTALISM ? 'text-black' : 'text-red-500')}`}>
            ${(summary?.netBalance ?? 0).toFixed(2)}
          </h2>
        </Card>
      </div>

      {/* Charts Row 1: Balance Overview + Group Distribution */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card title="Balance Overview">
          <div className="h-[300px] w-full mt-4">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={balanceChartData}>
                <XAxis
                  dataKey="name"
                  tick={{ fill: mode === 'dark' ? '#fff' : '#000' }}
                  axisLine={false}
                  tickLine={false}
                />
                <YAxis
                  tick={{ fill: mode === 'dark' ? '#fff' : '#000' }}
                  axisLine={false}
                  tickLine={false}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: mode === 'dark' ? '#333' : '#fff',
                    borderRadius: style === THEMES.GLASSMORPHISM ? '12px' : '0px',
                    border: style === THEMES.NEOBRUTALISM ? '2px solid black' : 'none',
                    boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)'
                  }}
                  cursor={{ fill: 'transparent' }}
                />
                <Bar dataKey="value" radius={style === THEMES.GLASSMORPHISM ? [8, 8, 0, 0] : 0} barSize={60}>
                  {balanceChartData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} stroke={style === THEMES.NEOBRUTALISM ? 'black' : 'none'} strokeWidth={2} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>

        <Card title="Spending by Group">
          {groupBalanceData.length > 0 ? (
            <div className="h-[300px] w-full mt-4">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={groupBalanceData}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={100}
                    paddingAngle={2}
                    dataKey="value"
                    stroke={style === THEMES.NEOBRUTALISM ? 'black' : 'none'}
                    strokeWidth={style === THEMES.NEOBRUTALISM ? 2 : 0}
                  >
                    {groupBalanceData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip content={<CustomPieTooltip />} />
                  <Legend
                    formatter={(value) => <span className="text-sm">{value}</span>}
                    wrapperStyle={{ fontSize: '12px' }}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center h-[300px] opacity-50">
              <PieChartIcon size={48} className="mb-2" />
              <p>No group balances to display</p>
            </div>
          )}
        </Card>
      </div>

      {/* Charts Row 2: Friends Balance + Quick Actions */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card title="Friends Balance Distribution">
          {friendsBalanceData.length > 0 ? (
            <div className="h-[300px] w-full mt-4">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={friendsBalanceData} layout="vertical">
                  <XAxis
                    type="number"
                    tick={{ fill: mode === 'dark' ? '#fff' : '#000' }}
                    axisLine={false}
                    tickLine={false}
                  />
                  <YAxis
                    type="category"
                    dataKey="name"
                    tick={{ fill: mode === 'dark' ? '#fff' : '#000', fontSize: 12 }}
                    axisLine={false}
                    tickLine={false}
                    width={100}
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: mode === 'dark' ? '#333' : '#fff',
                      borderRadius: style === THEMES.GLASSMORPHISM ? '12px' : '0px',
                      border: style === THEMES.NEOBRUTALISM ? '2px solid black' : 'none',
                    }}
                    formatter={(value: number, name: string, props: any) => [
                      `$${value.toFixed(2)}`,
                      props.payload.isPositive ? 'Owes You' : 'You Owe'
                    ]}
                  />
                  <Bar
                    dataKey="value"
                    radius={style === THEMES.GLASSMORPHISM ? [0, 4, 4, 0] : 0}
                    barSize={20}
                  >
                    {friendsBalanceData.map((entry, index) => (
                      <Cell
                        key={`cell-${index}`}
                        fill={entry.color}
                        stroke={style === THEMES.NEOBRUTALISM ? 'black' : 'none'}
                        strokeWidth={1}
                      />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center h-[300px] opacity-50">
              <Users size={48} className="mb-2" />
              <p>No friend balances to display</p>
            </div>
          )}
        </Card>

        <Card title="Quick Actions">
          <div className="space-y-4 mt-4">
            {/* Groups with balances */}
            {groups.filter(g => Math.abs(g.userBalance || 0) > 0.01).slice(0, 5).map((group) => (
              <button
                key={group._id}
                type="button"
                onClick={() => navigate(`/groups/${group._id}`)}
                className={`w-full p-4 flex items-center justify-between transition-all ${style === THEMES.NEOBRUTALISM
                    ? 'bg-white border-2 border-black hover:shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] hover:-translate-y-1'
                    : 'bg-white/50 backdrop-blur-sm rounded-lg hover:bg-white/80'
                  }`}
              >
                <div className="text-left">
                  <p className="font-bold">{group.name}</p>
                  <p className={`text-sm ${(group.userBalance || 0) >= 0 ? 'text-emerald-500' : 'text-red-500'}`}>
                    {(group.userBalance || 0) >= 0 ? 'You are owed' : 'You owe'}: ${Math.abs(group.userBalance || 0).toFixed(2)}
                  </p>
                </div>
                <ArrowRight size={20} />
              </button>
            ))}

            {groups.filter(g => Math.abs(g.userBalance || 0) > 0.01).length === 0 && (
              <div className="flex flex-col items-center justify-center h-[200px] opacity-50">
                <p>All groups are settled up!</p>
              </div>
            )}
          </div>
        </Card>
      </div>

      {/* Individual vs Group Totals */}
      {summary?.groupsSummary && summary.groupsSummary.length > 0 && (
        <Card title="Your Share vs Group Total by Group">
          <p className="text-sm opacity-70 mb-4">Compare your personal share against total group spending</p>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {summary.groupsSummary.map((groupSum: any, index: number) => {
              const group = groups.find(g => g._id === groupSum.group_id);
              if (!group) return null;

              const yourBalance = Math.abs(groupSum.yourBalanceInGroup);
              const isPositive = groupSum.yourBalanceInGroup >= 0;

              return (
                <button
                  key={groupSum.group_id}
                  type="button"
                  onClick={() => navigate(`/groups/${groupSum.group_id}`)}
                  className={`p-4 text-left transition-all ${style === THEMES.NEOBRUTALISM
                      ? 'bg-white border-2 border-black hover:shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] hover:-translate-y-1'
                      : 'bg-white/50 backdrop-blur-sm rounded-lg hover:bg-white/80'
                    }`}
                >
                  <p className="font-bold text-sm truncate">{groupSum.group_name}</p>
                  <p className={`text-xl font-black mt-2 ${isPositive ? 'text-emerald-500' : 'text-red-500'}`}>
                    {isPositive ? '+' : '-'}${yourBalance.toFixed(2)}
                  </p>
                  <div className="w-full bg-gray-200 h-2 mt-2 rounded-full overflow-hidden">
                    <div
                      className={`h-full ${isPositive ? 'bg-emerald-500' : 'bg-red-500'}`}
                      style={{ width: `${Math.min(100, (yourBalance / (summary.totalOwedToYou + summary.totalYouOwe)) * 100)}%` }}
                    />
                  </div>
                </button>
              );
            })}
          </div>
        </Card>
      )}
    </div>
  );
};