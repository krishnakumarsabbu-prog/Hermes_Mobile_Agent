import React, { createContext, useContext, useEffect, useMemo, useState } from 'react';
import { AccountSummary, ChatMessage, Transaction, TransferApproval, TransferResult } from './models';
import { AccountService, TransactionService, TransferService } from './services';

interface AppContextValue {
  account: AccountSummary;
  transactions: Transaction[];
  approval?: TransferApproval;
  transferResult?: TransferResult;
  refresh: () => Promise<void>;
  setApproval: (approval?: TransferApproval) => void;
  setTransferResult: (result?: TransferResult) => void;
  authorize: () => Promise<TransferResult>;
  cancel: () => Promise<void>;
}
const AppContext = createContext<AppContextValue | null>(null);
export const AppProvider = ({ children }: React.PropsWithChildren) => {
  const [account, setAccount] = useState<AccountSummary>({ id: 'acct_01', name: 'Everyday Checking', maskedNumber: '•••• 0987', balancePaise: 10000000, currency: 'INR' });
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [approval, setApproval] = useState<TransferApproval>();
  const [transferResult, setTransferResult] = useState<TransferResult>();
  const refresh = async () => { const [nextAccount, nextTransactions] = await Promise.all([AccountService.getAccountSummary(), TransactionService.listTransactions()]); setAccount(nextAccount); setTransactions(nextTransactions); };
  useEffect(() => { void refresh(); }, []);
  const authorize = async () => { if (!approval) throw new Error('No transfer is waiting for approval.'); const result = await TransferService.authorizeTransfer(approval.approvalId); setTransferResult(result); setApproval(undefined); await refresh(); return result; };
  const cancel = async () => { if (approval) { await TransferService.cancelTransfer(approval.approvalId); setApproval(undefined); } };
  const value = useMemo(() => ({ account, transactions, approval, transferResult, refresh, setApproval, setTransferResult, authorize, cancel }), [account, transactions, approval, transferResult]);
  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
};
export const useApp = (): AppContextValue => { const value = useContext(AppContext); if (!value) throw new Error('AppProvider is missing.'); return value; };

export const useChat = () => useState<ChatMessage[]>([{ id: 'welcome', role: 'assistant', text: 'Good evening, Alex. I can help you understand your spending or prepare a simulated transfer.', }]);
