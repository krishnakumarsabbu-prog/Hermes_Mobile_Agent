import React, { useEffect, useState } from 'react';
import {
  ActivityIndicator,
  Platform,
  Pressable,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { router, useLocalSearchParams } from 'expo-router';
import {
  ArrowLeft,
  CircleCheck as CheckCircle2,
  Clock,
  XCircle,
} from 'lucide-react-native';
import { useApp } from '../../src/AppContext';
import { apiMode } from '../../src/config';
import { api } from '../../src/apiClient';
import { colors, radii, shadows, spacing, typography } from '../../src/theme';
import { formatDateTime, formatINR } from '../../src/utils';
import { Card, Screen } from '../../src/ui';
import { Transaction } from '../../src/models';

export default function TransactionDetail() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const { transactions } = useApp();
  const [txn, setTxn] = useState<Transaction | undefined>(
    transactions.find((item) => item.id === id),
  );
  const [loading, setLoading] = useState(!txn);

  useEffect(() => {
    if (txn) return;
    if (apiMode !== 'http') return;
    setLoading(true);
    api
      .get<Record<string, unknown>>(`/api/v1/transactions/${id}`)
      .then((raw) => {
        setTxn({
          id: raw.id as string,
          merchant: raw.merchant as string,
          category: raw.category as Transaction['category'],
          amountPaise: raw.amountPaise as number,
          date: raw.date as string,
          status: raw.status as Transaction['status'],
          reference: raw.reference as string,
          note: raw.note as string | undefined,
        });
      })
      .catch(() => setTxn(undefined))
      .finally(() => setLoading(false));
  }, [id]);

  // Loading state
  if (loading && !txn) {
    return (
      <Screen style={styles.screenOverride}>
        <View style={styles.loadingWrap}>
          <ActivityIndicator color={colors.brand} size="large" />
          <Text style={styles.loadingText}>Loading transaction...</Text>
        </View>
      </Screen>
    );
  }

  // Not found state
  if (!txn) {
    return (
      <Screen style={styles.screenOverride}>
        <View style={styles.emptyState}>
          <Text style={{ fontSize: 48, marginBottom: 16 }}>🔍</Text>
          <Text style={styles.emptyTitle}>Transaction not found</Text>
          <Text style={styles.emptySubtitle}>
            This transaction may no longer be available.
          </Text>
          <Pressable
            onPress={() => router.back()}
            style={styles.primaryButton}
          >
            <Text style={styles.primaryButtonText}>Go back</Text>
          </Pressable>
        </View>
      </Screen>
    );
  }

  // Status config
  const statusConfig = {
    successful: {
      icon: <CheckCircle2 color={colors.green} size={28} />,
      label: 'Successful',
      color: colors.green,
      bg: colors.greenSoft,
    },
    pending: {
      icon: <Clock color={colors.amber} size={28} />,
      label: 'Pending',
      color: colors.amber,
      bg: colors.amberSoft,
    },
    failed: {
      icon: <XCircle color={colors.red} size={28} />,
      label: 'Failed',
      color: colors.red,
      bg: colors.redSoft,
    },
    cancelled: {
      icon: <XCircle color={colors.muted} size={28} />,
      label: 'Cancelled',
      color: colors.muted,
      bg: colors.lineSoft,
    },
  };

  const status = statusConfig[txn.status] ?? statusConfig.successful;

  // Category emoji
  const categoryEmoji: Record<string, string> = {
    Dining: '🍽',
    Shopping: '🛍',
    Utility: '⚡',
    Transfer: '↗',
  };

  return (
    <Screen style={styles.screenOverride}>
      {/* ─── Header ─── */}
      <View style={styles.header}>
        <Pressable onPress={() => router.back()} style={styles.backButton}>
          <ArrowLeft color={colors.ink} size={20} />
        </Pressable>
        <Text style={styles.headerTitle}>Transaction details</Text>
        <View style={{ width: 40 }} />
      </View>

      {/* ─── Hero Section ─── */}
      <View style={styles.hero}>
        {/* Status icon */}
        <View style={[styles.statusCircle, { backgroundColor: status.bg }]}>
          {status.icon}
        </View>

        {/* Merchant */}
        <Text style={styles.merchant}>{txn.merchant}</Text>

        {/* Amount */}
        <Text style={styles.amount}>-{formatINR(txn.amountPaise)}</Text>

        {/* Status badge */}
        <View style={[styles.statusBadge, { backgroundColor: status.bg }]}>
          <View
            style={[styles.statusDot, { backgroundColor: status.color }]}
          />
          <Text style={[styles.statusText, { color: status.color }]}>
            {status.label}
          </Text>
        </View>
      </View>

      {/* ─── Details Card ─── */}
      <Card style={styles.detailsCard}>
        <DetailRow
          label="Category"
          value={`${categoryEmoji[txn.category] ?? ''} ${txn.category}`}
        />
        <DetailRow label="Date" value={formatDateTime(txn.date)} />
        <DetailRow label="Reference" value={txn.reference} />
        <DetailRow
          label="Status"
          value={status.label}
          valueColor={status.color}
        />
        {txn.note && <DetailRow label="Note" value={txn.note} />}
      </Card>

      {/* ─── Report / Help ─── */}
      <View style={styles.helpSection}>
        <Pressable style={styles.helpButton}>
          <Text style={styles.helpButtonText}>
            Report an issue with this transaction
          </Text>
        </Pressable>
      </View>
    </Screen>
  );
}

