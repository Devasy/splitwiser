import React from 'react';
import { THEMES } from '../../constants';
import { useTheme } from '../../contexts/ThemeContext';
import { Spinner } from './Spinner';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'danger' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  isLoading?: boolean;
}

export const Button: React.FC<ButtonProps> = ({
  children,
  variant = 'primary',
  size = 'md',
  className = '',
  isLoading = false,
  ...props
}) => {
  const { style } = useTheme();

  const baseStyles = "transition-all duration-200 font-bold flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed";

  const sizeStyles = {
    sm: "px-3 py-1.5 text-sm",
    md: "px-5 py-2.5 text-base",
    lg: "px-6 py-3 text-lg"
  };

  const spinnerSizes = {
    sm: 16,
    md: 20,
    lg: 24
  };

  let themeStyles = "";

  if (style === THEMES.NEOBRUTALISM) {
    themeStyles = "border-2 border-black shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] hover:translate-x-[2px] hover:translate-y-[2px] hover:shadow-[2px_2px_0px_0px_rgba(0,0,0,1)] active:translate-x-[4px] active:translate-y-[4px] active:shadow-none rounded-none uppercase tracking-wider font-mono";

    if (variant === 'primary') themeStyles += " bg-neo-main text-white";
    if (variant === 'secondary') themeStyles += " bg-neo-second text-black";
    if (variant === 'danger') themeStyles += " bg-red-500 text-white";
    if (variant === 'ghost') themeStyles += " bg-transparent border-transparent shadow-none hover:bg-gray-200 hover:shadow-none hover:translate-x-0 hover:translate-y-0 active:translate-x-0 active:translate-y-0";

  } else {
    // Glassmorphism
    themeStyles = "rounded-xl backdrop-blur-md border border-white/20 shadow-lg hover:shadow-xl active:scale-95";

    if (variant === 'primary') themeStyles += " bg-gradient-to-r from-blue-500 to-purple-600 text-white shadow-blue-500/30";
    if (variant === 'secondary') themeStyles += " bg-white/10 text-white hover:bg-white/20";
    if (variant === 'danger') themeStyles += " bg-gradient-to-r from-red-500 to-pink-600 text-white shadow-red-500/30";
    if (variant === 'ghost') themeStyles += " bg-transparent border-none shadow-none hover:bg-white/10 text-current";
  }

  return (
    <button
      className={`${baseStyles} ${sizeStyles[size]} ${themeStyles} ${className}`}
      disabled={isLoading || props.disabled}
      {...props}
    >
      {isLoading && <Spinner className="mr-1" size={spinnerSizes[size]} />}
      {children}
    </button>
  );
};
