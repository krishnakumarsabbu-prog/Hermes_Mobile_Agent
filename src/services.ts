import { AccountSummary, AssistantResponse, Beneficiary, Transaction, TransferApproval, TransferResult } from './models';
import { initialAccount, initialTransactions, ravi } from './mock';
import { summarizeTransactions } from './utils';
import { formatINR } from './utils';
import {
  AccountServiceContract,
  AssistantServiceContract,
  TransferServiceContract,
  TransactionServiceContract,
} from './serviceContracts';

let account = { ...initialAccount };
let transactions = [...initialTransactions];
const pendingApprovals = new Map<string, TransferApproval>();
const consumedApprovals = new Set<string>();

const isExpired = (approval: TransferApproval): boolean => Date.now() > new Date(approval.expiresAt).getTime();

export const AccountService: AccountServiceContract = {
  getAccountSummary: async (): Promise<AccountSummary> => ({ ...account }),
  getAvailableBalance: async (): Promise<number> => account.balancePaise,
};

export const TransactionService: TransactionServiceContract = {
  listTransactions: async (): Promise<Transaction[]> => [...transactions].sort((a, b) => +new Date(b.date) - +new Date(a.date)),
  getTransaction: async (id: string): Promise<Transaction | undefined> => transactions.find((item) => item.id === id),
};

export const getSummary = async () => summarizeTransactions(transactions);

const findBeneficiary = (value: string): Beneficiary | undefined => (value.toLowerCase().includes('ravi') ? ravi : undefined);

const validateTransferPreconditions = (amountPaise: number, beneficiaryName: string): Beneficiary => {
  const beneficiary = findBeneficiary(beneficiaryName);
  if (!beneficiary) throw new Error('We could not find that beneficiary.');
  if (!(amountPaise > 0)) throw new Error('The transfer amount must be positive.');
  if (amountPaise > account.balancePaise) throw new Error('This transfer exceeds your available balance.');
  if (amountPaise > beneficiary.dailyLimitPaise) throw new Error('This transfer exceeds the beneficiary daily limit.');
  return beneficiary;
};

export const TransferService: TransferServiceContract = {
  prepareTransfer: async (request): Promise<TransferApproval> => {
    const amountPaise = request.amountPaise;
    const beneficiary = validateTransferPreconditions(amountPaise, request.beneficiaryName);
    const approval: TransferApproval = {
      approvalId: `approval_${Date.now()}_${Math.floor(Math.random() * 1000)}`,
      beneficiary,
      amountPaise,
      sourceAccountId: account.id,
      currentBalancePaise: account.balancePaise,
      projectedBalancePaise: account.balancePaise - amountPaise,
      expiresAt: new Date(Date.now() + 5 * 60 * 1000).toISOString(),
      status: 'WAITING_FOR_APPROVAL',
      consumed: false,
    };
    pendingApprovals.set(approval.approvalId, approval);
    return approval;
  },

  authorizeTransfer: async (request): Promise<TransferResult> => {
    const { approvalId } = request;
    const approval = pendingApprovals.get(approvalId);

    if (!approval) throw new Error('This approval is no longer available.');
    if (consumedApprovals.has(approvalId)) throw new Error('This approval has already been used.');
    if (approval.status !== 'WAITING_FOR_APPROVAL') throw new Error(`This approval is ${approval.status.toLowerCase()} and cannot be authorized.`);
    if (isExpired(approval)) {
      const expired = { ...approval, status: 'EXPIRED' as const, consumed: true };
      pendingApprovals.set(approvalId, expired);
      consumedApprovals.add(approvalId);
      throw new Error('This approval has expired.');
    }

    // Revalidate every precondition at authorization time — the UI is not the authority.
    if (!(approval.amountPaise > 0)) throw new Error('The transfer amount must be positive.');
    if (approval.amountPaise > approval.beneficiary.dailyLimitPaise) throw new Error('This transfer exceeds the beneficiary daily limit.');
    if (approval.amountPaise > account.balancePaise) throw new Error('The available balance is no longer sufficient.');

    // Mark consumed *before* mutation so a duplicate call cannot double-debit.
    consumedApprovals.add(approvalId);

    const transaction: Transaction = {
      id: `txn_transfer_${Date.now()}`,
      merchant: approval.beneficiary.fullName,
      category: 'Transfer',
      amountPaise: approval.amountPaise,
      date: new Date().toISOString(),
      status: 'successful',
      reference: `HMS-${Date.now().toString().slice(-8)}-${Math.floor(Math.random() * 1000)}`,
      note: 'Simulated transfer',
    };

    account = { ...account, balancePaise: account.balancePaise - approval.amountPaise };
    transactions = [transaction, ...transactions];

    const completed = { ...approval, status: 'COMPLETED' as const, consumed: true };
    pendingApprovals.set(approvalId, completed);

    return { approval: completed, transaction, updatedBalancePaise: account.balancePaise };
  },

  cancelTransfer: async (request): Promise<TransferApproval> => {
    const { approvalId } = request;
    const approval = pendingApprovals.get(approvalId);
    if (!approval) throw new Error('This approval is no longer available.');
    if (consumedApprovals.has(approvalId)) throw new Error('This approval has already been used.');
    const cancelled = { ...approval, status: 'CANCELLED' as const, consumed: true };
    pendingApprovals.set(approvalId, cancelled);
    consumedApprovals.add(approvalId);
    return cancelled;
  },

  getTransferStatus: async (approvalId: string) => {
    const approval = pendingApprovals.get(approvalId);
    if (!approval) throw new Error('This approval is no longer available.');
    // Auto-expire if past TTL and still pending.
    if (approval.status === 'WAITING_FOR_APPROVAL' && isExpired(approval)) {
      const expired = { ...approval, status: 'EXPIRED' as const, consumed: true };
      pendingApprovals.set(approvalId, expired);
      consumedApprovals.add(approvalId);
      return { approval: expired };
    }
    const txn = approval.status === 'COMPLETED' ? transactions.find((t) => t.note === 'Simulated transfer' && t.amountPaise === approval.amountPaise) : undefined;
    return {
      approval,
      transaction: txn,
      updatedBalancePaise: approval.status === 'COMPLETED' ? account.balancePaise : undefined,
    };
  },
};

