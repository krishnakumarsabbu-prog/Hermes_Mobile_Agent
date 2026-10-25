import React, { useRef, useEffect, useState } from 'react';
import {
  ActivityIndicator,
  Animated,
  Dimensions,
  Image,
  Modal,
  Platform,
  Pressable,
  RefreshControl,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { router } from 'expo-router';
import {
  Bell,
  ChevronRight,
  CreditCard,
  Home as HomeIcon,
  MessageSquare,
  Mic,
  PiggyBank,
  Search,
  Smartphone,
  Sparkles,
  TrendingUp,
  Wallet,
} from 'lucide-react-native';
import { useApp } from '../../src/AppContext';
import { colors, radii, shadows, spacing, typography } from '../../src/theme';
import { formatINR } from '../../src/utils';
import { Card, TransactionRow } from '../../src/ui';
import { FargoAssistant } from '../../src/FargoAssistant';

const { width: SCREEN_WIDTH } = Dimensions.get('window');

export default function AccountsScreen() {
  const { account, transactions, loading, error, refresh } = useApp();
  const [assistantOpen, setAssistantOpen] = useState(false);

  // Dynamic greeting based on time of day
  const hour = new Date().getHours();
  const greetingTime =
    hour < 12 ? 'Good morning' : hour < 17 ? 'Good afternoon' : 'Good evening';

  // Entry animation
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const slideAnim = useRef(new Animated.Value(15)).current;

  useEffect(() => {
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
    ]).start();
  }, []);

  const handleSignOff = () => {
    router.replace('/');
  };

  const handleOpenAssistant = () => {
    setAssistantOpen(true);
  };

  return (
    <View style={styles.root}>
      {/* ─── Top Simulated iOS Status Bar (9:41 AM, Wifi, Battery) ─── */}
      <View style={styles.statusBar}>
        <Text style={styles.statusTime}>9:41</Text>
        <View style={styles.statusIcons}>
          <Text style={styles.statusIcon}>📶</Text>
          <Text style={styles.statusIcon}>ᯤ</Text>
          <View style={styles.batteryPill}>
            <View style={styles.batteryLevel} />
          </View>
        </View>
      </View>

      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={styles.content}
        showsVerticalScrollIndicator={false}
        refreshControl={
          <RefreshControl
            refreshing={loading && transactions.length > 0}
            onRefresh={refresh}
            tintColor="#C8102E"
          />
        }
      >
        {/* ─── Header: Need Help? Search Pill | Bell | Sign off ─── */}
        <Animated.View style={[styles.headerRow, { opacity: fadeAnim }]}>
          {/* Need help pill with Fargo Assistant badge */}
          <Pressable
            onPress={handleOpenAssistant}
            style={({ pressed }) => [
              styles.needHelpPill,
              pressed && { opacity: 0.8 },
            ]}
          >
            <Search size={16} color="#666666" />
            <Text style={styles.needHelpText}>Need help?</Text>
            {/* Fargo Icon + Red Badge '3' */}
            <View style={styles.fargoBadgeWrapper}>
              <View style={styles.fargoIconBox}>
                <Text style={styles.fargoLetter}>F</Text>
              </View>
              <View style={styles.badgeCount}>
                <Text style={styles.badgeText}>3</Text>
              </View>
            </View>
          </Pressable>

          {/* Right: Chat Icon, Bell & Sign Off */}
          <View style={styles.headerRight}>
            <Pressable
              onPress={handleOpenAssistant}
              style={({ pressed }) => [
                styles.chatHeaderBtn,
                pressed && { opacity: 0.75, transform: [{ scale: 0.95 }] },
              ]}
              accessibilityLabel="Open Fargo AI Chat"
            >
              <MessageSquare size={21} color="#582C83" strokeWidth={2} />
              <View style={styles.chatHeaderBadge}>
                <Sparkles size={8} color="#FFFFFF" />
              </View>
            </Pressable>
            <Pressable style={styles.bellBtn}>
              <Bell size={21} color="#333333" strokeWidth={1.75} />
            </Pressable>
            <Pressable onPress={handleSignOff} style={styles.signOffBtn}>
              <Text style={styles.signOffText}>Sign off</Text>
            </Pressable>
          </View>
        </Animated.View>

        {/* ─── Greeting Section: "Good evening, Sabbu" ─── */}
        <Animated.View
          style={[
            styles.greetingSection,
            {
              opacity: fadeAnim,
              transform: [{ translateY: slideAnim }],
            },
          ]}
        >
          <Text style={styles.greetingText}>{greetingTime}, Sabbu</Text>
        </Animated.View>

        {/* ─── Account Cards ─── */}
        <Animated.View
          style={[
            styles.cardsSection,
            {
              opacity: fadeAnim,
              transform: [{ translateY: slideAnim }],
            },
          ]}
        >
          {/* Card 1: EVERYDAY CHECKING */}
          <Pressable
            style={({ pressed }) => [
              styles.accountCard,
              pressed && styles.cardPressed,
            ]}
            onPress={() => router.push('/(tabs)/pay')}
          >
            <View style={styles.accountCardTop}>
              <Text style={styles.accountTitle}>EVERYDAY CHECKING...0987</Text>
            </View>
            <Text style={styles.accountAmount}>$2,667.93</Text>
            <Text style={styles.accountSubtitle}>Available balance</Text>
          </Pressable>

          {/* Card 2: WAY2SAVE */}
          <Pressable
            style={({ pressed }) => [
              styles.accountCard,
              pressed && styles.cardPressed,
            ]}
            onPress={() => router.push('/(tabs)/pay')}
          >
            <View style={styles.accountCardTop}>
              <Text style={styles.accountTitle}>WAY2SAVE ...6543</Text>
            </View>
            <Text style={styles.accountAmount}>$1,636.85</Text>
            <Text style={styles.accountSubtitle}>Available balance</Text>
          </Pressable>

          {/* ─── Open an Account Section ─── */}
          <View style={styles.openAccountCard}>
            <View style={styles.openAccountHeader}>
              <Text style={styles.openAccountTitle}>Open an account</Text>
              <Pressable
                onPress={() => router.push('/(tabs)/explore')}
                style={styles.exploreAllBtn}
              >
                <Text style={styles.exploreAllText}>Explore all</Text>
                <ChevronRight size={15} color="#5B4BC4" />
              </Pressable>
            </View>

            <View style={styles.productRow}>
              {/* Checking */}
              <Pressable
                style={styles.productItem}
                onPress={() => router.push('/(tabs)/explore')}
              >
                <View style={[styles.productIconBox, { backgroundColor: '#EDE9FE' }]}>
                  <Smartphone size={24} color="#7C3AED" />
                </View>
                <Text style={styles.productLabel}>Checking</Text>
              </Pressable>

              {/* Savings & CDs */}
              <Pressable
                style={styles.productItem}
                onPress={() => router.push('/(tabs)/explore')}
              >
                <View style={[styles.productIconBox, { backgroundColor: '#FEF3C7' }]}>
                  <PiggyBank size={24} color="#D97706" />
                </View>
                <Text style={styles.productLabel}>Savings & CDs</Text>
              </Pressable>

              {/* Credit cards */}
              <Pressable
                style={styles.productItem}
                onPress={() => router.push('/(tabs)/explore')}
              >
                <View style={[styles.productIconBox, { backgroundColor: '#FEE2E2' }]}>
                  <CreditCard size={24} color="#DC2626" />
                </View>
                <Text style={styles.productLabel}>Credit cards</Text>
              </Pressable>

              {/* Loans */}
              <Pressable
                style={styles.productItem}
                onPress={() => router.push('/(tabs)/explore')}
              >
                <View style={[styles.productIconBox, { backgroundColor: '#E0E7FF' }]}>
                  <HomeIcon size={24} color="#4338CA" />
                </View>
                <Text style={styles.productLabel}>Loans</Text>
              </Pressable>
            </View>
          </View>

          {/* ─── FICO Score Card ─── */}
          <Pressable
            style={({ pressed }) => [
              styles.ficoCard,
              pressed && styles.cardPressed,
            ]}
            onPress={() => router.push('/spending')}
          >
            <View style={styles.ficoGaugeContainer}>
              <View style={styles.ficoRing}>
                <Text style={styles.ficoNumber}>820</Text>
              </View>
            </View>

            <View style={styles.ficoDetails}>
              <Text style={styles.ficoHeadline}>
                Your FICO® Score went up 20 points
              </Text>
              <Text style={styles.ficoSubtext}>Updated 12/19/2023</Text>
            </View>

            <ChevronRight size={18} color="#999999" />
          </Pressable>

          {/* ─── Build for your future Promotional Banner ─── */}
          <Pressable
            style={styles.promoCard}
            onPress={() => router.push('/(tabs)/explore')}
          >
            <Image
              source={{
                uri: 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=400&q=80',
              }}
              style={styles.promoImage}
              resizeMode="cover"
            />
            <View style={styles.promoInfo}>
              <Text style={styles.promoTitle}>Build for your future</Text>
              <Text style={styles.promoSubtitle}>Set financial goals</Text>
            </View>
            <ChevronRight size={18} color="#999999" />
          </Pressable>

          {/* ─── Recent Activity Section ─── */}
          <View style={styles.activityHeader}>
            <Text style={styles.activityHeading}>Recent Activity</Text>
            <Pressable
              onPress={() => router.push('/(tabs)/pay')}
              style={styles.seeAllBtn}
            >
              <Text style={styles.seeAllText}>See all</Text>
              <ChevronRight size={14} color="#C8102E" />
            </Pressable>
          </View>

          <View style={styles.activityCard}>
            {transactions.slice(0, 4).map((transaction) => (
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
        </Animated.View>
      </ScrollView>

      {/* ─── Floating Fargo AI Chat & Voice FAB ─── */}
      <Pressable
        onPress={handleOpenAssistant}
        style={({ pressed }) => [
          styles.fabContainer,
          pressed && styles.fabPressed,
        ]}
        accessibilityLabel="Ask Fargo AI Assistant"
      >
        <View style={styles.fabInner}>
          <View style={styles.fabIconBox}>
            <Sparkles size={16} color="#FFFFFF" />
          </View>
          <View style={styles.fabTextCol}>
            <Text style={styles.fabTitle}>Ask Fargo</Text>
            <Text style={styles.fabSub}>Chat & Voice</Text>
          </View>
          <View style={styles.fabMicPill}>
            <Mic size={14} color="#582C83" />
          </View>
        </View>
      </Pressable>

      {/* ─── Fargo AI Chat & Voice Modal ─── */}
      <Modal
        visible={assistantOpen}
        animationType="slide"
        presentationStyle="pageSheet"
        onRequestClose={() => setAssistantOpen(false)}
      >
        <FargoAssistant isModal={true} onClose={() => setAssistantOpen(false)} />
      </Modal>
    </View>
  );
}

const styles = StyleSheet.create({
  root: {
    flex: 1,
    backgroundColor: '#F3F4F6',
  },
  statusBar: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 24,
    paddingTop: Platform.OS === 'ios' ? 50 : 16,
    paddingBottom: 6,
    backgroundColor: '#F3F4F6',
  },
  statusTime: {
    fontSize: 15,
    fontWeight: '700',
    color: '#111111',
  },
  statusIcons: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  statusIcon: {
    fontSize: 13,
    color: '#111111',
  },
  batteryPill: {
    width: 22,
    height: 11,
    borderWidth: 1.2,
    borderColor: '#111111',
    borderRadius: 3.5,
    padding: 1.5,
  },
  batteryLevel: {
    flex: 1,
    backgroundColor: '#111111',
    borderRadius: 1.5,
  },

  scrollView: {
    flex: 1,
  },
  content: {
    paddingHorizontal: 16,
    paddingBottom: 40,
    paddingTop: 8,
  },

  // Header Row
  headerRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 20,
    marginTop: 4,
  },
  needHelpPill: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FFFFFF',
    borderRadius: 24,
    paddingLeft: 12,
    paddingRight: 6,
    paddingVertical: 6,
    gap: 8,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1.5 },
    shadowOpacity: 0.08,
    shadowRadius: 4,
    elevation: 2,
  },
  needHelpText: {
    fontSize: 14,
    color: '#555555',
    fontWeight: '500',
  },
  fargoBadgeWrapper: {
    position: 'relative',
    marginLeft: 4,
  },
  fargoIconBox: {
    width: 28,
    height: 28,
    borderRadius: 14,
    backgroundColor: '#582C83',
    alignItems: 'center',
    justifyContent: 'center',
  },
  fargoLetter: {
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: '800',
  },
  badgeCount: {
    position: 'absolute',
    top: -4,
    right: -4,
    backgroundColor: '#C8102E',
    width: 16,
    height: 16,
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1.5,
    borderColor: '#FFFFFF',
  },
  badgeText: {
    color: '#FFFFFF',
    fontSize: 9,
    fontWeight: '800',
  },

  headerRight: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 14,
  },
  chatHeaderBtn: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: '#F3E8FF',
    alignItems: 'center',
    justifyContent: 'center',
    position: 'relative',
  },
  chatHeaderBadge: {
    position: 'absolute',
    top: -2,
    right: -2,
    backgroundColor: '#582C83',
    width: 14,
    height: 14,
    borderRadius: 7,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1.5,
    borderColor: '#FFFFFF',
  },
  bellBtn: {
    padding: 4,
  },
  signOffBtn: {
    paddingVertical: 4,
  },
  signOffText: {
    color: '#222222',
    fontSize: 14,
    fontWeight: '600',
  },

  // Greeting
  greetingSection: {
    marginBottom: 20,
    paddingLeft: 4,
  },
  greetingText: {
    fontSize: 28,
    fontWeight: '600',
    color: '#222222',
    letterSpacing: -0.4,
  },

  // Account Cards
  cardsSection: {
    gap: 14,
  },
  accountCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.06,
    shadowRadius: 6,
    elevation: 2,
  },
  cardPressed: {
    opacity: 0.94,
    transform: [{ scale: 0.995 }],
  },
  accountCardTop: {
    marginBottom: 8,
  },
  accountTitle: {
    fontSize: 13,
    fontWeight: '700',
    color: '#333333',
    letterSpacing: 0.6,
  },
  accountAmount: {
    fontSize: 30,
    fontWeight: '700',
    color: '#111111',
    letterSpacing: -0.5,
    marginBottom: 6,
  },
  accountSubtitle: {
    fontSize: 13,
    color: '#666666',
    fontWeight: '400',
  },

  // Open an account Card
  openAccountCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.06,
    shadowRadius: 6,
    elevation: 2,
  },
  openAccountHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 18,
  },
  openAccountTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#111111',
  },
  exploreAllBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 2,
  },
  exploreAllText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#5B4BC4',
  },
  productRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
  },
  productItem: {
    alignItems: 'center',
    width: '23%',
  },
  productIconBox: {
    width: 52,
    height: 52,
    borderRadius: 14,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 8,
  },
  productLabel: {
    fontSize: 12,
    color: '#444444',
    fontWeight: '500',
    textAlign: 'center',
    lineHeight: 15,
  },

  // FICO Card
  ficoCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 18,
    flexDirection: 'row',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.06,
    shadowRadius: 6,
    elevation: 2,
  },
  ficoGaugeContainer: {
    marginRight: 16,
  },
  ficoRing: {
    width: 54,
    height: 54,
    borderRadius: 27,
    borderWidth: 4,
    borderColor: '#059669',
    alignItems: 'center',
    justifyContent: 'center',
  },
  ficoNumber: {
    fontSize: 16,
    fontWeight: '800',
    color: '#111111',
  },
  ficoDetails: {
    flex: 1,
  },
  ficoHeadline: {
    fontSize: 14,
    fontWeight: '700',
    color: '#111111',
    marginBottom: 4,
  },
  ficoSubtext: {
    fontSize: 12,
    color: '#777777',
  },

  // Promo Banner
  promoCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 14,
    flexDirection: 'row',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.06,
    shadowRadius: 6,
    elevation: 2,
    gap: 14,
  },
  promoImage: {
    width: 60,
    height: 60,
    borderRadius: 12,
  },
  promoInfo: {
    flex: 1,
  },
  promoTitle: {
    fontSize: 15,
    fontWeight: '700',
    color: '#111111',
    marginBottom: 2,
  },
  promoSubtitle: {
    fontSize: 13,
    color: '#666666',
  },

  // Activity Section
  activityHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: 10,
    marginBottom: 10,
  },
  activityHeading: {
    fontSize: 17,
    fontWeight: '700',
    color: '#111111',
  },
  seeAllBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 2,
  },
  seeAllText: {
    fontSize: 13,
    fontWeight: '600',
    color: '#C8102E',
  },
  activityCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    paddingHorizontal: 16,
    paddingVertical: 8,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.06,
    shadowRadius: 6,
    elevation: 2,
  },

  // Floating Fargo AI FAB
  fabContainer: {
    position: 'absolute',
    bottom: 22,
    right: 16,
    borderRadius: 30,
    backgroundColor: '#582C83',
    shadowColor: '#582C83',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.35,
    shadowRadius: 8,
    elevation: 6,
    zIndex: 99,
  },
  fabPressed: {
    transform: [{ scale: 0.95 }],
    opacity: 0.9,
  },
  fabInner: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 8,
    paddingHorizontal: 14,
    gap: 8,
  },
  fabIconBox: {
    width: 28,
    height: 28,
    borderRadius: 14,
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  fabTextCol: {
    justifyContent: 'center',
  },
  fabTitle: {
    fontSize: 13,
    fontWeight: '800',
    color: '#FFFFFF',
    letterSpacing: -0.2,
  },
  fabSub: {
    fontSize: 9.5,
    fontWeight: '600',
    color: 'rgba(255, 255, 255, 0.75)',
  },
  fabMicPill: {
    width: 24,
    height: 24,
    borderRadius: 12,
    backgroundColor: '#FFFFFF',
    alignItems: 'center',
    justifyContent: 'center',
    marginLeft: 2,
  },
});
