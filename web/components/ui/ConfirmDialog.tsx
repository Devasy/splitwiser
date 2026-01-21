import { AlertTriangle, Info } from 'lucide-react';
import React from 'react';
import { THEMES } from '../../constants';
import { useTheme } from '../../contexts/ThemeContext';
import { Button } from './Button';
import { Modal } from './Modal';

export type ConfirmVariant = 'danger' | 'warning' | 'info';

export interface ConfirmDialogProps {
  isOpen: boolean;
  title: string;
  description: string;
  confirmText?: string;
  cancelText?: string;
  variant?: ConfirmVariant;
  onConfirm: () => void;
  onCancel: () => void;
}

export const ConfirmDialog: React.FC<ConfirmDialogProps> = ({
  isOpen,
  title,
  description,
  confirmText = 'Confirm',
  cancelText = 'Cancel',
  variant = 'danger',
  onConfirm,
  onCancel,
}) => {
  const { style, mode } = useTheme();
  const isNeo = style === THEMES.NEOBRUTALISM;

  // Determine styles based on variant
  const getIcon = () => {
    switch (variant) {
      case 'danger':
        return <AlertTriangle size={32} className={isNeo ? 'text-black' : 'text-red-500'} />;
      case 'warning':
        return <AlertTriangle size={32} className={isNeo ? 'text-black' : 'text-yellow-500'} />;
      case 'info':
        return <Info size={32} className={isNeo ? 'text-black' : 'text-blue-500'} />;
    }
  };

  const getIconBg = () => {
    switch (variant) {
      case 'danger':
        return isNeo ? 'bg-red-400 border-2 border-black rounded-none' : 'bg-red-500/20 rounded-full';
      case 'warning':
        return isNeo ? 'bg-yellow-400 border-2 border-black rounded-none' : 'bg-yellow-500/20 rounded-full';
      case 'info':
        return isNeo ? 'bg-blue-400 border-2 border-black rounded-none' : 'bg-blue-500/20 rounded-full';
    }
  };

  const getButtonVariant = () => {
    switch (variant) {
      case 'danger': return 'danger';
      case 'warning': return 'primary';
      case 'info': return 'primary';
      default: return 'primary';
    }
  };

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
          <Button variant={getButtonVariant()} onClick={onConfirm} autoFocus>
            {confirmText}
          </Button>
        </>
      }
    >
      <div className="flex flex-col items-center text-center sm:flex-row sm:text-left sm:items-start gap-4">
        <div className={`p-3 shrink-0 ${getIconBg()}`}>
          {getIcon()}
        </div>
        <div>
          <p className={`text-base leading-relaxed ${isNeo ? 'text-black' : 'text-white/80'}`}>
            {description}
          </p>
        </div>
      </div>
    </Modal>
  );
};
