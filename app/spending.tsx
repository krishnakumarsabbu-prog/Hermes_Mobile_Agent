import React from 'react';
import { Platform, Pressable, StyleSheet, Text, View } from 'react-native';
import { router } from 'expo-router';
import { ArrowLeft, TrendingUp } from 'lucide-react-native';
import { useApp } from '../src/AppContext';
import { colors, radii, shadows, spacing, typography } from '../src/theme';
import { formatINR, summarizeTransactions } from '../src/utils';
import { Card, Screen } from '../src/ui';

export default function SpendingScreen() {
  const { transactions } = useApp();
  const summary = summarizeTransactions(transactions);

  const categories = [
    { label: 'Dining', value: summary.byCategory.Dining, color: colors.amber, emoji: '🍽' },
    { label: 'Shopping', value: summary.byCategory.Shopping, color: '#7C3AED', emoji: '🛍' },
    { label: 'Utility', value: summary.byCategory.Utility, color: colors.blue, emoji: '⚡' },
  ];

  return (
    <Screen style={styles.screenOverride}>
      {/* Header */}
      <View style={styles.header}>
        <Pressable
          onPress={() => router.back()}
          style={styles.backButton}
        >
          <ArrowLeft color={colors.ink} size={20} />
        </Pressable>
        <View style={{ flex: 1, marginLeft: 14 }}>
          <Text style={styles.title}>Spending analysis</Text>
          <Text style={styles.subtitle}>Your month at a glance</Text>
        </View>
        <View style={styles.trendIcon}>
          <TrendingUp color={colors.brand} size={20} />
        </View>
      </View>

      {/* Hero card */}
      <Card style={styles.heroCard}>
        <Text style={styles.heroLabel}>TOTAL SPENDING</Text>
        <Text style={styles.heroValue}>{formatINR(summary.totalPaise)}</Text>
        <View style={styles.heroDivider} />
        <Text style={styles.heroHint}>
          {summary.transactionCount} successful transactions this month
        </Text>
      </Card>

      {/* Category breakdown */}
      <Text style={styles.sectionTitle}>Breakdown by category</Text>
      <Card style={styles.breakdownCard}>
        {categories.map(({ label, value, color, emoji }) => {
          const percentage = summary.totalPaise
            ? Math.round((value / summary.totalPaise) * 100)
            : 0;
          return (
            <View key={label} style={styles.categoryRow}>
              <View style={styles.categoryHeader}>
                <View style={styles.categoryName}>
                  <Text style={{ fontSize: 18 }}>{emoji}</Text>
                  <Text style={styles.categoryLabel}>{label}</Text>
                </View>
                <Text style={styles.categoryValue}>{formatINR(value)}</Text>
              </View>
              <View style={styles.progressTrack}>
                <View
                  style={[
                    styles.progressBar,
                    { width: `${percentage}%`, backgroundColor: color },
                  ]}
                />
              </View>
              <Text style={styles.percentText}>
                {percentage}% of monthly spending
              </Text>
            </View>
          );
        })}
      </Card>

      {/* Insight card */}
      <Text style={styles.sectionTitle}>What this means</Text>
      <Card style={styles.insightCard}>
        <Text style={styles.insightIcon}>💡</Text>
        <Text style={styles.insightTitle}>
          Shopping is your largest category
        </Text>
        <Text style={styles.insightText}>
          Your shopping activity represents{' '}
          {summary.totalPaise
            ? Math.round(
                (summary.byCategory.Shopping / summary.totalPaise) * 100,
              )
            : 0}
          % of this month's spending. Consider setting a budget to manage
          discretionary expenses.
        </Text>
      </Card>
    </Screen>
  );
}

const styles = StyleSheet.create({
  screenOverride: {
    paddingTop: Platform.OS === 'ios' ? 60 : 44,
  },

  // Header
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 24,
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
  },
  title: {
    color: colors.ink,
    ...typography.h2,
  },
  subtitle: {
    color: colors.muted,
    fontSize: 13,
    marginTop: 3,
  },
  trendIcon: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: colors.brandSoft,
    alignItems: 'center',
    justifyContent: 'center',
  },

  // Hero card
  heroCard: {
    backgroundColor: colors.brand,
    borderColor: colors.brand,
    padding: spacing.lg,
    ...shadows.elevated,
  },
  heroLabel: {
    color: 'rgba(255,255,255,0.7)',
    fontSize: 11,
    fontWeight: '700',
    letterSpacing: 1.2,
  },
  heroValue: {
    color: colors.surface,
    fontSize: 34,
    fontWeight: '800',
    marginTop: 12,
  },
  heroDivider: {
    height: 1,
    backgroundColor: 'rgba(255,255,255,0.2)',
    marginVertical: 14,
  },
  heroHint: {
    color: 'rgba(255,255,255,0.65)',
    fontSize: 13,
  },

  // Category breakdown
  sectionTitle: {
    color: colors.ink,
    ...typography.h3,
    marginTop: 26,
    marginBottom: 12,
  },
  breakdownCard: {
    padding: 18,
  },
  categoryRow: {
    paddingVertical: 14,
    borderBottomWidth: 1,
    borderBottomColor: colors.lineSoft,
  },
  categoryHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  categoryName: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  categoryLabel: {
    color: colors.ink,
    fontWeight: '700',
    fontSize: 15,
  },
  categoryValue: {
    color: colors.ink,
    fontWeight: '700',
    fontSize: 15,
  },
  progressTrack: {
    height: 8,
    backgroundColor: colors.background,
    borderRadius: 6,
    marginTop: 12,
    overflow: 'hidden',
  },
  progressBar: {
    height: 8,
    borderRadius: 6,
  },
  percentText: {
    color: colors.muted,
    fontSize: 11,
    marginTop: 6,
    fontWeight: '500',
  },

  // Insight card
  insightCard: {
    backgroundColor: colors.blueSoft,
    borderColor: 'rgba(37,99,235,0.15)',
    padding: 20,
  },
  insightIcon: {
    fontSize: 28,
    marginBottom: 10,
  },
  insightTitle: {
    color: colors.ink,
    fontWeight: '700',
    fontSize: 15,
    marginBottom: 6,
  },
  insightText: {
    color: colors.inkSecondary,
    lineHeight: 20,
    fontSize: 13,
  },
});
