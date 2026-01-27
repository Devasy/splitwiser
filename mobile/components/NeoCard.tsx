import { View } from 'react-native';
import { cn } from '../lib/utils';

interface CardProps {
  className?: string;
  children: React.ReactNode;
}

export function NeoCard({ className, children }: CardProps) {
  return (
    <View className={cn("bg-neo-white border-2 border-neo-dark shadow-neo p-4", className)}>
      {children}
    </View>
  );
}
