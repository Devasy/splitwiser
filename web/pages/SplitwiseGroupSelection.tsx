import { motion } from 'framer-motion';
import { Check, ChevronLeft, Receipt, Users } from 'lucide-react';
import { useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { THEMES } from '../constants';
import { useTheme } from '../contexts/ThemeContext';
import { useToast } from '../contexts/ToastContext';
import { handleSplitwiseCallback } from '../services/api';
import { getCurrencySymbol } from '../utils/formatters';

interface PreviewGroup {
  splitwiseId: string;
  name: string;
  currency: string;
  memberCount: number;
  expenseCount: number;
  totalAmount: number;
  imageUrl?: string;
}

export const SplitwiseGroupSelection = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { addToast } = useToast();

  const [groups, setGroups] = useState<PreviewGroup[]>([]);
  const [selectedGroupIds, setSelectedGroupIds] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(true);
  const [importing, setImporting] = useState(false);
  const [accessToken, setAccessToken] = useState('');
  const { style } = useTheme();
  const isNeo = style === THEMES.NEOBRUTALISM;

  useEffect(() => {
    // Get OAuth params from location state (passed from callback)
    const state = location.state as { accessToken?: string; groups?: PreviewGroup[] };

    if (state?.groups) {
      setGroups(state.groups);
      setAccessToken(state.accessToken || '');
      // Select all groups by default
      setSelectedGroupIds(new Set(state.groups.map(g => g.splitwiseId)));
      setLoading(false);
    } else {
      addToast('No group data available', 'error');
      navigate('/import/splitwise');
    }
  }, [location.state, addToast, navigate]);

  const toggleGroup = (groupId: string) => {
    const newSelected = new Set(selectedGroupIds);
    if (newSelected.has(groupId)) {
      newSelected.delete(groupId);
    } else {
      newSelected.add(groupId);
    }
    setSelectedGroupIds(newSelected);
  };

  const handleSelectAll = () => {
    if (selectedGroupIds.size === groups.length) {
      setSelectedGroupIds(new Set());
    } else {
      setSelectedGroupIds(new Set(groups.map(g => g.splitwiseId)));
    }
  };

  const handleStartImport = async () => {
    if (selectedGroupIds.size === 0) {
      addToast('Please select at least one group', 'error');
      return;
    }

    // Check if user is authenticated
    const token = localStorage.getItem('access_token');
    console.log('Auth token present:', !!token);
    if (!token) {
      addToast('Authentication required. Please log in again.', 'error');
      navigate('/login');
      return;
    }

    setImporting(true);
    try {
      // Call the import API with selected groups and access token
      const response = await handleSplitwiseCallback(
        undefined, // no code
        undefined, // no state
        Array.from(selectedGroupIds),
        accessToken // pass stored access token
      );

      const jobId = response.data.import_job_id || response.data.importJobId;

      // Navigate to callback/progress page
      navigate('/import/splitwise/callback', {
        state: { jobId, skipOAuth: true }
      });

    } catch (error: any) {
      console.error('Import start error:', error);
      addToast(
        error.response?.data?.detail || 'Failed to start import',
        'error'
      );
      setImporting(false);
    }
  };

  if (loading) {
    return (
      <div className={`min-h-screen flex items-center justify-center ${isNeo ? 'bg-[#C1E1C1]' : 'bg-gray-50 dark:bg-gray-900'}`}>
        <div className="text-center">
          <div className={`animate-spin rounded-full h-12 w-12 border-b-2 mx-auto mb-4 ${isNeo ? 'border-black' : 'border-blue-50'}`}></div>
          <p className={`font-bold ${isNeo ? 'text-black uppercase' : 'text-gray-600 dark:text-gray-400'}`}>Loading groups...</p>
        </div>
      </div>
    );
  }

  return (
    <div className={`min-h-screen py-8 px-4 transition-colors duration-300 ${isNeo ? 'bg-[#C1E1C1]' : 'bg-gray-50 dark:bg-gray-900'}`}>
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <button
            onClick={() => navigate('/import/splitwise')}
            className={`flex items-center gap-2 mb-6 font-bold transition-transform hover:-translate-x-1 ${isNeo ? 'text-black uppercase tracking-tighter bg-white border-2 border-black px-3 py-1 shadow-[2px_2px_0px_0px_rgba(0,0,0,1)]' : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
              }`}
          >
            <ChevronLeft className={isNeo ? 'w-5 h-5 stroke-[3]' : 'w-5 h-5'} />
            <span>Back</span>
          </button>

          <motion.div
            initial={{ y: -20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            className={`${isNeo
              ? 'bg-white border-4 border-black shadow-[8px_8px_0px_0px_rgba(0,0,0,1)] p-8 rounded-none'
              : 'bg-white dark:bg-gray-800 rounded-lg shadow-lg p-8'}`}
          >
            <h1 className={`text-4xl font-black mb-3 tracking-tighter ${isNeo ? 'text-black uppercase' : 'text-gray-900 dark:text-white'}`}>
              Select Groups to Import
            </h1>
            <p className={`text-lg font-bold ${isNeo ? 'text-black/70' : 'text-gray-600 dark:text-gray-400'}`}>
              Your Splitwise groups are ready. Choose which once to bring to Splitwiser.
            </p>
          </motion.div>
        </div>

        {/* Selection Controls */}
        <div className={`${isNeo
          ? 'bg-white border-4 border-black p-4 mb-6 flex items-center justify-between rounded-none shadow-[4px_4px_0px_0px_rgba(0,0,0,1)]'
          : 'bg-white dark:bg-gray-800 rounded-lg shadow p-4 mb-4 flex items-center justify-between'}`}>
          <div className={`font-black ${isNeo ? 'text-black uppercase text-sm' : 'text-sm text-gray-600 dark:text-gray-400'}`}>
            <span className={isNeo ? 'text-blue-600' : 'font-medium text-gray-900 dark:text-white'}>
              {selectedGroupIds.size}
            </span> of {groups.length} groups selected
          </div>
          <button
            onClick={handleSelectAll}
            className={`font-black uppercase text-sm transition-all hover:scale-105 active:scale-95 ${isNeo ? 'text-black bg-pink-200 border-2 border-black px-4 py-1 shadow-[2px_2px_0px_0px_rgba(0,0,0,1)]' : 'text-blue-500 hover:text-blue-600'
              }`}
          >
            {selectedGroupIds.size === groups.length ? 'Deselect All' : 'Select All'}
          </button>
        </div>

        {/* Groups List */}
        <div className="space-y-4 mb-10">
          {groups.map((group) => {
            const isSelected = selectedGroupIds.has(group.splitwiseId);

            return (
              <motion.div
                key={group.splitwiseId}
                initial={{ x: -20, opacity: 0 }}
                animate={{ x: 0, opacity: 1 }}
                onClick={() => toggleGroup(group.splitwiseId)}
                className={`transition-all cursor-pointer ${isNeo
                    ? `bg-white border-4 border-black p-5 rounded-none shadow-[6px_6px_0px_0px_rgba(0,0,0,1)] hover:shadow-none hover:translate-x-1 hover:translate-y-1 ${isSelected ? 'bg-blue-50' : ''}`
                    : `bg-white dark:bg-gray-800 rounded-xl shadow hover:shadow-md border-2 ${isSelected ? 'border-blue-500' : 'border-transparent'}`
                  }`}
              >
                <div className="flex items-center gap-6">
                  {/* Checkbox */}
                  <div className={`flex-shrink-0 w-8 h-8 flex items-center justify-center border-4 border-black transition-all ${isSelected ? 'bg-black' : 'bg-white'
                    } ${isNeo ? 'rounded-none' : 'rounded-md border-2'}`}>
                    {isSelected && <Check className="w-6 h-6 text-white stroke-[4]" />}
                  </div>

                  {/* Group Image */}
                  <div className="flex-shrink-0">
                    <div className={`w-16 h-16 flex items-center justify-center font-black text-2xl border-4 border-black ${isNeo ? 'rounded-none shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] bg-purple-300' : 'rounded-xl bg-gradient-to-br from-blue-500 to-purple-500 text-white'
                      }`}>
                      {group.imageUrl ? (
                        <img
                          src={group.imageUrl}
                          alt={group.name}
                          className="w-full h-full object-cover"
                        />
                      ) : (
                        group.name.charAt(0).toUpperCase()
                      )}
                    </div>
                  </div>

                  {/* Group Details */}
                  <div className="flex-1 min-w-0">
                    <h3 className={`text-2xl font-black mb-2 truncate ${isNeo ? 'text-black uppercase tracking-tighter' : 'text-gray-900 dark:text-white'}`}>
                      {group.name}
                    </h3>

                    <div className="flex flex-wrap gap-x-6 gap-y-2">
                      <div className={`flex items-center gap-2 font-bold ${isNeo ? 'text-black/70' : 'text-gray-600 dark:text-gray-400'}`}>
                        <Users className="w-5 h-5 stroke-[2.5]" />
                        <span>{group.memberCount} members</span>
                      </div>

                      <div className={`flex items-center gap-2 font-bold ${isNeo ? 'text-black/70' : 'text-gray-600 dark:text-gray-400'}`}>
                        <Receipt className="w-5 h-5 stroke-[2.5]" />
                        <span>{group.expenseCount} expenses</span>
                      </div>

                      <div className={`flex items-center gap-2 font-black ${isNeo ? 'text-blue-600' : 'text-gray-900'}`}>
                        <span className="text-xl">{getCurrencySymbol(group.currency)}</span>
                        <span className="text-lg">
                          {new Intl.NumberFormat('en-IN', {
                            minimumFractionDigits: 0,
                            maximumFractionDigits: 0,
                          }).format(group.totalAmount)}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              </motion.div>
            );
          })}
        </div>

        {/* Import Button */}
        <motion.div
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          className={`${isNeo
            ? 'bg-white border-4 border-black p-8 rounded-none shadow-[10px_10px_0px_0px_rgba(0,0,0,1)]'
            : 'bg-white dark:bg-gray-800 rounded-xl shadow-lg p-8'}`}
        >
          <button
            onClick={handleStartImport}
            disabled={importing || selectedGroupIds.size === 0}
            className={`w-full py-5 px-8 flex items-center justify-center gap-4 transition-all active:translate-y-1 ${isNeo
                ? 'bg-[#FF6B6B] border-4 border-black text-black font-black text-2xl shadow-[6px_6px_0px_0px_rgba(0,0,0,1)] hover:shadow-none hover:translate-x-1 hover:translate-y-1 rounded-none'
                : 'bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg shadow-lg hover:shadow-xl'
              } disabled:opacity-50 disabled:cursor-not-allowed`}
          >
            {importing ? (
              <>
                <div className={`animate-spin rounded-full h-8 w-8 border-4 ${isNeo ? 'border-black border-t-transparent' : 'border-white border-t-transparent'}`}></div>
                <span className="uppercase">Importing...</span>
              </>
            ) : (
              <span className={isNeo ? 'uppercase text-white' : ''}>
                Import {selectedGroupIds.size} Selected Group{selectedGroupIds.size !== 1 ? 's' : ''}
              </span>
            )}
          </button>

          {selectedGroupIds.size === 0 && (
            <p className={`text-center font-bold mt-4 ${isNeo ? 'text-black uppercase animate-pulse' : 'text-gray-500'}`}>
              ⚠️ Select at least one group to proceed ⚠️
            </p>
          )}
        </motion.div>
      </div>
    </div>
  );
};
