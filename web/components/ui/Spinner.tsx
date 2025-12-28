import React from 'react';
import { Loader2 } from 'lucide-react';

interface SpinnerProps extends React.SVGProps<SVGSVGElement> {
  size?: number | string;
  className?: string;
  ariaLabel?: string;
}

export const Spinner: React.FC<SpinnerProps> = ({
  size = 20,
  className = '',
  ariaLabel = 'Loading',
  ...props
}) => {
  return (
    <Loader2
      className={`animate-spin ${className}`}
      size={size}
      aria-label={ariaLabel}
      {...props}
    />
  );
};
