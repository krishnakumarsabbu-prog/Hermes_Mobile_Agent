import React, { useMemo, useState } from 'react';
import { Platform, StyleSheet, Text, View } from 'react-native';
import { useApp } from '../../src/AppContext';
import { colors, radii, shadows, spacing, typography } from '../../src/theme';
import { Chip, Screen, SearchBox, TransactionRow } from '../../src/ui';
import { router } from 'expo-router';

const filters = ['All', 'Dining', 'Shopping', 'Utility', 'Transfer'] as const;

export default function ActivityScreen() {
  const { transactions } = useApp();
  const [filter, setFilter] = useState<typeof filters[number]>('All');
  const [search, setSearch] = useState('');

  const visible = useMemo(
    () =>
      transactions.filter(
        (item) =>
          (filter === 'All' || item.category === filter) &&
          `${item.merchant} ${item.reference}`
            .toLowerCase()
            .includes(search.toLowerCase()),
      ),
    [transactions, filter, search],
  );

  return (
    <Screen style={styles.screenOverride}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.title}>Activity</Text>
        <Text style={styles.subtitle}>Your recent account activity</Text>
      </View>

      {/* Search */}
      <SearchBox
        value={search}
        onChangeText={setSearch}
        placeholder="Search merchant or reference"
      />

      {/* Filter chips */}
      <View style={styles.chips}>
        {filters.map((item) => (
          <Chip
            key={item}
            label={item}
            selected={filter === item}
            onPress={() => setFilter(item)}
          />
        ))}
      </View>

      {/* Results count */}
      <Text style={styles.resultCount}>
        {visible.length} transaction{visible.length !== 1 ? 's' : ''}
      </Text>

      {/* Transaction list */}
      {visible.length > 0 ? (
        <View style={styles.list}>
          {visible.map((transaction) => (
            <TransactionRow
              key={transaction.id}
              transaction={transaction}
              onPress={() =>
                router.push({
                  pathname: '/transaction/[id]',
                  params: { id: transaction.id },
                })
              }
            />
          ))}
        </View>
      ) : (
        <View style={styles.empty}>
          <Text style={styles.emptyIcon}>🔍</Text>
          <Text style={styles.emptyTitle}>No activity found</Text>
          <Text style={styles.emptyText}>
            Try another category or search term.
          </Text>
        </View>
      )}
    </Screen>
  );
}

const styles = StyleSheet.create({
  screenOverride: {
    paddingTop: Platform.OS === 'ios' ? 60 : 44,
  },

  header: {
    marginBottom: 20,
  },
  title: {
    color: colors.ink,
    ...typography.h1,
  },
  subtitle: {
    color: colors.muted,
    fontSize: 14,
    marginTop: 6,
  },

  chips: {
    flexDirection: 'row',
    marginTop: 16,
    marginBottom: 12,
  },

  resultCount: {
    color: colors.soft,
    fontSize: 12,
    fontWeight: '600',
    marginBottom: 8,
  },

  list: {
    backgroundColor: colors.surface,
    borderRadius: radii.md,
    paddingHorizontal: 14,
    borderWidth: 1,
    borderColor: colors.line,
    ...shadows.card,
  },

  empty: {
    alignItems: 'center',
    paddingTop: 80,
  },
  emptyIcon: {
    fontSize: 40,
    marginBottom: 16,
  },
  emptyTitle: {
    color: colors.ink,
    ...typography.h3,
  },
  emptyText: {
    color: colors.muted,
    marginTop: 8,
    fontSize: 14,
  },
});
