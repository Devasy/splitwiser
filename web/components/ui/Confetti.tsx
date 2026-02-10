import { motion } from 'framer-motion';
import React, { useEffect, useState } from 'react';
import { COLORS } from '../../constants';

interface ConfettiProps {
  count?: number;
}

interface Particle {
  id: number;
  x: number;
  y: number;
  color: string;
  size: number;
  rotation: number;
  duration: number;
  delay: number;
}

export const Confetti = ({ count = 50 }: ConfettiProps) => {
  const [particles, setParticles] = useState<Particle[]>([]);

  useEffect(() => {
    const newParticles: Particle[] = Array.from({ length: count }).map((_, i) => ({
      id: i,
      x: Math.random() * 100, // percent
      y: -10, // start above
      color: COLORS[Math.floor(Math.random() * COLORS.length)],
      size: Math.random() * 8 + 4,
      rotation: Math.random() * 360,
      duration: Math.random() * 2 + 2,
      delay: Math.random() * 0.5,
    }));
    setParticles(newParticles);
  }, [count]);

  return (
    <div className="fixed inset-0 pointer-events-none z-50 overflow-hidden" aria-hidden="true">
      {particles.map((p) => (
        <motion.div
          key={p.id}
          initial={{ y: '-5vh', x: `${p.x}vw`, rotate: p.rotation, opacity: 1 }}
          animate={{
            y: '105vh',
            rotate: p.rotation + 720,
            x: `${p.x + (Math.random() * 20 - 10)}vw`,
            opacity: 0,
          }}
          transition={{
            duration: p.duration,
            delay: p.delay,
            ease: 'easeOut',
          }}
          style={{
            position: 'absolute',
            width: p.size,
            height: p.size,
            backgroundColor: p.color,
            borderRadius: Math.random() > 0.5 ? '50%' : '0%',
          }}
        />
      ))}
    </div>
  );
};
