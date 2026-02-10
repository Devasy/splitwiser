import { motion } from 'framer-motion';
import { Check } from 'lucide-react';
import React from 'react';
import { THEMES } from '../constants';
import { useTheme } from '../contexts/ThemeContext';
import { Confetti } from './ui/Confetti';

export const SettledUpState = () => {
    const { style } = useTheme();

    return (
        <div className="col-span-full flex flex-col items-center justify-center py-20 relative">
            <Confetti count={100} />

            <motion.div
                initial={{ scale: 0, rotate: -180 }}
                animate={{ scale: 1, rotate: 0 }}
                transition={{
                    type: "spring",
                    stiffness: 260,
                    damping: 20,
                    delay: 0.1
                }}
                className={`w-24 h-24 flex items-center justify-center mx-auto mb-6 ${
                    style === THEMES.NEOBRUTALISM
                        ? 'bg-emerald-100 border-2 border-black rounded-none shadow-[4px_4px_0px_0px_rgba(0,0,0,1)]'
                        : 'bg-emerald-100 dark:bg-emerald-900/20 rounded-full ring-4 ring-emerald-500/20'
                }`}
            >
                <motion.div
                    initial={{ opacity: 0, scale: 0.5 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ delay: 0.2 }}
                >
                    <Check size={48} strokeWidth={3} className={style === THEMES.NEOBRUTALISM ? 'text-black' : 'text-emerald-500'} />
                </motion.div>
            </motion.div>

            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.3 }}
                className="text-center"
            >
                <h3 className={`text-3xl font-black mb-2 ${style === THEMES.NEOBRUTALISM ? 'text-black' : 'text-emerald-500'}`}>
                    All Settled Up!
                </h3>
                <p className="opacity-60 text-lg">No outstanding balances in this group.</p>
            </motion.div>
        </div>
    );
};
