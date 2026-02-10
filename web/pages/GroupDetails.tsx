import { AnimatePresence, motion } from 'framer-motion';
import { ArrowRight, Banknote, Check, Copy, DollarSign, Hash, Layers, LogOut, PieChart, Plus, Receipt, Search, Settings, Share2, Trash2, UserMinus } from 'lucide-react';
import React, { useEffect, useMemo, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { AnalyticsContent } from '../components/AnalyticsContent';
import { SettledUpState } from '../components/SettledUpState';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Modal } from '../components/ui/Modal';
import { Skeleton } from '../components/ui/Skeleton';
import { CURRENCIES, THEMES } from '../constants';
import { useAuth } from '../contexts/AuthContext';
import { useConfirm } from '../contexts/ConfirmContext';
import { useTheme } from '../contexts/ThemeContext';
import { useToast } from '../contexts/ToastContext';
import {
    createExpense,
    createSettlement,
    deleteExpense,
    deleteGroup,
    getExpenses,
    getGroupAnalytics,
    getGroupDetails,
    getGroupMembers,
    getOptimizedSettlements,
    leaveGroup, removeMember,
    updateExpense,
    updateGroup
} from '../services/api';
import { Expense, Group, GroupAnalytics, GroupMember, SplitType } from '../types';
import { formatCurrency } from '../utils/formatters';

type UnequalMode = 'amount' | 'percentage' | 'shares';

interface Settlement {
    fromUserId: string;
    fromUserName: string;
    toUserId: string;
    toUserName: string;
    amount: number;
}

