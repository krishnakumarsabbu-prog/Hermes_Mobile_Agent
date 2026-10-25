import { AccountSummary, AssistantResponse, Transaction, TransferApproval, TransferResult } from './models';

// Request/response models for the transfer approval lifecycle.
export interface PrepareTransferRequest {
  amountPaise: number;
  beneficiaryName: string;
}

export interface AuthorizeTransferRequest {
  approvalId: string;
}

export interface CancelTransferRequest {
  approvalId: string;
}

export interface TransferStatusResponse {
  approval: TransferApproval;
  transaction?: Transaction;
  updatedBalancePaise?: number;
}

// Service contracts. Mock implementations live in services.ts; Phase 2 will
// provide HTTP implementations that satisfy the same shapes, so screens never
// need to change.
export interface AccountServiceContract {
  getAccountSummary(): Promise<AccountSummary>;
  getAvailableBalance(): Promise<number>;
}

export interface TransactionServiceContract {
  listTransactions(): Promise<Transaction[]>;
  getTransaction(id: string): Promise<Transaction | undefined>;
}

export interface ChatAction {
  type: 'confirm_transfer' | 'approve_transfer' | 'reject_transfer';
  approvalId: string;
  context?: {
    approvalId?: string;
    beneficiaryId?: string;
    beneficiaryName?: string;
    amountPaise?: number;
    sourceAccountId?: string;
    status?: string;
  };
}

export interface AssistantServiceContract {
  sendMessage(message: string, conversationId?: string, action?: ChatAction): Promise<AssistantResponse>;
}

export interface TransferServiceContract {
  prepareTransfer(request: PrepareTransferRequest): Promise<TransferApproval>;
  authorizeTransfer(request: AuthorizeTransferRequest): Promise<TransferResult>;
  cancelTransfer(request: CancelTransferRequest): Promise<TransferApproval>;
  getTransferStatus(approvalId: string): Promise<TransferStatusResponse>;
}
