import React from 'react';
import { Button } from './Button';
import { Modal } from './Modal';
import { useTheme } from '../../contexts/ThemeContext';
import { THEMES } from '../../constants';
import { AlertTriangle, Info } from 'lucide-react';

interface ConfirmDialogProps {
    isOpen: boolean;
    onClose: () => void;
    title: string;
    message: string;
    confirmText?: string;
    cancelText?: string;
    variant?: 'danger' | 'default';
    onConfirm: () => void;
    onCancel: () => void;
}

export const ConfirmDialog: React.FC<ConfirmDialogProps> = ({
    isOpen,
    onClose,
    title,
    message,
    confirmText = 'Confirm',
    cancelText = 'Cancel',
    variant = 'default',
    onConfirm,
    onCancel,
}) => {
    const { style } = useTheme();

    return (
        <Modal
            isOpen={isOpen}
            onClose={onClose}
            title={title}
            footer={
                <>
                    <Button variant="ghost" onClick={onCancel}>
                        {cancelText}
                    </Button>
                    <Button
                        variant={variant === 'danger' ? 'danger' : 'primary'}
                        onClick={onConfirm}
                        autoFocus
                    >
                        {confirmText}
                    </Button>
                </>
            }
        >
            <div className="flex flex-col gap-4">
                <div className="flex items-start gap-4">
                     <div className={`p-3 rounded-full flex-shrink-0 ${
                         variant === 'danger'
                            ? (style === THEMES.NEOBRUTALISM ? 'bg-red-100 border-2 border-black rounded-none' : 'bg-red-500/20 text-red-500')
                            : (style === THEMES.NEOBRUTALISM ? 'bg-blue-100 border-2 border-black rounded-none' : 'bg-blue-500/20 text-blue-500')
                     }`}>
                        {variant === 'danger' ? <AlertTriangle size={24} /> : <Info size={24} />}
                     </div>
                     <div className="flex-1 pt-1">
                        <p className={`text-base leading-relaxed opacity-90 ${style === THEMES.NEOBRUTALISM ? 'font-medium' : ''}`}>
                            {message}
                        </p>
                     </div>
                </div>
            </div>
        </Modal>
    );
};
