import { AccountSummary, AssistantResponse, Beneficiary, Transaction, TransferApproval, TransferResult } from './models';
import { initialAccount, initialTransactions, ravi } from './mock';
import { summarizeTransactions } from './utils';

let account = { ...initialAccount };
let transactions = [...initialTransactions];
let pendingApprovals = new Map<string, TransferApproval>();

export const AccountService = { getAccountSummary: async (): Promise<AccountSummary> => ({ ...account }), getAvailableBalance: async (): Promise<number> => account.balancePaise };
export const TransactionService = {
  listTransactions: async (): Promise<Transaction[]> => [...transactions].sort((a, b) => +new Date(b.date) - +new Date(a.date)),
  getTransaction: async (id: string): Promise<Transaction | undefined> => transactions.find((item) => item.id === id),
};
export const getSummary = async () => summarizeTransactions(transactions);

const findBeneficiary = (value: string): Beneficiary | undefined => value.toLowerCase().includes('ravi') ? ravi : undefined;

export const TransferService = {
  prepareTransfer: async (amountPaise: number, beneficiaryName: string): Promise<TransferApproval> => {
    const beneficiary = findBeneficiary(beneficiaryName);
    if (!beneficiary) throw new Error('We could not find that beneficiary.');
    if (amountPaise <= 0) throw new Error('The transfer amount must be positive.');
    if (amountPaise > account.balancePaise) throw new Error('This transfer exceeds your available balance.');
    if (amountPaise > beneficiary.dailyLimitPaise) throw new Error('This transfer exceeds the beneficiary daily limit.');
    const approval: TransferApproval = { approvalId: `approval_${Date.now()}`, beneficiary, amountPaise, sourceAccountId: account.id, currentBalancePaise: account.balancePaise, projectedBalancePaise: account.balancePaise - amountPaise, expiresAt: new Date(Date.now() + 5 * 60 * 1000).toISOString(), status: 'pending' };
    pendingApprovals.set(approval.approvalId, approval);
    return approval;
  },
  authorizeTransfer: async (approvalId: string): Promise<TransferResult> => {
    const approval = pendingApprovals.get(approvalId);
    if (!approval || approval.status !== 'pending') throw new Error('This approval is no longer available.');
    if (approval.amountPaise > account.balancePaise) throw new Error('The available balance has changed.');
    const transaction: Transaction = { id: `txn_transfer_${Date.now()}`, merchant: approval.beneficiary.fullName, category: 'Transfer', amountPaise: approval.amountPaise, date: new Date().toISOString(), status: 'successful', reference: `HMS-${Date.now().toString().slice(-8)}`, note: 'Simulated transfer' };
    account = { ...account, balancePaise: account.balancePaise - approval.amountPaise };
    transactions = [transaction, ...transactions];
    const completed = { ...approval, status: 'authorized' as const };
    pendingApprovals.set(approvalId, completed);
    return { approval: completed, transaction, updatedBalancePaise: account.balancePaise };
  },
  cancelTransfer: async (approvalId: string): Promise<TransferApproval> => {
    const approval = pendingApprovals.get(approvalId);
    if (!approval) throw new Error('This approval is no longer available.');
    const cancelled = { ...approval, status: 'cancelled' as const };
    pendingApprovals.set(approvalId, cancelled);
    return cancelled;
  },
};

export const MockAssistantService = {
  sendMessage: async (message: string): Promise<AssistantResponse> => {
    const normalized = message.toLowerCase();
    const summary = await getSummary();
    if (normalized.includes('transfer') && normalized.includes('ravi')) {
      const amountMatch = normalized.match(/(?:₹|rs\.?\s?|inr\s?)([\d,]+)/i);
      const amountRupees = amountMatch ? Number(amountMatch[1].replace(/,/g, '')) : 75000;
      try {
        const approval = await TransferService.prepareTransfer(amountRupees * 100, 'Ravi');
        return { kind: 'transfer_approval', approval, text: `Here is your monthly snapshot: you have spent ${formatAmount(summary.totalPaise)} this month, including ${formatAmount(summary.byCategory.Dining)} on dining. Your current balance is ${formatAmount(approval.currentBalancePaise)}. I can prepare a simulated transfer of ${formatAmount(approval.amountPaise)} to Ravi Sharma, leaving ${formatAmount(approval.projectedBalancePaise)}. Please review and explicitly authorize it below.` };
      } catch (error) { return { kind: 'error', text: error instanceof Error ? error.message : 'I could not prepare that transfer.' }; }
    }
    if (normalized.includes('dining')) return { kind: 'analysis', text: `You spent ${formatAmount(summary.byCategory.Dining)} on dining this month across 2 transactions.` };
    if (normalized.includes('spending') || normalized.includes('month')) return { kind: 'analysis', text: `You have spent ${formatAmount(summary.totalPaise)} this month across ${summary.transactionCount} transactions.` };
    if (normalized.includes('recent') || normalized.includes('transaction')) return { kind: 'history', text: `You have ${summary.transactionCount} successful transactions this month. I can show the full activity list from the Activity tab.` };
    return { kind: 'normal', text: 'I can help with spending insights, recent transactions, or a simulated transfer to Ravi.' };
  },
};

const formatAmount = (paise: number): string => `₹${(paise / 100).toLocaleString('en-IN', { minimumFractionDigits: 2 })}`;
