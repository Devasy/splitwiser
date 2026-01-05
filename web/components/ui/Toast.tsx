import { AnimatePresence, motion } from 'framer-motion';
import { AlertCircle, CheckCircle, Info, X } from 'lucide-react';
import React from 'react';
import { THEMES } from '../../constants';
import { useTheme } from '../../contexts/ThemeContext';
import { Toast, useToast } from '../../contexts/ToastContext';

const ToastItem: React.FC<{ toast: Toast }> = ({ toast }) => {
  const { removeToast } = useToast();
  const { style } = useTheme();
  const isNeo = style === THEMES.NEOBRUTALISM;

  const icons = {
    success: <CheckCircle className={isNeo ? "text-black" : "text-green-500"} size={20} />,
    error: <AlertCircle className={isNeo ? "text-black" : "text-red-500"} size={20} />,
    info: <Info className={isNeo ? "text-black" : "text-blue-500"} size={20} />,
  };

  const neoStyles = {
    success: 'bg-[#00cc88] text-black border-2 border-black shadow-[4px_4px_0px_0px_rgba(0,0,0,1)]',
    error: 'bg-[#ff5555] text-black border-2 border-black shadow-[4px_4px_0px_0px_rgba(0,0,0,1)]',
    info: 'bg-[#8855ff] text-black border-2 border-black shadow-[4px_4px_0px_0px_rgba(0,0,0,1)]',
  };

  const glassStyles = {
    success: 'bg-green-50/90 border-green-200 text-green-900',
    error: 'bg-red-50/90 border-red-200 text-red-900',
    info: 'bg-blue-50/90 border-blue-200 text-blue-900',
  };

  const baseClasses = isNeo
    ? `flex items-center gap-3 p-4 min-w-[300px] font-bold rounded-none ${neoStyles[toast.type]}`
    : `flex items-center gap-3 p-4 min-w-[300px] rounded-xl backdrop-blur-md border shadow-lg ${glassStyles[toast.type]}`;

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 50, scale: 0.9 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, scale: 0.9, transition: { duration: 0.2 } }}
      className={baseClasses}
    >
      {icons[toast.type]}
      <p className="flex-1 text-sm">{toast.message}</p>
      <button
        onClick={() => removeToast(toast.id)}
        className={`p-1 hover:opacity-70 transition-opacity ${isNeo ? 'bg-black text-white' : 'bg-transparent text-current'}`}
        aria-label="Close notification"
      >
        <X size={16} />
      </button>
    </motion.div>
  );
};

export const ToastContainer = () => {
  const { toasts } = useToast();

  return (
    <div className="fixed bottom-6 right-6 z-50 flex flex-col gap-4 pointer-events-none">
      <AnimatePresence mode="popLayout">
        {toasts.map((toast) => (
          <div key={toast.id} className="pointer-events-auto">
            <ToastItem toast={toast} />
          </div>
        ))}
      </AnimatePresence>
    </div>
  );
};
