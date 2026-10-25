// HTTP service implementations that satisfy the existing service contracts.
// These talk to the FastAPI backend and convert API responses (integer paise,
// ISO timestamps) into the frontend model shapes screens already consume.

import { api, ApiError, isApiError } from './apiClient';
import {
  AccountServiceContract,
  AssistantServiceContract,
  TransactionServiceContract,
  TransferServiceContract,
} from './serviceContracts';
import {
  AccountSummary,
  AssistantResponse,
  Beneficiary,
  Transaction,
  TransferApproval,
  TransferResult,
  TransactionCategory,
  TransactionStatus,
} from './models';

// --- Mappers from API JSON shapes to frontend models ---

function mapTransaction(raw: Record<string, unknown>): Transaction {
  return {
    id: raw.id as string,
    merchant: raw.merchant as string,
    category: raw.category as TransactionCategory,
    amountPaise: raw.amountPaise as number,
    date: raw.date as string,
    status: raw.status as TransactionStatus,
    reference: raw.reference as string,
    note: raw.note as string | undefined,
  };
}

function mapBeneficiary(raw: Record<string, unknown>): Beneficiary {
  return {
    id: raw.id as string,
    fullName: raw.fullName as string,
    alias: raw.alias as string,
    dailyLimitPaise: raw.dailyLimitPaise as number,
  };
}

function mapApproval(raw: Record<string, unknown>): TransferApproval {
  return {
    approvalId: raw.approvalId as string,
    beneficiary: mapBeneficiary(raw.beneficiary as Record<string, unknown>),
    amountPaise: raw.amountPaise as number,
    sourceAccountId: raw.sourceAccountId as string,
    currentBalancePaise: raw.currentBalancePaise as number,
    projectedBalancePaise: raw.projectedBalancePaise as number,
    expiresAt: raw.expiresAt as string,
    status: raw.status as TransferApproval['status'],
    consumed: raw.consumed as boolean,
  };
}

// --- HTTP Account Service ---

export const HttpAccountService: AccountServiceContract = {
  getAccountSummary: async (): Promise<AccountSummary> => {
    const raw = await api.get<Record<string, unknown>>('/api/v1/account');
    return {
      id: raw.id as string,
      userId: raw.userId as string,
      name: raw.name as string,
      maskedNumber: raw.maskedNumber as string,
      balancePaise: raw.balancePaise as number,
      currency: raw.currency as 'INR',
    };
  },
  getAvailableBalance: async (): Promise<number> => {
    const raw = await api.get<Record<string, unknown>>('/api/v1/account/balance');
    return raw.balancePaise as number;
  },
};

// --- HTTP Transaction Service ---

export const HttpTransactionService: TransactionServiceContract = {
  listTransactions: async (): Promise<Transaction[]> => {
    const raw = await api.get<{ items: Record<string, unknown>[] }>('/api/v1/transactions?pageSize=100');
    return raw.items.map(mapTransaction);
  },
  getTransaction: async (id: string): Promise<Transaction | undefined> => {
    try {
      const raw = await api.get<Record<string, unknown>>(`/api/v1/transactions/${id}`);
      return mapTransaction(raw);
    } catch (err) {
      if (isApiError(err) && err.status === 404) return undefined;
      throw err;
    }
  },
};

// --- HTTP Assistant Service ---

export const HttpAssistantService: AssistantServiceContract = {
  sendMessage: async (message: string, conversationId?: string, action?: import('./serviceContracts').ChatAction): Promise<AssistantResponse> => {
    const raw = await api.post<Record<string, unknown>>('/api/v1/agent/chat', { message, conversationId, action });
    return {
      kind: raw.kind as AssistantResponse['kind'],
      text: raw.text as string,
      approval: raw.approval ? mapApproval(raw.approval as Record<string, unknown>) : undefined,
      summary: raw.summary as AssistantResponse['summary'] | undefined,
      conversationId: raw.conversationId as string | undefined,
    };
  },
};

// --- HTTP Transfer Service ---

export const HttpTransferService: TransferServiceContract = {
  prepareTransfer: async (request): Promise<TransferApproval> => {
    // The backend uses beneficiaryId + idempotencyKey; the frontend contract
    // uses beneficiaryName. We resolve the beneficiary first, then prepare.
    const beneficiaries = await api.get<{ items: Record<string, unknown>[] }>(
      `/api/v1/beneficiaries?search=${encodeURIComponent(request.beneficiaryName)}`,
    );
    if (!beneficiaries.items.length) {
      const err: ApiError = { code: 'BENEFICIARY_NOT_FOUND', message: 'We could not find that beneficiary.', status: 404 };
      throw err;
    }
    const ben = beneficiaries.items[0];
    const raw = await api.post<Record<string, unknown>>('/api/v1/transfers/prepare', {
      beneficiaryId: ben.id,
      amountPaise: request.amountPaise,
      currency: 'INR',
      idempotencyKey: `fe-prepare-${Date.now()}-${request.amountPaise}`,
    });
    return mapApproval(raw);
  },
  authorizeTransfer: async (request): Promise<TransferResult> => {
    const raw = await api.post<Record<string, unknown>>(
      `/api/v1/transfers/${request.approvalId}/authorize`,
      { idempotencyKey: `fe-authorize-${Date.now()}` },
    );
    return {
      approval: mapApproval(raw.approval as Record<string, unknown>),
      transaction: mapTransaction(raw.transaction as Record<string, unknown>),
      updatedBalancePaise: raw.updatedBalancePaise as number,
    };
  },
  cancelTransfer: async (request): Promise<TransferApproval> => {
    const raw = await api.post<Record<string, unknown>>(`/api/v1/transfers/${request.approvalId}/cancel`);
    return mapApproval(raw);
  },
  getTransferStatus: async (approvalId: string) => {
    const raw = await api.get<Record<string, unknown>>(`/api/v1/transfers/${approvalId}`);
    return {
      approval: mapApproval(raw.approval as Record<string, unknown>),
      transaction: raw.transaction ? mapTransaction(raw.transaction as Record<string, unknown>) : undefined,
      updatedBalancePaise: raw.updatedBalancePaise as number | undefined,
    };
  },
};
