import React, { useState } from 'react';
import {
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
  ArrowLeftRight,
  ChevronRight,
  Clock,
  DollarSign,
  FileText,
  Send,
  Zap,
} from 'lucide-react-native';
import { useApp } from '../../src/AppContext';
import { formatINR } from '../../src/utils';
import { TransactionRow } from '../../src/ui';

export default function PayAndTransferScreen() {
  const { account, transactions, setApproval } = useApp();
  const [recipient, setRecipient] = useState('');
  const [amount, setAmount] = useState('150.00');
  const [memo, setMemo] = useState('Dinner split');

  const handleReviewTransfer = () => {
    const paise = Math.round(parseFloat(amount || '0') * 100);
    const amt = paise > 0 ? paise : 15000;
    setApproval({
      approvalId: `appr_${Date.now()}`,
      beneficiary: {
        id: 'b1',
        fullName: recipient || 'Sarah Jenkins',
        alias: recipient || 'Sarah Jenkins',
        dailyLimitPaise: 5000000,
      },
      amountPaise: amt,
      sourceAccountId: account.id,
      currentBalancePaise: account.balancePaise,
      projectedBalancePaise: account.balancePaise - amt,
      expiresAt: new Date(Date.now() + 15 * 60 * 1000).toISOString(),
      status: 'WAITING_FOR_APPROVAL',
      consumed: false,
    });
    router.push('/transfer/review');
  };

  return (
    <View style={styles.root}>
      {/* ─── Top Header ─── */}
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Pay & Transfer</Text>
      </View>

      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={styles.content}
        showsVerticalScrollIndicator={false}
      >
        {/* ─── Hub Action Buttons ─── */}
        <View style={styles.hubGrid}>
          {/* Zelle */}
          <Pressable
            style={({ pressed }) => [
              styles.hubCard,
              pressed && { opacity: 0.9 },
            ]}
            onPress={() => {
              setRecipient('Sarah Jenkins (Zelle)');
              handleReviewTransfer();
            }}
          >
            <View style={[styles.hubIconBox, { backgroundColor: '#7414CA' }]}>
              <Zap size={22} color="#FFFFFF" />
            </View>
            <Text style={styles.hubTitle}>Send with Zelle®</Text>
            <Text style={styles.hubSubtitle}>Fast, free, and easy</Text>
          </Pressable>

          {/* Transfer */}
          <Pressable
            style={({ pressed }) => [
              styles.hubCard,
              pressed && { opacity: 0.9 },
            ]}
            onPress={() => {
              setRecipient('WAY2SAVE ...6543');
              handleReviewTransfer();
            }}
          >
            <View style={[styles.hubIconBox, { backgroundColor: '#C8102E' }]}>
              <ArrowLeftRight size={22} color="#FFFFFF" />
            </View>
            <Text style={styles.hubTitle}>Transfer</Text>
            <Text style={styles.hubSubtitle}>Between WF accounts</Text>
          </Pressable>

          {/* Bill Pay */}
          <Pressable
            style={({ pressed }) => [
              styles.hubCard,
              pressed && { opacity: 0.9 },
            ]}
          >
            <View style={[styles.hubIconBox, { backgroundColor: '#0284C7' }]}>
              <FileText size={22} color="#FFFFFF" />
            </View>
            <Text style={styles.hubTitle}>Pay Bills</Text>
            <Text style={styles.hubSubtitle}>Utilities, cards & more</Text>
          </Pressable>

          {/* Wire */}
          <Pressable
            style={({ pressed }) => [
              styles.hubCard,
              pressed && { opacity: 0.9 },
            ]}
          >
            <View style={[styles.hubIconBox, { backgroundColor: '#059669' }]}>
              <DollarSign size={22} color="#FFFFFF" />
            </View>
            <Text style={styles.hubTitle}>Wires</Text>
            <Text style={styles.hubSubtitle}>Domestic & global</Text>
          </Pressable>
        </View>

        {/* ─── Quick Transfer Section ─── */}
        <View style={styles.card}>
          <Text style={styles.cardSectionTitle}>Quick Transfer</Text>

          {/* From Account */}
          <View style={styles.fieldGroup}>
            <Text style={styles.fieldLabel}>From</Text>
            <View style={styles.accountBox}>
              <Text style={styles.accountName}>EVERYDAY CHECKING...0987</Text>
              <Text style={styles.accountBal}>Available: $2,667.93</Text>
            </View>
          </View>

          {/* To Recipient */}
          <View style={styles.fieldGroup}>
            <Text style={styles.fieldLabel}>To</Text>
            <TextInput
              value={recipient}
              onChangeText={setRecipient}
              placeholder="Name, email, or mobile number"
              placeholderTextColor="#999999"
              style={styles.textInput}
            />
          </View>

          {/* Amount */}
          <View style={styles.fieldGroup}>
            <Text style={styles.fieldLabel}>Amount</Text>
            <View style={styles.amountBox}>
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

          {/* Memo */}
          <View style={styles.fieldGroup}>
            <Text style={styles.fieldLabel}>Memo (optional)</Text>
            <TextInput
              value={memo}
              onChangeText={setMemo}
              placeholder="What's this for?"
              placeholderTextColor="#999999"
              style={styles.textInput}
            />
          </View>

          {/* Review Button */}
          <Pressable
            onPress={handleReviewTransfer}
            style={({ pressed }) => [
              styles.reviewBtn,
              pressed && { backgroundColor: '#A60E26' },
            ]}
          >
            <Text style={styles.reviewBtnText}>Continue to Review</Text>
          </Pressable>
        </View>

        {/* ─── Recent Transfers ─── */}
        <View style={styles.sectionHeader}>
          <Text style={styles.sectionHeading}>Transfer Activity</Text>
          <Pressable
            onPress={() => router.push('/spending')}
            style={styles.viewAllBtn}
          >
            <Text style={styles.viewAllText}>Analysis</Text>
            <ChevronRight size={14} color="#C8102E" />
          </Pressable>
        </View>

        <View style={styles.activityList}>
          {transactions.map((tx) => (
            <TransactionRow
              key={tx.id}
              transaction={tx}
              onPress={() =>
                router.push({
                  pathname: '/transaction/[id]',
                  params: { id: tx.id },
                })
              }
            />
          ))}
        </View>
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
  scrollView: {
    flex: 1,
  },
  content: {
    padding: 16,
    gap: 16,
  },

  // Hub Grid
  hubGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 10,
  },
  hubCard: {
    width: '48.3%',
    backgroundColor: '#FFFFFF',
    borderRadius: 14,
    padding: 14,
    gap: 4,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1.5 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 2,
  },
  hubIconBox: {
    width: 38,
    height: 38,
    borderRadius: 10,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 4,
  },
  hubTitle: {
    fontSize: 14,
    fontWeight: '700',
    color: '#111111',
  },
  hubSubtitle: {
    fontSize: 11,
    color: '#666666',
  },

  // Quick Transfer Card
  card: {
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 18,
    gap: 14,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.06,
    shadowRadius: 6,
    elevation: 2,
  },
  cardSectionTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#111111',
    marginBottom: 4,
  },
  fieldGroup: {
    gap: 6,
  },
  fieldLabel: {
    fontSize: 12,
    fontWeight: '700',
    color: '#555555',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  accountBox: {
    backgroundColor: '#F9FAFB',
    borderRadius: 10,
    padding: 12,
    borderWidth: 1,
    borderColor: '#E5E7EB',
  },
  accountName: {
    fontSize: 14,
    fontWeight: '700',
    color: '#111111',
  },
  accountBal: {
    fontSize: 12,
    color: '#666666',
    marginTop: 2,
  },
  textInput: {
    backgroundColor: '#FFFFFF',
    borderRadius: 10,
    paddingHorizontal: 14,
    height: 48,
    borderWidth: 1,
    borderColor: '#D1D5DB',
    fontSize: 15,
    color: '#111111',
  },
  amountBox: {
    backgroundColor: '#FFFFFF',
    borderRadius: 10,
    paddingHorizontal: 14,
    height: 52,
    borderWidth: 1,
    borderColor: '#D1D5DB',
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  currencySymbol: {
    fontSize: 20,
    fontWeight: '700',
    color: '#111111',
  },
  amountInput: {
    flex: 1,
    fontSize: 20,
    fontWeight: '700',
    color: '#111111',
  },
  reviewBtn: {
    backgroundColor: '#C8102E',
    height: 50,
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
  reviewBtnText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '700',
  },

  // Activity
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: 6,
  },
  sectionHeading: {
    fontSize: 17,
    fontWeight: '700',
    color: '#111111',
  },
  viewAllBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 2,
  },
  viewAllText: {
    fontSize: 13,
    fontWeight: '600',
    color: '#C8102E',
  },
  activityList: {
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    paddingHorizontal: 14,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.06,
    shadowRadius: 6,
    elevation: 2,
  },
});