export const GroupDetails = () => {
    const { id } = useParams<{ id: string }>();
    const navigate = useNavigate();
    const { user } = useAuth();
    const { confirm } = useConfirm();
    const { style } = useTheme();
    const { addToast } = useToast();

    const [group, setGroup] = useState<Group | null>(null);
    const [expenses, setExpenses] = useState<Expense[]>([]);
    const [totalSummary, setTotalSummary] = useState<any>(null); // Summary for ALL expenses in group
    const [members, setMembers] = useState<GroupMember[]>([]);
    const [settlements, setSettlements] = useState<Settlement[]>([]);
    const [loading, setLoading] = useState(true);
    const [activeTab, setActiveTab] = useState<'expenses' | 'settlements' | 'analytics'>('expenses');

    // Search and Filter State
    const [searchQuery, setSearchQuery] = useState('');
    const [analytics, setAnalytics] = useState<GroupAnalytics | null>(null);
    const [timeframe, setTimeframe] = useState<'month' | '6months' | 'year'>('month');
    const [selectedYear, setSelectedYear] = useState(new Date().getFullYear());
    const [selectedMonth, setSelectedMonth] = useState(new Date().getMonth() + 1);

    // Pagination State
    const [page, setPage] = useState(1);
    const [hasMore, setHasMore] = useState(true);
    const [loadingMore, setLoadingMore] = useState(false);

    // Modals
    const [isExpenseModalOpen, setIsExpenseModalOpen] = useState(false);
    const [isPaymentModalOpen, setIsPaymentModalOpen] = useState(false);
    const [isSettingsModalOpen, setIsSettingsModalOpen] = useState(false);

    // Expense Form State
    const [editingExpenseId, setEditingExpenseId] = useState<string | null>(null);
    const [description, setDescription] = useState('');
    const [amount, setAmount] = useState('');
    const [currency, setCurrency] = useState('USD');
    const [splitType, setSplitType] = useState<SplitType>(SplitType.EQUAL);
    const [unequalMode, setUnequalMode] = useState<UnequalMode>('amount');
    const [selectedUsers, setSelectedUsers] = useState<Set<string>>(new Set());
    const [splitValues, setSplitValues] = useState<{ [key: string]: string }>({});
    const [payerId, setPayerId] = useState('');

    // Payment Form State
    const [paymentPayerId, setPaymentPayerId] = useState('');
    const [paymentPayeeId, setPaymentPayeeId] = useState('');
    const [paymentAmount, setPaymentAmount] = useState('');

    // Group Settings State
    const [editGroupName, setEditGroupName] = useState('');
    const [editGroupCurrency, setEditGroupCurrency] = useState('USD');
    const [settingsTab, setSettingsTab] = useState<'info' | 'members' | 'danger'>('info');
    const [copied, setCopied] = useState(false);

    // Check if current user is admin
    const isAdmin = useMemo(() => {
        const me = members.find(m => m.userId === user?._id);
        return me?.role === 'admin';
    }, [members, user?._id]);

    // Calculate group totals using totalSummary (for ALL expenses, not filtered)
    const groupTotals = useMemo(() => {
        if (!totalSummary) {
            // Fallback to calculating from current expenses if totalSummary not available yet
            const totalSpent = expenses.reduce((sum, e) => sum + e.amount, 0);
            const myContribution = expenses
                .filter(e => e.paidBy === user?._id)
                .reduce((sum, e) => sum + e.amount, 0);
            const myShare = expenses.reduce((sum, e) => {
                const mySplit = e.splits.find(s => s.userId === user?._id);
                return sum + (mySplit?.amount || 0);
            }, 0);
            const netBalance = myContribution - myShare;

            return {
                totalSpent,
                myContribution,
                myShare,
                netBalance,
                expenseCount: expenses.length
            };
        }

        // Use totalSummary from backend (includes ALL expenses)
        return {
            totalSpent: totalSummary.totalAmount || 0,
            myContribution: 0, // This would need to be added to backend summary
            myShare: 0, // This would need to be added to backend summary
            netBalance: 0, // This would need to be added to backend summary
            expenseCount: totalSummary.expenseCount || 0
        };
    }, [totalSummary, expenses, user?._id]);

    useEffect(() => {
        if (id) fetchData();
    }, [id]);

    useEffect(() => {
        if (members.length > 0) {
            if (!editingExpenseId) {
                setSelectedUsers(new Set(members.map(m => m.userId)));
                if (group?.currency) setCurrency(group.currency);
                if (user && !payerId) setPayerId(user._id);
            }

            // Defaults for payment modal
            if (user && !paymentPayerId) setPaymentPayerId(user._id);
            if (members.length > 1 && !paymentPayeeId) {
                const other = members.find(m => m.userId !== user?._id);
                if (other) setPaymentPayeeId(other.userId);
            }
        }
    }, [members, group, user, editingExpenseId, payerId, paymentPayerId, paymentPayeeId]);

    // Search with debounce
    const [debouncedSearch, setDebouncedSearch] = useState('');

    useEffect(() => {
        const handler = setTimeout(() => {
            setDebouncedSearch(searchQuery);
        }, 300); // 300ms debounce

        return () => clearTimeout(handler);
    }, [searchQuery]);

    // Refetch when search changes
    useEffect(() => {
        if (id && !loading) {
            fetchData();
        }
    }, [debouncedSearch]);

    const fetchData = async () => {
        if (!id) return;
        setLoading(true);
        try {
            const [groupRes, expRes, memRes, setRes] = await Promise.all([
                getGroupDetails(id),
                getExpenses(id, 1, 20, debouncedSearch || undefined),
                getGroupMembers(id),
                getOptimizedSettlements(id)
            ]);
            setGroup(groupRes.data);
            setExpenses(expRes.data.expenses);
            setPage(1);
            setHasMore(expRes.data.pagination?.page < expRes.data.pagination?.totalPages);
            setMembers(memRes.data);
            setSettlements(setRes.data.optimizedSettlements);
            setEditGroupName(groupRes.data.name);
            setEditGroupCurrency(groupRes.data.currency || 'USD');

            // Store totalSummary separately
            if (expRes.data.totalSummary) {
                setTotalSummary(expRes.data.totalSummary);
            }
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    const loadMoreExpenses = async () => {
        if (!id || !hasMore || loadingMore) return;
        setLoadingMore(true);
        try {
            const nextPage = page + 1;
            const res = await getExpenses(id, nextPage);
            setExpenses(prev => [...prev, ...res.data.expenses]);
            setPage(nextPage);
            setHasMore(res.data.pagination?.page < res.data.pagination?.totalPages);
        } catch (err) {
            console.error(err);
            addToast("Failed to load more expenses", "error");
        } finally {
            setLoadingMore(false);
        }
    };

    const fetchAnalytics = async () => {
        if (!id) return;
        try {
            // For 6 months, don't pass month/year as backend handles it
            if (timeframe === '6months') {
                const res = await getGroupAnalytics(id, '6months', undefined, undefined);
                setAnalytics(res.data);
            } else if (timeframe === 'year') {
                const res = await getGroupAnalytics(id, 'year', selectedYear, undefined);
                setAnalytics(res.data);
            } else {
                // month - use selected year and month
                const res = await getGroupAnalytics(id, 'month', selectedYear, selectedMonth);
                setAnalytics(res.data);
            }
        } catch (err) {
            console.error(err);
            addToast("Failed to load analytics", "error");
        }
    };

    // Fetch analytics when switching to analytics tab
    useEffect(() => {
        if (activeTab === 'analytics' && !analytics) {
            fetchAnalytics();
        }
    }, [activeTab]);

    // Refetch analytics when timeframe, year, or month changes
    useEffect(() => {
        if (activeTab === 'analytics' && analytics) {
            fetchAnalytics();
        }
    }, [timeframe, selectedYear, selectedMonth]);

    // Fetch settlements
    const fetchSettlements = async () => {
        if (!id) return;
        try {
            const res = await getOptimizedSettlements(id);
            setSettlements(res.data.optimizedSettlements);
        } catch (err) {
            console.error(err);
            addToast("Failed to load settlements", "error");
        }
    };

    // Fetch settlements when switching to settlements tab
    useEffect(() => {
        if (activeTab === 'settlements') {
            fetchSettlements();
        }
    }, [activeTab]);

    const copyToClipboard = () => {
        if (group?.joinCode) {
            navigator.clipboard.writeText(group.joinCode)
                .then(() => {
                    setCopied(true);
                    setTimeout(() => setCopied(false), 2000);
                })
                .catch(() => {
                    alert('Failed to copy to clipboard');
                });
        }
    };

    const shareInvite = async () => {
        if (!group?.joinCode) return;
        const text = `Join my group on Splitwiser! Use code ${group.joinCode}`;

        if (navigator.share) {
            try {
                await navigator.share({
                    title: 'Join my Splitwiser group',
                    text,
                });
            } catch (err) {
                navigator.clipboard.writeText(text);
                alert('Invite copied to clipboard!');
            }
        } else {
            navigator.clipboard.writeText(text);
            alert('Invite copied to clipboard!');
        }
    };

    const remainingAmount = useMemo(() => {
        const total = parseFloat(amount) || 0;
        if (splitType === SplitType.EQUAL) return 0;

        const values = Object.values(splitValues) as string[];

        if (unequalMode === 'amount') {
            const sum = values.reduce((acc, val) => acc + (parseFloat(val) || 0), 0);
            return total - sum;
        }
        if (unequalMode === 'percentage') {
            const sum = values.reduce((acc, val) => acc + (parseFloat(val) || 0), 0);
            return 100 - sum;
        }
        return 0;
    }, [amount, splitType, unequalMode, splitValues]);

    // --- Handlers ---

    const openAddExpense = () => {
        setEditingExpenseId(null);
        resetExpenseForm();
        setIsExpenseModalOpen(true);
    };

    const openEditExpense = (expense: Expense) => {
        setEditingExpenseId(expense._id);
        setDescription(expense.description);
        setAmount(expense.amount.toString());
        setPayerId(expense.paidBy);
        setSplitType(expense.splitType);

        if (expense.splitType === SplitType.EQUAL) {
            setSelectedUsers(new Set(expense.splits.map(s => s.userId)));
        } else {
            setUnequalMode('amount');
            const vals: Record<string, string> = {};
            expense.splits.forEach(s => vals[s.userId] = s.amount.toString());
            setSplitValues(vals);
        }
        setIsExpenseModalOpen(true);
    };

    const handleExpenseSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!id) return;

        const numAmount = parseFloat(amount);
        let requestSplits: { userId: string; amount: number }[] = [];

        if (splitType === SplitType.EQUAL) {
            const involvedMembers = members.filter(m => selectedUsers.has(m.userId));
            if (involvedMembers.length === 0) return alert("Select at least one person.");
            const splitAmount = numAmount / involvedMembers.length;
            requestSplits = involvedMembers.map(m => ({ userId: m.userId, amount: splitAmount }));
        } else {
            const splitVals = Object.values(splitValues) as string[];
            if (unequalMode === 'amount') {
                const sum = splitVals.reduce((acc, val) => acc + (parseFloat(val) || 0), 0);
                if (Math.abs(sum - numAmount) > 0.01) return alert(`Amounts must match total.`);
                requestSplits = Object.entries(splitValues).map(([uid, val]) => ({ userId: uid, amount: parseFloat(val as string) || 0 }));
            } else if (unequalMode === 'percentage') {
                const sum = splitVals.reduce((acc, val) => acc + (parseFloat(val) || 0), 0);
                if (Math.abs(sum - 100) > 0.1) return alert(`Percentages must equal 100%.`);
                requestSplits = Object.entries(splitValues).map(([uid, val]) => ({ userId: uid, amount: (numAmount * (parseFloat(val as string) || 0)) / 100 }));
            } else if (unequalMode === 'shares') {
                const totalShares = splitVals.reduce((acc, val) => acc + (parseFloat(val) || 0), 0);
                if (totalShares === 0) return alert("Total shares cannot be zero.");
                requestSplits = Object.entries(splitValues).map(([uid, val]) => ({ userId: uid, amount: (numAmount * (parseFloat(val as string) || 0)) / totalShares }));
            }
        }

        requestSplits = requestSplits.filter(s => s.amount > 0);

        const payload = {
            description,
            amount: numAmount,
            paidBy: payerId,
            splitType,
            splits: requestSplits,
            currency,
        };

        try {
            if (editingExpenseId) {
                await updateExpense(id, editingExpenseId, payload);
                addToast('Expense updated successfully!', 'success');
            } else {
                await createExpense(id, payload);
                addToast('Expense created successfully!', 'success');
            }
            setIsExpenseModalOpen(false);
            fetchData();
        } catch (err) {
            console.error(err);
            addToast('Error saving expense', 'error');
        }
    };

    const handleDeleteExpense = async () => {
        if (!editingExpenseId || !id) return;

        const confirmed = await confirm({
            title: 'Delete Expense',
            description: 'Are you sure you want to delete this expense? This action cannot be undone.',
            confirmText: 'Delete',
            variant: 'danger'
        });

        if (confirmed) {
            try {
                await deleteExpense(id, editingExpenseId);
                setIsExpenseModalOpen(false);
                fetchData();
                addToast('Expense deleted successfully', 'success');
            } catch (err) {
                addToast("Failed to delete expense", 'error');
            }
        }
    };

    const handleRecordPayment = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!id) return;

        const numAmount = parseFloat(paymentAmount);
        if (paymentPayerId === paymentPayeeId) {
            alert('Payer and payee cannot be the same');
            return;
        }
        if (!numAmount || numAmount <= 0) {
            alert('Please enter a valid amount');
            return;
        }

        try {
            await createSettlement(id, {
                payer_id: paymentPayerId,
                payee_id: paymentPayeeId,
                amount: numAmount
            });
            setIsPaymentModalOpen(false);
            setPaymentAmount('');
            fetchData();
            addToast('Payment recorded successfully!', 'success');
        } catch (err) {
            addToast("Failed to record payment", 'error');
        }
    };

    const handleUpdateGroup = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!id) return;
        try {
            await updateGroup(id, {
                name: editGroupName,
                currency: editGroupCurrency
            });
            fetchData();
            setIsSettingsModalOpen(false);
            addToast('Group updated successfully!', 'success');
        } catch (err) {
            addToast("Failed to update group", 'error');
        }
    };

    const handleDeleteGroup = async () => {
        if (!id) return;

        const confirmed = await confirm({
            title: 'Delete Group',
            description: 'Are you sure? This will permanently delete the group and all its expenses. This action cannot be undone.',
            confirmText: 'Delete Group',
            variant: 'danger'
        });

        if (confirmed) {
            try {
                await deleteGroup(id);
                navigate('/groups');
                addToast('Group deleted successfully', 'success');
            } catch (err) {
                addToast("Failed to delete group", 'error');
            }
        }
    };

    const handleLeaveGroup = async () => {
        if (!id) return;

        const confirmed = await confirm({
            title: 'Leave Group',
            description: 'You can only leave when your balances are settled. Are you sure you want to leave?',
            confirmText: 'Leave',
            variant: 'warning'
        });

        if (confirmed) {
            try {
                await leaveGroup(id);
                addToast('You have left the group', 'success');
                navigate('/groups');
            } catch (err: any) {
                addToast(err.response?.data?.detail || "Cannot leave - please settle balances first", 'error');
            }
        }
    };

    const handleKickMember = async (memberId: string, memberName: string) => {
        if (!id || !isAdmin) return;
        if (memberId === user?._id) return;

        const hasUnsettled = settlements.some(
            s => (s.fromUserId === memberId || s.toUserId === memberId) && (s.amount || 0) > 0
        );

        if (hasUnsettled) {
            await confirm({
                title: 'Cannot Remove Member',
                description: 'This member has unsettled balances in the group. Please settle all debts before removing them.',
                confirmText: 'OK',
                variant: 'info',
                cancelText: 'Close'
            });
            return;
        }

        const confirmed = await confirm({
            title: 'Remove Member',
            description: `Are you sure you want to remove ${memberName} from the group?`,
            confirmText: 'Remove',
            variant: 'danger'
        });

        if (confirmed) {
            try {
                await removeMember(id, memberId);
                fetchData();
                addToast(`Removed ${memberName} from group`, 'success');
            } catch (err: any) {
                addToast(err.response?.data?.detail || "Failed to remove member", 'error');
            }
        }
    };

    const resetExpenseForm = () => {
        setDescription('');
        setAmount('');
        setSplitValues({});
        setSplitType(SplitType.EQUAL);
        setUnequalMode('amount');
        setSelectedUsers(new Set(members.map(m => m.userId)));
        if (user) setPayerId(user._id);
    };

    if (loading && !group) return <div className="p-8"><Skeleton className="h-64 w-full" /></div>;
    if (!group) return <div className="p-8">Group not found</div>;

    return (
        <div className="p-4 md:p-6 max-w-7xl mx-auto space-y-8 min-h-screen">
            {/* Immersive Header */}
            <motion.div
                initial={{ y: -20, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                className="relative overflow-hidden rounded-3xl"
            >
                <div className={`absolute inset-0 ${style === THEMES.NEOBRUTALISM ? 'bg-pink-200' : 'bg-gradient-to-r from-purple-600 to-pink-600'}`} />
                <div className="absolute inset-0 opacity-20 bg-[url('https://grainy-gradients.vercel.app/noise.svg')] filter contrast-125 brightness-100" />

                <div className="relative z-10 p-8 md:p-12 flex flex-col md:flex-row justify-between items-start md:items-end gap-6">
                    <div>
                        <div className="flex items-center gap-3 mb-2">
                            <span className={`px-3 py-1 text-xs font-black uppercase tracking-widest ${style === THEMES.NEOBRUTALISM ? 'bg-black text-white rounded-none' : 'bg-white/20 text-white backdrop-blur-md rounded-full'}`}>
                                Group
                            </span>
                            <button type="button" onClick={copyToClipboard} className="flex items-center gap-1 text-xs font-bold opacity-70 hover:opacity-100 transition-opacity">
                                <Copy size={12} /> {group.joinCode} {copied && <Check size={12} />}
                            </button>
                        </div>
                        <h1 className={`text-5xl md:text-7xl font-black tracking-tighter ${style === THEMES.NEOBRUTALISM ? 'text-black' : 'text-white'}`}>
                            {group.name}
                        </h1>
                    </div>

                    <div className="flex flex-col items-end gap-4">
                        <div className="flex -space-x-4">
                            {members.slice(0, 5).map((m, i) => (
                                <div key={m.userId} className={`w-12 h-12 flex items-center justify-center text-sm font-bold border-4 ${style === THEMES.NEOBRUTALISM ? 'border-black bg-white rounded-none' : 'border-indigo-600 bg-indigo-800 text-white rounded-full'}`} title={m.user?.name}>
                                    {m.user?.name?.charAt(0)}
                                </div>
                            ))}
                            {members.length > 5 && (
                                <div className={`w-12 h-12 flex items-center justify-center text-sm font-bold border-4 ${style === THEMES.NEOBRUTALISM ? 'border-black bg-gray-200 rounded-none' : 'border-indigo-600 bg-indigo-900 text-white rounded-full'}`}>
                                    +{members.length - 5}
                                </div>
                            )}
                            <button
                                type="button"
                                onClick={() => setIsSettingsModalOpen(true)}
                                className={`w-12 h-12 flex items-center justify-center border-4 hover:scale-110 transition-transform ${style === THEMES.NEOBRUTALISM ? 'border-black bg-black text-white rounded-none' : 'border-indigo-600 bg-white/20 text-white backdrop-blur-md rounded-full'}`}
                            >
                                <Settings size={20} />
                            </button>
                        </div>
                        <div className="flex gap-3">
                            <Button onClick={() => setIsPaymentModalOpen(true)} variant="secondary" size="sm" className={`shadow-lg ${style === THEMES.NEOBRUTALISM ? 'rounded-none' : ''}`}>
                                <Banknote size={16} /> Settle Up
                            </Button>
                            <Button onClick={openAddExpense} size="sm" className={`shadow-lg ${style === THEMES.NEOBRUTALISM ? 'rounded-none' : ''}`}>
                                <Plus size={16} /> Add Expense
                            </Button>
                        </div>
                    </div>
                </div>
            </motion.div>

            {/* Group Totals Summary Cards */}
            <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="grid grid-cols-2 md:grid-cols-4 gap-4 max-w-5xl mx-auto"
            >
                <div className={`p-4 text-center ${style === THEMES.NEOBRUTALISM ? 'bg-white border-2 border-black shadow-[4px_4px_0px_0px_rgba(0,0,0,1)]' : 'bg-white/5 backdrop-blur-sm rounded-2xl border border-white/10'}`}>
                    <p className="text-xs font-bold opacity-50 uppercase tracking-wider">Total Spent</p>
                    <p className="text-2xl font-black">{formatCurrency(groupTotals.totalSpent, group.currency)}</p>
                    <p className="text-xs opacity-50">{groupTotals.expenseCount} expenses</p>
                </div>
                <div className={`p-4 text-center ${style === THEMES.NEOBRUTALISM ? 'bg-emerald-50 border-2 border-black shadow-[4px_4px_0px_0px_rgba(0,0,0,1)]' : 'bg-emerald-500/10 backdrop-blur-sm rounded-2xl border border-emerald-500/20'}`}>
                    <p className="text-xs font-bold opacity-50 uppercase tracking-wider">You Paid</p>
                    <p className="text-2xl font-black text-emerald-600">{formatCurrency(groupTotals.myContribution, group.currency)}</p>
                </div>
                <div className={`p-4 text-center ${style === THEMES.NEOBRUTALISM ? 'bg-blue-50 border-2 border-black shadow-[4px_4px_0px_0px_rgba(0,0,0,1)]' : 'bg-blue-500/10 backdrop-blur-sm rounded-2xl border border-blue-500/20'}`}>
                    <p className="text-xs font-bold opacity-50 uppercase tracking-wider">Your Share</p>
                    <p className="text-2xl font-black text-blue-600">{formatCurrency(groupTotals.myShare, group.currency)}</p>
                </div>
                <div className={`p-4 text-center ${style === THEMES.NEOBRUTALISM ? (groupTotals.netBalance >= 0 ? 'bg-emerald-100' : 'bg-red-100') + ' border-2 border-black shadow-[4px_4px_0px_0px_rgba(0,0,0,1)]' : (groupTotals.netBalance >= 0 ? 'bg-emerald-500/10 border-emerald-500/20' : 'bg-red-500/10 border-red-500/20') + ' backdrop-blur-sm rounded-2xl border'}`}>
                    <p className="text-xs font-bold opacity-50 uppercase tracking-wider">Net Balance</p>
                    <p className={`text-2xl font-black ${groupTotals.netBalance >= 0 ? 'text-emerald-600' : 'text-red-600'}`}>
                        {groupTotals.netBalance >= 0 ? '+' : ''}{formatCurrency(groupTotals.netBalance, group.currency)}
                    </p>
                    <p className="text-xs opacity-50">{groupTotals.netBalance >= 0 ? 'owed to you' : 'you owe'}</p>
                </div>
            </motion.div>

            {/* Navigation Pills */}
            <div className="flex justify-center">
                <div className={`p-1.5 flex gap-2 ${style === THEMES.NEOBRUTALISM ? 'bg-white border-2 border-black shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] rounded-none' : 'bg-white/5 border border-white/10 backdrop-blur-xl rounded-2xl'}`}>
                    <button
                        type="button"
                        onClick={() => setActiveTab('expenses')}
                        className={`px-6 py-2 font-bold transition-all flex items-center gap-2 ${activeTab === 'expenses' ? (style === THEMES.NEOBRUTALISM ? 'bg-black text-white rounded-none' : 'bg-white/20 text-white shadow-sm rounded-xl') : 'opacity-60 hover:opacity-100'}`}
                    >
                        <Receipt size={18} /> Expenses
                    </button>
                    <button
                        type="button"
                        onClick={() => setActiveTab('settlements')}
                        className={`px-6 py-2 font-bold transition-all flex items-center gap-2 ${activeTab === 'settlements' ? (style === THEMES.NEOBRUTALISM ? 'bg-emerald-500 text-white rounded-none' : 'bg-emerald-500/20 text-emerald-400 shadow-sm rounded-xl') : 'opacity-60 hover:opacity-100'}`}
                    >
                        <ScaleIcon /> Balances
                    </button>
                    <button
                        type="button"
                        onClick={() => setActiveTab('analytics')}
                        className={`px-6 py-2 font-bold transition-all flex items-center gap-2 ${activeTab === 'analytics' ? (style === THEMES.NEOBRUTALISM ? 'bg-purple-500 text-white rounded-none' : 'bg-purple-500/20 text-purple-400 shadow-sm rounded-xl') : 'opacity-60 hover:opacity-100'}`}
                    >
                        <PieChart size={18} /> Analytics
                    </button>
                </div>
            </div>

            {/* Content Area */}
            <AnimatePresence mode="wait">
                {activeTab === 'expenses' ? (
                    <motion.div
                        key="expenses"
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -20 }}
                        className="space-y-4 max-w-3xl mx-auto"
                    >
                        {/* Search Bar */}
                        <div className={`relative ${style === THEMES.NEOBRUTALISM ? '' : ''}`}>
                            <Search size={20} className="absolute left-4 top-1/2 -translate-y-1/2 opacity-50" />
                            <input
                                type="text"
                                placeholder="Search expenses by description or tag..."
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                className={`w-full pl-12 pr-4 py-3 font-medium ${style === THEMES.NEOBRUTALISM
                                    ? 'bg-white border-2 border-black focus:shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] focus:-translate-y-1 transition-all rounded-none'
                                    : 'bg-white/5 border border-white/10 rounded-2xl backdrop-blur-sm focus:border-white/30 focus:bg-white/10'
                                    } outline-none`}
                            />
                            {searchQuery && (
                                <button
                                    type="button"
                                    onClick={() => setSearchQuery('')}
                                    className="absolute right-4 top-1/2 -translate-y-1/2 opacity-50 hover:opacity-100"
                                >
                                    ✕
                                </button>
                            )}
                        </div>

                        {/* Search Results Count */}
                        {searchQuery && (
                            <p className="text-sm opacity-70">
                                Found {expenses.length} expense{expenses.length !== 1 ? 's' : ''} matching "{searchQuery}"
                            </p>
                        )}

                        {loading ? Array(3).fill(0).map((_, i) => <Skeleton key={i} className="h-24 w-full rounded-2xl" />) :
                            expenses.map((expense, idx) => (
                                <motion.div
                                    layout
                                    key={expense._id}
                                    initial={{ opacity: 0, scale: 0.95 }}
                                    animate={{ opacity: 1, scale: 1 }}
                                    whileHover={{ scale: 1.02 }}
                                    onClick={() => openEditExpense(expense)}
                                    onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); openEditExpense(expense); } }}
                                    tabIndex={0}
                                    role="button"
                                    aria-label={`Expense: ${expense.description}, ${formatCurrency(expense.amount, group?.currency)}`}
                                    className={`p-5 flex items-center gap-5 cursor-pointer group relative overflow-hidden ${style === THEMES.NEOBRUTALISM
                                        ? 'bg-white border-2 border-black shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] hover:translate-x-[2px] hover:translate-y-[2px] hover:shadow-[2px_2px_0px_0px_rgba(0,0,0,1)] rounded-none'
                                        : 'bg-white/5 border border-white/10 rounded-2xl backdrop-blur-sm hover:bg-white/10 transition-all'
                                        }`}
                                >
                                    {/* Date Box */}
                                    <div className={`flex flex-col items-center justify-center w-16 h-16 flex-shrink-0 ${style === THEMES.NEOBRUTALISM ? 'bg-gray-100 border-2 border-black rounded-none' : 'bg-white/5 border border-white/10 rounded-xl'}`}>
                                        <span className="text-xs font-bold uppercase opacity-60">{new Date(expense.createdAt).toLocaleString('default', { month: 'short' })}</span>
                                        <span className="text-2xl font-black">{new Date(expense.createdAt).getDate()}</span>
                                    </div>

                                    <div className="flex-1 min-w-0">
                                        <h4 className="font-bold text-xl truncate">{expense.description}</h4>
                                        <div className="flex items-center gap-2 mt-1">
                                            <div className={`w-5 h-5 flex items-center justify-center text-[10px] font-bold ${style === THEMES.NEOBRUTALISM ? 'bg-black text-white rounded-none' : 'bg-blue-500 text-white rounded-full'}`}>
                                                {members.find(m => m.userId === expense.paidBy)?.user?.name?.charAt(0)}
                                            </div>
                                            <p className="text-sm opacity-60 truncate">
                                                <span className="font-semibold text-foreground">{members.find(m => m.userId === expense.paidBy)?.user?.name || 'Unknown'}</span> paid <span className="font-bold">{formatCurrency(expense.amount, group?.currency)}</span>
                                            </p>
                                        </div>
                                    </div>

                                    <div className="text-right">
                                        <span className={`text-xs font-bold px-2 py-1 uppercase tracking-wider ${style === THEMES.NEOBRUTALISM ? 'bg-gray-200 rounded-none' : 'bg-white/10 rounded-md'}`}>
                                            {expense.splitType}
                                        </span>
                                    </div>
                                </motion.div>
                            ))}
                        {!loading && expenses.length === 0 && (
                            <div className="text-center py-20 opacity-50 flex flex-col items-center">
                                <div className="w-20 h-20 bg-gray-100 dark:bg-white/5 rounded-full flex items-center justify-center mb-4">
                                    <Layers size={40} className="opacity-50" />
                                </div>
                                <p className="text-xl font-bold">No expenses yet</p>
                                <p className="text-sm">Add your first expense to get started!</p>
                            </div>
                        )}

                        {hasMore && expenses.length > 0 && (
                            <div className="flex justify-center py-4">
                                <Button
                                    variant="secondary"
                                    onClick={(e) => { e.stopPropagation(); loadMoreExpenses(); }}
                                    disabled={loadingMore}
                                >
                                    {loadingMore ? 'Loading...' : 'Load More'}
                                </Button>
                            </div>
                        )}
                    </motion.div>
                ) : activeTab === 'analytics' ? (
                    <motion.div
                        key="analytics"
                        initial={{ opacity: 0, scale: 0.95 }}
                        animate={{ opacity: 1, scale: 1 }}
                        exit={{ opacity: 0, scale: 0.95 }}
                        className="space-y-6 max-w-6xl mx-auto"
                    >
                        <AnalyticsContent
                            analytics={analytics}
                            groupCurrency={group?.currency || 'USD'}
                            timeframe={timeframe}
                            onTimeframeChange={setTimeframe}
                            selectedYear={selectedYear}
                            selectedMonth={selectedMonth}
                            onYearChange={setSelectedYear}
                            onMonthChange={setSelectedMonth}
                        />
                    </motion.div>
                ) : (
                    <motion.div
                        key="settlements"
                        initial={{ opacity: 0, x: 20 }}
                        animate={{ opacity: 1, x: 0 }}
                        exit={{ opacity: 0, x: -20 }}
                        className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-5xl mx-auto"
                    >
                        {loading ? <Skeleton className="h-40 w-full col-span-2" /> : settlements.map((s, idx) => (
                            <motion.div
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: idx * 0.1 }}
                                key={`${s.fromUserId}-${s.toUserId}`}
                                className={`p-6 flex flex-col items-center justify-center text-center gap-4 relative overflow-hidden ${style === THEMES.NEOBRUTALISM
                                    ? 'bg-white border-2 border-black shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] rounded-none'
                                    : 'bg-white/5 border border-white/10 rounded-3xl backdrop-blur-sm'
                                    }`}
                            >
                                <div className="flex items-center gap-4 w-full justify-center">
                                    <div className="flex flex-col items-center gap-2">
                                        <div className={`w-12 h-12 flex items-center justify-center text-lg font-bold ${style === THEMES.NEOBRUTALISM ? 'bg-red-100 border-2 border-black text-black rounded-none' : 'bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400 border-2 border-transparent dark:border-red-500/30 rounded-full'}`}>
                                            {s.fromUserName.charAt(0)}
                                        </div>
                                        <span className="font-bold text-sm truncate max-w-[80px]">{s.fromUserName}</span>
                                    </div>

                                    <div className="flex-1 flex flex-col items-center gap-1">
                                        <span className="text-xs font-bold uppercase opacity-50 tracking-widest">Pays</span>
                                        <div className="h-0.5 w-full bg-gray-200 dark:bg-gray-700 relative">
                                            <div className="absolute right-0 top-1/2 -translate-y-1/2 w-2 h-2 bg-gray-400 rounded-full" />
                                        </div>
                                        <span className="font-mono font-black text-xl">{formatCurrency(s.amount, group?.currency)}</span>
                                    </div>

                                    <div className="flex flex-col items-center gap-2">
                                        <div className={`w-12 h-12 flex items-center justify-center text-lg font-bold ${style === THEMES.NEOBRUTALISM ? 'bg-emerald-100 border-2 border-black text-black rounded-none' : 'bg-emerald-100 dark:bg-emerald-900/30 text-emerald-600 dark:text-emerald-400 border-2 border-transparent dark:border-emerald-500/30 rounded-full'}`}>
                                            {s.toUserName.charAt(0)}
                                        </div>
                                        <span className="font-bold text-sm truncate max-w-[80px]">{s.toUserName}</span>
                                    </div>
                                </div>
                            </motion.div>
                        ))}
                        {!loading && settlements.length === 0 && (
                            <SettledUpState />
                        )}
                    </motion.div>
                )}
            </AnimatePresence>

            {/* --- MODALS --- */}

            <Modal
                isOpen={isExpenseModalOpen}
                onClose={() => setIsExpenseModalOpen(false)}
                title={editingExpenseId ? 'Edit Expense' : 'Add Expense'}
                footer={
                    <div className="flex w-full justify-between gap-3">
                        {editingExpenseId ? (
                            <Button variant="danger" type="button" onClick={handleDeleteExpense}>
                                <Trash2 size={16} /> Delete
                            </Button>
                        ) : <div />}
                        <div className="flex gap-3">
                            <Button variant="ghost" type="button" onClick={() => setIsExpenseModalOpen(false)}>Cancel</Button>
                            <Button onClick={handleExpenseSubmit} disabled={remainingAmount > 0.01 && splitType === SplitType.UNEQUAL && unequalMode !== 'shares'}>
                                {editingExpenseId ? 'Save Changes' : 'Create Expense'}
                            </Button>
                        </div>
                    </div>
                }
            >
                <form className="space-y-6">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <Input
                            label="Description"
                            value={description}
                            onChange={e => setDescription(e.target.value)}
                            placeholder="e.g. Dinner at Mario's"
                            required
                            autoFocus
                        />
                        <div className="flex gap-2 items-end">
                            <div className="flex-1">
                                <Input
                                    label="Amount"
                                    type="number"
                                    step="0.01"
                                    value={amount}
                                    onChange={e => setAmount(e.target.value)}
                                    placeholder="0.00"
                                    required
                                />
                            </div>
                            <div className="w-24 flex flex-col gap-1">
                                <label className="text-sm font-semibold opacity-80">Currency</label>
                                <div className={`w-full p-3 font-bold text-center opacity-80 ${style === THEMES.NEOBRUTALISM ? 'border-2 border-black bg-white rounded-none' : 'bg-white/10 border border-white/20 rounded-lg'}`}>
                                    {currency}
                                </div>
                            </div>
                        </div>
                    </div>

                    <div>
                        <label className="block text-sm font-bold mb-2 opacity-80">Paid By</label>
                        <div className="flex flex-wrap gap-2">
                            {members.map(m => (
                                <button
                                    key={m.userId}
                                    type="button"
                                    onClick={() => setPayerId(m.userId)}
                                    className={`px-4 py-2 text-sm font-bold transition-all border ${payerId === m.userId
                                        ? (style === THEMES.NEOBRUTALISM ? 'bg-black text-white border-black rounded-none' : 'bg-blue-600 border-blue-500 text-white rounded-full')
                                        : (style === THEMES.NEOBRUTALISM ? 'bg-white text-black border-black hover:bg-gray-100 rounded-none' : 'bg-transparent border-gray-600 text-gray-400 hover:border-gray-400 rounded-full')
                                        }`}
                                >
                                    {m.userId === user?._id ? 'You' : m.user?.name}
                                </button>
                            ))}
                        </div>
                    </div>

                    <div className={`p-4 ${style === THEMES.NEOBRUTALISM ? 'border-2 border-black bg-gray-50 rounded-none' : 'bg-white/5 border border-white/10 rounded-xl'}`}>
                        <div className="flex mb-4 border-b border-gray-500/20 pb-4 gap-4">
                            <button
                                type="button"
                                onClick={() => setSplitType(SplitType.EQUAL)}
                                className={`flex items-center gap-2 font-bold ${splitType === SplitType.EQUAL ? 'text-blue-500' : 'opacity-50 hover:opacity-100'}`}
                            >
                                <div className={`w-4 h-4 rounded-full border flex items-center justify-center ${splitType === SplitType.EQUAL ? 'border-blue-500' : 'border-gray-500'}`}>
                                    {splitType === SplitType.EQUAL && <div className="w-2 h-2 rounded-full bg-blue-500" />}
                                </div>
                                Split Equally
                            </button>
                            <button
                                type="button"
                                onClick={() => setSplitType(SplitType.UNEQUAL)}
                                className={`flex items-center gap-2 font-bold ${splitType === SplitType.UNEQUAL ? 'text-blue-500' : 'opacity-50 hover:opacity-100'}`}
                            >
                                <div className={`w-4 h-4 rounded-full border flex items-center justify-center ${splitType === SplitType.UNEQUAL ? 'border-blue-500' : 'border-gray-500'}`}>
                                    {splitType === SplitType.UNEQUAL && <div className="w-2 h-2 rounded-full bg-blue-500" />}
                                </div>
                                Split Unequally
                            </button>
                        </div>

                        {splitType === SplitType.EQUAL ? (
                            <div>
                                <div className="flex justify-between items-center mb-3">
                                    <p className="text-sm opacity-60">Who is involved?</p>
                                    <button
                                        type="button"
                                        onClick={() => {
                                            if (selectedUsers.size === members.length) setSelectedUsers(new Set());
                                            else setSelectedUsers(new Set(members.map(m => m.userId)));
                                        }}
                                        className="text-xs font-bold text-blue-500 hover:underline"
                                    >
                                        {selectedUsers.size === members.length ? 'Deselect All' : 'Select All'}
                                    </button>
                                </div>
                                <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                                    {members.map(m => {
                                        const isSelected = selectedUsers.has(m.userId);
                                        return (
                                            <div
                                                key={m.userId}
                                                onClick={() => {
                                                    const newSet = new Set(selectedUsers);
                                                    if (isSelected) newSet.delete(m.userId);
                                                    else newSet.add(m.userId);
                                                    setSelectedUsers(newSet);
                                                }}
                                                className={`cursor-pointer flex items-center gap-2 p-2 border transition-all ${isSelected
                                                    ? (style === THEMES.NEOBRUTALISM ? 'bg-white border-black shadow-[2px_2px_0px_0px_rgba(0,0,0,1)] rounded-none' : 'bg-blue-500/20 border-blue-500/50 text-white rounded')
                                                    : (style === THEMES.NEOBRUTALISM ? 'bg-transparent border-gray-400 opacity-60 rounded-none' : 'bg-transparent border-gray-700 opacity-50 rounded')
                                                    }`}
                                            >
                                                <div className={`w-4 h-4 flex items-center justify-center border ${isSelected ? 'bg-blue-500 border-blue-500 text-white' : 'border-gray-500'} ${style === THEMES.NEOBRUTALISM ? 'rounded-none' : 'rounded'}`}>
                                                    {isSelected && <Check size={10} strokeWidth={4} />}
                                                </div>
                                                <span className="truncate font-medium text-sm">{m.user?.name}</span>
                                            </div>
                                        );
                                    })}
                                </div>
                            </div>
                        ) : (
                            <div>
                                <div className="flex gap-2 mb-4">
                                    {[
                                        { id: 'amount', label: 'Amount', icon: DollarSign },
                                        { id: 'percentage', label: 'Percentage', icon: PieChart },
                                        { id: 'shares', label: 'Shares', icon: Hash },
                                    ].map(mode => (
                                        <button
                                            key={mode.id}
                                            type="button"
                                            onClick={() => setUnequalMode(mode.id as UnequalMode)}
                                            className={`flex-1 py-1.5 px-2 text-sm font-bold flex items-center justify-center gap-1 transition-all ${unequalMode === mode.id
                                                ? (style === THEMES.NEOBRUTALISM ? 'bg-black text-white rounded-none' : 'bg-blue-600 text-white shadow-md rounded')
                                                : (style === THEMES.NEOBRUTALISM ? 'bg-gray-200 text-black rounded-none' : 'bg-gray-200 dark:bg-gray-800 opacity-70 hover:opacity-100 dark:text-gray-300 rounded')
                                                }`}
                                        >
                                            <mode.icon size={14} /> {mode.label}
                                        </button>
                                    ))}
                                </div>

                                <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
                                    {members.map(m => (
                                        <div key={m.userId} className="flex items-center gap-2">
                                            <span className="text-sm w-1/3 truncate font-medium">{m.user?.name}</span>
                                            <div className="relative flex-1">
                                                <input
                                                    type="number"
                                                    className={`w-full p-2 text-right font-mono font-bold outline-none border focus:border-blue-500 ${style === THEMES.NEOBRUTALISM ? 'border-black bg-white rounded-none' : 'bg-black/20 border-gray-600 text-white rounded'}`}
                                                    placeholder="0"
                                                    value={splitValues[m.userId] || ''}
                                                    onChange={e => setSplitValues({ ...splitValues, [m.userId]: e.target.value })}
                                                />
                                                <span className="absolute right-8 top-1/2 -translate-y-1/2 opacity-50 text-xs pointer-events-none">
                                                    {unequalMode === 'percentage' ? '%' : (unequalMode === 'shares' ? 'shares' : currency)}
                                                </span>
                                            </div>
                                        </div>
                                    ))}
                                </div>

                                {(unequalMode === 'amount' || unequalMode === 'percentage') && (
                                    <div className={`mt-3 text-right text-sm font-bold ${Math.abs(remainingAmount) < 0.01 ? 'text-emerald-500' : 'text-red-500'}`}>
                                        {Math.abs(remainingAmount) < 0.01 ? (
                                            <span className="flex items-center justify-end gap-1"><Check size={14} /> Perfectly distributed</span>
                                        ) : (
                                            <span>{remainingAmount > 0 ? `${remainingAmount.toFixed(2)} remaining` : `${Math.abs(remainingAmount).toFixed(2)} over limit`}</span>
                                        )}
                                    </div>
                                )}
                            </div>
                        )}
                    </div>
                </form>
            </Modal>

            <Modal
                isOpen={isPaymentModalOpen}
                onClose={() => setIsPaymentModalOpen(false)}
                title="Record Payment"
                footer={
                    <>
                        <Button variant="ghost" onClick={() => setIsPaymentModalOpen(false)}>Cancel</Button>
                        <Button onClick={handleRecordPayment}>Record</Button>
                    </>
                }
            >
                <div className="space-y-4">
                    <div className="flex flex-col gap-1">
                        <label className="text-sm font-bold opacity-80">Payer</label>
                        <select
                            className={`w-full p-3 outline-none font-bold ${style === THEMES.NEOBRUTALISM ? 'border-2 border-black bg-white rounded-none' : 'bg-white/10 border border-white/20 rounded-lg text-white'}`}
                            value={paymentPayerId}
                            onChange={e => setPaymentPayerId(e.target.value)}
                        >
                            {members.map(m => <option key={m.userId} value={m.userId}>{m.user?.name}</option>)}
                        </select>
                    </div>
                    <div className="flex justify-center">
                        <ArrowRight className="rotate-90 opacity-50" />
                    </div>
                    <div className="flex flex-col gap-1">
                        <label className="text-sm font-bold opacity-80">Payee</label>
                        <select
                            className={`w-full p-3 outline-none font-bold ${style === THEMES.NEOBRUTALISM ? 'border-2 border-black bg-white rounded-none' : 'bg-white/10 border border-white/20 rounded-lg text-white'}`}
                            value={paymentPayeeId}
                            onChange={e => setPaymentPayeeId(e.target.value)}
                        >
                            {members.filter(m => m.userId !== paymentPayerId).map(m => <option key={m.userId} value={m.userId}>{m.user?.name}</option>)}
                        </select>
                    </div>
                    <Input
                        label={`Amount (${group?.currency || 'USD'})`}
                        type="number"
                        placeholder="0.00"
                        value={paymentAmount}
                        onChange={e => setPaymentAmount(e.target.value)}
                        required
                    />
                </div>
            </Modal>

            <Modal
                isOpen={isSettingsModalOpen}
                onClose={() => { setIsSettingsModalOpen(false); setSettingsTab('info'); }}
                title="Group Settings"
            >
                <div className="space-y-4">
                    <div className={`flex gap-1 p-1 ${style === THEMES.NEOBRUTALISM ? 'border-2 border-black bg-gray-100 rounded-none' : 'bg-white/10 rounded-lg'}`}>
                        <button
                            type="button"
                            onClick={() => setSettingsTab('info')}
                            className={`flex-1 px-3 py-2 text-sm font-bold transition-all ${settingsTab === 'info' ? (style === THEMES.NEOBRUTALISM ? 'bg-white border-2 border-black rounded-none' : 'bg-white/20 rounded-md') : 'opacity-60 hover:opacity-100'}`}
                        >
                            Info
                        </button>
                        <button
                            type="button"
                            onClick={() => setSettingsTab('members')}
                            className={`flex-1 px-3 py-2 text-sm font-bold transition-all ${settingsTab === 'members' ? (style === THEMES.NEOBRUTALISM ? 'bg-white border-2 border-black rounded-none' : 'bg-white/20 rounded-md') : 'opacity-60 hover:opacity-100'}`}
                        >
                            Members
                        </button>
                        <button
                            type="button"
                            onClick={() => setSettingsTab('danger')}
                            className={`flex-1 px-3 py-2 text-sm font-bold transition-all ${settingsTab === 'danger' ? (style === THEMES.NEOBRUTALISM ? 'bg-red-100 border-2 border-black text-red-600 rounded-none' : 'bg-red-500/20 text-red-400 rounded-md') : 'opacity-60 hover:opacity-100'}`}
                        >
                            Danger
                        </button>
                    </div>

                    {settingsTab === 'info' && (
                        <div className="space-y-4">
                            <form onSubmit={handleUpdateGroup} className="space-y-4">
                                <Input
                                    label="Group Name"
                                    value={editGroupName}
                                    onChange={e => setEditGroupName(e.target.value)}
                                    disabled={!isAdmin}
                                    required
                                />
                                <div className="space-y-1.5">
                                    <label htmlFor="group-currency-select" className={`text-sm font-bold ${style === THEMES.NEOBRUTALISM ? 'text-black uppercase' : 'opacity-70'}`}>
                                        Group Currency
                                    </label>
                                    <select
                                        id="group-currency-select"
                                        value={editGroupCurrency}
                                        onChange={e => setEditGroupCurrency(e.target.value)}
                                        disabled={!isAdmin}
                                        className={`w-full p-3 font-bold transition-all outline-none ${style === THEMES.NEOBRUTALISM
                                            ? 'bg-white border-2 border-black rounded-none'
                                            : 'bg-white/10 dark:bg-white/5 border border-white/20 dark:border-white/10 rounded-xl'
                                            }`}
                                    >
                                        {Object.values(CURRENCIES).map((c) => (
                                            <option key={c.code} value={c.code}>
                                                {c.code} ({c.symbol}) - {c.name}
                                            </option>
                                        ))}
                                    </select>
                                </div>
                                {isAdmin && <Button type="submit" className="w-full">Update Group</Button>}
                            </form>
                            <div className={`p-4 ${style === THEMES.NEOBRUTALISM ? 'bg-gray-100 border-2 border-black rounded-none' : 'bg-black/5 dark:bg-white/5 rounded-lg'}`}>
                                <p className="text-sm font-bold mb-2">Invite Code</p>
                                <div className="flex items-center gap-2">
                                    <code className={`flex-1 p-2 font-mono text-lg text-center select-all ${style === THEMES.NEOBRUTALISM ? 'bg-white border-2 border-black rounded-none' : 'bg-black/10 dark:bg-black/30 rounded'}`}>
                                        {group.joinCode}
                                    </code>
                                    <Button size="sm" variant="secondary" onClick={copyToClipboard}>
                                        {copied ? <Check size={16} /> : <Copy size={16} />}
                                    </Button>
                                    <Button size="sm" variant="secondary" onClick={shareInvite}>
                                        <Share2 size={16} />
                                    </Button>
                                </div>
                            </div>
                        </div>
                    )}

                    {settingsTab === 'members' && (
                        <div className="space-y-2">
                            {members.map(m => (
                                <div key={m.userId} className={`flex items-center justify-between p-2 ${style === THEMES.NEOBRUTALISM ? 'hover:bg-gray-100 rounded-none' : 'hover:bg-black/5 dark:hover:bg-white/5 rounded'}`}>
                                    <div className="flex items-center gap-3">
                                        <div className={`w-8 h-8 flex items-center justify-center text-white text-xs font-bold ${style === THEMES.NEOBRUTALISM ? 'bg-black rounded-none' : 'bg-gradient-to-br from-purple-400 to-blue-500 rounded-full'}`}>
                                            {m.user?.name?.charAt(0)}
                                        </div>
                                        <div>
                                            <p className="font-bold text-sm">{m.user?.name}</p>
                                            <p className="text-xs opacity-50 capitalize">{m.role}</p>
                                        </div>
                                    </div>
                                    {isAdmin && m.userId !== user?._id && (
                                        <button
                                            type="button"
                                            onClick={() => handleKickMember(m.userId, m.user?.name)}
                                            className={`text-red-500 hover:bg-red-500/10 p-2 transition-colors ${style === THEMES.NEOBRUTALISM ? 'rounded-none' : 'rounded'}`}
                                            title="Remove member"
                                        >
                                            <UserMinus size={16} />
                                        </button>
                                    )}
                                </div>
                            ))}
                        </div>
                    )}

                    {settingsTab === 'danger' && (
                        <div className="space-y-4">
                            <div className={`p-4 border border-red-500/30 bg-red-500/5 ${style === THEMES.NEOBRUTALISM ? 'rounded-none' : 'rounded-lg'}`}>
                                <h4 className="font-bold text-red-500 mb-2">Leave Group</h4>
                                <p className="text-xs opacity-60 mb-4">You can only leave if you have no outstanding balances.</p>
                                <Button variant="danger" onClick={handleLeaveGroup} className="w-full">
                                    <LogOut size={16} /> Leave Group
                                </Button>
                            </div>

                            {isAdmin && (
                                <div className={`p-4 border border-red-500/30 bg-red-500/5 ${style === THEMES.NEOBRUTALISM ? 'rounded-none' : 'rounded-lg'}`}>
                                    <h4 className="font-bold text-red-500 mb-2">Delete Group</h4>
                                    <p className="text-xs opacity-60 mb-4">Permanently delete this group and all expenses. This cannot be undone.</p>
                                    <Button variant="danger" onClick={handleDeleteGroup} className="w-full">
                                        <Trash2 size={16} /> Delete Group
                                    </Button>
                                </div>
                            )}
                        </div>
                    )}
                </div>
            </Modal>
        </div >
    );
};

const ScaleIcon = () => (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" role="img" aria-labelledby="scale-icon-title">
        <title id="scale-icon-title">Balance scale icon</title>
        <path d="m16 16 3-8 3 8c-.87.65-1.92 1-3 1s-2.13-.35-3-1Z" />
        <path d="m2 16 3-8 3 8c-.87.65-1.92 1-3 1s-2.13-.35-3-1Z" />
        <path d="M7 21h10" />
        <path d="M12 3v18" />
        <path d="M3 7h2c2 0 5-1 7-2 2 1 5 2 7 2h2" />
    </svg>
);
