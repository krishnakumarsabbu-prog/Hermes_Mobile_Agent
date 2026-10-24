// ─── Hermes Personal Banking — Premium Theme ───────────────────────────────
// Inspired by top-tier banking apps (Wells Fargo, Chase, Amex).
// Warm neutral palette with strategic accent colors for trust & professionalism.

export const colors = {
  // Core neutrals
  ink: '#1A1D21',
  inkSecondary: '#3D4148',
  muted: '#6B7280',
  soft: '#9CA3AF',
  placeholder: '#BCC3CE',
  background: '#F5F5F7',
  surface: '#FFFFFF',
  surfaceElevated: '#FAFBFC',
  line: '#E5E7EB',
  lineSoft: '#F0F1F3',

  // Brand — deep crimson / warm red (Wells Fargo-inspired)
  brand: '#CF1322',
  brandDark: '#A6101C',
  brandSoft: '#FFF1F0',
  brandGold: '#FFBF00',

  // Navy — authority & trust
  navy: '#1B2A4A',
  navyMid: '#2D4266',
  navySoft: '#3B5178',
  navyLight: '#E8EDF4',

  // Success / positive
  green: '#059669',
  greenSoft: '#ECFDF5',

  // Warning / amber
  amber: '#D97706',
  amberSoft: '#FFFBEB',

  // Info / blue
  blue: '#2563EB',
  blueSoft: '#EFF6FF',

  // Danger
  red: '#DC2626',
  redSoft: '#FEF2F2',

  // Teal accent
  teal: '#0D9488',
  tealSoft: '#F0FDFA',

  // Overlay
  overlayDark: 'rgba(0,0,0,0.55)',
  overlayLight: 'rgba(255,255,255,0.15)',
  glassBorder: 'rgba(255,255,255,0.28)',
  glassBackground: 'rgba(255,255,255,0.12)',
};

export const spacing = {
  xxs: 2,
  xs: 4,
  sm: 8,
  md: 16,
  lg: 24,
  xl: 32,
  xxl: 48,
  xxxl: 64,
};

export const radii = {
  xs: 6,
  sm: 10,
  md: 14,
  lg: 20,
  xl: 28,
  pill: 999,
};

export const typography = {
  hero: { fontSize: 34, fontWeight: '800' as const, letterSpacing: -0.5 },
  h1: { fontSize: 28, fontWeight: '700' as const, letterSpacing: -0.3 },
  h2: { fontSize: 22, fontWeight: '700' as const },
  h3: { fontSize: 18, fontWeight: '700' as const },
  h4: { fontSize: 15, fontWeight: '600' as const },
  body: { fontSize: 15, fontWeight: '400' as const, lineHeight: 22 },
  bodySmall: { fontSize: 13, fontWeight: '400' as const, lineHeight: 18 },
  caption: { fontSize: 11, fontWeight: '500' as const },
  eyebrow: { fontSize: 10, fontWeight: '700' as const, letterSpacing: 1.4 },
  button: { fontSize: 16, fontWeight: '700' as const },
  tabLabel: { fontSize: 10, fontWeight: '600' as const },
};

export const shadows = {
  card: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.06,
    shadowRadius: 8,
    elevation: 3,
  },
  elevated: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.1,
    shadowRadius: 16,
    elevation: 6,
  },
  soft: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.04,
    shadowRadius: 4,
    elevation: 2,
  },
};
