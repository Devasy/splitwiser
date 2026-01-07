import React from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { Check, Info, X, AlertCircle } from 'lucide-react';
import { useTheme } from '../../contexts/ThemeContext';
import { THEMES } from '../../constants';
import { Toast } from '../../types';

interface ToastContainerProps {
  toasts: Toast[];
  removeToast: (id: string) => void;
}

export const ToastContainer: React.FC<ToastContainerProps> = ({ toasts, removeToast }) => {
  return (
    <div className="fixed bottom-4 right-4 z-[100] flex flex-col gap-2 pointer-events-none">
      <AnimatePresence>
        {toasts.map((toast) => (
          <ToastItem key={toast.id} toast={toast} removeToast={removeToast} />
        ))}
      </AnimatePresence>
    </div>
  );
};

interface ToastItemProps {
  toast: Toast;
  removeToast: (id: string) => void;
}

const ToastItem: React.FC<ToastItemProps> = ({ toast, removeToast }) => {
  const { style, mode } = useTheme();

  // Auto-remove handled by context, but we can also add a safety timeout here if needed.
  // Context handles the state removal.

  const getIcon = () => {
    switch (toast.type) {
      case 'success':
        return <Check size={18} />;
      case 'error':
        return <AlertCircle size={18} />;
      default:
        return <Info size={18} />;
    }
  };

  const getStyles = () => {
    if (style === THEMES.NEOBRUTALISM) {
      const base = "border-2 border-black shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] rounded-none";
      switch (toast.type) {
        case 'success':
          return `bg-emerald-300 text-black ${base}`;
        case 'error':
          return `bg-red-300 text-black ${base}`;
        default:
          return `bg-blue-300 text-black ${base}`;
      }
    } else {
      // Glassmorphism
      const base = "backdrop-blur-md border shadow-lg rounded-xl";
      if (mode === 'dark') {
        switch (toast.type) {
          case 'success':
            return `bg-emerald-900/40 border-emerald-500/30 text-emerald-100 ${base}`;
          case 'error':
            return `bg-red-900/40 border-red-500/30 text-red-100 ${base}`;
          default:
            return `bg-blue-900/40 border-blue-500/30 text-blue-100 ${base}`;
        }
      } else {
        switch (toast.type) {
          case 'success':
            return `bg-emerald-100/80 border-emerald-200 text-emerald-800 ${base}`;
          case 'error':
            return `bg-red-100/80 border-red-200 text-red-800 ${base}`;
          default:
            return `bg-blue-100/80 border-blue-200 text-blue-800 ${base}`;
        }
      }
    }
  };

  return (
    <motion.div
      layout
      initial={{ opacity: 0, x: 20, scale: 0.9 }}
      animate={{ opacity: 1, x: 0, scale: 1 }}
      exit={{ opacity: 0, x: 20, scale: 0.9 }}
      className={`pointer-events-auto flex items-center gap-3 px-4 py-3 min-w-[300px] max-w-sm ${getStyles()}`}
    >
      <div className="shrink-0">{getIcon()}</div>
      <p className="text-sm font-bold flex-1">{toast.message}</p>
      <button
        onClick={() => removeToast(toast.id)}
        className="opacity-60 hover:opacity-100 transition-opacity"
        aria-label="Close"
      >
        <X size={16} />
      </button>
    </motion.div>
  );
};
