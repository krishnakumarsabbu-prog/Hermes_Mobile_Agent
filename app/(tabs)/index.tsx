import React from 'react';
import { ActivityIndicator, Pressable, RefreshControl, ScrollView, StyleSheet, Text, View } from 'react-native';
import { router } from 'expo-router';
import { ArrowUpRight, Bell, ChevronRight, Eye, Plus, ScanLine, TrendingUp, WalletCards } from 'lucide-react-native';
import { useApp } from '../../src/AppContext';
import { colors, radii, spacing } from '../../src/theme';
import { formatINR, summarizeTransactions } from '../../src/utils';
import { Avatar, Card, Screen, SectionTitle, TransactionRow } from '../../src/ui';

export default function HomeScreen() {
  const { account, transactions, loading, error, refresh } = useApp();
  const summary = summarizeTransactions(transactions);

  return (
    <ScrollView
      style={{ flex: 1, backgroundColor: colors.background }}
      contentContainerStyle={{ padding: spacing.md, paddingBottom: 36 }}
      showsVerticalScrollIndicator={false}
      refreshControl={<RefreshControl refreshing={loading && transactions.length > 0} onRefresh={refresh} tintColor={colors.teal} />}
    >
      <View style={styles.top}>
        <View>
          <Text style={styles.eyebrow}>PERSONAL BANKING</Text>
          <Text style={styles.greeting}>Good evening, Alex</Text>
        </View>
        <View style={styles.topActions}>
          <Bell size={19} color={colors.ink} />
          <Avatar small />
        </View>
      </View>

      <View style={styles.searchPill}>
        <ScanLine size={16} color={colors.muted} />
        <Text style={styles.searchText}>Ask Hermes anything</Text>
        <Text style={styles.searchKey}>⌘ K</Text>
      </View>

      {loading && transactions.length === 0 ? (
        <View style={styles.loadingContainer}>
          <ActivityIndicator color={colors.teal} size="large" />
          <Text style={styles.loadingText}>Loading your account...</Text>
        </View>
      ) : error ? (
        <View style={styles.errorContainer}>
          <Text style={styles.errorTitle}>Could not load data</Text>
          <Text style={styles.errorText}>{error}</Text>
          <Pressable onPress={refresh} style={styles.retryButton}>
            <Text style={styles.retryText}>Try again</Text>
          </Pressable>
        </View>
      ) : (
        <>
          <Card style={styles.balanceCard}>
            <View style={styles.cardTop}>
              <View>
                <Text style={styles.accountLabel}>{account.name.toUpperCase()} {account.maskedNumber}</Text>
                <Text style={styles.balance}>{formatINR(account.balancePaise)}</Text>
                <Text style={styles.available}>Available balance</Text>
              </View>
              <View style={styles.balanceIcon}>
                <WalletCards size={21} color={colors.surface} />
              </View>
            </View>
            <View style={styles.cardBottom}>
              <View style={styles.simBadge}>
                <View style={styles.dot} />
                <Text style={styles.simText}>SIMULATED POC ACCOUNT</Text>
              </View>
              <Eye size={17} color="#B9C9D5" />
            </View>
          </Card>

          <SectionTitle title="Quick actions" />
          <View style={styles.quickRow}>
            <QuickAction icon={<ArrowUpRight color={colors.teal} size={20} />} label="Transfer" onPress={() => router.push('/transfer/review')} />
            <QuickAction icon={<TrendingUp color={colors.blue} size={20} />} label="Analyze" onPress={() => router.push('/spending')} />
            <QuickAction icon={<WalletCards color={colors.amber} size={20} />} label="Accounts" onPress={() => {}} />
          </View>

          <View style={styles.summaryHeader}>
            <Text style={styles.sectionHeading}>This month</Text>
            <Pressable onPress={() => router.push('/spending')}>
              <Text style={styles.viewAll}>View analysis <ChevronRight size={13} color={colors.teal} /></Text>
            </Pressable>
          </View>
          <View style={styles.summaryGrid}>
            <Card style={styles.summaryCard}>
              <Text style={styles.summaryLabel}>Total spending</Text>
              <Text style={styles.summaryValue}>{formatINR(summary.totalPaise)}</Text>
              <Text style={styles.summaryHint}>Across {summary.transactionCount} transactions</Text>
            </Card>
            <Card style={styles.summaryCard}>
              <Text style={styles.summaryLabel}>Dining</Text>
              <Text style={styles.summaryValue}>{formatINR(summary.byCategory.Dining)}</Text>
              <Text style={styles.summaryHint}>This month</Text>
            </Card>
          </View>

          <SectionTitle title="Recent activity" action="See all" onAction={() => router.push('/(tabs)/activity')} />
          <Card>
            {transactions.slice(0, 4).map((transaction) => (
              <TransactionRow key={transaction.id} transaction={transaction} onPress={() => router.push({ pathname: '/transaction/[id]', params: { id: transaction.id } })} />
            ))}
          </Card>
        </>
      )}
    </ScrollView>
  );
}

