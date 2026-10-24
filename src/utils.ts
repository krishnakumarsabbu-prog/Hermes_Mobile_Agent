import { Transaction, SpendingSummary } from './models';

export const formatINR = (paise: number): string => {
  const rupees = paise / 100;
  return `₹${rupees.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
};

export const formatDate = (value: string): string => new Date(value).toLocaleDateString('en-IN', { day: '2-digit', month: 'short' });
export const formatDateTime = (value: string): string => new Date(value).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' });

export const summarizeTransactions = (transactions: Transaction[]): SpendingSummary => {
  const byCategory = { Dining: 0, Shopping: 0, Utility: 0, Transfer: 0 } as SpendingSummary['byCategory'];
  transactions.forEach((transaction) => { if (transaction.status === 'successful') byCategory[transaction.category] += transaction.amountPaise; });
  return { totalPaise: Object.values(byCategory).reduce((sum, value) => sum + value, 0), byCategory, transactionCount: transactions.filter((transaction) => transaction.status === 'successful').length };
};
