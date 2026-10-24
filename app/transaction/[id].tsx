import React, { useEffect, useState } from 'react';
import { ActivityIndicator, StyleSheet, Text, View } from 'react-native';
import { router, useLocalSearchParams } from 'expo-router';
import { ArrowLeft, CircleCheck as CheckCircle2 } from 'lucide-react-native';
import { useApp } from '../../src/AppContext';
import { apiMode } from '../../src/config';
import { api } from '../../src/apiClient';
import { colors, radii } from '../../src/theme';
import { formatDateTime, formatINR } from '../../src/utils';
import { Card, Screen } from '../../src/ui';
import { Transaction } from '../../src/models';

export default function TransactionDetail() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const { transactions } = useApp();
  const [txn, setTxn] = useState<Transaction | undefined>(transactions.find((item) => item.id === id));
  const [loading, setLoading] = useState(!txn);

  useEffect(() => {
    if (txn) return;
    if (apiMode !== 'http') return;
    setLoading(true);
    api.get<Record<string, unknown>>(`/api/v1/transactions/${id}`)
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

  if (loading && !txn) {
    return <Screen><View style={styles.loading}><ActivityIndicator color={colors.teal} size="large" /></View></Screen>;
  }
  if (!txn) return <Screen><Text style={styles.title}>Transaction not found</Text></Screen>;

  return (
    <Screen>
      <View style={styles.header}>
        <ArrowLeft onPress={() => router.back()} color={colors.ink} size={21} />
        <Text style={styles.headerTitle}>Transaction details</Text>
        <View style={{ width: 21 }} />
      </View>
      <View style={styles.icon}>
        <CheckCircle2 color={colors.teal} size={30} />
      </View>
      <Text style={styles.merchant}>{txn.merchant}</Text>
      <Text style={styles.amount}>-{formatINR(txn.amountPaise)}</Text>
      <Text style={styles.status}>Successful</Text>
      <Card style={styles.card}>
        <Detail label="Category" value={txn.category} />
        <Detail label="Date" value={formatDateTime(txn.date)} />
        <Detail label="Reference" value={txn.reference} />
        <Detail label="Status" value={txn.status} />
      </Card>
    </Screen>
  );
}

function Detail({ label, value }: { label: string; value: string }) {
  return (
    <View style={styles.detail}>
      <Text style={styles.label}>{label}</Text>
      <Text style={styles.value}>{value}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  header: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginTop: 8, marginBottom: 42 },
  headerTitle: { color: colors.ink, fontWeight: '700', fontSize: 16 },
  loading: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  icon: { alignSelf: 'center', width: 64, height: 64, borderRadius: 32, backgroundColor: colors.tealSoft, alignItems: 'center', justifyContent: 'center' },
  merchant: { textAlign: 'center', color: colors.ink, fontSize: 23, fontWeight: '700', marginTop: 16 },
  amount: { textAlign: 'center', color: colors.ink, fontSize: 28, fontWeight: '700', marginTop: 8 },
  status: { alignSelf: 'center', color: colors.green, backgroundColor: colors.tealSoft, borderRadius: radii.pill, paddingHorizontal: 12, paddingVertical: 6, fontSize: 11, fontWeight: '700', marginTop: 9 },
  card: { marginTop: 30 },
  detail: { flexDirection: 'row', justifyContent: 'space-between', borderBottomWidth: 1, borderBottomColor: colors.line, paddingVertical: 14 },
  label: { color: colors.muted, fontSize: 13 },
  value: { color: colors.ink, fontSize: 13, fontWeight: '700' },
  title: { color: colors.ink, fontSize: 24, fontWeight: '700' },
});
