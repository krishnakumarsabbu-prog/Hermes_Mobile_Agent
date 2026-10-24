export type TransactionCategory = 'Dining' | 'Shopping' | 'Utility' | 'Transfer';
export type TransactionStatus = 'successful' | 'pending' | 'cancelled' | 'failed';

export interface Transaction {
  id: string;
  merchant: string;
  category: TransactionCategory;
  amountPaise: number;
  date: string;
  status: TransactionStatus;
  reference: string;
  note?: string;
}

export interface AccountSummary {
  id: string;
  name: string;
  maskedNumber: string;
  balancePaise: number;
  currency: 'INR';
}

export interface Beneficiary {
  id: string;
  fullName: string;
  alias: string;
  dailyLimitPaise: number;
}

export interface SpendingSummary {
  totalPaise: number;
  byCategory: Record<'Dining' | 'Shopping' | 'Utility' | 'Transfer', number>;
  transactionCount: number;
}

export type ApprovalStatus = 'pending' | 'authorized' | 'cancelled' | 'declined' | 'failed' | 'expired';
export interface TransferApproval {
  approvalId: string;
  beneficiary: Beneficiary;
  amountPaise: number;
  sourceAccountId: string;
  currentBalancePaise: number;
  projectedBalancePaise: number;
  expiresAt: string;
  status: ApprovalStatus;
}

export interface TransferResult {
  approval: TransferApproval;
  transaction: Transaction;
  updatedBalancePaise: number;
}

export interface AssistantResponse {
  kind: 'normal' | 'analysis' | 'history' | 'transfer_approval' | 'transfer_complete' | 'cancelled' | 'error';
  text: string;
  approval?: TransferApproval;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  text: string;
  response?: AssistantResponse;
}
