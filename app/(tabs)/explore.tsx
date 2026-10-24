import React from 'react';
import {
  Image,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { router } from 'expo-router';
import {
  Award,
  ChevronRight,
  CreditCard,
  Home,
  Percent,
  PiggyBank,
  Shield,
  TrendingUp,
} from 'lucide-react-native';

export default function ExploreScreen() {
  return (
    <View style={styles.root}>
      {/* ─── Top Header ─── */}
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Explore Products & Offers</Text>
      </View>

      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={styles.content}
        showsVerticalScrollIndicator={false}
      >
        {/* Featured Card Offer */}
        <View style={styles.featuredCard}>
          <View style={styles.cardBadge}>
            <Award size={14} color="#C8102E" />
            <Text style={styles.cardBadgeText}>FEATURED OFFER</Text>
          </View>
          <Text style={styles.featuredTitle}>Wells Fargo Active Cash® Card</Text>
          <Text style={styles.featuredReward}>Earn unlimited 2% cash rewards</Text>
          <Text style={styles.featuredSub}>
            Plus, earn a $200 cash rewards bonus when you spend $500 in purchases in the first 3 months.
          </Text>
          <Pressable style={styles.applyBtn}>
            <Text style={styles.applyBtnText}>Learn More & Apply</Text>
          </Pressable>
        </View>

        {/* Product Categories */}
        <Text style={styles.sectionTitle}>Banking & Borrowing</Text>
        <View style={styles.categoryList}>
          {/* Credit Cards */}
          <Pressable style={styles.categoryItem}>
            <View style={[styles.iconBox, { backgroundColor: '#FEE2E2' }]}>
              <CreditCard size={22} color="#DC2626" />
            </View>
            <View style={styles.categoryInfo}>
              <Text style={styles.categoryName}>Credit Cards</Text>
              <Text style={styles.categoryDesc}>Cash back, travel & 0% intro APR</Text>
            </View>
            <ChevronRight size={18} color="#999999" />
          </Pressable>

          {/* Savings & CDs */}
          <Pressable style={styles.categoryItem}>
            <View style={[styles.iconBox, { backgroundColor: '#FEF3C7' }]}>
              <PiggyBank size={22} color="#D97706" />
            </View>
            <View style={styles.categoryInfo}>
              <Text style={styles.categoryName}>Savings Accounts & CDs</Text>
              <Text style={styles.categoryDesc}>High-yield fixed rates & Way2Save</Text>
            </View>
            <ChevronRight size={18} color="#999999" />
          </Pressable>

          {/* Home Lending */}
          <Pressable style={styles.categoryItem}>
            <View style={[styles.iconBox, { backgroundColor: '#EDE9FE' }]}>
              <Home size={22} color="#7C3AED" />
            </View>
            <View style={styles.categoryInfo}>
              <Text style={styles.categoryName}>Mortgages & Refinancing</Text>
              <Text style={styles.categoryDesc}>Check today's competitive rates</Text>
            </View>
            <ChevronRight size={18} color="#999999" />
          </Pressable>

          {/* Investing */}
          <Pressable style={styles.categoryItem}>
            <View style={[styles.iconBox, { backgroundColor: '#E0E7FF' }]}>
              <TrendingUp size={22} color="#4338CA" />
            </View>
            <View style={styles.categoryInfo}>
              <Text style={styles.categoryName}>Investing & Retirement</Text>
              <Text style={styles.categoryDesc}>Wells Fargo Advisors automated investing</Text>
            </View>
            <ChevronRight size={18} color="#999999" />
          </Pressable>
        </View>

        {/* Financial Planning Tools */}
        <Text style={styles.sectionTitle}>Planning & Tools</Text>
        <Pressable
          style={styles.toolCard}
          onPress={() => router.push('/spending')}
        >
          <View style={styles.toolIconBox}>
            <Percent size={24} color="#059669" />
          </View>
          <View style={styles.toolInfo}>
            <Text style={styles.toolTitle}>Spending & Budget Analysis</Text>
            <Text style={styles.toolSub}>Track cash flow and category breakdown</Text>
          </View>
          <ChevronRight size={18} color="#999999" />
        </Pressable>
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

  // Featured Offer Card
  featuredCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.06,
    shadowRadius: 6,
    elevation: 2,
    gap: 8,
  },
  cardBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  cardBadgeText: {
    fontSize: 11,
    fontWeight: '800',
    color: '#C8102E',
    letterSpacing: 0.8,
  },
  featuredTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: '#111111',
  },
  featuredReward: {
    fontSize: 15,
    fontWeight: '600',
    color: '#059669',
  },
  featuredSub: {
    fontSize: 13,
    color: '#555555',
    lineHeight: 18,
  },
  applyBtn: {
    backgroundColor: '#C8102E',
    borderRadius: 10,
    paddingVertical: 12,
    alignItems: 'center',
    marginTop: 6,
  },
  applyBtnText: {
    color: '#FFFFFF',
    fontWeight: '700',
    fontSize: 14,
  },

  sectionTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#111111',
    marginTop: 6,
  },
  categoryList: {
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    paddingVertical: 4,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.06,
    shadowRadius: 6,
    elevation: 2,
  },
  categoryItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 14,
    paddingHorizontal: 16,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: '#F0F0F0',
    gap: 14,
  },
  iconBox: {
    width: 44,
    height: 44,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
  },
  categoryInfo: {
    flex: 1,
  },
  categoryName: {
    fontSize: 15,
    fontWeight: '600',
    color: '#111111',
  },
  categoryDesc: {
    fontSize: 12,
    color: '#666666',
    marginTop: 2,
  },

  // Tool Card
  toolCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 16,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 14,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.06,
    shadowRadius: 6,
    elevation: 2,
  },
  toolIconBox: {
    width: 48,
    height: 48,
    borderRadius: 14,
    backgroundColor: '#ECFDF5',
    alignItems: 'center',
    justifyContent: 'center',
  },
  toolInfo: {
    flex: 1,
  },
  toolTitle: {
    fontSize: 15,
    fontWeight: '700',
    color: '#111111',
  },
  toolSub: {
    fontSize: 12,
    color: '#666666',
    marginTop: 2,
  },
});
