import { View, Text, ViewProps, TouchableOpacity, TextProps } from 'react-native';
import { cn } from '../lib/utils';

export function ThemedView({ style, className, ...otherProps }: ViewProps & { className?: string }) {
  return <View style={style} className={cn("bg-neo-bg", className)} {...otherProps} />;
}

export function ThemedText({ style, className, type = 'default', ...otherProps }: TextProps & { className?: string, type?: 'title' | 'subtitle' | 'default' | 'defaultSemiBold' | 'link' }) {
  const getStyles = () => {
    switch (type) {
      case 'title': return "text-4xl font-mono-bold text-neo-dark";
      case 'subtitle': return "text-2xl font-mono-bold text-neo-dark";
      case 'defaultSemiBold': return "text-base font-sans-bold text-neo-dark";
      case 'link': return "text-base font-sans text-neo-main underline";
      default: return "text-base font-sans text-neo-dark";
    }
  };

  return <Text style={style} className={cn(getStyles(), className)} {...otherProps} />;
}

export function ThemedButton({ title, onPress, variant = 'primary', className, ...otherProps }: { title: string, onPress?: () => void, variant?: 'primary' | 'secondary' | 'accent', className?: string }) {
  const getBgColor = () => {
    switch(variant) {
      case 'secondary': return "bg-neo-second";
      case 'accent': return "bg-neo-accent";
      default: return "bg-neo-main";
    }
  }

  return (
    <TouchableOpacity
      activeOpacity={0.8}
      onPress={onPress}
      className={cn(
        getBgColor(),
        "px-6 py-4 border-2 border-neo-dark shadow-neo active:shadow-neo-sm active:translate-x-[2px] active:translate-y-[2px] transition-all",
        className
      )}
      {...otherProps}
    >
      <Text className="text-neo-white font-mono-bold text-lg text-center uppercase tracking-wider">{title}</Text>
    </TouchableOpacity>
  );
}
