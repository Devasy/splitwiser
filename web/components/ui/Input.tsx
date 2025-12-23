import React, { useState, useId } from 'react';
import { Eye, EyeOff } from 'lucide-react';
import { useTheme } from '../../contexts/ThemeContext';
import { THEMES } from '../../constants';

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
}

export const Input: React.FC<InputProps> = ({ label, error, className = '', type, ...props }) => {
  const { style, mode } = useTheme();
  const [showPassword, setShowPassword] = useState(false);
  const generatedId = useId();
  const inputId = props.id || generatedId;

  const isPassword = type === 'password';
  const inputType = isPassword ? (showPassword ? 'text' : 'password') : type;

  let inputStyles = "w-full outline-none transition-all duration-200";

  if (style === THEMES.NEOBRUTALISM) {
    inputStyles += ` p-3 border-2 border-black shadow-[2px_2px_0px_0px_rgba(0,0,0,1)] focus:shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] focus:-translate-y-0.5 rounded-none font-bold ${mode === 'dark' ? 'bg-zinc-800 text-white' : 'bg-white text-black'}`;
  } else {
    inputStyles += ` p-3 rounded-lg border border-white/20 bg-white/5 backdrop-blur-sm focus:bg-white/10 focus:border-blue-400 focus:ring-2 focus:ring-blue-500/20 ${mode === 'dark' ? 'text-white placeholder-white/40' : 'text-gray-900 placeholder-gray-500'}`;
  }

  if (isPassword) {
    inputStyles += " pr-10";
  }

  return (
    <div className="flex flex-col gap-1 w-full">
      {label && <label htmlFor={inputId} className={`text-sm font-semibold ${style === THEMES.NEOBRUTALISM ? 'uppercase' : 'ml-1 opacity-80'}`}>{label}</label>}
      <div className="relative">
        <input
          id={inputId}
          type={inputType}
          className={`${inputStyles} ${className}`}
          {...props}
        />
        {isPassword && (
          <button
            type="button"
            onClick={() => setShowPassword(!showPassword)}
            className={`absolute right-3 top-1/2 -translate-y-1/2 p-1 rounded-md transition-opacity hover:opacity-100 focus:outline-none focus:ring-2 focus:ring-offset-1 ${
              style === THEMES.NEOBRUTALISM
                ? (mode === 'dark' ? 'text-white opacity-80 focus:ring-white' : 'text-black opacity-60 focus:ring-black')
                : 'text-white/60 hover:text-white focus:ring-white/50'
            }`}
            aria-label={showPassword ? "Hide password" : "Show password"}
          >
            {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
          </button>
        )}
      </div>
      {error && <span className="text-red-500 text-xs font-bold mt-1">{error}</span>}
    </div>
  );
};
