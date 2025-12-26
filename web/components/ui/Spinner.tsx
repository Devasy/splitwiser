import React from 'react';
import { Loader2 } from 'lucide-react';

interface SpinnerProps {
  className?: string;
  size?: number;
  ariaLabel?: string;
}

export const Spinner: React.FC<SpinnerProps> = ({ className = '', size = 18, ariaLabel = "Loading" }) => {
  return (
    <Loader2
      className={`animate-spin ${className}`}
      size={size}
      aria-label={ariaLabel}
    />
  );
};
