import React, { createContext, useContext, useEffect, useMemo, useState } from 'react';
import { AccountSummary, ChatMessage, Transaction, TransferApproval, TransferResult } from './models';
import { apiMode } from './config';
import { AccountService as MockAccountService, TransactionService as MockTransactionService, TransferService as MockTransferService, MockAssistantService } from './services';
import { HttpAccountService, HttpTransactionService, HttpTransferService, HttpAssistantService } from './httpServices';
import { AccountServiceContract, AssistantServiceContract, TransactionServiceContract, TransferServiceContract } from './serviceContracts';

// Pick the active service implementations based on the configured API mode.
// Mock services remain available for isolated UI development; when backend
// mode is enabled the app talks to the FastAPI backend instead.
const AccountService: AccountServiceContract = apiMode === 'http' ? HttpAccountService : MockAccountService;
const TransactionService: TransactionServiceContract = apiMode === 'http' ? HttpTransactionService : MockTransactionService;
const TransferService: TransferServiceContract = apiMode === 'http' ? HttpTransferService : MockTransferService;
export const AssistantService: AssistantServiceContract = apiMode === 'http' ? HttpAssistantService : MockAssistantService;

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

export const useChat = () =>
  useState<ChatMessage[]>([
    { id: 'welcome', role: 'assistant', text: 'Good evening, Alex. I can help you understand your spending or prepare a simulated transfer.' },
  ]);
