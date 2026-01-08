import React, { useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Toast as ToastType } from '../../types';
import { useTheme } from '../../contexts/ThemeContext';
import { X, CheckCircle, AlertCircle, Info } from 'lucide-react';

interface ToastContainerProps {
  toasts: ToastType[];
  removeToast: (id: string) => void;
}

export const ToastContainer: React.FC<ToastContainerProps> = ({ toasts, removeToast }) => {
  return (
    <div className="fixed top-4 right-4 z-50 flex flex-col gap-2 pointer-events-none">
      <AnimatePresence>
        {toasts.map((toast) => (
          <ToastItem key={toast.id} toast={toast} removeToast={removeToast} />
        ))}
      </AnimatePresence>
    </div>
  );
};

interface ToastItemProps {
  toast: ToastType;
  removeToast: (id: string) => void;
}

const ToastItem: React.FC<ToastItemProps> = ({ toast, removeToast }) => {
  const { theme } = useTheme();

  const getIcon = () => {
    switch (toast.type) {
      case 'success':
        return <CheckCircle size={20} className="text-green-500" />;
      case 'error':
        return <AlertCircle size={20} className="text-red-500" />;
      default:
        return <Info size={20} className="text-blue-500" />;
    }
  };

  const getBgColor = () => {
    if (theme === 'neobrutalism') {
      return 'bg-white border-2 border-black shadow-[4px_4px_0px_0px_rgba(0,0,0,1)]';
    }
    // Glassmorphism
    return 'bg-white/80 backdrop-blur-md border border-white/20 shadow-lg';
  };

  return (
    <motion.div
      initial={{ opacity: 0, x: 50, scale: 0.9 }}
      animate={{ opacity: 1, x: 0, scale: 1 }}
      exit={{ opacity: 0, x: 20, scale: 0.9 }}
      transition={{ duration: 0.2 }}
      layout
      className={`
        pointer-events-auto w-80 max-w-[calc(100vw-2rem)] p-4 rounded-lg flex items-start gap-3
        ${getBgColor()}
        dark:bg-slate-800 dark:border-slate-700
      `}
      role="alert"
    >
      <div className="flex-shrink-0 mt-0.5">{getIcon()}</div>
      <div className="flex-1 text-sm font-medium text-slate-900 dark:text-white">
        {toast.message}
      </div>
      <button
        onClick={() => removeToast(toast.id)}
        className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 transition-colors"
        aria-label="Close"
      >
        <X size={16} />
      </button>
    </motion.div>
  );
};
