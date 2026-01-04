import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, CheckCircle, AlertCircle, Info } from 'lucide-react';
import { useToast, Toast } from '../../contexts/ToastContext';
import { useTheme } from '../../contexts/ThemeContext';
import { THEMES } from '../../constants';

const ToastItem: React.FC<{ toast: Toast }> = ({ toast }) => {
  const { removeToast } = useToast();
  const { style } = useTheme();

  const isNeo = style === THEMES.NEOBRUTALISM;

  const icons = {
    success: <CheckCircle className="w-5 h-5" />,
    error: <AlertCircle className="w-5 h-5" />,
    info: <Info className="w-5 h-5" />,
  };

  const colors = {
    success: isNeo
      ? 'bg-[#00cc88] text-black border-2 border-black shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] rounded-none'
      : 'bg-green-500/90 text-white backdrop-blur-md shadow-lg rounded-lg border border-white/20',
    error: isNeo
      ? 'bg-[#ff5555] text-black border-2 border-black shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] rounded-none'
      : 'bg-red-500/90 text-white backdrop-blur-md shadow-lg rounded-lg border border-white/20',
    info: isNeo
      ? 'bg-[#8855ff] text-white border-2 border-black shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] rounded-none'
      : 'bg-blue-500/90 text-white backdrop-blur-md shadow-lg rounded-lg border border-white/20',
  };

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 50, scale: 0.3 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, scale: 0.5, transition: { duration: 0.2 } }}
      className={`
        flex items-center gap-3 px-4 py-3 mb-3 min-w-[300px] max-w-md pointer-events-auto
        ${colors[toast.type]}
      `}
    >
      <span className="shrink-0">{icons[toast.type]}</span>
      <p className="flex-1 text-sm font-medium">{toast.message}</p>
      <button
        onClick={() => removeToast(toast.id)}
        className="shrink-0 hover:opacity-70 transition-opacity"
        aria-label="Close notification"
      >
        <X className="w-4 h-4" />
      </button>
    </motion.div>
  );
};

export const ToastContainer: React.FC = () => {
  const { toasts } = useToast();

  return (
    <div className="fixed bottom-4 right-4 z-50 flex flex-col items-end pointer-events-none p-4">
      <AnimatePresence mode="popLayout">
        {toasts.map((toast) => (
          <ToastItem key={toast.id} toast={toast} />
        ))}
      </AnimatePresence>
    </div>
  );
};
