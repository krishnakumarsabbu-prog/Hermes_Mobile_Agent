import React, { useRef, useEffect } from 'react';
import {
  Animated,
  Platform,
  Pressable,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { router } from 'expo-router';
import { Check, FileText, ReceiptText } from 'lucide-react-native';
import { useApp } from '../../src/AppContext';
import { colors, radii, shadows, spacing, typography } from '../../src/theme';
import { formatDateTime, formatINR } from '../../src/utils';
import { Card, Screen } from '../../src/ui';

export default function TransferResult() {
  const { transferResult } = useApp();

  // Animations
  const scaleAnim = useRef(new Animated.Value(0)).current;
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const slideAnim = useRef(new Animated.Value(30)).current;

  useEffect(() => {
    Animated.sequence([
      Animated.spring(scaleAnim, {
        toValue: 1,
        friction: 5,
        tension: 120,
        useNativeDriver: true,
      }),
      Animated.parallel([
        Animated.timing(fadeAnim, {
          toValue: 1,
          duration: 500,
          useNativeDriver: true,
        }),
        Animated.timing(slideAnim, {
          toValue: 0,
          duration: 500,
          useNativeDriver: true,
        }),
      ]),
    ]).start();
  }, []);

  // No result state
  if (!transferResult) {
    return (
      <Screen style={styles.screenOverride}>
        <View style={styles.emptyState}>
          <Text style={{ fontSize: 48, marginBottom: 16 }}>📋</Text>
          <Text style={styles.emptyTitle}>Transfer unavailable</Text>
          <Text style={styles.emptySubtitle}>
            No transfer result to display.
          </Text>
          <Pressable
            onPress={() => router.replace('/(tabs)')}
            style={styles.primaryButton}
          >
            <Text style={styles.primaryButtonText}>Return home</Text>
          </Pressable>
        </View>
      </Screen>
    );
  }

  const { transaction, approval, updatedBalancePaise } = transferResult;

  return (
    <Screen style={styles.screenOverride}>
      {/* ─── Success Hero ─── */}
      <View style={styles.hero}>
        {/* Animated success checkmark */}
        <Animated.View
          style={[
            styles.successCircleOuter,
            { transform: [{ scale: scaleAnim }] },
          ]}
        >
          <View style={styles.successCircleInner}>
            <Check color={colors.surface} size={32} strokeWidth={3} />
          </View>
        </Animated.View>

        <Animated.View style={{ opacity: fadeAnim }}>
          <Text style={styles.successTitle}>Transfer successful</Text>
          <Text style={styles.successSubtitle}>
            Your simulated payment to {approval.beneficiary.fullName} is
            complete.
          </Text>
        </Animated.View>
      </View>

      {/* ─── Result Card ─── */}
      <Animated.View
        style={{
          opacity: fadeAnim,
          transform: [{ translateY: slideAnim }],
        }}
      >
        <Card style={styles.resultCard}>
          {/* Amount */}
          <View style={styles.amountSection}>
            <Text style={styles.amountLabel}>AMOUNT TRANSFERRED</Text>
            <Text style={styles.amountValue}>
              {formatINR(transaction.amountPaise)}
            </Text>
          </View>

          <View style={styles.divider} />

          {/* Details */}
          <DetailRow
            label="To"
            value={`${approval.beneficiary.fullName} (${approval.beneficiary.alias})`}
          />
          <DetailRow label="Reference" value={transaction.reference} />
          <DetailRow label="Date" value={formatDateTime(transaction.date)} />
          <DetailRow
            label="Updated balance"
            value={formatINR(updatedBalancePaise)}
            highlight
          />
        </Card>

        {/* ─── Info Notice ─── */}
        <View style={styles.noticeBanner}>
          <View style={styles.noticeIconWrap}>
            <ReceiptText color={colors.blue} size={18} />
          </View>
          <Text style={styles.noticeText}>
            This is a simulated transaction for the Hermes POC. No real funds
            were moved.
          </Text>
        </View>

        {/* ─── Action Buttons ─── */}
        <Pressable
          onPress={() => router.replace('/(tabs)')}
          style={({ pressed }) => [
            styles.primaryButton,
            pressed && styles.buttonPressed,
          ]}
        >
          <Text style={styles.primaryButtonText}>Return home</Text>
        </Pressable>

        <Pressable
          onPress={() =>
            router.replace({
              pathname: '/transaction/[id]',
              params: { id: transaction.id },
            })
          }
          style={({ pressed }) => [
            styles.secondaryButton,
            pressed && { backgroundColor: colors.lineSoft },
          ]}
        >
          <FileText size={16} color={colors.brand} />
          <Text style={styles.secondaryButtonText}>
            View transaction details
          </Text>
        </Pressable>
      </Animated.View>
    </Screen>
  );
}

/* ─── Detail Row ────────────────────────────────────────────────────────── */

function DetailRow({
  label,
  value,
  highlight,
}: {
  label: string;
  value: string;
  highlight?: boolean;
}) {
  return (
    <View style={styles.detailRow}>
      <Text style={styles.detailLabel}>{label}</Text>
      <Text
        style={[
          styles.detailValue,
          highlight && { color: colors.green, fontWeight: '800' },
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

  // Hero
  hero: {
    alignItems: 'center',
    paddingTop: 20,
    paddingBottom: 30,
  },
  successCircleOuter: {
    width: 88,
    height: 88,
    borderRadius: 44,
    backgroundColor: colors.greenSoft,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 24,
  },
  successCircleInner: {
    width: 68,
    height: 68,
    borderRadius: 34,
    backgroundColor: colors.green,
    alignItems: 'center',
    justifyContent: 'center',
    ...shadows.elevated,
  },
  successTitle: {
    color: colors.ink,
    ...typography.h1,
    textAlign: 'center',
  },
  successSubtitle: {
    color: colors.muted,
    fontSize: 14,
    textAlign: 'center',
    lineHeight: 21,
    marginTop: 10,
    maxWidth: 280,
  },

  // Result card
  resultCard: {
    padding: 22,
  },
  amountSection: {
    marginBottom: 4,
  },
  amountLabel: {
    color: colors.muted,
    ...typography.eyebrow,
  },
  amountValue: {
    color: colors.green,
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
    gap: 14,
    paddingVertical: 11,
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
    fontWeight: '700',
    textAlign: 'right',
    flex: 1,
  },

  // Notice banner
  noticeBanner: {
    flexDirection: 'row',
    gap: 12,
    backgroundColor: colors.blueSoft,
    borderRadius: radii.md,
    padding: 16,
    marginVertical: 20,
    borderWidth: 1,
    borderColor: 'rgba(37,99,235,0.1)',
    alignItems: 'flex-start',
  },
  noticeIconWrap: {
    width: 36,
    height: 36,
    borderRadius: 10,
    backgroundColor: 'rgba(37,99,235,0.1)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  noticeText: {
    color: colors.inkSecondary,
    fontSize: 13,
    lineHeight: 19,
    flex: 1,
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
  buttonPressed: {
    backgroundColor: colors.brandDark,
    transform: [{ scale: 0.98 }],
  },
  secondaryButton: {
    height: 52,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    borderRadius: radii.sm,
    marginTop: 8,
  },
  secondaryButtonText: {
    color: colors.brand,
    fontWeight: '700',
    fontSize: 15,
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
  },
});
