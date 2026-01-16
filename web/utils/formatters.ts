import { CURRENCIES } from '../constants';

export const formatCurrency = (amount: number, currencyCode: string = 'USD'): string => {
    const currency = (CURRENCIES as any)[currencyCode] || CURRENCIES.USD;

    return new Intl.NumberFormat('en-IN', {
        style: 'currency',
        currency: currency.code,
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
    }).format(amount);
};

export const getCurrencySymbol = (currencyCode: string = 'USD'): string => {
    const currency = (CURRENCIES as any)[currencyCode] || CURRENCIES.USD;
    return currency.symbol;
};
