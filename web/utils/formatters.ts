import { CURRENCIES } from '../constants';

// Type for valid currency codes
type CurrencyCode = keyof typeof CURRENCIES;

/**
 * Check if a currency code is valid
 */
const isValidCurrencyCode = (code: string): code is CurrencyCode => {
    return code in CURRENCIES;
};

/**
 * Format a number as currency
 * @param amount - The amount to format
 * @param currencyCode - The currency code (defaults to USD)
 * @param locale - Optional locale for number formatting (defaults to user's browser locale)
 */
export const formatCurrency = (
    amount: number,
    currencyCode: string = 'USD',
    locale?: string
): string => {
    const currency = isValidCurrencyCode(currencyCode)
        ? CURRENCIES[currencyCode]
        : CURRENCIES.USD;

    // Use provided locale, or undefined to use browser default
    return new Intl.NumberFormat(locale, {
        style: 'currency',
        currency: currency.code,
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
    }).format(amount);
};

/**
 * Get the symbol for a currency
 * @param currencyCode - The currency code (defaults to USD)
 */
export const getCurrencySymbol = (currencyCode: string = 'USD'): string => {
    const currency = isValidCurrencyCode(currencyCode)
        ? CURRENCIES[currencyCode]
        : CURRENCIES.USD;
    return currency.symbol;
};