/* ─── Detail Row ────────────────────────────────────────────────────────── */

function DetailRow({
  label,
  value,
  valueColor,
}: {
  label: string;
  value: string;
  valueColor?: string;
}) {
  return (
    <View style={styles.detailRow}>
      <Text style={styles.detailLabel}>{label}</Text>
      <Text
        style={[
          styles.detailValue,
          valueColor ? { color: valueColor } : undefined,
        ]}
      >
        {value}
      </Text>
    </View>
  );
}

/* ─── Styles ────────────────────────────────────────────────────────────── */

const styles = StyleSheet.create({
  screenOverride: {
    paddingTop: Platform.OS === 'ios' ? 60 : 44,
  },

  // Header
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  backButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: colors.surface,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: colors.line,
    ...shadows.soft,
  },
  headerTitle: {
    color: colors.ink,
    fontWeight: '700',
    fontSize: 17,
  },

  // Hero
  hero: {
    alignItems: 'center',
    paddingVertical: 24,
  },
  statusCircle: {
    width: 72,
    height: 72,
    borderRadius: 36,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 18,
  },
  merchant: {
    color: colors.ink,
    ...typography.h1,
    textAlign: 'center',
  },
  amount: {
    color: colors.ink,
    fontSize: 32,
    fontWeight: '800',
    marginTop: 10,
    textAlign: 'center',
  },
  statusBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingHorizontal: 14,
    paddingVertical: 6,
    borderRadius: radii.pill,
    marginTop: 14,
  },
  statusDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
  },
  statusText: {
    fontSize: 13,
    fontWeight: '700',
  },

  // Details card
  detailsCard: {
    padding: 20,
    marginTop: 8,
  },
  detailRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 14,
    borderBottomWidth: 1,
    borderBottomColor: colors.lineSoft,
    gap: 14,
  },
  detailLabel: {
    color: colors.muted,
    fontSize: 14,
  },
  detailValue: {
    color: colors.ink,
    fontSize: 14,
    fontWeight: '700',
    textAlign: 'right',
    flex: 1,
  },

  // Help section
  helpSection: {
    marginTop: 24,
    alignItems: 'center',
  },
  helpButton: {
    paddingVertical: 12,
  },
  helpButtonText: {
    color: colors.brand,
    fontSize: 14,
    fontWeight: '600',
  },

  // Loading
  loadingWrap: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    color: colors.muted,
    fontSize: 14,
    marginTop: 16,
  },

  // Empty state
  emptyState: {
    alignItems: 'center',
    paddingTop: 80,
  },
  emptyTitle: {
    color: colors.ink,
    ...typography.h2,
  },
  emptySubtitle: {
    color: colors.muted,
    fontSize: 14,
    marginTop: 8,
    marginBottom: 28,
    textAlign: 'center',
  },
  primaryButton: {
    height: 56,
    backgroundColor: colors.brand,
    borderRadius: radii.sm,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 32,
    ...shadows.elevated,
  },
  primaryButtonText: {
    color: colors.surface,
    ...typography.button,
  },
});
