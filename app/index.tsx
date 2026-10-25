import React, { useState, useRef, useEffect } from 'react';
import {
  Animated,
  Dimensions,
  Image,
  KeyboardAvoidingView,
  Platform,
  Pressable,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';
import { router } from 'expo-router';
import { Lock, User, Eye, EyeOff } from 'lucide-react-native';

const { width: SCREEN_WIDTH, height: SCREEN_HEIGHT } = Dimensions.get('window');

export default function LoginScreen() {
  const [username, setUsername] = useState('sabbu');
  const [password, setPassword] = useState('sabbu');
  const [showPassword, setShowPassword] = useState(false);
  const [focusedField, setFocusedField] = useState<string | null>(null);

  // Smooth entrance animation
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const slideAnim = useRef(new Animated.Value(15)).current;

  useEffect(() => {
    Animated.parallel([
      Animated.timing(fadeAnim, {
        toValue: 1,
        duration: 700,
        useNativeDriver: true,
      }),
      Animated.timing(slideAnim, {
        toValue: 0,
        duration: 700,
        useNativeDriver: true,
      }),
    ]).start();
  }, []);

  const handleSignOn = () => {
    router.replace('/(tabs)');
  };

  return (
    <View style={styles.root}>
      {/* ─── Background Scenic Stagecoach / Autumn Landscape ─── */}
      <Image
        source={{
          uri: 'https://images.pexels.com/photos/417074/pexels-photo-417074.jpeg?auto=compress&cs=tinysrgb&w=1200',
        }}
        style={styles.backgroundImage}
        resizeMode="cover"
      />

      {/* ─── Soft dark vignette over the top and middle ─── */}
      <View style={styles.vignetteOverlay} />

      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
        style={styles.container}
      >
        {/* ─── Top Simulated iOS Status Bar (Matching reference 9:41 AM) ─── */}
        <View style={styles.statusBarRow}>
          <View style={styles.carrierRow}>
            <View style={styles.signalDots}>
              <View style={[styles.dot, styles.dotFilled]} />
              <View style={[styles.dot, styles.dotFilled]} />
              <View style={[styles.dot, styles.dotFilled]} />
              <View style={[styles.dot, styles.dotFilled]} />
              <View style={[styles.dot, styles.dotEmpty]} />
            </View>
            <Text style={styles.statusText}>AT&T</Text>
            <Text style={styles.wifiIcon}>📶</Text>
          </View>
          <Text style={[styles.statusText, styles.statusTime]}>9:41 AM</Text>
          <View style={styles.batteryRow}>
            <Text style={styles.statusText}>100%</Text>
            <View style={styles.batteryPill}>
              <View style={styles.batteryLevel} />
            </View>
          </View>
        </View>

        {/* ─── Center Red Box Logo & Form ─── */}
        <Animated.View
          style={[
            styles.centerSection,
            {
              opacity: fadeAnim,
              transform: [{ translateY: slideAnim }],
            },
          ]}
        >
          {/* Authentic Wells Fargo Red Square Logo */}
          <View style={styles.logoSquare}>
            <Text style={styles.wellsText}>WELLS</Text>
            <Text style={styles.fargoText}>FARGO</Text>
          </View>

          {/* Unified Frosted Glass Input Card */}
          <View style={styles.glassCard}>
            {/* Username Row */}
            <View
              style={[
                styles.inputRow,
                focusedField === 'username' && styles.inputRowFocused,
              ]}
            >
              <User
                size={22}
                color={
                  focusedField === 'username'
                    ? '#FFFFFF'
                    : 'rgba(255, 255, 255, 0.65)'
                }
                strokeWidth={1.75}
              />
              <TextInput
                value={username}
                onChangeText={setUsername}
                placeholder="Username"
                placeholderTextColor="rgba(255, 255, 255, 0.6)"
                style={styles.textInput}
                autoCapitalize="none"
                autoCorrect={false}
                onFocus={() => setFocusedField('username')}
                onBlur={() => setFocusedField(null)}
              />
              {/* Subtle red indicator dot as in reference */}
              <View style={styles.redDot} />
            </View>

            {/* Hairline Divider */}
            <View style={styles.divider} />

            {/* Password Row */}
            <View
              style={[
                styles.inputRow,
                focusedField === 'password' && styles.inputRowFocused,
              ]}
            >
              <Lock
                size={22}
                color={
                  focusedField === 'password'
                    ? '#FFFFFF'
                    : 'rgba(255, 255, 255, 0.65)'
                }
                strokeWidth={1.75}
              />
              <TextInput
                value={password}
                onChangeText={setPassword}
                placeholder="Password"
                placeholderTextColor="rgba(255, 255, 255, 0.6)"
                style={styles.textInput}
                secureTextEntry={!showPassword}
                onFocus={() => setFocusedField('password')}
                onBlur={() => setFocusedField(null)}
              />
              {password.length > 0 && (
                <Pressable
                  onPress={() => setShowPassword(!showPassword)}
                  hitSlop={8}
                >
                  {showPassword ? (
                    <EyeOff size={18} color="rgba(255,255,255,0.7)" />
                  ) : (
                    <Eye size={18} color="rgba(255,255,255,0.7)" />
                  )}
                </Pressable>
              )}
            </View>
          </View>

          {/* Solid Red Sign On Button */}
          <Pressable
            onPress={handleSignOn}
            style={({ pressed }) => [
              styles.signOnBtn,
              pressed && styles.signOnBtnPressed,
            ]}
          >
            <Text style={styles.signOnText}>Sign On</Text>
          </Pressable>

          {/* Forgot Username or Password? */}
          <Pressable
            onPress={handleSignOn}
            style={styles.forgotBtn}
          >
            <Text style={styles.forgotText}>Forgot Username or Password?</Text>
          </Pressable>
        </Animated.View>

        {/* ─── Bottom Copyright ─── */}
        <Animated.View style={[styles.bottomSection, { opacity: fadeAnim }]}>
          <Text style={styles.copyrightText}>
            © 2016 Wells Fargo. All rights reserved.
          </Text>
        </Animated.View>
      </KeyboardAvoidingView>
    </View>
  );
}

const styles = StyleSheet.create({
  root: {
    flex: 1,
    backgroundColor: '#1E1B18',
  },
  backgroundImage: {
    ...StyleSheet.absoluteFill as any,
    width: SCREEN_WIDTH,
    height: SCREEN_HEIGHT,
  },
  vignetteOverlay: {
    ...StyleSheet.absoluteFill as any,
    backgroundColor: 'rgba(20, 20, 24, 0.42)',
  },
  container: {
    flex: 1,
    justifyContent: 'space-between',
    paddingHorizontal: 28,
    paddingTop: Platform.OS === 'ios' ? 12 : 16,
    paddingBottom: Platform.OS === 'ios' ? 24 : 16,
  },

  // Simulated Status Bar
  statusBarRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingTop: 6,
    paddingBottom: 10,
  },
  carrierRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  signalDots: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 3,
  },
  dot: {
    width: 5.5,
    height: 5.5,
    borderRadius: 3,
  },
  dotFilled: {
    backgroundColor: '#FFFFFF',
  },
  dotEmpty: {
    backgroundColor: 'rgba(255,255,255,0.4)',
  },
  statusText: {
    color: '#FFFFFF',
    fontSize: 12,
    fontWeight: '600',
    letterSpacing: -0.2,
  },
  statusTime: {
    fontSize: 13,
    fontWeight: '700',
  },
  wifiIcon: {
    fontSize: 10,
  },
  batteryRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 5,
  },
  batteryPill: {
    width: 22,
    height: 11,
    borderWidth: 1,
    borderColor: '#FFFFFF',
    borderRadius: 3,
    padding: 1.5,
  },
  batteryLevel: {
    flex: 1,
    backgroundColor: '#FFFFFF',
    borderRadius: 1.5,
  },

  // Center Logo & Form
  centerSection: {
    width: '100%',
    alignItems: 'center',
    marginTop: -40,
  },

  // Wells Fargo Red Box Logo
  logoSquare: {
    width: 140,
    height: 140,
    backgroundColor: '#BA0C2F',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 44,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.35,
    shadowRadius: 10,
    elevation: 8,
  },
  wellsText: {
    color: '#FFCD00',
    fontSize: 27,
    fontWeight: '900',
    fontFamily: Platform.OS === 'ios' ? 'Times New Roman' : 'serif',
    letterSpacing: 2,
    lineHeight: 32,
  },
  fargoText: {
    color: '#FFCD00',
    fontSize: 27,
    fontWeight: '900',
    fontFamily: Platform.OS === 'ios' ? 'Times New Roman' : 'serif',
    letterSpacing: 2,
    lineHeight: 32,
  },

  // Frosted Glass Card
  glassCard: {
    width: '100%',
    borderRadius: 14,
    backgroundColor: 'rgba(55, 55, 60, 0.58)',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.15)',
    overflow: 'hidden',
  },
  inputRow: {
    flexDirection: 'row',
    alignItems: 'center',
    height: 54,
    paddingHorizontal: 16,
    gap: 14,
  },
  inputRowFocused: {
    backgroundColor: 'rgba(255, 255, 255, 0.08)',
  },
  textInput: {
    flex: 1,
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '400',
    paddingVertical: 0,
  },
  redDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: '#BA0C2F',
    marginRight: 6,
  },
  divider: {
    height: StyleSheet.hairlineWidth,
    backgroundColor: 'rgba(255, 255, 255, 0.22)',
    marginLeft: 52,
  },

  // Sign On Button
  signOnBtn: {
    width: '100%',
    height: 52,
    backgroundColor: '#C8102E',
    borderRadius: 14,
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 18,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 3 },
    shadowOpacity: 0.25,
    shadowRadius: 6,
    elevation: 4,
  },
  signOnBtnPressed: {
    backgroundColor: '#A60E26',
    transform: [{ scale: 0.99 }],
  },
  signOnText: {
    color: '#FFFFFF',
    fontSize: 17,
    fontWeight: '700',
    letterSpacing: 0.3,
  },

  // Forgot Password
  forgotBtn: {
    paddingVertical: 18,
    alignItems: 'center',
  },
  forgotText: {
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: '500',
    letterSpacing: -0.2,
    opacity: 0.95,
  },

  // Bottom Copyright
  bottomSection: {
    alignItems: 'center',
    paddingBottom: 10,
  },
  copyrightText: {
    color: '#FFFFFF',
    fontSize: 12,
    fontWeight: '500',
    opacity: 0.85,
    textAlign: 'center',
    textShadowColor: 'rgba(0, 0, 0, 0.75)',
    textShadowOffset: { width: 0, height: 1 },
    textShadowRadius: 3,
  },
});
