import { Stack } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { AppProvider } from '../src/AppContext'
import { useFrameworkReady } from '@/hooks/useFrameworkReady';
export default function RootLayout() {
  useFrameworkReady(); return <AppProvider><StatusBar style="dark" /><Stack screenOptions={{ headerShown: false, animation: 'slide_from_right' }} /></AppProvider>; }
