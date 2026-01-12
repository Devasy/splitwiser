import { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useToast } from '../contexts/ToastContext';
import { getImportStatus, handleSplitwiseCallback } from '../services/api';

export const SplitwiseCallback = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { showToast } = useToast();
  const [status, setStatus] = useState('Processing authorization...');
  const [progress, setProgress] = useState(0);
  const [importing, setImporting] = useState(true);

  useEffect(() => {
    const handleCallback = async () => {
      const code = searchParams.get('code');
      const state = searchParams.get('state');

      if (!code) {
        showToast('Authorization failed - no code received', 'error');
        navigate('/import/splitwise');
        return;
      }

      try {
        // Send code to backend to exchange for access token and start import
        const response = await handleSplitwiseCallback(code, state || '');
        const jobId = response.data.import_job_id || response.data.importJobId;

        if (!jobId) {
          throw new Error('No import job ID received');
        }

        showToast('Authorization successful! Starting import...', 'success');
        setStatus('Import started...');

        // Poll for progress
        const pollInterval = setInterval(async () => {
          try {
            const statusResponse = await getImportStatus(jobId);
            const statusData = statusResponse.data;

            setProgress(statusData.progress_percentage || 0);
            setStatus(statusData.current_stage || 'Processing...');

            if (statusData.status === 'completed') {
              clearInterval(pollInterval);
              setImporting(false);
              showToast('Import completed successfully!', 'success');
              setStatus('Completed! Redirecting to dashboard...');
              setTimeout(() => navigate('/dashboard'), 2000);
            } else if (statusData.status === 'failed') {
              clearInterval(pollInterval);
              setImporting(false);
              showToast('Import failed', 'error');
              setStatus(`Failed: ${statusData.error_details || 'Unknown error'}`);
            }
          } catch (error) {
            console.error('Error polling import status:', error);
          }
        }, 2000);

        return () => clearInterval(pollInterval);
      } catch (error: any) {
        console.error('Callback error:', error);
        showToast(
          error.response?.data?.detail || 'Failed to process authorization',
          'error'
        );
        setImporting(false);
        setTimeout(() => navigate('/import/splitwise'), 2000);
      }
    };

    handleCallback();
  }, [searchParams, navigate, showToast]);

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center px-4">
      <div className="max-w-md w-full bg-white dark:bg-gray-800 rounded-lg shadow-lg p-8">
        <div className="text-center mb-6">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mb-4"></div>
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
            {importing ? 'Importing Data' : 'Processing'}
          </h2>
          <p className="text-gray-600 dark:text-gray-400">{status}</p>
        </div>

        {importing && (
          <div className="space-y-3">
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-600 dark:text-gray-400">Progress</span>
              <span className="font-medium text-gray-900 dark:text-white">
                {progress.toFixed(0)}%
              </span>
            </div>
            <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3">
              <div
                className="bg-blue-500 h-3 rounded-full transition-all duration-300 ease-out"
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>
        )}

        <div className="mt-6 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
          <p className="text-sm text-blue-800 dark:text-blue-200">
            Please don't close this page until the import is complete.
          </p>
        </div>
      </div>
    </div>
  );
};
