import React, { useState } from 'react';
import {
  ActivityIndicator,
  Platform,
  Pressable,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { router } from 'expo-router';
import {
  ArrowLeft,
  Check,
  ChevronRight,
  ShieldAlert,
  ShieldCheck,
} from 'lucide-react-native';
import { useApp } from '../../src/AppContext';
import { colors, radii, shadows, spacing, typography } from '../../src/theme';
import { formatINR } from '../../src/utils';
import { Card, Screen } from '../../src/ui';

export default function TransferReview() {
  const { approval, account, authorize, cancel } = useApp();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  // No approval state
  if (!approval) {
    return (
      <Screen style={styles.screenOverride}>
        <View style={styles.emptyState}>
          <View style={styles.emptyIcon}>
            <Text style={{ fontSize: 48 }}>💸</Text>
          </View>
          <Text style={styles.emptyTitle}>No transfer to review</Text>
          <Text style={styles.emptySubtitle}>
            Ask Hermes to prepare a transfer first.
          </Text>
          <Pressable
            onPress={() => router.replace('/(tabs)/pay')}
            style={styles.primaryButton}
          >
            <Text style={styles.primaryButtonText}>Go to Pay & Transfer</Text>
          </Pressable>
        </View>
      </Screen>
    );
  }

  const confirm = async () => {
    setBusy(true);
    setError('');
    try {
      await authorize();
      router.replace('/transfer/result');
    } catch (e) {
      setError(
        e instanceof Error
          ? e.message
          : 'The transfer could not be completed.',
      );
      setBusy(false);
    }
  };

  const decline = async () => {
    await cancel();
    router.replace('/(tabs)/assistant');
  };

  return (
    <Screen style={styles.screenOverride}>
      {/* ─── Header ─── */}
      <View style={styles.header}>
        <Pressable onPress={() => router.back()} style={styles.backButton}>
          <ArrowLeft color={colors.ink} size={20} />
        </Pressable>
        <Text style={styles.headerTitle}>Review transfer</Text>
        <View style={{ width: 40 }} />
      </View>

      {/* ─── Security Warning Banner ─── */}
      <View style={styles.warningBanner}>
        <View style={styles.warningIconWrap}>
          <ShieldAlert color={colors.amber} size={22} />
        </View>
        <View style={{ flex: 1 }}>
          <Text style={styles.warningTitle}>
            SIMULATED TRANSFER — NO REAL MONEY MOVES
          </Text>
          <Text style={styles.warningText}>
            No real money moves. Review every detail before authorizing.
          </Text>
        </View>
      </View>

      {/* ─── Title ─── */}
      <Text style={styles.pageTitle}>
        Confirm payment to {approval.beneficiary.alias}
      </Text>
      <Text style={styles.pageSubtitle}>
        This action requires your explicit approval.
      </Text>

      {/* ─── Amount Card ─── */}
      <Card style={styles.amountCard}>
        {/* Amount header */}
        <View style={styles.amountHeader}>
          <Text style={styles.amountLabel}>TRANSFER AMOUNT</Text>
          <View style={styles.securityBadge}>
            <ShieldCheck size={14} color={colors.green} />
            <Text style={styles.securityBadgeText}>Secured</Text>
          </View>
        </View>
        <Text style={styles.amountValue}>
          {formatINR(approval.amountPaise)}
        </Text>

        <View style={styles.divider} />

        {/* Details */}
        <DetailRow
          label="Beneficiary"
          value={`${approval.beneficiary.fullName} (${approval.beneficiary.alias})`}
        />
        <DetailRow
          label="Beneficiary ID"
          value={approval.beneficiary.id}
        />
        <DetailRow
          label="Source account"
          value={`${account.name} ${account.maskedNumber}`}
        />
        <DetailRow
          label="Available balance"
          value={formatINR(approval.currentBalancePaise)}
        />
        <DetailRow
          label="Balance after transfer"
          value={formatINR(approval.projectedBalancePaise)}
          valueColor={colors.brand}
          strong
        />
        <DetailRow
          label="Daily transfer limit"
          value={formatINR(approval.beneficiary.dailyLimitPaise)}
        />
      </Card>

      {/* ─── Error ─── */}
      {error ? (
        <View style={styles.errorBanner}>
          <Text style={styles.errorText}>⚠️ {error}</Text>
        </View>
      ) : null}

      {/* ─── Confirmation checkbox ─── */}
      <View style={styles.confirmRow}>
        <View style={styles.checkCircle}>
          <Check size={14} color={colors.surface} strokeWidth={3} />
        </View>
        <Text style={styles.confirmText}>
          I confirm this exact simulated transfer of{' '}
          {formatINR(approval.amountPaise)} to{' '}
          {approval.beneficiary.fullName}.
        </Text>
      </View>

      {/* ─── Action Buttons ─── */}
      <Pressable
        disabled={busy}
        onPress={() => void confirm()}
        style={({ pressed }) => [
          styles.primaryButton,
          busy && styles.buttonDisabled,
          pressed && !busy && styles.buttonPressed,
        ]}
      >
        {busy ? (
          <View style={styles.busyRow}>
            <ActivityIndicator color={colors.surface} size="small" />
            <Text style={styles.primaryButtonText}>Authorizing...</Text>
          </View>
        ) : (
          <Text style={styles.primaryButtonText}>Authorize transfer</Text>
        )}
      </Pressable>

      <Pressable
        disabled={busy}
        onPress={() => void decline()}
        style={({ pressed }) => [
          styles.cancelButton,
          pressed && { backgroundColor: colors.lineSoft },
        ]}
      >
        <Text style={styles.cancelButtonText}>Cancel</Text>
      </Pressable>
    </Screen>
  );
}

/* ─── Detail Row Component ──────────────────────────────────────────────── */

function DetailRow({
  label,
  value,
  strong,
  valueColor,
}: {
  label: string;
  value: string;
  strong?: boolean;
  valueColor?: string;
}) {
  return (
    <View style={styles.detailRow}>
      <Text style={styles.detailLabel}>{label}</Text>
      <Text
        style={[
          styles.detailValue,
          strong && styles.detailStrong,
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
    marginBottom: 20,
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

  // Warning banner
  warningBanner: {
    flexDirection: 'row',
    gap: 14,
    backgroundColor: colors.amberSoft,
    borderRadius: radii.md,
    padding: 16,
    marginBottom: 24,
    borderWidth: 1,
    borderColor: 'rgba(217,119,6,0.15)',
  },
  warningIconWrap: {
    width: 40,
    height: 40,
    borderRadius: 12,
    backgroundColor: 'rgba(217,119,6,0.1)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  warningTitle: {
    color: colors.amber,
    fontSize: 11,
    fontWeight: '800',
    letterSpacing: 0.7,
  },
  warningText: {
    color: colors.inkSecondary,
    fontSize: 12,
    marginTop: 4,
    lineHeight: 17,
  },

  // Page title
  pageTitle: {
    color: colors.ink,
    ...typography.h2,
    lineHeight: 30,
  },
  pageSubtitle: {
    color: colors.muted,
    fontSize: 14,
    marginTop: 6,
    marginBottom: 20,
  },

  // Amount card
  amountCard: {
    padding: 20,
  },
  amountHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  amountLabel: {
    color: colors.muted,
    ...typography.eyebrow,
  },
  securityBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    backgroundColor: colors.greenSoft,
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: radii.pill,
  },
  securityBadgeText: {
    color: colors.green,
    fontSize: 11,
    fontWeight: '700',
  },
  amountValue: {
    color: colors.ink,
    fontSize: 34,
    fontWeight: '800',
    marginTop: 10,
  },
  divider: {
    height: 1,
    backgroundColor: colors.line,
    marginVertical: 18,
  },

  // Detail rows
  detailRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 10,
    gap: 16,
    borderBottomWidth: 1,
    borderBottomColor: colors.lineSoft,
  },
  detailLabel: {
    color: colors.muted,
    fontSize: 13,
  },
  detailValue: {
    color: colors.ink,
    fontSize: 13,
    fontWeight: '600',
    textAlign: 'right',
    flex: 1,
  },
  detailStrong: {
    fontWeight: '800',
  },

  // Error
  errorBanner: {
    backgroundColor: colors.redSoft,
    borderRadius: radii.sm,
    padding: 14,
    marginTop: 14,
    borderWidth: 1,
    borderColor: 'rgba(220,38,38,0.15)',
  },
  errorText: {
    color: colors.red,
    fontSize: 13,
    lineHeight: 19,
  },

  // Confirm row
  confirmRow: {
    flexDirection: 'row',
    gap: 12,
    alignItems: 'flex-start',
    marginVertical: 22,
  },
  checkCircle: {
    backgroundColor: colors.green,
    width: 24,
    height: 24,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 1,
  },
  confirmText: {
    flex: 1,
    color: colors.inkSecondary,
    fontSize: 13,
    lineHeight: 19,
  },

  // Buttons
  primaryButton: {
    height: 56,
    backgroundColor: colors.brand,
    borderRadius: radii.sm,
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 4,
    ...shadows.elevated,
  },
  primaryButtonText: {
    color: colors.surface,
    ...typography.button,
    letterSpacing: 0.3,
  },
  buttonDisabled: {
    opacity: 0.6,
  },
  buttonPressed: {
    backgroundColor: colors.brandDark,
    transform: [{ scale: 0.98 }],
  },
  busyRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  cancelButton: {
    height: 52,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: radii.sm,
    marginTop: 6,
  },
  cancelButtonText: {
    color: colors.muted,
    fontWeight: '700',
    fontSize: 15,
  },

  // Empty state
  emptyState: {
    alignItems: 'center',
    paddingTop: 80,
    paddingHorizontal: 24,
  },
  emptyIcon: {
    width: 100,
    height: 100,
    borderRadius: 50,
    backgroundColor: colors.brandSoft,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 24,
  },
  emptyTitle: {
    color: colors.ink,
    ...typography.h2,
    textAlign: 'center',
  },
  emptySubtitle: {
    color: colors.muted,
    fontSize: 15,
    marginTop: 8,
    textAlign: 'center',
    lineHeight: 22,
    marginBottom: 28,
  },
});
