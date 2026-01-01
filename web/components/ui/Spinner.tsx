import React from 'react';
import { Loader2 } from 'lucide-react';

interface SpinnerProps {
  size?: number;
  className?: string;
  ariaLabel?: string;
}

export const Spinner: React.FC<SpinnerProps> = ({
  size = 24,
  className = '',
  ariaLabel = 'Loading'
}) => {
  return (
    <div role="status" aria-label={ariaLabel}>
      <Loader2
        size={size}
        className={`animate-spin ${className}`}
        aria-hidden="true"
      />
    </div>
  );
};
