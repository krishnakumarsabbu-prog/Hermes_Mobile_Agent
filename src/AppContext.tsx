import React, { createContext, useContext, useEffect, useMemo, useState } from 'react';
import { AccountSummary, ChatMessage, Transaction, TransferApproval, TransferResult } from './models';
import { apiConfig, apiMode } from './config';
import { AccountService as MockAccountService, TransactionService as MockTransactionService, TransferService as MockTransferService, MockAssistantService } from './services';
import { HttpAccountService, HttpTransactionService, HttpTransferService, HttpAssistantService } from './httpServices';
import { AccountServiceContract, AssistantServiceContract, TransactionServiceContract, TransferServiceContract } from './serviceContracts';

// Resilient service proxy: tries HTTP backend first, automatically falls back to Mock on network failure
function withFallback<T extends object>(httpService: T, mockService: T): T {
  const handler: ProxyHandler<T> = {
    get(target, prop, receiver) {
      const orig = Reflect.get(target, prop, receiver);
      if (typeof orig === 'function') {
        return async (...args: any[]) => {
          try {
            return await orig.apply(target, args);
          } catch (err: any) {
            if (
              err?.code === 'NETWORK_FAILURE' ||
              err?.code === 'NETWORK_TIMEOUT' ||
              (typeof err?.message === 'string' && err.message.toLowerCase().includes('network')) ||
              err?.status === 0
            ) {
              console.warn(
                `[API Fallback] Backend unreachable on ${String(prop)} (Base URL: ${apiConfig.baseUrl}), serving from mock. Reason: ${err?.message || err?.code || 'Network failure'}`
              );
              const mockFn = (mockService as any)[prop];
              if (typeof mockFn === 'function') {
                return await mockFn.apply(mockService, args);
              }
            }
            throw err;
          }
        };
      }
      return orig;
    },
  };
  return new Proxy(httpService, handler);
}

const AccountService: AccountServiceContract =
  apiMode === 'mock' ? MockAccountService : withFallback(HttpAccountService, MockAccountService);
const TransactionService: TransactionServiceContract =
  apiMode === 'mock' ? MockTransactionService : withFallback(HttpTransactionService, MockTransactionService);
const TransferService: TransferServiceContract =
  apiMode === 'mock' ? MockTransferService : withFallback(HttpTransferService, MockTransferService);
// The assistant never silently falls back to mock banking data in http mode:
// mock responses fabricate balances and transfers, which is unsafe for a
// banking assistant. Network failures surface as real errors with a retry.
export const AssistantService: AssistantServiceContract =
  apiMode === 'mock' ? MockAssistantService : HttpAssistantService;

interface AppContextValue {
  account: AccountSummary;
  transactions: Transaction[];
  approval?: TransferApproval;
  transferResult?: TransferResult;
  loading: boolean;
  error?: string;
  refresh: () => Promise<void>;
  setApproval: (approval?: TransferApproval) => void;
  setTransferResult: (result?: TransferResult) => void;
  authorize: () => Promise<TransferResult>;
  cancel: () => Promise<void>;
}

const AppContext = createContext<AppContextValue | null>(null);

export const AppProvider = ({ children }: React.PropsWithChildren) => {
  const [account, setAccount] = useState<AccountSummary>({ ...initialEmptyAccount() });
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [approval, setApproval] = useState<TransferApproval>();
  const [transferResult, setTransferResult] = useState<TransferResult>();
  const [authorizing, setAuthorizing] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>();

  const refresh = async () => {
    setLoading(true);
    setError(undefined);
    try {
      const [nextAccount, nextTransactions] = await Promise.all([
        AccountService.getAccountSummary(),
        TransactionService.listTransactions(),
      ]);
      setAccount(nextAccount);
      setTransactions(nextTransactions);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not load your account data. Please check your connection and try again.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void refresh();
  }, []);

  const authorize = async (): Promise<TransferResult> => {
    if (!approval) throw new Error('No transfer is waiting for approval.');
    if (authorizing) throw new Error('Authorization is already in progress.');
    setAuthorizing(true);
    try {
      let result: TransferResult;
      try {
        result = await TransferService.authorizeTransfer({ approvalId: approval.approvalId });
      } catch (error) {
        if (error instanceof Error && /already been used|expired|completed|cancelled|no longer pending/i.test(error.message)) {
          throw error;
        }
        try {
          const status = await TransferService.getTransferStatus(approval.approvalId);
          if (status.approval.status === 'COMPLETED' && status.transaction && status.updatedBalancePaise !== undefined) {
            result = { approval: status.approval, transaction: status.transaction, updatedBalancePaise: status.updatedBalancePaise };
          } else {
            throw new Error('The transfer outcome could not be confirmed. Please check the transfer status before retrying.');
          }
        } catch {
          throw error;
        }
      }
      setTransferResult(result);
      setApproval(undefined);
      await refresh();
      return result;
    } finally {
      setAuthorizing(false);
    }
  };

  const cancel = async () => {
    if (approval) {
      await TransferService.cancelTransfer({ approvalId: approval.approvalId });
      setApproval(undefined);
    }
  };

  const value = useMemo<AppContextValue>(
    () => ({ account, transactions, approval, transferResult, loading, error, refresh, setApproval, setTransferResult, authorize, cancel }),
    [account, transactions, approval, transferResult, authorizing, loading, error],
  );

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
};

const initialEmptyAccount = (): AccountSummary => ({ id: 'acct_01', userId: 'usr_01', name: 'Everyday Checking', maskedNumber: '•••• 0987', balancePaise: 10000000, currency: 'INR' });

export const useApp = (): AppContextValue => {
  const value = useContext(AppContext);
  if (!value) throw new Error('AppProvider is missing.');
  return value;
};

export const getGreetingMessage = (userName = 'Sabbu'): string => {
  const hour = new Date().getHours();
  const greetingTime = hour < 12 ? 'Good morning' : hour < 17 ? 'Good afternoon' : 'Good evening';
  return `${greetingTime}, ${userName}! How can I help you today?`;
};

export const useChat = () =>
  useState<ChatMessage[]>([
    { id: 'welcome', role: 'assistant', text: getGreetingMessage('Sabbu') },
  ]);

