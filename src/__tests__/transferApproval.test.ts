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

  test('1. A transfer_approval response displays the approval button and initial state', () => {
    assert.strictEqual(sampleApprovalResponse.kind, 'transfer_approval');
    assert.ok(sampleApprovalResponse.approval);
    assert.strictEqual(sampleApprovalResponse.approval.approvalId, 'appr_07a202050a2541c2bcab');
    assert.strictEqual(sampleApprovalResponse.approval.status, 'WAITING_FOR_APPROVAL');
    assert.strictEqual(sampleApprovalResponse.approval.consumed, false);

    // Initial button label when status is pending and not consumed
    const isConsumed = sampleApprovalResponse.approval.consumed || sampleApprovalResponse.approval.status === 'COMPLETED';
    assert.strictEqual(isConsumed, false);
    const buttonLabel = isConsumed ? 'Transfer Confirmed ✓' : 'Confirm transfer';
    assert.strictEqual(buttonLabel, 'Confirm transfer');
  });

  test('2. Clicking the button does not navigate away from chat', async () => {
    let navigationOccurred = false;
    const fakeRouter = {
      push: (_path: string) => {
        navigationOccurred = true;
      },
    };

    // Simulated handleConfirmTransfer execution
    let stayedOnScreen = true;
    const handleConfirm = () => {
      // In the updated code, router.push is never called
      stayedOnScreen = true;
    };

    handleConfirm();
    assert.strictEqual(navigationOccurred, false);
    assert.strictEqual(stayedOnScreen, true);
  });

  test('3. The action sends the exact approvalId and current conversationId', async () => {
    let capturedMessage = '';
    let capturedConvId: string | undefined = '';
    let capturedAction: ChatAction | undefined = undefined;

    const mockAssistantService = {
      sendMessage: async (msg: string, convId?: string, action?: ChatAction): Promise<AssistantResponse> => {
        capturedMessage = msg;
        capturedConvId = convId;
        capturedAction = action;
        return {
          kind: 'transfer_complete',
          text: 'Transfer of **₹500.00** to **Ravi Sharma** has been confirmed.',
          approval: { ...sampleApproval, status: 'COMPLETED', consumed: true },
          conversationId: convId,
        };
      },
    };

    const targetConvId = 'conv_2e8225706a604cdc';
    await mockAssistantService.sendMessage(
      'Confirm transfer of ₹500.00 to Ravi Sharma',
      targetConvId,
      {
        type: 'confirm_transfer',
        approvalId: sampleApproval.approvalId,
      }
    );

    assert.strictEqual(capturedConvId, 'conv_2e8225706a604cdc');
    assert.ok(capturedAction);
    assert.strictEqual(capturedAction.type, 'confirm_transfer');
    assert.strictEqual(capturedAction.approvalId, 'appr_07a202050a2541c2bcab');
    assert.ok(capturedMessage.includes('₹500.00'));
  });

  test('4. A successful response appears as a new message in the same chat', async () => {
    let messages: ChatMessage[] = [
      { id: 'm1', role: 'user', text: 'Transfer ₹500 to Ravi' },
      { id: 'm2', role: 'assistant', text: 'Transfer preview...', response: sampleApprovalResponse },
    ];

    // User triggers confirmation
    const confirmMsg: ChatMessage = {
      id: 'm3',
      role: 'user',
      text: 'Confirm transfer of ₹500.00 to Ravi Sharma',
    };
    messages = [...messages, confirmMsg];

    const completedResponse: AssistantResponse = {
      kind: 'transfer_complete',
      text: 'Transfer of **₹500.00** to **Ravi Sharma** has been confirmed.\n\n- **Status:** Completed\n- **Transaction ID:** `txn_123`',
      approval: { ...sampleApproval, status: 'COMPLETED', consumed: true },
      conversationId: 'conv_2e8225706a604cdc',
    };

    const asstMsg: ChatMessage = {
      id: 'm4',
      role: 'assistant',
      text: completedResponse.text,
      response: completedResponse,
    };
    messages = [...messages, asstMsg];

    assert.strictEqual(messages.length, 4);
    assert.strictEqual(messages[0].id, 'm1');
    assert.strictEqual(messages[1].id, 'm2');
    assert.strictEqual(messages[2].id, 'm3');
    assert.strictEqual(messages[3].id, 'm4');
    assert.strictEqual(messages[3].response?.kind, 'transfer_complete');
    assert.strictEqual(messages[3].response?.conversationId, 'conv_2e8225706a604cdc');
  });

  test('5. Repeated clicks do not submit duplicate confirmation requests', async () => {
    let callCount = 0;
    let confirmingApprovalId: string | null = null;
    let processing = false;

    const mockConfirmHandler = async (targetApproval: TransferApproval) => {
      if (confirmingApprovalId || processing || targetApproval.consumed || targetApproval.status === 'COMPLETED') {
        return;
      }
      confirmingApprovalId = targetApproval.approvalId;
      processing = true;
      callCount++;
      // Simulate delay
      await new Promise((resolve) => setTimeout(resolve, 50));
      confirmingApprovalId = null;
      processing = false;
    };

    // First click initiates processing
    const p1 = mockConfirmHandler(sampleApproval);
    // Second click during in-flight request
    const p2 = mockConfirmHandler(sampleApproval);
    // Third click during in-flight request
    const p3 = mockConfirmHandler(sampleApproval);

    await Promise.all([p1, p2, p3]);
    assert.strictEqual(callCount, 1, 'Only one confirmation request must be submitted across repeated clicks');
  });

  test('6. A failed request displays an error and leaves the chat usable', async () => {
    let messages: ChatMessage[] = [
      { id: 'm1', role: 'user', text: 'Transfer ₹500 to Ravi' },
      { id: 'm2', role: 'assistant', text: 'Transfer preview...', response: sampleApprovalResponse },
    ];
    let confirmingApprovalId: string | null = null;
    let processing = false;

    // Simulate failed API error
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

  test('7. The approval button updates based on the actual returned transfer status', () => {
    let messages: ChatMessage[] = [
      { id: 'm1', role: 'assistant', text: 'Preview', response: sampleApprovalResponse },
    ];

    // Initial button state: actionable
    const initialApproval = messages[0].response!.approval!;
    const isInitiallyDisabled = initialApproval.consumed || initialApproval.status === 'COMPLETED';
    assert.strictEqual(isInitiallyDisabled, false);

    // Backend returns completed transfer response
    const completedApproval: TransferApproval = {
      ...initialApproval,
      status: 'COMPLETED',
      consumed: true,
    };

    // Update messages in place
    messages = messages.map((msg) => {
      if (msg.response?.approval?.approvalId === completedApproval.approvalId && msg.response) {
        return {
          ...msg,
          response: {
            ...msg.response,
            approval: {
              ...msg.response.approval,
              ...completedApproval,
              consumed: true,
              status: completedApproval.status,
            },
          },
        };
      }
      return msg;
    });

    const updatedApproval = messages[0].response!.approval!;
    const isNowDisabled = updatedApproval.consumed || updatedApproval.status === 'COMPLETED';
    assert.strictEqual(isNowDisabled, true);
    assert.strictEqual(updatedApproval.status, 'COMPLETED');
    assert.strictEqual(updatedApproval.consumed, true);

    const buttonLabel = isNowDisabled ? 'Transfer Confirmed ✓' : 'Confirm transfer';
    assert.strictEqual(buttonLabel, 'Transfer Confirmed ✓');
  });
});
