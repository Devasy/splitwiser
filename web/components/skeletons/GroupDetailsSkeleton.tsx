import React from 'react';
import { useTheme } from '../../contexts/ThemeContext';
import { THEMES } from '../../constants';
import { Skeleton } from '../ui/Skeleton';
import { motion } from 'framer-motion';

export const GroupDetailsSkeleton = () => {
    const { style } = useTheme();

    return (
        <div className="p-4 md:p-6 max-w-7xl mx-auto space-y-8 min-h-screen">
            {/* Hero Section Skeleton */}
            <motion.div
                initial={{ y: -20, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                className={`relative overflow-hidden rounded-3xl h-48 md:h-64 ${
                    style === THEMES.NEOBRUTALISM ? 'border-2 border-black shadow-[8px_8px_0px_0px_rgba(0,0,0,1)]' : 'border border-white/10 shadow-2xl'
                }`}
            >
                <div className={`absolute inset-0 ${style === THEMES.NEOBRUTALISM ? 'bg-pink-100' : 'bg-gradient-to-r from-purple-600/20 to-pink-600/20 backdrop-blur-3xl'}`} />
                <div className="relative z-10 p-8 md:p-12 h-full flex flex-col md:flex-row justify-between items-start md:items-end gap-6">
                    <div className="space-y-4 w-full max-w-sm">
                        <div className="flex items-center gap-3">
                            <Skeleton className="h-6 w-16" />
                            <Skeleton className="h-4 w-24" />
                        </div>
                        <Skeleton className="h-12 md:h-16 w-3/4" />
                    </div>
                    <div className="flex flex-col items-end gap-4">
                        <div className="flex -space-x-4">
                            {[1, 2, 3, 4, 5].map((i) => (
                                <Skeleton
                                    key={i}
                                    className={`w-12 h-12 rounded-full border-4 ${style === THEMES.NEOBRUTALISM ? 'border-black' : 'border-indigo-600'}`}
                                />
                            ))}
                            <Skeleton className={`w-12 h-12 rounded-full border-4 ${style === THEMES.NEOBRUTALISM ? 'border-black' : 'border-indigo-600'}`} />
                        </div>
                        <div className="flex gap-3">
                            <Skeleton className={`h-10 w-28 ${style === THEMES.NEOBRUTALISM ? 'rounded-none border-2 border-black' : 'rounded-xl'}`} />
                            <Skeleton className={`h-10 w-32 ${style === THEMES.NEOBRUTALISM ? 'rounded-none border-2 border-black' : 'rounded-xl'}`} />
                        </div>
                    </div>
                </div>
            </motion.div>

            {/* Group Totals Summary Cards Skeleton */}
            <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.1 }}
                className="grid grid-cols-2 md:grid-cols-4 gap-4 max-w-5xl mx-auto"
            >
                {[1, 2, 3, 4].map((i) => (
                    <div
                        key={i}
                        className={`p-4 flex flex-col items-center justify-center h-28 ${
                            style === THEMES.NEOBRUTALISM
                                ? 'bg-white border-2 border-black shadow-[4px_4px_0px_0px_rgba(0,0,0,1)]'
                                : 'bg-white/5 backdrop-blur-sm rounded-2xl border border-white/10'
                        }`}
                    >
                        <Skeleton className="h-3 w-20 mb-3" />
                        <Skeleton className="h-8 w-24 mb-2" />
                        <Skeleton className="h-3 w-16" />
                    </div>
                ))}
            </motion.div>

            {/* Navigation Pills Skeleton */}
            <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: 0.2 }}
                className="flex justify-center"
            >
                <div className={`p-1.5 flex gap-2 ${
                    style === THEMES.NEOBRUTALISM
                        ? 'bg-white border-2 border-black shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] rounded-none'
                        : 'bg-white/5 border border-white/10 backdrop-blur-xl rounded-2xl'
                }`}>
                    <Skeleton className={`h-10 w-32 ${style === THEMES.NEOBRUTALISM ? 'rounded-none' : 'rounded-xl'}`} />
                    <Skeleton className={`h-10 w-32 ${style === THEMES.NEOBRUTALISM ? 'rounded-none' : 'rounded-xl'}`} />
                    <Skeleton className={`h-10 w-32 ${style === THEMES.NEOBRUTALISM ? 'rounded-none' : 'rounded-xl'}`} />
                </div>
            </motion.div>

            {/* Content Area Skeleton (Expenses List) */}
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.3 }}
                className="space-y-4 max-w-3xl mx-auto"
            >
                {/* Search Bar Skeleton */}
                <div className="relative mb-6">
                    <Skeleton className={`w-full h-12 ${
                        style === THEMES.NEOBRUTALISM ? 'rounded-none border-2 border-black' : 'rounded-2xl'
                    }`} />
                </div>

                {/* List Items Skeletons */}
                {[1, 2, 3, 4, 5].map((i) => (
                    <div
                        key={i}
                        className={`p-5 flex items-center gap-5 ${
                            style === THEMES.NEOBRUTALISM
                                ? 'bg-white border-2 border-black shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] rounded-none'
                                : 'bg-white/5 border border-white/10 rounded-2xl backdrop-blur-sm'
                        }`}
                    >
                        {/* Date Box */}
                        <Skeleton className={`w-16 h-16 flex-shrink-0 ${
                            style === THEMES.NEOBRUTALISM ? 'rounded-none border-2 border-black' : 'rounded-xl'
                        }`} />

                        {/* Description & Payer */}
                        <div className="flex-1 space-y-3">
                            <Skeleton className="h-6 w-3/4 max-w-[200px]" />
                            <div className="flex items-center gap-2">
                                <Skeleton className={`w-5 h-5 ${style === THEMES.NEOBRUTALISM ? 'rounded-none' : 'rounded-full'}`} />
                                <Skeleton className="h-4 w-32" />
                            </div>
                        </div>

                        {/* Amount & Share */}
                        <div className="text-right space-y-2">
                            <Skeleton className="h-7 w-20 ml-auto" />
                            <Skeleton className="h-4 w-16 ml-auto" />
                        </div>
                    </div>
                ))}
            </motion.div>
        </div>
    );
};
