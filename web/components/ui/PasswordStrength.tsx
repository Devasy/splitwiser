import React, { useMemo } from 'react';
import { useTheme } from '../../contexts/ThemeContext';
import { THEMES } from '../../constants';
import { Check } from 'lucide-react';

interface PasswordStrengthProps {
  password?: string;
}

export const PasswordStrength: React.FC<PasswordStrengthProps> = ({ password = '' }) => {
  const { style } = useTheme();

  const { score, label, metCriteria } = useMemo(() => {
    let s = 0;
    const criteria = {
      length: password.length >= 8,
      hasUpper: /[A-Z]/.test(password),
      hasLower: /[a-z]/.test(password),
      hasNumber: /[0-9]/.test(password),
      hasSpecial: /[^A-Za-z0-9]/.test(password),
    };

    let l = 'Weak';

    if (password.length > 0) {
      if (password.length < 6) {
        s = 1; // Very Weak
        l = 'Too Short';
      } else {
        s = 1;
        // Bonus for length
        if (criteria.length) s++;

        // Bonus for complexity
        const complexity = (criteria.hasUpper ? 1 : 0) +
                           (criteria.hasLower ? 1 : 0) +
                           (criteria.hasNumber ? 1 : 0) +
                           (criteria.hasSpecial ? 1 : 0);

        if (complexity >= 2) s++;
        if (complexity >= 4) s++; // Max bonus

        // Adjust label based on final score
        if (s >= 4) l = 'Strong';
        else if (s === 3) l = 'Good';
        else if (s === 2) l = 'Fair';
        else l = 'Weak';
      }
    } else {
      l = '';
    }

    // Normalize score 0-4
    if (s > 4) s = 4;

    return { score: s, label: l, metCriteria: criteria };
  }, [password]);

  const getColor = (s: number) => {
    switch (s) {
      case 1: return 'bg-red-500';
      case 2: return 'bg-orange-500';
      case 3: return 'bg-yellow-500';
      case 4: return 'bg-green-500';
      default: return 'bg-gray-200 dark:bg-zinc-700';
    }
  };

  const isNeo = style === THEMES.NEOBRUTALISM;

  if (!password) return null;

  return (
    <div className="w-full flex flex-col gap-2 mt-2" aria-label="Password strength indicator">
      {/* Strength Bar */}
      <div className="flex w-full gap-1 h-2">
        {[1, 2, 3, 4].map((level) => (
          <div
            key={level}
            className={`flex-1 h-full transition-all duration-300 ${
              score >= level
                ? getColor(score)
                : (isNeo ? 'bg-gray-200 dark:bg-zinc-800' : 'bg-white/10')
            } ${isNeo ? 'border-2 border-black' : 'rounded-full'}`}
          />
        ))}
      </div>

      {/* Label and Criteria */}
      <div className="flex justify-between items-center h-4">
        <span className={`text-xs font-bold transition-colors duration-300 ${
            score === 4 ? 'text-green-600 dark:text-green-400' :
            score === 3 ? 'text-yellow-600 dark:text-yellow-400' :
            score === 2 ? 'text-orange-600 dark:text-orange-400' :
            'text-red-600 dark:text-red-400'
        } ${isNeo ? 'uppercase tracking-wider' : ''}`}>
            {label}
        </span>
      </div>

      <div className="grid grid-cols-2 gap-y-1 gap-x-4 text-[10px] text-gray-500 dark:text-gray-400 transition-opacity duration-300">
          <div className={`flex items-center gap-1.5 ${metCriteria.length ? 'text-green-600 dark:text-green-400 font-bold' : ''}`}>
            {metCriteria.length ? <Check size={12} strokeWidth={3} /> : <div className="w-3" />}
            8+ characters
          </div>
          <div className={`flex items-center gap-1.5 ${(metCriteria.hasUpper && metCriteria.hasLower) ? 'text-green-600 dark:text-green-400 font-bold' : ''}`}>
             {(metCriteria.hasUpper && metCriteria.hasLower) ? <Check size={12} strokeWidth={3} /> : <div className="w-3" />}
             Mixed case
          </div>
          <div className={`flex items-center gap-1.5 ${metCriteria.hasNumber ? 'text-green-600 dark:text-green-400 font-bold' : ''}`}>
             {metCriteria.hasNumber ? <Check size={12} strokeWidth={3} /> : <div className="w-3" />}
             Number
          </div>
          <div className={`flex items-center gap-1.5 ${metCriteria.hasSpecial ? 'text-green-600 dark:text-green-400 font-bold' : ''}`}>
             {metCriteria.hasSpecial ? <Check size={12} strokeWidth={3} /> : <div className="w-3" />}
             Symbol
          </div>
      </div>

      {/* Hidden live region for accessibility */}
      <output className="sr-only" aria-live="polite">
        Password strength: {label}.
        {score < 4 && label ? "Add more characters, numbers, or symbols to strengthen." : ""}
      </output>
    </div>
  );
};
