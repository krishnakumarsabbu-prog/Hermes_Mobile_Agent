import React, { useState } from 'react';
import {
  Modal,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Switch,
  Text,
  View,
} from 'react-native';
import { router } from 'expo-router';
import {
  Bell,
  ChevronRight,
  CreditCard,
  FileText,
  Fingerprint,
  HelpCircle,
  Lock,
  LogOut,
  MapPin,
  Phone,
  Settings,
  Shield,
  Sparkles,
  User,
} from 'lucide-react-native';
import { FargoAssistant } from '../../src/FargoAssistant';

export default function MenuScreen() {
  const [cardLocked, setCardLocked] = useState(false);
  const [biometricsEnabled, setBiometricsEnabled] = useState(true);
  const [assistantOpen, setAssistantOpen] = useState(false);

  const handleSignOff = () => {
    router.replace('/');
  };

  return (
    <View style={styles.root}>
      {/* ─── Top Header ─── */}
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Menu</Text>
      </View>

      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={styles.content}
        showsVerticalScrollIndicator={false}
      >
        {/* Profile Card */}
        <View style={styles.profileCard}>
          <View style={styles.avatarBox}>
            <Text style={styles.avatarText}>S</Text>
          </View>
          <View style={styles.profileInfo}>
            <Text style={styles.profileName}>Sabbu</Text>
            <Text style={styles.profileSub}>Customer since 2014 · Tier 1</Text>
          </View>
          <Pressable style={styles.editBtn}>
            <Settings size={20} color="#666666" />
          </Pressable>
        </View>

        {/* Fargo AI Assistant Banner */}
        <Pressable
          style={styles.fargoCard}
          onPress={() => setAssistantOpen(true)}
        >
          <View style={styles.fargoIcon}>
            <Sparkles size={20} color="#FFFFFF" />
          </View>
          <View style={styles.fargoInfo}>
            <Text style={styles.fargoTitle}>Fargo® Virtual Assistant</Text>
            <Text style={styles.fargoSub}>Ask questions, check balances, or transfer</Text>
          </View>
          <ChevronRight size={18} color="#FFFFFF" />
        </Pressable>

        {/* Account Management Group */}
        <Text style={styles.groupHeading}>Account & Services</Text>
        <View style={styles.menuGroup}>
          {/* Card Controls */}
          <View style={styles.menuItem}>
            <View style={[styles.itemIconBox, { backgroundColor: '#FEE2E2' }]}>
              <CreditCard size={20} color="#C8102E" />
            </View>
            <View style={styles.itemTextContainer}>
              <Text style={styles.itemTitle}>Lock Debit Card (...0987)</Text>
              <Text style={styles.itemSub}>Temporarily prevent new purchases</Text>
            </View>
            <Switch
              value={cardLocked}
              onValueChange={setCardLocked}
              trackColor={{ false: '#D1D5DB', true: '#C8102E' }}
              thumbColor="#FFFFFF"
            />
          </View>

          {/* Statements */}
          <Pressable style={styles.menuItem}>
            <View style={[styles.itemIconBox, { backgroundColor: '#E0E7FF' }]}>
              <FileText size={20} color="#4338CA" />
            </View>
            <View style={styles.itemTextContainer}>
              <Text style={styles.itemTitle}>Statements & Documents</Text>
              <Text style={styles.itemSub}>eStatements, tax forms & notices</Text>
            </View>
            <ChevronRight size={18} color="#999999" />
          </Pressable>

          {/* Alerts */}
          <Pressable style={styles.menuItem}>
            <View style={[styles.itemIconBox, { backgroundColor: '#FEF3C7' }]}>
              <Bell size={20} color="#D97706" />
            </View>
            <View style={styles.itemTextContainer}>
              <Text style={styles.itemTitle}>Manage Alerts</Text>
              <Text style={styles.itemSub}>Transaction and security alerts</Text>
            </View>
            <ChevronRight size={18} color="#999999" />
          </Pressable>
        </View>

        {/* Security & Settings Group */}
        <Text style={styles.groupHeading}>Security & Preferences</Text>
        <View style={styles.menuGroup}>
          {/* Biometrics */}
          <View style={styles.menuItem}>
            <View style={[styles.itemIconBox, { backgroundColor: '#ECFDF5' }]}>
              <Fingerprint size={20} color="#059669" />
            </View>
            <View style={styles.itemTextContainer}>
              <Text style={styles.itemTitle}>Face ID / Biometrics</Text>
              <Text style={styles.itemSub}>Quick sign-on with face scan</Text>
            </View>
            <Switch
              value={biometricsEnabled}
              onValueChange={setBiometricsEnabled}
              trackColor={{ false: '#D1D5DB', true: '#059669' }}
              thumbColor="#FFFFFF"
            />
          </View>

          {/* Security Center */}
          <Pressable style={styles.menuItem}>
            <View style={[styles.itemIconBox, { backgroundColor: '#F3F4F6' }]}>
              <Shield size={20} color="#374151" />
            </View>
            <View style={styles.itemTextContainer}>
              <Text style={styles.itemTitle}>Security Center</Text>
              <Text style={styles.itemSub}>2-Step verification & password</Text>
            </View>
            <ChevronRight size={18} color="#999999" />
          </Pressable>
        </View>

        {/* Support */}
        <Text style={styles.groupHeading}>Support</Text>
        <View style={styles.menuGroup}>
          <Pressable style={styles.menuItem}>
            <View style={[styles.itemIconBox, { backgroundColor: '#EFF6FF' }]}>
              <Phone size={20} color="#2563EB" />
            </View>
            <View style={styles.itemTextContainer}>
              <Text style={styles.itemTitle}>Contact Customer Service</Text>
              <Text style={styles.itemSub}>1-800-869-3557 · 24/7 Support</Text>
            </View>
            <ChevronRight size={18} color="#999999" />
          </Pressable>

          <Pressable style={styles.menuItem}>
            <View style={[styles.itemIconBox, { backgroundColor: '#F3F4F6' }]}>
              <MapPin size={20} color="#374151" />
            </View>
            <View style={styles.itemTextContainer}>
              <Text style={styles.itemTitle}>Find ATM or Branch</Text>
              <Text style={styles.itemSub}>Nearby Wells Fargo locations</Text>
            </View>
            <ChevronRight size={18} color="#999999" />
          </Pressable>
        </View>

        {/* Sign Off Button */}
        <Pressable
          onPress={handleSignOff}
          style={({ pressed }) => [
            styles.signOffBtn,
            pressed && { backgroundColor: '#A60E26' },
          ]}
        >
          <LogOut size={18} color="#FFFFFF" />
          <Text style={styles.signOffBtnText}>Sign Off</Text>
        </Pressable>
      </ScrollView>

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

  // Profile Card
  profileCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 18,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 14,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.06,
    shadowRadius: 6,
    elevation: 2,
  },
  avatarBox: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: '#C8102E',
    alignItems: 'center',
    justifyContent: 'center',
  },
  avatarText: {
    color: '#FFFFFF',
    fontSize: 18,
    fontWeight: '800',
  },
  profileInfo: {
    flex: 1,
  },
  profileName: {
    fontSize: 17,
    fontWeight: '700',
    color: '#111111',
  },
  profileSub: {
    fontSize: 12,
    color: '#666666',
    marginTop: 2,
  },
  editBtn: {
    padding: 6,
  },

  // Fargo Card
  fargoCard: {
    backgroundColor: '#582C83',
    borderRadius: 16,
    padding: 16,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 14,
    shadowColor: '#582C83',
    shadowOffset: { width: 0, height: 3 },
    shadowOpacity: 0.2,
    shadowRadius: 6,
    elevation: 3,
  },
  fargoIcon: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: 'rgba(255,255,255,0.2)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  fargoInfo: {
    flex: 1,
  },
  fargoTitle: {
    fontSize: 15,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  fargoSub: {
    fontSize: 12,
    color: 'rgba(255,255,255,0.85)',
    marginTop: 2,
  },

  groupHeading: {
    fontSize: 13,
    fontWeight: '700',
    color: '#666666',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginTop: 6,
    marginLeft: 4,
  },
  menuGroup: {
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    paddingVertical: 4,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.06,
    shadowRadius: 6,
    elevation: 2,
  },
  menuItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 14,
    paddingHorizontal: 16,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: '#F0F0F0',
    gap: 14,
  },
  itemIconBox: {
    width: 38,
    height: 38,
    borderRadius: 10,
    alignItems: 'center',
    justifyContent: 'center',
  },
  itemTextContainer: {
    flex: 1,
  },
  itemTitle: {
    fontSize: 15,
    fontWeight: '600',
    color: '#111111',
  },
  itemSub: {
    fontSize: 12,
    color: '#666666',
    marginTop: 2,
  },

  signOffBtn: {
    backgroundColor: '#C8102E',
    height: 50,
    borderRadius: 12,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    marginTop: 10,
    marginBottom: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.15,
    shadowRadius: 4,
    elevation: 3,
  },
  signOffBtnText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '700',
  },
});
