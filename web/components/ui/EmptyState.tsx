import React from 'react';
import { motion } from 'framer-motion';
import { useTheme } from '../../contexts/ThemeContext';
import { THEMES } from '../../constants';
import { Button } from './Button';

interface EmptyStateProps {
  icon: React.ReactNode;
  title: string;
  description: string;
  action?: {
    label: string;
    onClick: () => void;
  };
  className?: string;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  icon,
  title,
  description,
  action,
  className = ''
}) => {
  const { style, mode } = useTheme();
  const isNeo = style === THEMES.NEOBRUTALISM;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ type: 'spring', stiffness: 100 }}
      className={`
        flex flex-col items-center justify-center text-center p-12 w-full
        ${isNeo
          ? 'bg-white border-2 border-black shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] rounded-none'
          : `backdrop-blur-md border rounded-3xl ${mode === 'dark' ? 'bg-white/5 border-white/10' : 'bg-white/60 border-black/5'}`
        }
        ${className}
      `}
    >
      <div
        aria-hidden="true"
        className={`
        mb-6 p-4 text-4xl
        ${isNeo
          ? 'bg-neo-second border-2 border-black shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] rounded-none'
          : 'bg-gradient-to-br from-blue-500/20 to-purple-600/20 text-blue-500 rounded-2xl'
        }
      `}>
        {icon}
      </div>

      <h3 className={`text-2xl font-black mb-2 ${isNeo ? 'text-black uppercase' : (mode === 'dark' ? 'text-white' : 'text-gray-900')}`}>
        {title}
      </h3>

      <p className={`text-lg mb-8 max-w-md ${isNeo ? 'font-mono text-black/70' : (mode === 'dark' ? 'text-white/60' : 'text-gray-600')}`}>
        {description}
      </p>

      {action && (
        <Button onClick={action.onClick} variant="primary" size="lg">
          {action.label}
        </Button>
      )}
    </motion.div>
  );
};
