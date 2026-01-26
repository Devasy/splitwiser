import React from 'react';
import { AlertTriangle, Info } from 'lucide-react';
import { Button } from './Button';
import { Modal } from './Modal';
import { ConfirmOptions } from '../../contexts/ConfirmContext';

interface ConfirmDialogProps {
  isOpen: boolean;
  onConfirm: () => void;
  onCancel: () => void;
  options: ConfirmOptions;
}

export const ConfirmDialog: React.FC<ConfirmDialogProps> = ({
  isOpen,
  onConfirm,
  onCancel,
  options,
}) => {
  const {
    title = 'Confirm Action',
    message,
    variant = 'info',
    confirmText = 'Confirm',
    cancelText = 'Cancel',
  } = options;

  const isDanger = variant === 'danger';

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
            variant={isDanger ? 'danger' : 'primary'}
            onClick={onConfirm}
            autoFocus
          >
            {confirmText}
          </Button>
        </>
      }
    >
      <div className="flex items-start gap-4">
        <div
          className={`p-3 rounded-full flex-shrink-0 ${
            isDanger ? 'bg-red-100 text-red-600' : 'bg-blue-100 text-blue-600'
          }`}
        >
          {isDanger ? <AlertTriangle size={24} /> : <Info size={24} />}
        </div>
        <div className="mt-1">
          <p className="text-base opacity-90 leading-relaxed">{message}</p>
        </div>
      </div>
    </Modal>
  );
};
