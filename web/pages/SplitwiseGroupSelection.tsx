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
  const { style, mode } = useTheme();
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
      <div className={`min-h-screen flex items-center justify-center ${isNeo ? 'bg-gray-100' : 'bg-gray-50 dark:bg-gray-900'}`}>
        <div className="text-center">
          <div className={`animate-spin rounded-full h-10 w-10 border-2 mx-auto mb-4 ${isNeo ? 'border-black border-t-transparent' : 'border-blue-500 border-t-transparent'}`}></div>
          <p className={`${isNeo ? 'text-black' : 'text-gray-600 dark:text-gray-400'}`}>Loading groups...</p>
        </div>
      </div>
    );
  }

  return (
    <div className={`min-h-screen py-6 px-4 transition-colors duration-300 ${isNeo ? 'bg-gray-100' : 'bg-gray-50 dark:bg-gray-900'}`}>
      <div className="max-w-3xl mx-auto">
        {/* Back Button */}
        <button
          onClick={() => navigate('/import/splitwise')}
          className={`flex items-center gap-1 mb-4 text-sm font-medium transition-colors ${isNeo
            ? 'text-black hover:text-gray-700'
            : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
            }`}
        >
          <ChevronLeft className="w-4 h-4" />
          <span>Back</span>
        </button>

        {/* Header */}
        <motion.div
          initial={{ y: -20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          className={`mb-6 ${isNeo
            ? 'bg-white border-2 border-black shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] p-6 rounded-none'
            : 'bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6'}`}
        >
          <h1 className={`text-2xl md:text-3xl font-bold mb-2 ${isNeo ? 'text-black' : 'text-gray-900 dark:text-white'}`}>
            Select Groups to Import
          </h1>
          <p className={`text-base ${isNeo ? 'text-black/70' : 'text-gray-600 dark:text-gray-400'}`}>
            Your Splitwise groups are ready. Choose which ones to bring to Splitwiser.
          </p>
        </motion.div>

        {/* Selection Controls */}
        <div className={`${isNeo
          ? 'bg-white border-2 border-black p-4 mb-4 flex items-center justify-between rounded-none shadow-[2px_2px_0px_0px_rgba(0,0,0,1)]'
          : 'bg-white dark:bg-gray-800 rounded-lg shadow p-4 mb-4 flex items-center justify-between'}`}>
          <div className={`text-sm ${isNeo ? 'text-black' : 'text-gray-600 dark:text-gray-400'}`}>
            <span className={`font-bold ${isNeo ? 'text-blue-600' : 'text-gray-900 dark:text-white'}`}>
              {selectedGroupIds.size}
            </span> of {groups.length} groups selected
          </div>
          <button
            onClick={handleSelectAll}
            className={`text-sm font-medium transition-colors ${isNeo
              ? 'text-black hover:text-gray-700'
              : 'text-blue-500 hover:text-blue-600'
              }`}
          >
            {selectedGroupIds.size === groups.length ? 'Deselect All' : 'Select All'}
          </button>
        </div>

        {/* Groups List */}
        <div className="space-y-3 mb-6">
          {groups.map((group) => {
            const isSelected = selectedGroupIds.has(group.splitwiseId);

            return (
              <motion.div
                key={group.splitwiseId}
                initial={{ x: -20, opacity: 0 }}
                animate={{ x: 0, opacity: 1 }}
                onClick={() => toggleGroup(group.splitwiseId)}
                className={`transition-all cursor-pointer p-4 ${isNeo
                  ? `bg-white border-2 border-black rounded-none shadow-[2px_2px_0px_0px_rgba(0,0,0,1)] hover:shadow-none hover:translate-x-[2px] hover:translate-y-[2px] ${isSelected ? 'bg-blue-50' : ''}`
                  : `bg-white dark:bg-gray-800 rounded-xl shadow hover:shadow-md border-2 ${isSelected ? 'border-blue-500' : 'border-transparent'}`
                  }`}
              >
                <div className="flex items-center gap-4">
                  {/* Checkbox */}
                  <div className={`flex-shrink-0 w-6 h-6 flex items-center justify-center transition-all ${isSelected
                    ? (isNeo ? 'bg-black' : 'bg-blue-500')
                    : 'bg-white'
                    } ${isNeo ? 'border-2 border-black rounded-none' : 'border-2 border-gray-300 rounded-md'}`}>
                    {isSelected && <Check className="w-4 h-4 text-white stroke-[3]" />}
                  </div>

                  {/* Group Image */}
                  <div className="flex-shrink-0">
                    <div className={`w-12 h-12 flex items-center justify-center font-bold text-lg ${isNeo
                      ? 'border-2 border-black rounded-none bg-purple-200 text-black'
                      : 'rounded-xl bg-gradient-to-br from-blue-500 to-purple-500 text-white'
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
                    <h3 className={`text-lg font-bold mb-1 truncate ${isNeo ? 'text-black' : 'text-gray-900 dark:text-white'}`}>
                      {group.name}
                    </h3>

                    <div className="flex flex-wrap gap-x-4 gap-y-1 text-sm">
                      <div className={`flex items-center gap-1 ${isNeo ? 'text-black/60' : 'text-gray-500 dark:text-gray-400'}`}>
                        <Users className="w-4 h-4" />
                        <span>{group.memberCount} members</span>
                      </div>

                      <div className={`flex items-center gap-1 ${isNeo ? 'text-black/60' : 'text-gray-500 dark:text-gray-400'}`}>
                        <Receipt className="w-4 h-4" />
                        <span>{group.expenseCount} expenses</span>
                      </div>

                      <div className={`flex items-center gap-1 font-bold ${isNeo ? 'text-blue-600' : 'text-gray-900 dark:text-white'}`}>
                        <span>{getCurrencySymbol(group.currency)}</span>
                        <span>
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
            ? 'bg-white border-2 border-black p-6 rounded-none shadow-[4px_4px_0px_0px_rgba(0,0,0,1)]'
            : 'bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6'}`}
        >
          <button
            onClick={handleStartImport}
            disabled={importing || selectedGroupIds.size === 0}
            className={`w-full py-4 px-6 flex items-center justify-center gap-3 transition-all ${isNeo
              ? 'bg-blue-500 border-2 border-black text-white font-bold shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] hover:shadow-[2px_2px_0px_0px_rgba(0,0,0,1)] hover:translate-x-[2px] hover:translate-y-[2px] rounded-none'
              : 'bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg shadow-lg hover:shadow-xl'
              } disabled:opacity-50 disabled:cursor-not-allowed`}
          >
            {importing ? (
              <>
                <div className={`animate-spin rounded-full h-5 w-5 border-2 ${isNeo ? 'border-white border-t-transparent' : 'border-white border-t-transparent'}`}></div>
                <span>Importing...</span>
              </>
            ) : (
              <span>
                Import {selectedGroupIds.size} Selected Group{selectedGroupIds.size !== 1 ? 's' : ''}
              </span>
            )}
          </button>

          {selectedGroupIds.size === 0 && (
            <p className={`text-center text-sm mt-3 ${isNeo ? 'text-black/60' : 'text-gray-500'}`}>
              Select at least one group to proceed
            </p>
          )}
        </motion.div>
      </div>
    </div>
  );
};
