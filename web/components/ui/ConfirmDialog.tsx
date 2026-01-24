import React from 'react';
import { ConfirmOptions } from '../../contexts/ConfirmContext';
import { Button } from './Button';
import { Modal } from './Modal';

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
  options
}) => {
  const { title, message, confirmText = 'Confirm', cancelText = 'Cancel', variant = 'primary' } = options;

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
            variant={variant}
            onClick={onConfirm}
            autoFocus
          >
            {confirmText}
          </Button>
        </>
      }
    >
      <p className="opacity-80 text-lg leading-relaxed">{message}</p>
    </Modal>
  );
};
