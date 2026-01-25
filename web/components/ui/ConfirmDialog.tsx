import { AnimatePresence, motion, Variants } from 'framer-motion';
import { AlertTriangle, HelpCircle } from 'lucide-react';
import React, { useEffect, useRef } from 'react';
import { THEMES } from '../../constants';
import { useTheme } from '../../contexts/ThemeContext';
import { Button } from './Button';

interface ConfirmDialogProps {
    isOpen: boolean;
    onConfirm: () => void;
    onCancel: () => void;
    title: string;
    message: string;
    confirmText?: string;
    cancelText?: string;
    variant?: 'danger' | 'primary' | 'secondary';
}

export const ConfirmDialog: React.FC<ConfirmDialogProps> = ({
    isOpen,
    onConfirm,
    onCancel,
    title,
    message,
    confirmText = 'Confirm',
    cancelText = 'Cancel',
    variant = 'primary'
}) => {
    const { style } = useTheme();
    const cancelButtonRef = useRef<HTMLButtonElement>(null);

    // Focus management
    useEffect(() => {
        if (isOpen) {
            // Small delay to ensure render
            setTimeout(() => {
                cancelButtonRef.current?.focus();
            }, 50);
        }
    }, [isOpen]);

    // Close on Escape
    useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            if (e.key === 'Escape' && isOpen) {
                onCancel();
            }
        };
        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, [isOpen, onCancel]);

    const overlayVariants: Variants = {
        hidden: { opacity: 0 },
        visible: { opacity: 1 },
    };

    const modalVariants: Variants = style === THEMES.NEOBRUTALISM ? {
        hidden: { y: '100%', scale: 0.9, opacity: 0 },
        visible: {
            y: 0,
            scale: 1,
            opacity: 1,
            transition: { type: 'spring', damping: 20, stiffness: 300 }
        },
        exit: { y: '100%', scale: 0.9, opacity: 0 }
    } : {
        hidden: { scale: 0.9, opacity: 0, backdropFilter: 'blur(0px)' },
        visible: {
            scale: 1,
            opacity: 1,
            backdropFilter: 'blur(4px)',
            transition: { type: 'spring', damping: 25, stiffness: 300 }
        },
        exit: { scale: 0.9, opacity: 0 }
    };

    const getIcon = () => {
        if (variant === 'danger') return <AlertTriangle className={style === THEMES.NEOBRUTALISM ? "text-black" : "text-red-500"} size={32} />;
        return <HelpCircle className={style === THEMES.NEOBRUTALISM ? "text-black" : "text-blue-500"} size={32} />;
    };

    return (
        <AnimatePresence>
            {isOpen && (
                <div className="fixed inset-0 z-[60] flex items-center justify-center p-4">
                    <motion.div
                        variants={overlayVariants}
                        initial="hidden"
                        animate="visible"
                        exit="hidden"
                        className="absolute inset-0 bg-black/50 backdrop-blur-sm"
                        onClick={onCancel}
                    />
                    <motion.div
                        role="alertdialog"
                        aria-modal="true"
                        aria-labelledby="confirm-title"
                        aria-describedby="confirm-desc"
                        variants={modalVariants}
                        initial="hidden"
                        animate="visible"
                        exit="exit"
                        className={`relative w-full max-w-md overflow-hidden flex flex-col
              ${style === THEMES.NEOBRUTALISM
                                ? 'bg-white border-2 border-black shadow-[8px_8px_0px_0px_rgba(0,0,0,1)] rounded-none'
                                : 'bg-gray-900/90 border border-white/20 rounded-3xl shadow-2xl text-white backdrop-blur-xl'}`}
                    >
                        <div className="p-6 flex flex-col items-center text-center gap-4">
                            <div className={`p-4 rounded-full flex items-center justify-center ${style === THEMES.NEOBRUTALISM ? 'bg-gray-100 border-2 border-black' : 'bg-white/10'}`}>
                                {getIcon()}
                            </div>

                            <div>
                                <h3 id="confirm-title" className={`text-xl font-bold mb-2 ${style === THEMES.NEOBRUTALISM ? 'text-black' : 'text-white'}`}>{title}</h3>
                                <p id="confirm-desc" className={`leading-relaxed ${style === THEMES.NEOBRUTALISM ? 'text-black/80' : 'text-white/80'}`}>{message}</p>
                            </div>

                            <div className="flex gap-3 w-full mt-4">
                                <Button
                                    ref={cancelButtonRef}
                                    variant="ghost"
                                    onClick={onCancel}
                                    className={`flex-1 ${style === THEMES.NEOBRUTALISM ? 'text-black' : ''}`}
                                >
                                    {cancelText}
                                </Button>
                                <Button
                                    variant={variant}
                                    onClick={onConfirm}
                                    className="flex-1"
                                >
                                    {confirmText}
                                </Button>
                            </div>
                        </div>
                    </motion.div>
                </div>
            )}
        </AnimatePresence>
    );
};