export const MockAssistantService: AssistantServiceContract = {
  sendMessage: async (message: string): Promise<AssistantResponse> => {
    const normalized = message.toLowerCase();
    const summary = await getSummary();

    if (normalized.includes('transfer') && normalized.includes('ravi')) {
      const amountMatch = normalized.match(/(?:₹|rs\.?\s?|inr\s?)([\d,]+)/i);
      const amountRupees = amountMatch ? Number(amountMatch[1].replace(/,/g, '')) : 75000;
      try {
        const balance = await AccountService.getAvailableBalance();
        const approval = await TransferService.prepareTransfer({ amountPaise: amountRupees * 100, beneficiaryName: 'Ravi' });
        return {
          kind: 'transfer_approval',
          approval,
          summary: {
            spendingPaise: summary.totalPaise,
            diningPaise: summary.byCategory.Dining,
            balancePaise: balance,
            proposedTransferPaise: approval.amountPaise,
            projectedBalancePaise: approval.projectedBalancePaise,
          },
          text: `Here is your monthly snapshot: you have spent ${formatINR(summary.totalPaise)} this month, including ${formatINR(summary.byCategory.Dining)} on dining. Your current balance is ${formatINR(approval.currentBalancePaise)}. I can prepare a simulated transfer of ${formatINR(approval.amountPaise)} to Ravi Sharma, leaving ${formatINR(approval.projectedBalancePaise)}. Please review and explicitly authorize it below.`,
        };
      } catch (error) {
        return { kind: 'error', text: error instanceof Error ? error.message : 'I could not prepare that transfer.' };
      }
    }

    if (normalized.includes('dining'))
      return { kind: 'analysis', text: `You spent ${formatINR(summary.byCategory.Dining)} on dining this month across 2 transactions.` };

    if (normalized.includes('spending') || normalized.includes('month'))
      return { kind: 'analysis', text: `You have spent ${formatINR(summary.totalPaise)} this month across ${summary.transactionCount} transactions.` };

    if (normalized.includes('recent') || normalized.includes('transaction'))
      return { kind: 'history', text: `You have ${summary.transactionCount} successful transactions this month. I can show the full activity list from the Activity tab.` };

    return { kind: 'normal', text: 'I can help with spending insights, recent transactions, or a simulated transfer to Ravi.' };
  },
};
