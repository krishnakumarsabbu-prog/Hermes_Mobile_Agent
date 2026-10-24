import { Stack } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { AppProvider } from '../src/AppContext';
export default function RootLayout() { return <AppProvider><StatusBar style="dark" /><Stack screenOptions={{ headerShown: false, animation: 'slide_from_right' }} /></AppProvider>; }
