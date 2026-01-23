import React from 'react';
import { Modal } from './Modal';
import { Button } from './Button';
import { AlertTriangle, Info } from 'lucide-react';
import { THEMES } from '../../constants';
import { useTheme } from '../../contexts/ThemeContext';

interface ConfirmDialogProps {
    isOpen: boolean;
    onConfirm: () => void;
    onCancel: () => void;
    title: string;
    message: string;
    variant?: 'danger' | 'info';
    confirmText?: string;
    cancelText?: string;
}

export const ConfirmDialog: React.FC<ConfirmDialogProps> = ({
    isOpen,
    onConfirm,
    onCancel,
    title,
    message,
    variant = 'info',
    confirmText = 'Confirm',
    cancelText = 'Cancel'
}) => {
    const { style } = useTheme();

    return (
        <Modal
            isOpen={isOpen}
            onClose={onCancel}
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
                      ? (style === THEMES.NEOBRUTALISM ? 'bg-red-200 border-2 border-black text-black' : 'bg-red-500/20 text-red-500')
                      : (style === THEMES.NEOBRUTALISM ? 'bg-blue-200 border-2 border-black text-black' : 'bg-blue-500/20 text-blue-500')
                  }`}>
                      {variant === 'danger' ? <AlertTriangle size={24} /> : <Info size={24} />}
                  </div>
                  <div className="mt-1">
                      <p className={`text-lg leading-relaxed ${style === THEMES.NEOBRUTALISM ? 'text-black' : 'text-gray-200'}`}>
                        {message}
                      </p>
                  </div>
               </div>
            </div>
        </Modal>
    );
};
