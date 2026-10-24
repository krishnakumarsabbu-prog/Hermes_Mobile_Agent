import { AccountSummary, Beneficiary, Transaction } from './models';

const currentMonthDate = (day: number): string => {
  const now = new Date();
  return new Date(now.getFullYear(), now.getMonth(), day, 12).toISOString();
};

export const initialAccount: AccountSummary = { id: 'acct_01', name: 'Everyday Checking', maskedNumber: '•••• 0987', balancePaise: 10000000, currency: 'INR' };
export const ravi: Beneficiary = { id: 'ben_ravi', fullName: 'Ravi Sharma', alias: 'Ravi', dailyLimitPaise: 10000000 };
export const initialTransactions: Transaction[] = [
  { id: 'txn_trattoria', merchant: 'Trattoria', category: 'Dining', amountPaise: 320000, date: currentMonthDate(3), status: 'successful', reference: 'HMS-2403-TRAT' },
  { id: 'txn_brew', merchant: 'Brew Room', category: 'Dining', amountPaise: 300000, date: currentMonthDate(7), status: 'successful', reference: 'HMS-2407-BREW' },
  { id: 'txn_shopping', merchant: 'Shopping Store', category: 'Shopping', amountPaise: 1800000, date: currentMonthDate(12), status: 'successful', reference: 'HMS-2412-SHOP' },
  { id: 'txn_electricity', merchant: 'Electricity Provider', category: 'Utility', amountPaise: 830000, date: currentMonthDate(16), status: 'successful', reference: 'HMS-2416-UTIL' },
];
