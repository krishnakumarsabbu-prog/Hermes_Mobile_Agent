import React from 'react';
import {
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';
import {
  ChevronRight,
  CircleHelp,
  Search,
  Sparkles,
} from 'lucide-react-native';
import { colors, radii, shadows, spacing, typography } from './theme';
import { formatDate, formatINR } from './utils';
import { Transaction } from './models';

/* ─── Screen wrapper ────────────────────────────────────────────────────── */

export const Screen = ({
  children,
  scroll = true,
  style,
}: React.PropsWithChildren<{ scroll?: boolean; style?: object }>) => {
  return scroll ? (
    <ScrollView
      contentContainerStyle={[styles.screen, style]}
      showsVerticalScrollIndicator={false}
    >
      {children}
    </ScrollView>
  ) : (
    <View style={[styles.screen, style]}>{children}</View>
  );
};

/* ─── Section title ─────────────────────────────────────────────────────── */

export const SectionTitle = ({
  title,
  action,
  onAction,
}: {
  title: string;
  action?: string;
  onAction?: () => void;
}) => (
  <View style={styles.sectionHeader}>
    <Text style={styles.sectionTitle}>{title}</Text>
    {action && (
      <Pressable onPress={onAction} accessibilityRole="button" style={styles.actionPressable}>
        <Text style={styles.action}>{action}</Text>
        <ChevronRight size={14} color={colors.brand} />
      </Pressable>
    )}
  </View>
);

/* ─── Card ──────────────────────────────────────────────────────────────── */

export const Card = ({
  children,
  style,
}: React.PropsWithChildren<{ style?: object }>) => (
  <View style={[styles.card, style]}>{children}</View>
);

/* ─── Avatar ────────────────────────────────────────────────────────────── */

export const Avatar = ({ small = false }: { small?: boolean }) => (
  <View style={[styles.avatar, small && styles.avatarSmall]}>
    <Text style={[styles.avatarText, small && styles.avatarTextSmall]}>A</Text>
  </View>
);

/* ─── Transaction Row ───────────────────────────────────────────────────── */

const categoryIcons: Record<string, { bg: string; fg: string; letter: string }> = {
  Dining: { bg: '#FEF3C7', fg: '#D97706', letter: '🍽' },
  Shopping: { bg: '#EDE9FE', fg: '#7C3AED', letter: '🛍' },
  Utility: { bg: '#DBEAFE', fg: '#2563EB', letter: '⚡' },
  Transfer: { bg: '#D1FAE5', fg: '#059669', letter: '↗' },
};

export const TransactionRow = ({
  transaction,
  onPress,
}: {
  transaction: Transaction;
  onPress?: () => void;
}) => {
  const cat = categoryIcons[transaction.category] ?? categoryIcons.Dining;
  return (
    <Pressable
      onPress={onPress}
      style={({ pressed }) => [
        styles.transactionRow,
        pressed && { backgroundColor: colors.lineSoft },
      ]}
    >
      <View style={[styles.transactionIcon, { backgroundColor: cat.bg }]}>
        <Text style={{ fontSize: 18 }}>{cat.letter}</Text>
      </View>
      <View style={styles.transactionInfo}>
        <Text style={styles.transactionMerchant}>{transaction.merchant}</Text>
        <Text style={styles.transactionMeta}>
          {transaction.category} · {formatDate(transaction.date)}
        </Text>
      </View>
      <View style={styles.transactionAmount}>
        <Text style={styles.amount}>-{formatINR(transaction.amountPaise)}</Text>
        <Text
          style={[
            styles.statusBadge,
            transaction.status === 'successful' && { color: colors.green },
            transaction.status === 'pending' && { color: colors.amber },
            transaction.status === 'failed' && { color: colors.red },
          ]}
        >
          {transaction.status === 'successful'
            ? 'Successful'
            : transaction.status.charAt(0).toUpperCase() +
              transaction.status.slice(1)}
        </Text>
      </View>
      <ChevronRight size={16} color={colors.soft} style={{ marginLeft: 4 }} />
    </Pressable>
  );
};

/* ─── Search Box ────────────────────────────────────────────────────────── */

export const SearchBox = ({
  value,
  onChangeText,
  placeholder,
}: {
  value: string;
  onChangeText: (text: string) => void;
  placeholder: string;
}) => (
  <View style={styles.searchBox}>
    <Search size={18} color={colors.muted} />
    <TextInput
      value={value}
      onChangeText={onChangeText}
      placeholder={placeholder}
      placeholderTextColor={colors.placeholder}
      style={styles.searchInput}
    />
  </View>
);

/* ─── Chip ──────────────────────────────────────────────────────────────── */

export const Chip = ({
  label,
  selected,
  onPress,
}: {
  label: string;
  selected?: boolean;
  onPress: () => void;
}) => (
  <Pressable
    onPress={onPress}
    style={[styles.chip, selected && styles.chipSelected]}
  >
    <Text style={[styles.chipText, selected && styles.chipTextSelected]}>
      {label}
    </Text>
  </Pressable>
);

/* ─── Assistant Badge ───────────────────────────────────────────────────── */

export const AssistantBadge = () => (
  <View style={styles.assistantBadge}>
    <Sparkles size={13} color={colors.blue} />
    <Text style={styles.assistantBadgeText}>Hermes AI</Text>
  </View>
);

/* ─── Help Row ──────────────────────────────────────────────────────────── */

export const HelpRow = () => (
  <View style={styles.helpRow}>
    <CircleHelp size={14} color={colors.muted} />
    <Text style={styles.helpText}>
      Need help? Your data is simulated for this POC.
    </Text>
  </View>
);

/* ─── Separator ─────────────────────────────────────────────────────────── */

export const Separator = () => <View style={styles.separator} />;

/* ─── Styles ────────────────────────────────────────────────────────────── */

export const styles = StyleSheet.create({
  screen: {
    flexGrow: 1,
    backgroundColor: colors.background,
    padding: spacing.md,
    paddingBottom: 40,
  },

  // Card
  card: {
    backgroundColor: colors.surface,
    borderRadius: radii.md,
    padding: spacing.md,
    borderWidth: 1,
    borderColor: colors.line,
    ...shadows.card,
  },

  // Section header
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: spacing.lg,
    marginBottom: spacing.sm,
  },
  sectionTitle: {
    color: colors.ink,
    ...typography.h3,
  },
  action: {
    color: colors.brand,
    fontSize: 13,
    fontWeight: '600',
  },
  actionPressable: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 2,
  },

  // Avatar
  avatar: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: colors.brand,
    alignItems: 'center',
    justifyContent: 'center',
  },
  avatarSmall: {
    width: 32,
    height: 32,
    borderRadius: 16,
  },
  avatarText: {
    color: colors.surface,
    fontSize: 17,
    fontWeight: '700',
  },
  avatarTextSmall: {
    fontSize: 13,
  },

  // Transaction row
  transactionRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 14,
    paddingHorizontal: 4,
    gap: 12,
    borderBottomWidth: 1,
    borderBottomColor: colors.lineSoft,
  },
  transactionIcon: {
    width: 44,
    height: 44,
    borderRadius: 14,
    alignItems: 'center',
    justifyContent: 'center',
  },
  transactionInfo: {
    flex: 1,
  },
  transactionMerchant: {
    color: colors.ink,
    fontWeight: '600',
    fontSize: 15,
  },
  transactionMeta: {
    color: colors.muted,
    fontSize: 12,
    marginTop: 3,
  },
  transactionAmount: {
    alignItems: 'flex-end',
  },
  amount: {
    color: colors.ink,
    fontWeight: '700',
    fontSize: 14,
  },
  statusBadge: {
    fontSize: 11,
    marginTop: 3,
    fontWeight: '600',
  },

  // Search box
  searchBox: {
    height: 48,
    borderRadius: radii.sm,
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.line,
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 14,
    gap: 10,
    ...shadows.soft,
  },
  searchInput: {
    flex: 1,
    color: colors.ink,
    fontSize: 14,
  },

  // Chip
  chip: {
    borderRadius: radii.pill,
    paddingHorizontal: 16,
    paddingVertical: 9,
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.line,
    marginRight: 8,
  },
  chipSelected: {
    backgroundColor: colors.brand,
    borderColor: colors.brand,
  },
  chipText: {
    color: colors.muted,
    fontSize: 12,
    fontWeight: '600',
  },
  chipTextSelected: {
    color: colors.surface,
  },

  // Assistant badge
  assistantBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 5,
    alignSelf: 'flex-start',
    backgroundColor: colors.blueSoft,
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: radii.pill,
  },
  assistantBadgeText: {
    color: colors.blue,
    fontSize: 11,
    fontWeight: '700',
  },

  // Help row
  helpRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    paddingVertical: 14,
  },
  helpText: {
    color: colors.muted,
    fontSize: 11,
  },

  // Separator
  separator: {
    height: 1,
    backgroundColor: colors.line,
    marginVertical: spacing.md,
  },
});
