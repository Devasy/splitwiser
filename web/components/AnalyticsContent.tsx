import { Calendar, PieChart as PieChartIcon, TrendingUp } from 'lucide-react';
import React from 'react';
import {
    Area,
    AreaChart,
    Cell,
    Legend,
    Line,
    LineChart,
    Pie,
    PieChart,
    ResponsiveContainer,
    Tooltip,
    XAxis,
    YAxis
} from 'recharts';
import { THEMES } from '../constants';
import { useTheme } from '../contexts/ThemeContext';
import { GroupAnalytics } from '../types';
import { formatCurrency } from '../utils/formatters';
import { Button } from './ui/Button';
import { Skeleton } from './ui/Skeleton';

interface AnalyticsContentProps {
    analytics: GroupAnalytics | null;
    groupCurrency: string;
    timeframe: 'month' | '6months' | 'year';
    onTimeframeChange: (timeframe: 'month' | '6months' | 'year') => void;
    selectedYear: number;
    selectedMonth: number;
    onYearChange: (year: number) => void;
    onMonthChange: (month: number) => void;
}

export const AnalyticsContent: React.FC<AnalyticsContentProps> = ({
    analytics,
    groupCurrency,
    timeframe,
    onTimeframeChange,
    selectedYear,
    selectedMonth,
    onYearChange,
    onMonthChange
}) => {
    const { style, mode } = useTheme();

    // Generate year options (last 5 years)
    const currentYear = new Date().getFullYear();
    const yearOptions = Array.from({ length: 5 }, (_, i) => currentYear - i);

    // Month options
    const monthOptions = [
        { value: 1, label: 'January' },
        { value: 2, label: 'February' },
        { value: 3, label: 'March' },
        { value: 4, label: 'April' },
        { value: 5, label: 'May' },
        { value: 6, label: 'June' },
        { value: 7, label: 'July' },
        { value: 8, label: 'August' },
        { value: 9, label: 'September' },
        { value: 10, label: 'October' },
        { value: 11, label: 'November' },
        { value: 12, label: 'December' },
    ];

    if (!analytics) {
        return (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <Skeleton className="h-80 w-full rounded-2xl" />
                <Skeleton className="h-80 w-full rounded-2xl" />
            </div>
        );
    }

    return (
        <>
            {/* Timeframe Filter */}
            <div className={`p-6 ${style === THEMES.NEOBRUTALISM ? 'bg-white border-2 border-black shadow-[4px_4px_0px_0px_rgba(0,0,0,1)]' : 'bg-white/5 backdrop-blur-sm rounded-2xl border border-white/10'}`}>
                <div className="flex flex-col gap-4">
                    <div className="flex items-center gap-2">
                        <Calendar size={20} className="opacity-60" />
                        <span className="font-bold">Select Timeframe:</span>
                    </div>

                    {/* Timeframe Type Selector */}
                    <div className="flex gap-2 flex-wrap">
                        <Button
                            onClick={() => onTimeframeChange('month')}
                            variant={timeframe === 'month' ? 'primary' : 'secondary'}
                            className={`px-4 py-2 text-sm ${timeframe === 'month' ? '' : 'opacity-60'}`}
                        >
                            Specific Month
                        </Button>
                        <Button
                            onClick={() => onTimeframeChange('6months')}
                            variant={timeframe === '6months' ? 'primary' : 'secondary'}
                            className={`px-4 py-2 text-sm ${timeframe === '6months' ? '' : 'opacity-60'}`}
                        >
                            Last 6 Months
                        </Button>
                        <Button
                            onClick={() => onTimeframeChange('year')}
                            variant={timeframe === 'year' ? 'primary' : 'secondary'}
                            className={`px-4 py-2 text-sm ${timeframe === 'year' ? '' : 'opacity-60'}`}
                        >
                            Specific Year
                        </Button>
                    </div>

                    {/* Date Selectors */}
                    <div className="flex gap-3 flex-wrap items-center">
                        {timeframe === 'month' && (
                            <>
                                <select
                                    value={selectedMonth}
                                    onChange={(e) => onMonthChange(Number(e.target.value))}
                                    className={`px-4 py-2 rounded-lg border font-medium ${style === THEMES.NEOBRUTALISM
                                        ? 'border-2 border-black bg-white'
                                        : mode === 'dark'
                                            ? 'bg-gray-800 border-gray-700 text-white'
                                            : 'bg-white border-gray-300'
                                        }`}
                                >
                                    {monthOptions.map(month => (
                                        <option key={month.value} value={month.value}>
                                            {month.label}
                                        </option>
                                    ))}
                                </select>
                                <select
                                    value={selectedYear}
                                    onChange={(e) => onYearChange(Number(e.target.value))}
                                    className={`px-4 py-2 rounded-lg border font-medium ${style === THEMES.NEOBRUTALISM
                                        ? 'border-2 border-black bg-white'
                                        : mode === 'dark'
                                            ? 'bg-gray-800 border-gray-700 text-white'
                                            : 'bg-white border-gray-300'
                                        }`}
                                >
                                    {yearOptions.map(year => (
                                        <option key={year} value={year}>
                                            {year}
                                        </option>
                                    ))}
                                </select>
                            </>
                        )}

                        {timeframe === 'year' && (
                            <select
                                value={selectedYear}
                                onChange={(e) => onYearChange(Number(e.target.value))}
                                className={`px-4 py-2 rounded-lg border font-medium ${style === THEMES.NEOBRUTALISM
                                    ? 'border-2 border-black bg-white'
                                    : mode === 'dark'
                                        ? 'bg-gray-800 border-gray-700 text-white'
                                        : 'bg-white border-gray-300'
                                    }`}
                            >
                                {yearOptions.map(year => (
                                    <option key={year} value={year}>
                                        {year}
                                    </option>
                                ))}
                            </select>
                        )}

                        {timeframe === '6months' && (
                            <p className="text-sm opacity-70">
                                Showing last 6 months from today
                            </p>
                        )}
                    </div>
                </div>
            </div>

            {/* Summary Stats */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div className={`p-6 text-center ${style === THEMES.NEOBRUTALISM ? 'bg-white border-2 border-black shadow-[4px_4px_0px_0px_rgba(0,0,0,1)]' : 'bg-white/5 backdrop-blur-sm rounded-2xl border border-white/10'}`}>
                    <p className="text-xs font-bold opacity-50 uppercase tracking-wider mb-2">Total Expenses</p>
                    <p className="text-3xl font-black">{formatCurrency(analytics.totalExpenses, groupCurrency)}</p>
                    <p className="text-xs opacity-50 mt-1">{analytics.expenseCount} transactions</p>
                </div>
                <div className={`p-6 text-center ${style === THEMES.NEOBRUTALISM ? 'bg-blue-50 border-2 border-black shadow-[4px_4px_0px_0px_rgba(0,0,0,1)]' : 'bg-blue-500/10 backdrop-blur-sm rounded-2xl border border-blue-500/20'}`}>
                    <p className="text-xs font-bold opacity-50 uppercase tracking-wider mb-2">Average Expense</p>
                    <p className="text-3xl font-black text-blue-600">{formatCurrency(analytics.avgExpenseAmount, groupCurrency)}</p>
                </div>
                <div className={`p-6 text-center ${style === THEMES.NEOBRUTALISM ? 'bg-purple-50 border-2 border-black shadow-[4px_4px_0px_0px_rgba(0,0,0,1)]' : 'bg-purple-500/10 backdrop-blur-sm rounded-2xl border border-purple-500/20'}`}>
                    <p className="text-xs font-bold opacity-50 uppercase tracking-wider mb-2">Period</p>
                    <p className="text-2xl font-black text-purple-600">{analytics.period}</p>
                </div>
            </div>

            {/* Charts Row */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Spending by Category - Pie Chart */}
                <div className={`p-6 ${style === THEMES.NEOBRUTALISM ? 'bg-white border-2 border-black shadow-[4px_4px_0px_0px_rgba(0,0,0,1)]' : 'bg-white/5 backdrop-blur-sm rounded-2xl border border-white/10'}`}>
                    <h3 className="text-xl font-black mb-4 flex items-center gap-2">
                        <PieChartIcon size={20} />
                        Spending by Category
                    </h3>
                    {analytics.topCategories.length > 0 ? (
                        <div className="h-[300px]">
                            <ResponsiveContainer width="100%" height="100%">
                                <PieChart>
                                    <Pie
                                        data={analytics.topCategories}
                                        cx="50%"
                                        cy="50%"
                                        labelLine={false}
                                        label={({ category, percentage }) => `${category}: ${percentage.toFixed(1)}%`}
                                        outerRadius={80}
                                        fill="#8884d8"
                                        dataKey="amount"
                                        nameKey="category"
                                        stroke={style === THEMES.NEOBRUTALISM ? 'black' : 'none'}
                                        strokeWidth={style === THEMES.NEOBRUTALISM ? 2 : 0}
                                    >
                                        {analytics.topCategories.map((entry, index) => (
                                            <Cell key={`cell-${index}`} fill={['#10b981', '#3b82f6', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#06b6d4', '#84cc16'][index % 8]} />
                                        ))}
                                    </Pie>
                                    <Tooltip
                                        formatter={(value: number) => formatCurrency(value, groupCurrency)}
                                        contentStyle={{
                                            backgroundColor: mode === 'dark' ? '#333' : '#fff',
                                            borderRadius: style === THEMES.GLASSMORPHISM ? '12px' : '0px',
                                            border: style === THEMES.NEOBRUTALISM ? '2px solid black' : 'none',
                                        }}
                                    />
                                    <Legend
                                        formatter={(value, entry: any) => `${value} (${entry.payload.count})`}
                                        wrapperStyle={{ fontSize: '12px' }}
                                    />
                                </PieChart>
                            </ResponsiveContainer>
                        </div>
                    ) : (
                        <div className="h-[300px] flex items-center justify-center opacity-50">
                            <p>No category data available</p>
                        </div>
                    )}
                </div>

                {/* Spending Trends - Area Chart */}
                <div className={`p-6 ${style === THEMES.NEOBRUTALISM ? 'bg-white border-2 border-black shadow-[4px_4px_0px_0px_rgba(0,0,0,1)]' : 'bg-white/5 backdrop-blur-sm rounded-2xl border border-white/10'}`}>
                    <h3 className="text-xl font-black mb-4 flex items-center gap-2">
                        <TrendingUp size={20} />
                        Spending Trends
                    </h3>
                    {analytics.expenseTrends.length > 0 ? (
                        <div className="h-[300px]">
                            <ResponsiveContainer width="100%" height="100%">
                                <AreaChart data={analytics.expenseTrends}>
                                    <defs>
                                        <linearGradient id="colorAmount" x1="0" y1="0" x2="0" y2="1">
                                            <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.8} />
                                            <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0} />
                                        </linearGradient>
                                    </defs>
                                    <XAxis
                                        dataKey="date"
                                        tick={{ fill: mode === 'dark' ? '#fff' : '#000', fontSize: 10 }}
                                        axisLine={false}
                                        tickLine={false}
                                        tickFormatter={(value) => new Date(value).getDate().toString()}
                                    />
                                    <YAxis
                                        tick={{ fill: mode === 'dark' ? '#fff' : '#000' }}
                                        axisLine={false}
                                        tickLine={false}
                                    />
                                    <Tooltip
                                        formatter={(value: number) => [formatCurrency(value, groupCurrency), 'Amount']}
                                        labelFormatter={(label) => new Date(label).toLocaleDateString()}
                                        contentStyle={{
                                            backgroundColor: mode === 'dark' ? '#333' : '#fff',
                                            borderRadius: style === THEMES.GLASSMORPHISM ? '12px' : '0px',
                                            border: style === THEMES.NEOBRUTALISM ? '2px solid black' : 'none',
                                        }}
                                    />
                                    <Area
                                        type="monotone"
                                        dataKey="amount"
                                        stroke="#8b5cf6"
                                        strokeWidth={style === THEMES.NEOBRUTALISM ? 3 : 2}
                                        fillOpacity={1}
                                        fill="url(#colorAmount)"
                                    />
                                </AreaChart>
                            </ResponsiveContainer>
                        </div>
                    ) : (
                        <div className="h-[300px] flex items-center justify-center opacity-50">
                            <p>No trend data available</p>
                        </div>
                    )}
                </div>
            </div>

            {/* Member Contributions Timeline */}
            <div className={`p-6 ${style === THEMES.NEOBRUTALISM ? 'bg-white border-2 border-black shadow-[4px_4px_0px_0px_rgba(0,0,0,1)]' : 'bg-white/5 backdrop-blur-sm rounded-2xl border border-white/10'}`}>
                <h3 className="text-xl font-black mb-4 flex items-center gap-2">
                    <TrendingUp size={20} />
                    Member Contributions Over Time
                </h3>
                {analytics.contributionTimeline && analytics.contributionTimeline.length > 0 ? (
                    <div className="h-[400px]">
                        <ResponsiveContainer width="100%" height="100%">
                            <LineChart data={analytics.contributionTimeline}>
                                <XAxis
                                    dataKey="date"
                                    tick={{ fill: mode === 'dark' ? '#fff' : '#000', fontSize: 10 }}
                                    axisLine={false}
                                    tickLine={false}
                                    tickFormatter={(value) => {
                                        const date = new Date(value);
                                        return `${date.getMonth() + 1}/${date.getDate()}`;
                                    }}
                                />
                                <YAxis
                                    tick={{ fill: mode === 'dark' ? '#fff' : '#000' }}
                                    axisLine={false}
                                    tickLine={false}
                                    tickFormatter={(value) => `${groupCurrency} ${value.toLocaleString()}`}
                                />
                                <Tooltip
                                    formatter={(value: number, name: string) => [formatCurrency(value, groupCurrency), name]}
                                    labelFormatter={(label) => new Date(label).toLocaleDateString()}
                                    contentStyle={{
                                        backgroundColor: mode === 'dark' ? '#333' : '#fff',
                                        borderRadius: style === THEMES.GLASSMORPHISM ? '12px' : '0px',
                                        border: style === THEMES.NEOBRUTALISM ? '2px solid black' : 'none',
                                    }}
                                />
                                <Legend />

                                {/* Total Expenses Line - Thicker and distinct */}
                                <Line
                                    type="monotone"
                                    dataKey="Total Expenses"
                                    stroke="#8b5cf6"
                                    strokeWidth={style === THEMES.NEOBRUTALISM ? 4 : 3}
                                    dot={{ r: 4 }}
                                    activeDot={{ r: 6 }}
                                />

                                {/* Individual Member Lines */}
                                {analytics.memberContributions.map((member, idx) => {
                                    const colors = ['#10b981', '#3b82f6', '#f59e0b', '#ef4444', '#ec4899', '#06b6d4', '#84cc16', '#f97316'];
                                    const color = colors[idx % colors.length];
                                    return (
                                        <Line
                                            key={member.userName}
                                            type="monotone"
                                            dataKey={member.userName}
                                            stroke={color}
                                            strokeWidth={style === THEMES.NEOBRUTALISM ? 3 : 2}
                                            dot={{ r: 3 }}
                                            activeDot={{ r: 5 }}
                                        />
                                    );
                                })}
                            </LineChart>
                        </ResponsiveContainer>
                    </div>
                ) : (
                    <div className="h-[400px] flex items-center justify-center opacity-50">
                        <p>No member contribution data available</p>
                    </div>
                )}
            </div>
        </>
    );
};
