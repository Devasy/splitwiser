import { useEffect, useRef, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useToast } from '../contexts/ToastContext';
import { getImportStatus, handleSplitwiseCallback } from '../services/api';

export const SplitwiseCallback = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { addToast } = useToast();
  const [status, setStatus] = useState('Processing authorization...');
  const [progress, setProgress] = useState(0);
  const [importing, setImporting] = useState(true);
  const hasStartedRef = useRef(false);

  useEffect(() => {
    // Check if we're in progress tracking mode (skipOAuth from group selection)
    const state = location.state as { jobId?: string; skipOAuth?: boolean };
    if (state?.skipOAuth && state?.jobId) {
      // Start polling for existing job
      startProgressPolling(state.jobId);
      return;
    }

    // Prevent duplicate execution in React Strict Mode using ref
    if (hasStartedRef.current) {
      console.log('Callback already started, skipping duplicate execution');
      return;
    }
    hasStartedRef.current = true;

    const handleCallback = async () => {
      // Parse query parameters from the full URL (before the hash)
      const urlParams = new URLSearchParams(window.location.search);
      const code = urlParams.get('code');
      const state = urlParams.get('state');

      console.log('OAuth callback - code:', code?.substring(0, 10), 'state:', state);

      if (!code) {
        console.error('No code received');
        addToast('Authorization failed - no code received', 'error');
        navigate('/import/splitwise');
        return;
      }

      try {
        setStatus('Fetching your Splitwise data...');
        
        // First, exchange OAuth code for access token and get preview
        console.log('Exchanging OAuth code for token...');
        const tokenResponse = await handleSplitwiseCallback(code, state || '');
        console.log('Token exchange response:', tokenResponse.data);
        
        // Check if we got groups in the response (from preview)
        if (tokenResponse.data.groups && tokenResponse.data.groups.length > 0) {
          // Navigate to group selection
          console.log('Navigating to group selection with', tokenResponse.data.groups.length, 'groups');
          navigate('/import/splitwise/select-groups', {
            state: {
              accessToken: tokenResponse.data.accessToken,
              groups: tokenResponse.data.groups
            }
          });
          return;
        }
        
        // If no groups or preview data, start import directly (backward compatibility)
        const jobId = tokenResponse.data.import_job_id || tokenResponse.data.importJobId;

        if (!jobId) {
          console.error('No job ID in response:', tokenResponse.data);
          throw new Error('No import job ID received');
        }

        console.log('Import job ID:', jobId);
        addToast('Authorization successful! Starting import...', 'success');
        
        startProgressPolling(jobId);
        
      } catch (error: any) {
        console.error('Callback error:', error);
        if (showToast) {
          showToast(
            error.response?.data?.detail || 'Failed to process authorization',
            'error'
          );
        }
        setImporting(false);
        setTimeout(() => navigate('/import/splitwise'), 2000);
      }
    };

    handleCallback();
  }, [navigate, addToast, location.state]);

  const startProgressPolling = (jobId: string) => {
    setStatus('Import started...');
    
    // Poll for progress
    const pollInterval = setInterval(async () => {
      try {
        const statusResponse = await getImportStatus(jobId);
        const statusData = statusResponse.data;
        
        console.log('Status response:', statusData);
        
        // Log errors if any
        if (statusData.errors && statusData.errors.length > 0) {
          console.warn('Import errors:', statusData.errors);
        }

        // Backend returns nested progress object with camelCase
        const progressPercentage = statusData.progress?.percentage || 0;
        const currentStage = statusData.progress?.currentStage || 'Processing...';
        
        console.log('Progress:', progressPercentage, '% -', currentStage, '- Status:', statusData.status);
        
        setProgress(progressPercentage);
        setStatus(currentStage);

        if (statusData.status === 'completed') {
          clearInterval(pollInterval);
          setImporting(false);
          addToast('Import completed successfully!', 'success');
          setStatus('Completed! Redirecting to dashboard...');
          setTimeout(() => navigate('/dashboard'), 2000);
        } else if (statusData.status === 'failed') {
          clearInterval(pollInterval);
          setImporting(false);
          addToast('Import failed', 'error');
          setStatus(`Failed: ${statusData.errors?.[0]?.message || 'Unknown error'}`);
        }
      } catch (error) {
        console.error('Error polling import status:', error);
      }
    }, 2000);
  };

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
