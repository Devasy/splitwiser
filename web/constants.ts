export const THEMES = {
  NEOBRUTALISM: 'neobrutalism',
  GLASSMORPHISM: 'glassmorphism',
};

export const COLORS = [
  '#FF6B6B', // Red
  '#4ECDC4', // Teal
  '#FFE66D', // Yellow
  '#1A535C', // Dark Teal
  '#F7FFF7', // Off White
];

export const CURRENCIES = {
  USD: { symbol: '$', name: 'US Dollar', code: 'USD' },
  INR: { symbol: '₹', name: 'Indian Rupee', code: 'INR' },
  EUR: { symbol: '€', name: 'Euro', code: 'EUR' },
} as const;

export type CurrencyCode = keyof typeof CURRENCIES;
