import { AnimatePresence, motion, Variants } from 'framer-motion';
import { X } from 'lucide-react';
import React from 'react';
import { THEMES } from '../../constants';
import { useTheme } from '../../contexts/ThemeContext';

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  children: React.ReactNode;
  footer?: React.ReactNode;
}

export const Modal: React.FC<ModalProps> = ({ isOpen, onClose, title, children, footer }) => {
  const { style, mode } = useTheme();
  const titleId = React.useId();

  const overlayVariants: Variants = {
    hidden: { opacity: 0 },
    visible: { opacity: 1 },
  };

  const modalVariants: Variants = style === THEMES.NEOBRUTALISM ? {
    hidden: { y: '100%', rotate: -5, opacity: 0 },
    visible: {
      y: 0,
      rotate: 0,
      opacity: 1,
      transition: { type: 'spring', damping: 15, stiffness: 200 }
    },
    exit: { y: '100%', rotate: 5, opacity: 0 }
  } : {
    hidden: { scale: 0.8, opacity: 0, backdropFilter: 'blur(0px)' },
    visible: {
      scale: 1,
      opacity: 1,
      backdropFilter: 'blur(10px)',
      transition: { type: 'spring', damping: 20, stiffness: 300 }
    },
    exit: { scale: 0.8, opacity: 0 }
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4" role="dialog" aria-modal="true" aria-labelledby={titleId}>
          <motion.div
            variants={overlayVariants}
            initial="hidden"
            animate="visible"
            exit="hidden"
            className="absolute inset-0 bg-black/60 backdrop-blur-sm"
            onClick={onClose}
          />
          <motion.div
            variants={modalVariants}
            initial="hidden"
            animate="visible"
            exit="exit"
            className={`relative w-full max-w-lg overflow-hidden flex flex-col max-h-[90vh] 
              ${style === THEMES.NEOBRUTALISM
                ? 'bg-white border-2 border-black shadow-[8px_8px_0px_0px_rgba(0,0,0,1)] rounded-none'
                : 'bg-gray-900/80 border border-white/20 rounded-3xl shadow-2xl text-white'}`}
          >
            {/* Header */}
            <div className={`p-6 flex justify-between items-center ${style === THEMES.NEOBRUTALISM ? 'border-b-2 border-black bg-neo-main text-white' : 'border-b border-white/10 bg-white/5'}`}>
              <h3 id={titleId} className={`text-2xl font-bold ${style === THEMES.NEOBRUTALISM ? 'uppercase font-mono tracking-tighter' : ''}`}>{title}</h3>
              <button
                type="button"
                onClick={onClose}
                className={`hover:rotate-90 transition-transform duration-200 outline-none rounded-sm ${
                  style === THEMES.NEOBRUTALISM
                    ? 'focus-visible:ring-2 focus-visible:ring-black focus-visible:ring-offset-2 focus-visible:ring-offset-[#8855ff]'
                    : 'focus-visible:ring-2 focus-visible:ring-blue-400 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-900'
                }`}
                aria-label="Close modal"
              >
                <X size={24} />
              </button>
            </div>

            {/* Body */}
            <div className="p-6 overflow-y-auto custom-scrollbar">
              {children}
            </div>

            {/* Footer */}
            {footer && (
              <div className={`p-6 pt-4 mt-auto flex justify-end gap-3 ${style === THEMES.NEOBRUTALISM ? 'border-t-2 border-black' : 'border-t border-white/10'}`}>
                {footer}
              </div>
            )}
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
};