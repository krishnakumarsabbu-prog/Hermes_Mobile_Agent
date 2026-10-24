import React, { useState } from 'react';
import {
  ActivityIndicator,
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
  Camera,
  CheckCircle2,
  ChevronDown,
  ChevronRight,
  HelpCircle,
  ShieldCheck,
} from 'lucide-react-native';

export default function DepositScreen() {
  const [selectedAccount, setSelectedAccount] = useState('EVERYDAY CHECKING...0987');
  const [amount, setAmount] = useState('');
  const [frontCaptured, setFrontCaptured] = useState(false);
  const [backCaptured, setBackCaptured] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [success, setSuccess] = useState(false);

  const handleSubmitDeposit = () => {
    if (!amount) return;
    setSubmitting(true);
    setTimeout(() => {
      setSubmitting(false);
      setSuccess(true);
    }, 1200);
  };

  return (
    <View style={styles.root}>
      {/* ─── Top Header ─── */}
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Deposit Checks</Text>
        <Pressable style={styles.helpBtn}>
          <HelpCircle size={20} color="#555555" />
        </Pressable>
      </View>

      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={styles.content}
        showsVerticalScrollIndicator={false}
      >
        {success ? (
          <View style={styles.successCard}>
            <CheckCircle2 size={56} color="#059669" />
            <Text style={styles.successTitle}>Check Submitted!</Text>
            <Text style={styles.successAmount}>${amount || '250.00'}</Text>
            <Text style={styles.successDesc}>
              Deposited to {selectedAccount}. Funds are typically available within 1 business day.
            </Text>
            <Pressable
              style={styles.anotherBtn}
              onPress={() => {
                setSuccess(false);
                setAmount('');
                setFrontCaptured(false);
                setBackCaptured(false);
              }}
            >
              <Text style={styles.anotherBtnText}>Make Another Deposit</Text>
            </Pressable>
          </View>
        ) : (
          <>
            {/* Daily Limits Card */}
            <View style={styles.limitCard}>
              <View style={styles.limitRow}>
                <Text style={styles.limitLabel}>Daily Deposit Limit</Text>
                <Text style={styles.limitValue}>$50,000.00</Text>
              </View>
              <View style={styles.limitRow}>
                <Text style={styles.limitLabel}>Remaining Today</Text>
                <Text style={styles.limitRemaining}>$47,332.07</Text>
              </View>
            </View>

            {/* Account Selector */}
            <View style={styles.section}>
              <Text style={styles.fieldLabel}>Deposit to</Text>
              <Pressable
                style={styles.selectBox}
                onPress={() =>
                  setSelectedAccount(
                    selectedAccount.includes('CHECKING')
                      ? 'WAY2SAVE ...6543'
                      : 'EVERYDAY CHECKING...0987',
                  )
                }
              >
                <View>
                  <Text style={styles.selectAccountName}>{selectedAccount}</Text>
                  <Text style={styles.selectAccountBalance}>
                    {selectedAccount.includes('CHECKING')
                      ? 'Available: $2,667.93'
                      : 'Available: $1,636.85'}
                  </Text>
                </View>
                <ChevronDown size={20} color="#666666" />
              </Pressable>
            </View>

            {/* Amount Input */}
            <View style={styles.section}>
              <Text style={styles.fieldLabel}>Amount</Text>
              <View style={styles.amountInputRow}>
                <Text style={styles.currencySymbol}>$</Text>
                <TextInput
                  value={amount}
                  onChangeText={setAmount}
                  placeholder="0.00"
                  placeholderTextColor="#999999"
                  keyboardType="numeric"
                  style={styles.amountInput}
                />
              </View>
            </View>

            {/* Check Photos */}
            <View style={styles.section}>
              <Text style={styles.fieldLabel}>Check Photos</Text>

              <View style={styles.photoGrid}>
                {/* Front of check */}
                <Pressable
                  style={[
                    styles.photoBox,
                    frontCaptured && styles.photoBoxCaptured,
                  ]}
                  onPress={() => setFrontCaptured(!frontCaptured)}
                >
                  {frontCaptured ? (
                    <View style={styles.capturedBadge}>
                      <CheckCircle2 size={24} color="#059669" />
                      <Text style={styles.capturedText}>Front Captured</Text>
                    </View>
                  ) : (
                    <>
                      <Camera size={26} color="#C8102E" />
                      <Text style={styles.photoTitle}>Front of Check</Text>
                      <Text style={styles.photoHint}>Tap to take photo</Text>
                    </>
                  )}
                </Pressable>

                {/* Back of check */}
                <Pressable
                  style={[
                    styles.photoBox,
                    backCaptured && styles.photoBoxCaptured,
                  ]}
                  onPress={() => setBackCaptured(!backCaptured)}
                >
                  {backCaptured ? (
                    <View style={styles.capturedBadge}>
                      <CheckCircle2 size={24} color="#059669" />
                      <Text style={styles.capturedText}>Back Captured</Text>
                    </View>
                  ) : (
                    <>
                      <Camera size={26} color="#C8102E" />
                      <Text style={styles.photoTitle}>Back of Check</Text>
                      <Text style={styles.photoHint}>Sign & endorse</Text>
                    </>
                  )}
                </Pressable>
              </View>
            </View>

            {/* Endorsement Note */}
            <View style={styles.noticeBox}>
              <ShieldCheck size={20} color="#059669" />
              <Text style={styles.noticeText}>
                Endorse check back with "For Mobile Deposit at Wells Fargo only".
              </Text>
            </View>

            {/* Deposit Button */}
            <Pressable
              onPress={handleSubmitDeposit}
              disabled={submitting}
              style={({ pressed }) => [
                styles.depositBtn,
                pressed && { backgroundColor: '#A60E26' },
                submitting && { opacity: 0.7 },
              ]}
            >
              {submitting ? (
                <ActivityIndicator color="#FFFFFF" />
              ) : (
                <Text style={styles.depositBtnText}>Deposit Check</Text>
              )}
            </Pressable>
          </>
        )}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  root: {
    flex: 1,
    backgroundColor: '#F3F4F6',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingTop: Platform.OS === 'ios' ? 56 : 24,
    paddingBottom: 16,
    backgroundColor: '#FFFFFF',
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: '#111111',
  },
  helpBtn: {
    padding: 4,
  },
  scrollView: {
    flex: 1,
  },
  content: {
    padding: 18,
    gap: 16,
  },

  limitCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 14,
    padding: 16,
    gap: 8,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1.5 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 2,
  },
  limitRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  limitLabel: {
    fontSize: 13,
    color: '#666666',
  },
  limitValue: {
    fontSize: 14,
    fontWeight: '600',
    color: '#111111',
  },
  limitRemaining: {
    fontSize: 14,
    fontWeight: '700',
    color: '#059669',
  },

  section: {
    gap: 8,
  },
  fieldLabel: {
    fontSize: 14,
    fontWeight: '700',
    color: '#333333',
  },
  selectBox: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#E5E7EB',
  },
  selectAccountName: {
    fontSize: 14,
    fontWeight: '700',
    color: '#111111',
    marginBottom: 2,
  },
  selectAccountBalance: {
    fontSize: 12,
    color: '#666666',
  },

  amountInputRow: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    paddingHorizontal: 16,
    height: 56,
    flexDirection: 'row',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#E5E7EB',
    gap: 6,
  },
  currencySymbol: {
    fontSize: 24,
    fontWeight: '600',
    color: '#111111',
  },
  amountInput: {
    flex: 1,
    fontSize: 24,
    fontWeight: '700',
    color: '#111111',
  },

  photoGrid: {
    flexDirection: 'row',
    gap: 12,
  },
  photoBox: {
    flex: 1,
    height: 120,
    backgroundColor: '#FFFFFF',
    borderRadius: 14,
    borderWidth: 1.5,
    borderColor: '#E5E7EB',
    borderStyle: 'dashed',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    padding: 8,
  },
  photoBoxCaptured: {
    borderColor: '#059669',
    backgroundColor: '#F0FDF4',
    borderStyle: 'solid',
  },
  photoTitle: {
    fontSize: 13,
    fontWeight: '700',
    color: '#111111',
  },
  photoHint: {
    fontSize: 11,
    color: '#777777',
  },
  capturedBadge: {
    alignItems: 'center',
    gap: 6,
  },
  capturedText: {
    fontSize: 12,
    fontWeight: '700',
    color: '#059669',
  },

  noticeBox: {
    backgroundColor: '#ECFDF5',
    borderRadius: 12,
    padding: 14,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    borderWidth: 1,
    borderColor: '#A7F3D0',
  },
  noticeText: {
    flex: 1,
    fontSize: 12,
    color: '#065F46',
    lineHeight: 16,
    fontWeight: '500',
  },

  depositBtn: {
    backgroundColor: '#C8102E',
    height: 52,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 8,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.15,
    shadowRadius: 4,
    elevation: 3,
  },
  depositBtnText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '700',
  },

  successCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 32,
    alignItems: 'center',
    gap: 12,
    marginTop: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.08,
    shadowRadius: 6,
    elevation: 3,
  },
  successTitle: {
    fontSize: 22,
    fontWeight: '700',
    color: '#111111',
  },
  successAmount: {
    fontSize: 32,
    fontWeight: '800',
    color: '#059669',
  },
  successDesc: {
    fontSize: 14,
    color: '#555555',
    textAlign: 'center',
    lineHeight: 20,
  },
  anotherBtn: {
    backgroundColor: '#C8102E',
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 10,
    marginTop: 10,
  },
  anotherBtnText: {
    color: '#FFFFFF',
    fontWeight: '700',
    fontSize: 14,
  },
});
