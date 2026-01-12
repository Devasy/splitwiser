import { useState } from 'react';
import { useToast } from '../contexts/ToastContext';
import { getSplitwiseAuthUrl } from '../services/api';

export const SplitwiseImport = () => {
  const [loading, setLoading] = useState(false);
  const { showToast } = useToast();

  const handleOAuthImport = async () => {
    setLoading(true);
    try {
      const response = await getSplitwiseAuthUrl();
      const { authorization_url } = response.data;
      
      // Redirect to Splitwise OAuth page
      window.location.href = authorization_url;
    } catch (error: any) {
      console.error('OAuth error:', error);
      showToast(
        error.response?.data?.detail || 'Failed to initiate authorization',
        'error'
      );
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 py-12 px-4">
      <div className="max-w-2xl mx-auto">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-8">
          <div className="text-center mb-8">
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
              Import from Splitwise
            </h1>
            <p className="text-gray-600 dark:text-gray-400">
              Import all your friends, groups, and expenses from Splitwise with one click
            </p>
          </div>

          <div className="space-y-6">
            <button
              onClick={handleOAuthImport}
              disabled={loading}
              className="w-full py-4 px-6 bg-blue-500 hover:bg-blue-600 text-white font-semibold 
                       rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed
                       disabled:hover:bg-blue-500 shadow-lg hover:shadow-xl flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                  <span>Connecting to Splitwise...</span>
                </>
              ) : (
                <>
                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                  <span>Connect with Splitwise & Import</span>
                </>
              )}
            </button>

            <div className="text-center">
              <p className="text-sm text-gray-600 dark:text-gray-400">
                You'll be redirected to Splitwise to authorize access
              </p>
            </div>

            <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 
                          rounded-lg p-4">
              <h3 className="font-medium text-blue-900 dark:text-blue-100 mb-2">
                What will be imported?
              </h3>
              <ul className="text-sm text-blue-800 dark:text-blue-200 space-y-1">
                <li>• All your friends and their details</li>
                <li>• All your groups with members</li>
                <li>• All expenses with split details</li>
                <li>• All balances and settlements</li>
              </ul>
            </div>

            <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 
                          dark:border-yellow-800 rounded-lg p-4">
              <h3 className="font-medium text-yellow-900 dark:text-yellow-100 mb-2">
                Important Notes
              </h3>
              <ul className="text-sm text-yellow-800 dark:text-yellow-200 space-y-1">
                <li>• This process may take a few minutes depending on your data size</li>
                <li>• Please don't close this page until import is complete</li>
                <li>• Existing data in Splitwiser won't be affected</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
