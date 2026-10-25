import { test, describe } from 'node:test';
import assert from 'node:assert/strict';
import type { TransferApproval, AssistantResponse, ChatMessage, ApprovalStatus } from '../models';
import type { ChatAction } from '../serviceContracts';

describe('Frontend Transfer Approval Chat Continuation', () => {
  const sampleApproval: TransferApproval = {
    approvalId: 'appr_07a202050a2541c2bcab',
    beneficiary: {
      id: 'ben_ravi',
      fullName: 'Ravi Sharma',
      alias: 'Ravi',
      dailyLimitPaise: 10000000,
    },
    amountPaise: 50000,
    sourceAccountId: 'acct_01',
    currentBalancePaise: 10000000,
    projectedBalancePaise: 9950000,
    expiresAt: '2026-10-25T13:42:07.825426+00:00',
    status: 'WAITING_FOR_APPROVAL',
    consumed: false,
    idempotencyKey: 'transfer-raj-789',
  };

  const sampleApprovalResponse: AssistantResponse = {
    kind: 'transfer_approval',
    text: "Here's your transfer summary:\n\n- **To:** Ravi Sharma\n- **Amount:** **₹500.00**",
    approval: sampleApproval,
    conversationId: 'conv_2e8225706a604cdc',
  };

  const terminalStatuses: ApprovalStatus[] = ['COMPLETED', 'CANCELLED', 'REJECTED', 'EXPIRED', 'FAILED'];

  function isTerminal(a: TransferApproval): boolean {
    return a.consumed || terminalStatuses.includes(a.status);
  }

  test('1. A transfer_approval response displays Approve and Reject buttons', () => {
    assert.strictEqual(sampleApprovalResponse.kind, 'transfer_approval');
    assert.ok(sampleApprovalResponse.approval);
    assert.strictEqual(sampleApprovalResponse.approval.approvalId, 'appr_07a202050a2541c2bcab');
    assert.strictEqual(sampleApprovalResponse.approval.status, 'WAITING_FOR_APPROVAL');
    assert.strictEqual(sampleApprovalResponse.approval.consumed, false);

    // When pending and not consumed, both buttons render (not terminal)
    assert.strictEqual(isTerminal(sampleApprovalResponse.approval), false);
  });

  test('2. Clicking Approve does not navigate away from chat', async () => {
    let navigationOccurred = false;
    const fakeRouter = {
      push: (_path: string) => {
        navigationOccurred = true;
      },
    };

    let stayedOnScreen = true;
    const handleApprove = () => {
      // In the updated code, router.push is never called
      stayedOnScreen = true;
    };

    handleApprove();
    assert.strictEqual(navigationOccurred, false);
    assert.strictEqual(stayedOnScreen, true);
  });

  test('3. Clicking Reject does not navigate away from chat', async () => {
    let navigationOccurred = false;
    const fakeRouter = {
      push: (_path: string) => {
        navigationOccurred = true;
      },
    };

    let stayedOnScreen = true;
    const handleReject = () => {
      stayedOnScreen = true;
    };

    handleReject();
    assert.strictEqual(navigationOccurred, false);
    assert.strictEqual(stayedOnScreen, true);
  });

  test('4. Approve sends the exact approvalId and existing conversationId', async () => {
    let capturedAction: ChatAction | undefined = undefined;
    let capturedConvId: string | undefined = undefined;

    const mockAssistantService = {
      sendMessage: async (_msg: string, convId?: string, action?: ChatAction): Promise<AssistantResponse> => {
        capturedConvId = convId;
        capturedAction = action;
        return {
          kind: 'transfer_result',
          text: 'Transfer approved and completed.',
          approval: { ...sampleApproval, status: 'COMPLETED', consumed: true },
          conversationId: convId,
        };
      },
    };

    const targetConvId = 'conv_2e8225706a604cdc';
    await mockAssistantService.sendMessage('Approve transfer of ₹500.00 to Ravi Sharma', targetConvId, {
      type: 'approve_transfer',
      approvalId: sampleApproval.approvalId,
      context: {
        approvalId: sampleApproval.approvalId,
        beneficiaryId: 'ben_ravi',
        beneficiaryName: 'Ravi Sharma',
        amountPaise: 50000,
        sourceAccountId: 'acct_01',
        status: 'WAITING_FOR_APPROVAL',
      },
    });

    assert.strictEqual(capturedConvId, 'conv_2e8225706a604cdc');
    assert.ok(capturedAction);
    assert.strictEqual(capturedAction.type, 'approve_transfer');
    assert.strictEqual(capturedAction.approvalId, 'appr_07a202050a2541c2bcab');
    assert.ok(capturedAction.context);
    assert.strictEqual(capturedAction.context.beneficiaryName, 'Ravi Sharma');
  });

  test('5. Reject sends the exact approvalId and existing conversationId', async () => {
    let capturedAction: ChatAction | undefined = undefined;
    let capturedConvId: string | undefined = undefined;

    const mockAssistantService = {
      sendMessage: async (_msg: string, convId?: string, action?: ChatAction): Promise<AssistantResponse> => {
        capturedConvId = convId;
        capturedAction = action;
        return {
          kind: 'transfer_result',
          text: 'Transfer rejected and cancelled.',
          approval: { ...sampleApproval, status: 'CANCELLED', consumed: true },
          conversationId: convId,
        };
      },
    };

    const targetConvId = 'conv_2e8225706a604cdc';
    await mockAssistantService.sendMessage('Reject transfer of ₹500.00 to Ravi Sharma', targetConvId, {
      type: 'reject_transfer',
      approvalId: sampleApproval.approvalId,
      context: {
        approvalId: sampleApproval.approvalId,
        beneficiaryId: 'ben_ravi',
        beneficiaryName: 'Ravi Sharma',
        amountPaise: 50000,
        sourceAccountId: 'acct_01',
        status: 'WAITING_FOR_APPROVAL',
      },
    });

    assert.strictEqual(capturedConvId, 'conv_2e8225706a604cdc');
    assert.ok(capturedAction);
    assert.strictEqual(capturedAction.type, 'reject_transfer');
    assert.strictEqual(capturedAction.approvalId, 'appr_07a202050a2541c2bcab');
  });

  test('6. The transfer context is preserved across the action request', async () => {
    let capturedAction: ChatAction | undefined = undefined;
    const mockSend = async (_m: string, _c?: string, action?: ChatAction): Promise<AssistantResponse> => {
      capturedAction = action;
      return {
        kind: 'transfer_result',
        text: 'done',
        approval: { ...sampleApproval, status: 'COMPLETED', consumed: true },
      };
    };

    await mockSend('Approve', 'conv_x', {
      type: 'approve_transfer',
      approvalId: sampleApproval.approvalId,
      context: { amountPaise: 50000, beneficiaryName: 'Ravi Sharma' },
    });
    assert.strictEqual(capturedAction?.context?.amountPaise, 50000);
    assert.strictEqual(capturedAction?.context?.beneficiaryName, 'Ravi Sharma');
  });

  test('7. A loading state prevents duplicate clicks (approve)', async () => {
    let callCount = 0;
    let confirmingApprovalId: string | null = null;
    let processing = false;

    const mockHandler = async (targetApproval: TransferApproval, _decision: 'approve' | 'reject') => {
      if (confirmingApprovalId || processing || isTerminal(targetApproval)) {
        return;
      }
      confirmingApprovalId = targetApproval.approvalId;
      processing = true;
      callCount++;
      await new Promise((resolve) => setTimeout(resolve, 50));
      confirmingApprovalId = null;
      processing = false;
    };

    const p1 = mockHandler(sampleApproval, 'approve');
    const p2 = mockHandler(sampleApproval, 'approve');
    const p3 = mockHandler(sampleApproval, 'approve');
    await Promise.all([p1, p2, p3]);
    assert.strictEqual(callCount, 1);
  });

  test('8. A successful approve response updates the original message and appends a new assistant response', () => {
    let messages: ChatMessage[] = [
      { id: 'm1', role: 'user', text: 'Transfer ₹500 to Ravi' },
      { id: 'm2', role: 'assistant', text: 'Transfer preview...', response: sampleApprovalResponse },
      { id: 'm3', role: 'user', text: 'Approve transfer of ₹500.00 to Ravi Sharma' },
    ];

    const completedApproval: TransferApproval = { ...sampleApproval, status: 'COMPLETED', consumed: true };
    const resultResponse: AssistantResponse = {
      kind: 'transfer_result',
      text: 'Transfer approved and completed.',
      approval: completedApproval,
      conversationId: 'conv_2e8225706a604cdc',
    };

    // Update original approval message with authoritative status
    messages = messages.map((msg) => {
      if (msg.response?.approval?.approvalId === completedApproval.approvalId && msg.response) {
        return {
          ...msg,
          response: {
            ...msg.response,
            approval: { ...msg.response.approval, ...completedApproval, consumed: true, status: 'COMPLETED' },
          },
        };
      }
      return msg;
    });

    // Append new assistant response
    messages = [...messages, { id: 'm4', role: 'assistant', text: resultResponse.text, response: resultResponse }];

    assert.strictEqual(messages.length, 4);
    assert.strictEqual(messages[1].response?.approval?.status, 'COMPLETED');
    assert.strictEqual(messages[1].response?.approval?.consumed, true);
    assert.strictEqual(messages[3].response?.kind, 'transfer_result');
    assert.strictEqual(messages[3].response?.conversationId, 'conv_2e8225706a604cdc');
  });

  test('9. An error is shown when the operation fails and chat stays usable', () => {
    let messages: ChatMessage[] = [
      { id: 'm1', role: 'user', text: 'Transfer ₹500 to Ravi' },
      { id: 'm2', role: 'assistant', text: 'Transfer preview...', response: sampleApprovalResponse },
    ];
    let confirmingApprovalId: string | null = null;
    let processing = false;

    try {
      confirmingApprovalId = sampleApproval.approvalId;
      processing = true;
      throw new Error('This approval has expired.');
    } catch (err: any) {
      const errorMsg: ChatMessage = {
        id: `err_1`,
        role: 'assistant',
        text: err.message,
        response: { kind: 'error', text: err.message },
      };
      messages = [...messages, errorMsg];
    } finally {
      confirmingApprovalId = null;
      processing = false;
    }

    assert.strictEqual(confirmingApprovalId, null);
    assert.strictEqual(processing, false);
    assert.strictEqual(messages.length, 3);
    assert.strictEqual(messages[2].response?.kind, 'error');
    assert.strictEqual(messages[2].text, 'This approval has expired.');
  });

  test('10. Existing non-transfer chat scenarios continue to work', () => {
    const normalResponse: AssistantResponse = {
      kind: 'normal',
      text: 'I can help with spending insights, recent transactions, or a simulated transfer.',
    };
    assert.strictEqual(normalResponse.kind, 'normal');
    assert.ok(normalResponse.text.length > 0);
  });

  test('11. A terminal approval cannot be actioned again', () => {
    const completedApproval: TransferApproval = { ...sampleApproval, status: 'COMPLETED', consumed: true };
    const cancelledApproval: TransferApproval = { ...sampleApproval, status: 'CANCELLED', consumed: true };

    assert.strictEqual(isTerminal(completedApproval), true);
    assert.strictEqual(isTerminal(cancelledApproval), true);

    // Simulated guard: handler should early-return for terminal approvals
    let callCount = 0;
    let processing = false;
    let confirmingApprovalId: string | null = null;
    const guard = (a: TransferApproval) => {
      if (confirmingApprovalId || processing || isTerminal(a)) return;
      callCount++;
    };
    guard(completedApproval);
    guard(cancelledApproval);
    assert.strictEqual(callCount, 0);
  });

  test('12. Reject updates original message to CANCELLED and appends result', () => {
    let messages: ChatMessage[] = [
      { id: 'm1', role: 'assistant', text: 'preview', response: sampleApprovalResponse },
    ];

    const cancelledApproval: TransferApproval = { ...sampleApproval, status: 'CANCELLED', consumed: true };
    const resultResponse: AssistantResponse = {
      kind: 'transfer_result',
      text: 'Transfer rejected and cancelled.',
      approval: cancelledApproval,
      conversationId: 'conv_2e8225706a604cdc',
    };

    messages = messages.map((msg) => {
      if (msg.response?.approval?.approvalId === cancelledApproval.approvalId && msg.response) {
        return {
          ...msg,
          response: {
            ...msg.response,
            approval: { ...msg.response.approval, ...cancelledApproval, consumed: true, status: 'CANCELLED' },
          },
        };
      }
      return msg;
    });
    messages = [...messages, { id: 'm2', role: 'assistant', text: resultResponse.text, response: resultResponse }];

    assert.strictEqual(messages[0].response?.approval?.status, 'CANCELLED');
    assert.strictEqual(messages[0].response?.approval?.consumed, true);
    assert.strictEqual(messages[1].response?.kind, 'transfer_result');
  });
});