function QuickAction({ icon, label, onPress }: { icon: React.ReactNode; label: string; onPress: () => void }) {
  return (
    <Pressable style={styles.quickAction} onPress={onPress}>
      <View style={styles.quickIcon}>{icon}</View>
      <Text style={styles.quickLabel}>{label}</Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  top: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginTop: 6 },
  eyebrow: { color: colors.muted, fontSize: 10, letterSpacing: 1.4, fontWeight: '700' },
  greeting: { color: colors.ink, fontSize: 24, fontWeight: '700', marginTop: 7 },
  topActions: { flexDirection: 'row', alignItems: 'center', gap: 18 },
  searchPill: { height: 42, backgroundColor: colors.surface, borderRadius: radii.pill, marginTop: 20, paddingHorizontal: 14, flexDirection: 'row', alignItems: 'center', gap: 8, borderWidth: 1, borderColor: colors.line },
  searchText: { flex: 1, color: colors.muted, fontSize: 13 },
  searchKey: { color: colors.soft, fontSize: 11 },
  loadingContainer: { alignItems: 'center', paddingTop: 80 },
  loadingText: { color: colors.muted, fontSize: 14, marginTop: 16 },
  errorContainer: { alignItems: 'center', paddingTop: 60, paddingHorizontal: 24 },
  errorTitle: { color: colors.ink, fontSize: 17, fontWeight: '700' },
  errorText: { color: colors.muted, fontSize: 14, marginTop: 8, textAlign: 'center', lineHeight: 20 },
  retryButton: { marginTop: 20, backgroundColor: colors.teal, borderRadius: radii.sm, paddingHorizontal: 24, paddingVertical: 12 },
  retryText: { color: colors.surface, fontSize: 14, fontWeight: '700' },
  balanceCard: { marginTop: spacing.md, backgroundColor: colors.navy, borderColor: colors.navy, padding: spacing.lg },
  cardTop: { flexDirection: 'row', justifyContent: 'space-between' },
  accountLabel: { color: '#AAB9C8', fontSize: 11, fontWeight: '700', letterSpacing: 0.6 },
  balance: { color: colors.surface, fontSize: 30, fontWeight: '700', marginTop: 14 },
  available: { color: '#AAB9C8', fontSize: 12, marginTop: 4 },
  balanceIcon: { width: 40, height: 40, borderRadius: 12, backgroundColor: '#314258', alignItems: 'center', justifyContent: 'center' },
  cardBottom: { marginTop: 26, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  simBadge: { flexDirection: 'row', gap: 7, alignItems: 'center' },
  dot: { width: 7, height: 7, borderRadius: 4, backgroundColor: '#5DD0A5' },
  simText: { color: '#B9C9D5', fontSize: 10, fontWeight: '700', letterSpacing: 0.6 },
  quickRow: { flexDirection: 'row', justifyContent: 'space-between', gap: 10 },
  quickAction: { flex: 1, backgroundColor: colors.surface, borderRadius: radii.md, padding: 12, alignItems: 'center', borderWidth: 1, borderColor: colors.line },
  quickIcon: { width: 38, height: 38, borderRadius: 13, backgroundColor: colors.background, alignItems: 'center', justifyContent: 'center' },
  quickLabel: { color: colors.ink, fontSize: 12, fontWeight: '700', marginTop: 8 },
  summaryHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginTop: spacing.lg, marginBottom: spacing.sm },
  sectionHeading: { fontSize: 17, fontWeight: '700', color: colors.ink },
  viewAll: { color: colors.teal, fontSize: 12, fontWeight: '700' },
  summaryGrid: { flexDirection: 'row', gap: 10 },
  summaryCard: { flex: 1, padding: 14 },
  summaryLabel: { color: colors.muted, fontSize: 12 },
  summaryValue: { color: colors.ink, fontSize: 18, fontWeight: '700', marginTop: 7 },
  summaryHint: { color: colors.soft, fontSize: 11, marginTop: 7 },
});
