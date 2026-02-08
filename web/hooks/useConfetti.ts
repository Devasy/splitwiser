import confetti from 'canvas-confetti';
import { useCallback, useEffect, useRef } from 'react';

export const useConfetti = () => {
    const fireworksIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

    // Cleanup interval on unmount
    useEffect(() => {
        return () => {
            if (fireworksIntervalRef.current) {
                clearInterval(fireworksIntervalRef.current);
            }
        };
    }, []);

    const fireConfetti = useCallback(() => {
        confetti({
            particleCount: 100,
            spread: 70,
            origin: { y: 0.6 },
            colors: ['#26ccff', '#a25afd', '#ff5e7e', '#88ff5a', '#fcff42', '#ffa62d', '#ff36ff'],
            disableForReducedMotion: true,
        });
    }, []);

    const fireFireworks = useCallback(() => {
        // Clear any existing interval
        if (fireworksIntervalRef.current) {
            clearInterval(fireworksIntervalRef.current);
        }

        const duration = 5 * 1000;
        const animationEnd = Date.now() + duration;
        const defaults = { startVelocity: 30, spread: 360, ticks: 60, zIndex: 0, disableForReducedMotion: true };

        const randomInRange = (min: number, max: number) => {
            return Math.random() * (max - min) + min;
        };

        fireworksIntervalRef.current = setInterval(function () {
            const timeLeft = animationEnd - Date.now();

            if (timeLeft <= 0) {
                if (fireworksIntervalRef.current) {
                    clearInterval(fireworksIntervalRef.current);
                }
                return;
            }

            const particleCount = 50 * (timeLeft / duration);
            // since particles fall down, start a bit higher than random
            confetti({ ...defaults, particleCount, origin: { x: randomInRange(0.1, 0.3), y: Math.random() - 0.2 } });
            confetti({ ...defaults, particleCount, origin: { x: randomInRange(0.7, 0.9), y: Math.random() - 0.2 } });
        }, 250);
    }, []);

    return { fireConfetti, fireFireworks };
};
