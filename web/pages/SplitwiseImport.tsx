import { motion } from 'framer-motion';
import { Download } from 'lucide-react';
import { useState } from 'react';
import { THEMES } from '../constants';
import { useTheme } from '../contexts/ThemeContext';
import { useToast } from '../contexts/ToastContext';
import { getSplitwiseAuthUrl } from '../services/api';

export const SplitwiseImport = () => {
  const [loading, setLoading] = useState(false);
  const { addToast } = useToast();
  const { style } = useTheme();
  const isNeo = style === THEMES.NEOBRUTALISM;

  const handleOAuthImport = async () => {
    setLoading(true);
    try {
      const response = await getSplitwiseAuthUrl();
      const { authorization_url } = response.data;

      // Redirect to Splitwise OAuth page
      window.location.href = authorization_url;
    } catch (error: any) {
      console.error('OAuth error:', error);
      addToast(error.response?.data?.detail || 'Failed to initiate authorization', 'error');
      setLoading(false);
    }
  };

  return (
    <div className={`min-h-screen py-8 px-4 transition-colors duration-300 ${isNeo ? 'bg-[#FFDEB4]' : 'bg-gray-50 dark:bg-gray-900'}`}>
      <div className="max-w-2xl mx-auto">
        <motion.div
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          className={`${isNeo
            ? 'bg-white border-4 border-black shadow-[8px_8px_0px_0px_rgba(0,0,0,1)] p-8 rounded-none'
            : 'bg-white dark:bg-gray-800 rounded-xl shadow-lg p-8'}`}
        >
          {/* Header */}
          <div className="text-center mb-8">
            <div className={`inline-flex items-center justify-center w-20 h-20 mb-6 transition-all ${isNeo
              ? 'bg-blue-300 border-4 border-black shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] rounded-none'
              : 'bg-blue-100 dark:bg-blue-900/30 rounded-full'
              }`}>
              <Download className={`w-10 h-10 ${isNeo ? 'text-black' : 'text-blue-600 dark:text-blue-400'}`} />
            </div>
            <h1 className={`text-4xl font-black mb-3 tracking-tighter ${isNeo ? 'text-black uppercase' : 'text-gray-900 dark:text-white'}`}>
              Import from Splitwise
            </h1>
            <p className={`text-lg font-bold ${isNeo ? 'text-black/70' : 'text-gray-600 dark:text-gray-400'}`}>
              Seamlessly migrate all your data in just a few clicks
            </p>
          </div>

          {/* Main Button */}
          <button
            onClick={handleOAuthImport}
            disabled={loading}
            className={`w-full py-5 px-8 flex items-center justify-center gap-4 transition-all active:translate-y-1 ${isNeo
              ? 'bg-[#4ECDC4] border-4 border-black text-black font-black text-xl shadow-[6px_6px_0px_0px_rgba(0,0,0,1)] hover:shadow-none hover:translate-x-1 hover:translate-y-1 rounded-none'
              : 'bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg shadow-lg hover:shadow-xl'
              } disabled:opacity-50 disabled:cursor-not-allowed mb-8`}
          >
            {loading ? (
              <>
                <div className={`animate-spin rounded-full h-6 w-6 border-4 ${isNeo ? 'border-black border-t-transparent' : 'border-white border-t-transparent'}`}></div>
                <span className="uppercase">Connecting...</span>
              </>
            ) : (
              <>
                <Download className={isNeo ? 'w-6 h-6 stroke-[3]' : 'w-5 h-5'} />
                <span className={isNeo ? 'uppercase' : ''}>Connect with Splitwise</span>
              </>
            )}
          </button>

          <p className={`text-center font-bold mb-8 ${isNeo ? 'text-black' : 'text-sm text-gray-600 dark:text-gray-400'}`}>
            {isNeo ? '→ AUTHORIZATION REQUIRED ←' : "You'll be redirected to Splitwise"}
          </p>

          <div className="grid grid-cols-1 gap-6">
            {/* What will be imported */}
            <div className={`${isNeo
              ? 'bg-blue-100 border-4 border-black p-6 rounded-none shadow-[4px_4px_0px_0px_rgba(0,0,0,1)]'
              : 'bg-blue-50 dark:bg-blue-900/10 border border-blue-200 dark:border-blue-800/50 rounded-lg p-6'}`}>
              <h3 className={`font-black text-lg mb-4 flex items-center gap-3 ${isNeo ? 'text-black uppercase' : 'text-gray-900 dark:text-white'}`}>
                <div className={`w-6 h-6 flex items-center justify-center border-2 border-black ${isNeo ? 'bg-black rounded-none shadow-[2px_2px_0px_0px_white]' : 'bg-blue-600 rounded-full'}`}>
                  <svg className="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                </div>
                What's being moved?
              </h3>
              <ul className={`space-y-3 font-bold ${isNeo ? 'text-black' : 'text-gray-700 dark:text-gray-300'}`}>
                {['All your friends', 'All your groups', 'All expenses & splits', 'All settlements'].map((item, idx) => (
                  <li key={idx} className="flex items-center gap-3">
                    <span className={`w-2 h-2 border border-black ${isNeo ? 'bg-black rounded-none' : 'bg-blue-600 rounded-full'}`}></span>
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* Important Notes */}
            <div className={`${isNeo
              ? 'bg-amber-100 border-4 border-black p-6 rounded-none shadow-[4px_4px_0px_0px_rgba(0,0,0,1)]'
              : 'bg-amber-50 dark:bg-amber-900/10 border border-amber-200 dark:border-amber-800/50 rounded-lg p-6'}`}>
              <h3 className={`font-black text-lg mb-4 flex items-center gap-3 ${isNeo ? 'text-black uppercase' : 'text-gray-900 dark:text-white'}`}>
                <svg className={`w-6 h-6 ${isNeo ? 'text-black stroke-[3]' : 'text-amber-600 dark:text-amber-500'}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
                Notice
              </h3>
              <ul className={`space-y-3 font-bold ${isNeo ? 'text-black' : 'text-gray-700 dark:text-gray-300'}`}>
                {[
                  'Process may take a few minutes',
                  'Select specific groups next',
                  "Existing data won't be affected"
                ].map((item, idx) => (
                  <li key={idx} className="flex items-center gap-3">
                    <span className={`w-2 h-2 border border-black ${isNeo ? 'bg-black rounded-none' : 'bg-amber-600 rounded-full'}`}></span>
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  );
};
