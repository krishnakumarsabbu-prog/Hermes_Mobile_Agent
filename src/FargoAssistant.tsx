import React, { useRef, useState, useEffect } from 'react';
import {
  ActivityIndicator,
  Animated,
  Dimensions,
  Easing,
  Keyboard,
  KeyboardAvoidingView,
  Modal,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';
import { router } from 'expo-router';
import {
  ArrowLeft,
  ArrowUp,
  ChevronRight,
  CreditCard,
  Mic,
  MicOff,
  RotateCcw,
  Sparkles,
  TrendingUp,
  Volume2,
  VolumeX,
  Wallet,
  X,
  Zap,
} from 'lucide-react-native';
import { useApp, useChat, AssistantService, getGreetingMessage } from './AppContext';
import { ChatMessage, TransferApproval, ApprovalStatus } from './models';
import { isApiError } from './apiClient';
import { ChatMarkdown } from './ChatMarkdown';

interface FargoAssistantProps {
  onClose?: () => void;
  isModal?: boolean;
}

export function FargoAssistant({ onClose, isModal = false }: FargoAssistantProps) {
  const [messages, setMessages] = useChat();
  const [text, setText] = useState('');
  const [processing, setProcessing] = useState(false);
  const [conversationId, setConversationId] = useState<string | undefined>(undefined);
  const [lastError, setLastError] = useState<string | null>(null);
  const [lastFailedPrompt, setLastFailedPrompt] = useState<string | null>(null);
  const [isListening, setIsListening] = useState(false);
  const [speakingMessageId, setSpeakingMessageId] = useState<string | null>(null);
  const [voiceModeOpen, setVoiceModeOpen] = useState(false);
  const [voiceModeStatus, setVoiceModeStatus] = useState<'listening' | 'thinking' | 'speaking'>('listening');
  const [voiceModeTranscript, setVoiceModeTranscript] = useState('');
  const [confirmingApprovalId, setConfirmingApprovalId] = useState<string | null>(null);

  const scroll = useRef<any>(null);
  const { setApproval } = useApp();

  // Waveform animations for Voice Mode and Mic recording
  const waveAnim1 = useRef(new Animated.Value(0.3)).current;
  const waveAnim2 = useRef(new Animated.Value(0.5)).current;
  const waveAnim3 = useRef(new Animated.Value(0.2)).current;
  const waveAnim4 = useRef(new Animated.Value(0.6)).current;
  const orbScale = useRef(new Animated.Value(1)).current;

  // Animate sound waves when listening or speaking
  useEffect(() => {
    let loop: Animated.CompositeAnimation | null = null;
    if (isListening || speakingMessageId !== null || voiceModeOpen) {
      loop = Animated.loop(
        Animated.parallel([
          Animated.sequence([
            Animated.timing(waveAnim1, { toValue: 1, duration: 400, useNativeDriver: true }),
            Animated.timing(waveAnim1, { toValue: 0.2, duration: 400, useNativeDriver: true }),
          ]),
          Animated.sequence([
            Animated.timing(waveAnim2, { toValue: 0.9, duration: 320, useNativeDriver: true }),
            Animated.timing(waveAnim2, { toValue: 0.3, duration: 320, useNativeDriver: true }),
          ]),
          Animated.sequence([
            Animated.timing(waveAnim3, { toValue: 1, duration: 500, useNativeDriver: true }),
            Animated.timing(waveAnim3, { toValue: 0.25, duration: 500, useNativeDriver: true }),
          ]),
          Animated.sequence([
            Animated.timing(waveAnim4, { toValue: 0.85, duration: 380, useNativeDriver: true }),
            Animated.timing(waveAnim4, { toValue: 0.35, duration: 380, useNativeDriver: true }),
          ]),
          Animated.sequence([
            Animated.timing(orbScale, { toValue: 1.15, duration: 800, easing: Easing.inOut(Easing.ease), useNativeDriver: true }),
            Animated.timing(orbScale, { toValue: 0.95, duration: 800, easing: Easing.inOut(Easing.ease), useNativeDriver: true }),
          ]),
        ])
      );
      loop.start();
    } else {
      waveAnim1.setValue(0.3);
      waveAnim2.setValue(0.5);
      waveAnim3.setValue(0.2);
      waveAnim4.setValue(0.6);
      orbScale.setValue(1);
    }
    return () => loop?.stop();
  }, [isListening, speakingMessageId, voiceModeOpen]);

  const scrollToBottom = (animated = true) => {
    scroll.current?.scrollToEnd({ animated });
  };

  // Auto-scroll whenever messages list or processing state changes
  useEffect(() => {
    const t1 = setTimeout(() => scrollToBottom(true), 50);
    const t2 = setTimeout(() => scrollToBottom(true), 200);
    return () => {
      clearTimeout(t1);
      clearTimeout(t2);
    };
  }, [messages.length, processing]);

  // Auto-scroll when software keyboard slides up on mobile
  useEffect(() => {
    const eventName = Platform.OS === 'ios' ? 'keyboardWillShow' : 'keyboardDidShow';
    const sub = Keyboard.addListener(eventName, () => {
      setTimeout(() => scrollToBottom(true), 80);
    });
    return () => sub.remove();
  }, []);

  // Send message handler
  const send = async (value = text) => {
    const message = value.trim();
    if (!message || processing) return;
    setText('');
    setIsListening(false);
    setLastError(null);
    setLastFailedPrompt(null);
    setVoiceModeStatus('thinking');

    setMessages((current) => [
      ...current,
      { id: `u_${Date.now()}`, role: 'user', text: message },
    ]);
    setProcessing(true);
    setTimeout(() => scrollToBottom(true), 50);
    setTimeout(() => scrollToBottom(true), 150);

    try {
      const response = await AssistantService.sendMessage(message, conversationId);

      if (response.conversationId) {
        setConversationId(response.conversationId);
      }

      const assistantMessage: ChatMessage = {
        id: `a_${Date.now()}`,
        role: 'assistant',
        text: response.text,
        response,
      };
      setMessages((current) => [...current, assistantMessage]);
      setTimeout(() => scrollToBottom(true), 60);
      setTimeout(() => scrollToBottom(true), 180);

      if (response.approval) {
        setApproval(response.approval);
      }

      // If in Voice Mode, speak response aloud
      if (voiceModeOpen || isListening) {
        setVoiceModeStatus('speaking');
        setVoiceModeTranscript(response.text);
        speakText(response.text, assistantMessage.id);
      }
    } catch (err) {
      const friendly = isApiError(err)
        ? err.message
        : 'I could not reach the assistant right now. Please check your connection and try again.';
      setLastError(friendly);
      setLastFailedPrompt(message);
      setMessages((current) => [
        ...current,
        {
          id: `err_${Date.now()}`,
          role: 'assistant',
          text: friendly,
          response: { kind: 'error', text: friendly },
        },
      ]);
    } finally {
      setProcessing(false);
      setTimeout(() => scrollToBottom(true), 80);
      setTimeout(() => scrollToBottom(true), 250);
    }
  };

  // Handle in-chat transfer confirmation without navigating away
  const handleConfirmTransfer = async (targetApproval: TransferApproval) => {
    if (confirmingApprovalId || processing || targetApproval.consumed || targetApproval.status === 'COMPLETED') {
      return;
    }
    setConfirmingApprovalId(targetApproval.approvalId);
    setProcessing(true);
    setLastError(null);

    const amountFormatted = `₹${(targetApproval.amountPaise / 100).toFixed(2)}`;
    const confirmMessage = `Confirm transfer of ${amountFormatted} to ${targetApproval.beneficiary.fullName}`;

    // Add user confirmation message into current conversation
    setMessages((current) => [
      ...current,
      { id: `u_${Date.now()}`, role: 'user', text: confirmMessage },
    ]);
    setTimeout(() => scrollToBottom(true), 50);

    try {
      const response = await AssistantService.sendMessage(
        confirmMessage,
        conversationId,
        {
          type: 'confirm_transfer',
          approvalId: targetApproval.approvalId,
        }
      );

      if (response.conversationId) {
        setConversationId(response.conversationId);
      }

      // Mark the original approval as completed and consumed in the messages list
      setMessages((current) =>
        current.map((msg): ChatMessage => {
          if (msg.response?.approval?.approvalId === targetApproval.approvalId && msg.response) {
            return {
              ...msg,
              response: {
                ...msg.response,
                approval: {
                  ...msg.response.approval,
                  ...(response.approval || {}),
                  consumed: true,
                  status: (response.approval?.status || 'COMPLETED') as ApprovalStatus,
                },
              },
            };
          }
          return msg;
        })
      );

      if (response.approval) {
        setApproval(response.approval);
      }

      const assistantMessage: ChatMessage = {
        id: `a_${Date.now()}`,
        role: 'assistant',
        text: response.text,
        response,
      };
      setMessages((current) => [...current, assistantMessage]);
      setTimeout(() => scrollToBottom(true), 60);

      // If in Voice Mode, speak response aloud
      if (voiceModeOpen || isListening) {
        setVoiceModeStatus('speaking');
        setVoiceModeTranscript(response.text);
        speakText(response.text, assistantMessage.id);
      }
    } catch (err) {
      const friendly = isApiError(err)
        ? err.message
        : 'I could not confirm the transfer right now. Please try again.';
      setLastError(friendly);
      setMessages((current) => [
        ...current,
        {
          id: `err_${Date.now()}`,
          role: 'assistant',
          text: friendly,
          response: { kind: 'error', text: friendly },
        },
      ]);
    } finally {
      setConfirmingApprovalId(null);
      setProcessing(false);
      setTimeout(() => scrollToBottom(true), 80);
      setTimeout(() => scrollToBottom(true), 250);
    }
  };

  const retryLast = () => {
    if (lastFailedPrompt && !processing) {
      void send(lastFailedPrompt);
    }
  };

  // ─── Speech Recognition (Voice Input) ──────────────────────────────────
  const startListening = () => {
    if (isListening) {
      setIsListening(false);
      return;
    }

    if (Platform.OS === 'web' && typeof window !== 'undefined') {
      const SpeechRecognition =
        (window as any).SpeechRecognition ||
        (window as any).webkitSpeechRecognition;

      if (SpeechRecognition) {
        try {
          const recognition = new SpeechRecognition();
          recognition.lang = 'en-US';
          recognition.interimResults = true;
          recognition.continuous = false;
          recognition.maxAlternatives = 1;

          recognition.onstart = () => {
            setIsListening(true);
            setVoiceModeStatus('listening');
          };

          recognition.onresult = (event: any) => {
            const transcript = event.results[0][0].transcript;
            setText(transcript);
            if (voiceModeOpen) {
              setVoiceModeTranscript(transcript);
            }
          };

          recognition.onerror = (e: any) => {
            console.warn('[Speech Recognition] Error/permission:', e?.error);
            setIsListening(false);
            // Simulated voice command fallback if permission denied
            if (!text.trim()) {
              setText('What is my Everyday Checking balance?');
              send('What is my Everyday Checking balance?');
            }
          };

          recognition.onend = () => {
            setIsListening(false);
            if (text.trim()) {
              send(text);
            }
          };

          recognition.start();
          return;
        } catch (e) {
          console.warn('SpeechRecognition start error:', e);
        }
      }
    }

    // Mobile / Unsupported platform fallback: auto-simulate voice query
    setIsListening(true);
    setVoiceModeStatus('listening');
    setTimeout(() => {
      const simulatedVoiceQueries = [
        'What is my Everyday Checking balance?',
        'How much did I spend on dining this month?',
        'Transfer $150 to Sarah Jenkins',
      ];
      const randomQuery = simulatedVoiceQueries[Math.floor(Math.random() * simulatedVoiceQueries.length)];
      setText(randomQuery);
      if (voiceModeOpen) {
        setVoiceModeTranscript(randomQuery);
      }
      setTimeout(() => {
        setIsListening(false);
        send(randomQuery);
      }, 1000);
    }, 1200);
  };

  // ─── Text-to-Speech (Voice Output) ─────────────────────────────────────
  const speakText = (content: string, messageId: string) => {
    if (speakingMessageId === messageId) {
      if (Platform.OS === 'web' && typeof window !== 'undefined' && window.speechSynthesis) {
        window.speechSynthesis.cancel();
      }
      setSpeakingMessageId(null);
      setVoiceModeStatus('listening');
      return;
    }

    // Clean markdown/symbols for natural speech
    const speechClean = content.replace(/[*_#`~]/g, '');

    if (Platform.OS === 'web' && typeof window !== 'undefined' && window.speechSynthesis) {
      try {
        window.speechSynthesis.cancel();
        const utterance = new SpeechSynthesisUtterance(speechClean);
        utterance.rate = 1.0;
        utterance.pitch = 1.02;

        utterance.onstart = () => {
          setSpeakingMessageId(messageId);
        };
        utterance.onend = () => {
          setSpeakingMessageId(null);
          setVoiceModeStatus('listening');
        };
        utterance.onerror = () => {
          setSpeakingMessageId(null);
          setVoiceModeStatus('listening');
        };

        window.speechSynthesis.speak(utterance);
        return;
      } catch (err) {
        console.warn('[TTS] Synthesis error:', err);
      }
    }

    // Visual speech indicator fallback
    setSpeakingMessageId(messageId);
    setTimeout(() => {
      setSpeakingMessageId(null);
      setVoiceModeStatus('listening');
    }, 3500);
  };

  const handleResetChat = () => {
    setConversationId(undefined);
    setLastError(null);
    setLastFailedPrompt(null);
    setMessages([
      {
        id: 'welcome',
        role: 'assistant',
        text: getGreetingMessage(),
      },
    ]);
  };

  const handleClose = () => {
    if (onClose) {
      onClose();
    } else {
      router.back();
    }
  };

  return (
    <KeyboardAvoidingView
      style={styles.page}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      keyboardVerticalOffset={Platform.OS === 'ios' ? 44 : 0}
    >
      {/* ─── Top Header ─── */}
      <View style={styles.header}>
        <View style={styles.headerLeft}>
          <Pressable onPress={handleClose} style={styles.backBtn} accessibilityLabel="Close assistant">
            {isModal ? <X size={22} color="#111111" /> : <ArrowLeft size={20} color="#111111" />}
          </Pressable>

          <View style={styles.fargoAvatarWrapper}>
            <View style={styles.fargoAvatarBox}>
              <Text style={styles.fargoAvatarLetter}>F</Text>
            </View>
            <View style={styles.onlineStatusDot} />
          </View>

          <View style={styles.headerTitleGroup}>
            <View style={styles.titleRow}>
              <Text style={styles.titleText}>Fargo® Assistant</Text>
              <View style={styles.aiPill}>
                <Sparkles size={10} color="#582C83" />
                <Text style={styles.aiPillText}>AI Voice</Text>
              </View>
            </View>
            <Text style={styles.subtitleText}>Online · Wells Fargo Banking AI</Text>
          </View>
        </View>

        {/* Right Action: Voice Mode Button & Reset */}
        <View style={styles.headerRight}>
          <Pressable
            onPress={() => {
              setVoiceModeOpen(true);
              startListening();
            }}
            style={({ pressed }) => [
              styles.voiceModeHeaderBtn,
              pressed && { transform: [{ scale: 0.95 }] },
            ]}
          >
            <Mic size={15} color="#FFFFFF" />
            <Text style={styles.voiceModeHeaderText}>Voice</Text>
          </Pressable>

          <Pressable onPress={handleResetChat} style={styles.resetBtn}>
            <RotateCcw size={17} color="#666666" />
          </Pressable>
        </View>
      </View>

      {/* ─── Listening Waveform Banner (Active when recording) ─── */}
      {isListening && (
        <View style={styles.listeningBanner}>
          <View style={styles.waveBarContainer}>
            <Animated.View style={[styles.waveBar, { transform: [{ scaleY: waveAnim1 }] }]} />
            <Animated.View style={[styles.waveBar, { transform: [{ scaleY: waveAnim2 }] }]} />
            <Animated.View style={[styles.waveBar, { transform: [{ scaleY: waveAnim3 }] }]} />
            <Animated.View style={[styles.waveBar, { transform: [{ scaleY: waveAnim4 }] }]} />
            <Animated.View style={[styles.waveBar, { transform: [{ scaleY: waveAnim2 }] }]} />
            <Animated.View style={[styles.waveBar, { transform: [{ scaleY: waveAnim1 }] }]} />
          </View>
          <Text style={styles.listeningText}>Listening... speak now or tap mic to send</Text>
          <Pressable onPress={() => setIsListening(false)} style={styles.stopMicBtn}>
            <MicOff size={16} color="#DC2626" />
          </Pressable>
        </View>
      )}

      {/* ─── Message List ─── */}
      <ScrollView
        ref={scroll}
        contentContainerStyle={styles.messagesContainer}
        showsVerticalScrollIndicator={false}
        keyboardShouldPersistTaps="handled"
        onContentSizeChange={() => scrollToBottom(true)}
        onLayout={() => scrollToBottom(false)}
      >
        {messages.map((message) => {
          const isUser = message.role === 'user';
          const isSpeakingThis = speakingMessageId === message.id;
          const approval = message.response?.approval;

          return (
            <View
              key={message.id}
              style={[
                styles.messageRow,
                isUser ? styles.messageRowUser : styles.messageRowAssistant,
              ]}
            >
              {!isUser && (
                <View style={styles.assistantAvatar}>
                  <Text style={styles.assistantAvatarLetter}>F</Text>
                </View>
              )}

              <View
                style={[
                  styles.bubbleContainer,
                  isUser ? styles.userBubble : styles.assistantBubble,
                ]}
              >
                {/* Header of Assistant Bubble with TTS Speaker */}
                {!isUser && (
                  <View style={styles.assistantBubbleHeader}>
                    <Text style={styles.assistantName}>Fargo Virtual Assistant</Text>
                    <Pressable
                      onPress={() => speakText(message.text, message.id)}
                      style={styles.speakerBtn}
                    >
                      {isSpeakingThis ? (
                        <View style={styles.speakingIndicatorRow}>
                          <Animated.View style={[styles.miniSoundDot, { transform: [{ scaleY: waveAnim1 }] }]} />
                          <Animated.View style={[styles.miniSoundDot, { transform: [{ scaleY: waveAnim2 }] }]} />
                          <Animated.View style={[styles.miniSoundDot, { transform: [{ scaleY: waveAnim3 }] }]} />
                          <VolumeX size={15} color="#582C83" />
                        </View>
                      ) : (
                        <Volume2 size={16} color="#777777" />
                      )}
                    </Pressable>
                  </View>
                )}

                {/* Message Text with Markdown formatting */}
                <ChatMarkdown content={message.text} isUser={isUser} />

                {/* ─── Rich Embedded Widget: Transfer Approval Card ─── */}
                {approval && !isUser && (
                  <View style={styles.richTransferCard}>
                    <View style={styles.transferCardHeader}>
                      <Zap size={16} color="#582C83" />
                      <Text style={styles.transferCardTag}>TRANSFER PREVIEW</Text>
                    </View>

                    <Text style={styles.transferAmountLarge}>
                      ₹{(approval.amountPaise / 100).toFixed(2)}
                    </Text>

                    <View style={styles.transferDetailsBox}>
                      <View style={styles.transferRow}>
                        <Text style={styles.transferRowLabel}>To:</Text>
                        <Text style={styles.transferRowVal}>
                          {approval.beneficiary.fullName}
                        </Text>
                      </View>
                      <View style={styles.transferRow}>
                        <Text style={styles.transferRowLabel}>From:</Text>
                        <Text style={styles.transferRowVal}>
                          Everyday Checking •••• 0987
                        </Text>
                      </View>
                      <View style={styles.transferRow}>
                        <Text style={styles.transferRowLabel}>Transfer Fee:</Text>
                        <Text style={[styles.transferRowVal, { color: '#059669', fontWeight: '700' }]}>
                          ₹0.00 (Free)
                        </Text>
                      </View>
                    </View>

                    <Pressable
                      testID={`confirm-transfer-btn-${approval.approvalId}`}
                      disabled={confirmingApprovalId === approval.approvalId || processing || approval.consumed || approval.status === 'COMPLETED'}
                      style={[
                        styles.authorizeTransferBtn,
                        (confirmingApprovalId === approval.approvalId || approval.consumed || approval.status === 'COMPLETED') && styles.authorizeBtnDisabled,
                      ]}
                      onPress={() => void handleConfirmTransfer(approval)}
                    >
                      {confirmingApprovalId === approval.approvalId ? (
                        <View style={styles.btnLoadingRow}>
                          <ActivityIndicator size="small" color="#FFFFFF" />
                          <Text style={styles.authorizeBtnText}>Processing confirmation…</Text>
                        </View>
                      ) : approval.consumed || approval.status === 'COMPLETED' ? (
                        <View style={styles.btnLoadingRow}>
                          <Text style={styles.authorizeBtnText}>Transfer Confirmed ✓</Text>
                        </View>
                      ) : (
                        <View style={styles.btnLoadingRow}>
                          <Text style={styles.authorizeBtnText}>Confirm transfer</Text>
                          <ChevronRight size={16} color="#FFFFFF" />
                        </View>
                      )}
                    </Pressable>
                  </View>
                )}


              </View>
            </View>
          );
        })}

        {/* Typing indicator */}
        {processing && (
          <View style={[styles.messageRow, styles.messageRowAssistant]}>
            <View style={styles.assistantAvatar}>
              <Text style={styles.assistantAvatarLetter}>F</Text>
            </View>
            <View style={[styles.bubbleContainer, styles.assistantBubble, styles.typingBubble]}>
              <ActivityIndicator color="#582C83" size="small" />
              <Text style={styles.typingText}>Fargo is thinking...</Text>
            </View>
          </View>
        )}

        {/* Retry banner when the last request failed */}
        {lastError && !processing && lastFailedPrompt && (
          <View style={styles.retryBanner}>
            <Text style={styles.retryText}>{lastError}</Text>
            <Pressable onPress={retryLast} style={styles.retryBtn}>
              <RotateCcw size={14} color="#582C83" />
              <Text style={styles.retryBtnText}>Retry</Text>
            </Pressable>
          </View>
        )}
      </ScrollView>

      {/* ─── Quick Suggestion Chips Carousel ─── */}
      <View style={styles.chipsRow}>
        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.chipsScroll}>
          {[
            { label: '💰 Check checking balance', prompt: 'What is my Everyday Checking balance?' },
            { label: '💸 Transfer $150 to Sarah', prompt: 'Transfer $150 to Sarah Jenkins' },
            { label: '🍽 How much on dining?', prompt: 'How much did I spend on dining this month?' },
            { label: '📋 Recent transactions', prompt: 'Show my recent transactions' },
            { label: '🔒 Lock my card', prompt: 'How do I lock my debit card?' },
          ].map((item) => (
            <Pressable
              key={item.label}
              onPress={() => void send(item.prompt)}
              style={({ pressed }) => [
                styles.chipBtn,
                pressed && styles.chipBtnPressed,
              ]}
            >
              <Text style={styles.chipText}>{item.label}</Text>
            </Pressable>
          ))}
        </ScrollView>
      </View>

      {/* ─── Bottom Composer with Mic & Send ─── */}
      <View style={styles.composerBar}>
        <TextInput
          value={text}
          onChangeText={setText}
          onFocus={() => {
            setTimeout(() => scrollToBottom(true), 120);
          }}
          onSubmitEditing={() => void send()}
          placeholder="Message Fargo or tap mic..."
          placeholderTextColor="#999999"
          style={styles.composerInput}
        />

        {/* Microphone Button */}
        <Pressable
          onPress={startListening}
          style={({ pressed }) => [
            styles.micBtn,
            isListening && styles.micBtnActive,
            pressed && { transform: [{ scale: 0.92 }] },
          ]}
          accessibilityLabel="Voice dictation"
        >
          <Mic size={20} color={isListening ? '#FFFFFF' : '#582C83'} />
        </Pressable>

        {/* Send Button */}
        <Pressable
          onPress={() => void send()}
          disabled={!text.trim() || processing}
          style={({ pressed }) => [
            styles.sendBtn,
            (!text.trim() || processing) && styles.sendBtnDisabled,
            pressed && { transform: [{ scale: 0.92 }] },
          ]}
        >
          <ArrowUp size={18} color="#FFFFFF" strokeWidth={2.5} />
        </Pressable>
      </View>

      {/* ─── Dedicated Immersive Voice Mode Modal ─── */}
      <Modal
        visible={voiceModeOpen}
        transparent
        animationType="fade"
        onRequestClose={() => setVoiceModeOpen(false)}
      >
        <View style={styles.voiceModalBackdrop}>
          {/* Header */}
          <View style={styles.voiceModalHeader}>
            <View style={styles.voiceModalBrand}>
              <View style={styles.voiceModalBadge}>
                <Text style={styles.voiceModalBadgeText}>F</Text>
              </View>
              <Text style={styles.voiceModalTitle}>Fargo® Live Voice</Text>
            </View>
            <Pressable
              onPress={() => {
                setVoiceModeOpen(false);
                setIsListening(false);
                if (Platform.OS === 'web' && typeof window !== 'undefined' && window.speechSynthesis) {
                  window.speechSynthesis.cancel();
                }
              }}
              style={styles.closeVoiceModalBtn}
            >
              <X size={22} color="#FFFFFF" />
            </Pressable>
          </View>

          {/* Central Pulsing 3D Voice Orb */}
          <View style={styles.orbContainer}>
            <Animated.View style={[styles.orbPulseRing3, { transform: [{ scale: orbScale }] }]} />
            <Animated.View style={[styles.orbPulseRing2, { transform: [{ scale: orbScale }] }]} />
            <Animated.View style={[styles.orbPulseRing1, { transform: [{ scale: orbScale }] }]} />

            <View style={styles.centralOrb}>
              <Sparkles size={42} color="#FFFFFF" />
            </View>
          </View>

          {/* Live Status & Transcript */}
          <View style={styles.voiceModalStatusContainer}>
            <Text style={styles.voiceStatusHeadline}>
              {voiceModeStatus === 'listening'
                ? 'Listening to you...'
                : voiceModeStatus === 'thinking'
                ? 'Fargo is thinking...'
                : 'Fargo is speaking...'}
            </Text>

            <Text style={styles.voiceTranscriptText}>
              {voiceModeTranscript ||
                (voiceModeStatus === 'listening'
                  ? 'Say "What is my checking balance?" or "Transfer $150 to Sarah"'
                  : '')}
            </Text>
          </View>

          {/* Voice Mode Action Controls */}
          <View style={styles.voiceModalFooter}>
            <Pressable
              style={styles.voiceActionMicBtn}
              onPress={startListening}
            >
              <Mic size={28} color="#FFFFFF" />
            </Pressable>

            <View style={styles.voicePresetRow}>
              <Pressable
                style={styles.voicePresetPill}
                onPress={() => send('What is my Everyday Checking balance?')}
              >
                <Text style={styles.voicePresetText}>"Check my balance"</Text>
              </Pressable>
              <Pressable
                style={styles.voicePresetPill}
                onPress={() => send('Transfer $150 to Sarah Jenkins')}
              >
                <Text style={styles.voicePresetText}>"Transfer $150 to Sarah"</Text>
              </Pressable>
            </View>
          </View>
        </View>
      </Modal>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  page: {
    flex: 1,
    backgroundColor: '#F3F4F6',
  },

  // Header
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingTop: Platform.OS === 'ios' ? 54 : 20,
    paddingBottom: 12,
    backgroundColor: '#FFFFFF',
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
  },
  headerLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  backBtn: {
    padding: 6,
  },
  fargoAvatarWrapper: {
    position: 'relative',
  },
  fargoAvatarBox: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: '#582C83',
    alignItems: 'center',
    justifyContent: 'center',
  },
  fargoAvatarLetter: {
    color: '#FFFFFF',
    fontSize: 18,
    fontWeight: '800',
  },
  onlineStatusDot: {
    position: 'absolute',
    bottom: -1,
    right: -1,
    width: 10,
    height: 10,
    borderRadius: 5,
    backgroundColor: '#10B981',
    borderWidth: 2,
    borderColor: '#FFFFFF',
  },
  headerTitleGroup: {
    gap: 2,
  },
  titleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  titleText: {
    fontSize: 16,
    fontWeight: '700',
    color: '#111111',
  },
  aiPill: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 3,
    backgroundColor: '#EDE9FE',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 10,
  },
  aiPillText: {
    fontSize: 10,
    fontWeight: '700',
    color: '#582C83',
  },
  subtitleText: {
    fontSize: 11,
    color: '#666666',
  },

  headerRight: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  voiceModeHeaderBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 5,
    backgroundColor: '#582C83',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
    shadowColor: '#582C83',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 4,
    elevation: 3,
  },
  voiceModeHeaderText: {
    color: '#FFFFFF',
    fontSize: 12,
    fontWeight: '700',
  },
  resetBtn: {
    padding: 6,
  },

  // Listening Waveform Banner
  listeningBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#EDE9FE',
    paddingHorizontal: 16,
    paddingVertical: 10,
    gap: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#DDD6FE',
  },
  waveBarContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 3,
    height: 20,
  },
  waveBar: {
    width: 3.5,
    height: 20,
    backgroundColor: '#582C83',
    borderRadius: 2,
  },
  listeningText: {
    flex: 1,
    fontSize: 12,
    fontWeight: '600',
    color: '#582C83',
  },
  stopMicBtn: {
    padding: 4,
  },

  // Messages Container
  messagesContainer: {
    padding: 16,
    gap: 16,
  },
  messageRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 10,
  },
  messageRowUser: {
    justifyContent: 'flex-end',
  },
  messageRowAssistant: {
    justifyContent: 'flex-start',
  },
  assistantAvatar: {
    width: 30,
    height: 30,
    borderRadius: 15,
    backgroundColor: '#582C83',
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 2,
  },
  assistantAvatarLetter: {
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: '800',
  },
  bubbleContainer: {
    maxWidth: '82%',
    borderRadius: 18,
    padding: 14,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1.5 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 2,
  },
  userBubble: {
    backgroundColor: '#C8102E', // Wells Fargo Crimson
    borderBottomRightRadius: 4,
  },
  assistantBubble: {
    backgroundColor: '#FFFFFF',
    borderBottomLeftRadius: 4,
    borderWidth: 1,
    borderColor: '#E5E7EB',
  },
  assistantBubbleHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 6,
  },
  assistantName: {
    fontSize: 11,
    fontWeight: '700',
    color: '#582C83',
  },
  speakerBtn: {
    padding: 2,
  },
  speakingIndicatorRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 3,
  },
  miniSoundDot: {
    width: 2.5,
    height: 12,
    backgroundColor: '#582C83',
    borderRadius: 1.5,
  },

  messageText: {
    fontSize: 14.5,
    lineHeight: 21,
  },
  userMessageText: {
    color: '#FFFFFF',
    fontWeight: '500',
  },
  assistantMessageText: {
    color: '#111111',
  },

  // Rich Transfer Card
  richTransferCard: {
    backgroundColor: '#FAF5FF',
    borderRadius: 14,
    padding: 14,
    marginTop: 12,
    borderWidth: 1,
    borderColor: '#E9D5FF',
    gap: 8,
  },
  transferCardHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  transferCardTag: {
    fontSize: 10,
    fontWeight: '800',
    color: '#582C83',
    letterSpacing: 0.8,
  },
  transferAmountLarge: {
    fontSize: 28,
    fontWeight: '800',
    color: '#111111',
  },
  transferDetailsBox: {
    backgroundColor: '#FFFFFF',
    borderRadius: 10,
    padding: 10,
    gap: 6,
    borderWidth: 1,
    borderColor: '#F3E8FF',
  },
  transferRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  transferRowLabel: {
    fontSize: 12,
    color: '#666666',
  },
  transferRowVal: {
    fontSize: 12,
    fontWeight: '600',
    color: '#111111',
  },
  authorizeTransferBtn: {
    backgroundColor: '#582C83',
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    paddingVertical: 10,
    borderRadius: 10,
    marginTop: 4,
  },
  authorizeBtnDisabled: {
    backgroundColor: '#9CA3AF',
    opacity: 0.85,
  },
  btnLoadingRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
  },
  authorizeBtnText: {
    color: '#FFFFFF',
    fontWeight: '700',
    fontSize: 13,
  },

  // Rich Balance Widget
  richBalanceWidget: {
    marginTop: 12,
    gap: 8,
  },
  balancePill: {
    backgroundColor: '#F9FAFB',
    borderRadius: 12,
    padding: 10,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    borderWidth: 1,
    borderColor: '#E5E7EB',
  },
  balanceAccountName: {
    fontSize: 12,
    fontWeight: '700',
    color: '#111111',
  },
  balanceSub: {
    fontSize: 10,
    color: '#666666',
  },
  balanceAmountText: {
    fontSize: 15,
    fontWeight: '800',
    color: '#111111',
  },

  // Rich Spending Widget
  richSpendingWidget: {
    backgroundColor: '#F9FAFB',
    borderRadius: 12,
    padding: 12,
    marginTop: 12,
    gap: 8,
    borderWidth: 1,
    borderColor: '#E5E7EB',
  },
  spendingWidgetHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  spendingWidgetTitle: {
    fontSize: 12,
    fontWeight: '700',
    color: '#111111',
  },
  progressContainer: {
    height: 8,
    borderRadius: 4,
    backgroundColor: '#E5E7EB',
    flexDirection: 'row',
    overflow: 'hidden',
  },
  progressBar: {
    height: '100%',
  },
  spendingLegend: {
    gap: 2,
  },
  legendItem: {
    fontSize: 11,
    color: '#555555',
  },
  viewFullAnalysisBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'flex-end',
    gap: 2,
    marginTop: 4,
  },
  viewFullAnalysisText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#582C83',
  },

  // Typing
  typingBubble: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    paddingVertical: 12,
    paddingHorizontal: 16,
  },
  typingText: {
    fontSize: 13,
    color: '#666666',
  },

  // Retry banner
  retryBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: '#FEF2F2',
    borderWidth: 1,
    borderColor: '#FECACA',
    borderRadius: 12,
    paddingHorizontal: 12,
    paddingVertical: 10,
    gap: 10,
  },
  retryText: {
    flex: 1,
    fontSize: 12,
    color: '#B91C1C',
  },
  retryBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    backgroundColor: '#FFFFFF',
    borderRadius: 14,
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderWidth: 1,
    borderColor: '#582C83',
  },
  retryBtnText: {
    fontSize: 12,
    fontWeight: '700',
    color: '#582C83',
  },

  // Chips
  chipsRow: {
    paddingVertical: 8,
    backgroundColor: '#FFFFFF',
    borderTopWidth: 1,
    borderTopColor: '#E5E7EB',
  },
  chipsScroll: {
    paddingHorizontal: 14,
    gap: 8,
  },
  chipBtn: {
    backgroundColor: '#F3F4F6',
    borderRadius: 20,
    paddingHorizontal: 14,
    paddingVertical: 7,
    borderWidth: 1,
    borderColor: '#E5E7EB',
  },
  chipBtnPressed: {
    backgroundColor: '#E5E7EB',
  },
  chipText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#333333',
  },

  // Composer
  composerBar: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingVertical: 10,
    backgroundColor: '#FFFFFF',
    gap: 8,
  },
  composerInput: {
    flex: 1,
    height: 44,
    backgroundColor: '#F3F4F6',
    borderRadius: 22,
    paddingHorizontal: 16,
    fontSize: 14,
    color: '#111111',
  },
  micBtn: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#EDE9FE',
    alignItems: 'center',
    justifyContent: 'center',
  },
  micBtnActive: {
    backgroundColor: '#582C83',
  },
  sendBtn: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#C8102E',
    alignItems: 'center',
    justifyContent: 'center',
  },
  sendBtnDisabled: {
    backgroundColor: '#D1D5DB',
  },

  // Immersive Voice Mode Modal
  voiceModalBackdrop: {
    flex: 1,
    backgroundColor: 'rgba(20, 10, 35, 0.96)',
    justifyContent: 'space-between',
    paddingHorizontal: 24,
    paddingTop: Platform.OS === 'ios' ? 60 : 30,
    paddingBottom: 40,
  },
  voiceModalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  voiceModalBrand: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  voiceModalBadge: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: '#582C83',
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1.5,
    borderColor: '#A855F7',
  },
  voiceModalBadgeText: {
    color: '#FFFFFF',
    fontWeight: '800',
    fontSize: 16,
  },
  voiceModalTitle: {
    color: '#FFFFFF',
    fontSize: 18,
    fontWeight: '700',
  },
  closeVoiceModalBtn: {
    padding: 6,
  },

  orbContainer: {
    alignItems: 'center',
    justifyContent: 'center',
    height: 280,
  },
  orbPulseRing3: {
    position: 'absolute',
    width: 240,
    height: 240,
    borderRadius: 120,
    backgroundColor: 'rgba(88, 44, 131, 0.2)',
  },
  orbPulseRing2: {
    position: 'absolute',
    width: 180,
    height: 180,
    borderRadius: 90,
    backgroundColor: 'rgba(124, 58, 237, 0.35)',
  },
  orbPulseRing1: {
    position: 'absolute',
    width: 130,
    height: 130,
    borderRadius: 65,
    backgroundColor: 'rgba(168, 85, 247, 0.5)',
  },
  centralOrb: {
    width: 90,
    height: 90,
    borderRadius: 45,
    backgroundColor: '#582C83',
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: '#A855F7',
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.8,
    shadowRadius: 20,
    elevation: 8,
  },

  voiceModalStatusContainer: {
    alignItems: 'center',
    gap: 12,
    paddingHorizontal: 20,
  },
  voiceStatusHeadline: {
    fontSize: 22,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  voiceTranscriptText: {
    fontSize: 15,
    color: 'rgba(255, 255, 255, 0.85)',
    textAlign: 'center',
    lineHeight: 22,
  },

  voiceModalFooter: {
    alignItems: 'center',
    gap: 20,
  },
  voiceActionMicBtn: {
    width: 72,
    height: 72,
    borderRadius: 36,
    backgroundColor: '#582C83',
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 2,
    borderColor: '#A855F7',
    shadowColor: '#A855F7',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.5,
    shadowRadius: 10,
    elevation: 6,
  },
  voicePresetRow: {
    flexDirection: 'row',
    gap: 10,
  },
  voicePresetPill: {
    backgroundColor: 'rgba(255, 255, 255, 0.12)',
    borderRadius: 20,
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.2)',
  },
  voicePresetText: {
    color: '#FFFFFF',
    fontSize: 12,
    fontWeight: '600',
  },
});
