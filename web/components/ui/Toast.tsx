import { AnimatePresence, motion } from 'framer-motion';
import { AlertCircle, CheckCircle, Info, X } from 'lucide-react';
import React from 'react';
import { THEMES } from '../../constants';
import { Toast, useToast } from '../../contexts/ToastContext';
import { useTheme } from '../../contexts/ThemeContext';

export const ToastContainer = () => {
  const { toasts, removeToast } = useToast();

  return (
    <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2 pointer-events-none">
      <AnimatePresence>
        {toasts.map((toast) => (
          <ToastItem key={toast.id} toast={toast} onClose={() => removeToast(toast.id)} />
        ))}
      </AnimatePresence>
    </div>
  );
};

const ToastItem = ({ toast, onClose }: { toast: Toast; onClose: () => void }) => {
  const { style } = useTheme();
  const isNeo = style === THEMES.NEOBRUTALISM;

  const icons = {
    success: <CheckCircle size={20} className={isNeo ? 'text-black' : 'text-emerald-400'} />,
    error: <AlertCircle size={20} className={isNeo ? 'text-black' : 'text-red-400'} />,
    info: <Info size={20} className={isNeo ? 'text-black' : 'text-blue-400'} />,
  };

  const bgColors = {
    success: isNeo ? 'bg-emerald-300' : 'bg-emerald-500/10 border-emerald-500/20',
    error: isNeo ? 'bg-red-300' : 'bg-red-500/10 border-red-500/20',
    info: isNeo ? 'bg-blue-300' : 'bg-blue-500/10 border-blue-500/20',
  };

  return (
    <motion.div
      initial={{ opacity: 0, x: 50, scale: 0.9 }}
      animate={{ opacity: 1, x: 0, scale: 1 }}
      exit={{ opacity: 0, x: 50, scale: 0.9 }}
      layout
      className={`pointer-events-auto min-w-[300px] max-w-sm flex items-center gap-3 p-4 pr-10 relative overflow-hidden ${
        isNeo
          ? `border-2 border-black shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] ${bgColors[toast.type]} text-black rounded-none`
          : `${bgColors[toast.type]} border backdrop-blur-md text-white rounded-xl shadow-lg`
      }`}
    >
      <div className="flex-shrink-0">{icons[toast.type]}</div>
      <p className="text-sm font-bold">{toast.message}</p>
      <button
        onClick={onClose}
        className={`absolute top-2 right-2 p-1 transition-colors ${
          isNeo ? 'hover:bg-black/10 text-black' : 'hover:bg-white/10 text-white/50 hover:text-white'
        }`}
        aria-label="Close notification"
      >
        <X size={14} />
      </button>
    </motion.div>
  );
};
