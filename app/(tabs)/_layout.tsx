import { Tabs } from 'expo-router';
import {
  Home,
  ArrowDownToLine,
  ArrowLeftRight,
  Compass,
  Menu,
} from 'lucide-react-native';
import { Platform, View } from 'react-native';

export default function TabsLayout() {
  return (
    <Tabs
      screenOptions={{
        headerShown: false,
        tabBarActiveTintColor: '#C8102E', // Wells Fargo authentic red
        tabBarInactiveTintColor: '#666666',
        tabBarStyle: {
          height: Platform.OS === 'ios' ? 86 : 68,
          paddingTop: 8,
          paddingBottom: Platform.OS === 'ios' ? 26 : 10,
          borderTopWidth: 1,
          borderTopColor: '#E5E7EB',
          backgroundColor: '#FFFFFF',
          elevation: 8,
          shadowColor: '#000',
          shadowOffset: { width: 0, height: -2 },
          shadowOpacity: 0.05,
          shadowRadius: 6,
        },
        tabBarLabelStyle: {
          fontSize: 10.5,
          fontWeight: '600',
          marginTop: 2,
        },
      }}
    >
      <Tabs.Screen
        name="index"
        options={{
          title: 'Accounts',
          tabBarIcon: ({ color, focused }) => (
            <View style={focused ? { transform: [{ scale: 1.05 }] } : undefined}>
              <Home color={color} size={22} strokeWidth={focused ? 2.2 : 1.8} />
            </View>
          ),
        }}
      />
      <Tabs.Screen
        name="deposit"
        options={{
          title: 'Deposit',
          tabBarIcon: ({ color, focused }) => (
            <View style={focused ? { transform: [{ scale: 1.05 }] } : undefined}>
              <ArrowDownToLine color={color} size={22} strokeWidth={focused ? 2.2 : 1.8} />
            </View>
          ),
        }}
      />
      <Tabs.Screen
        name="pay"
        options={{
          title: 'Pay & Transfer',
          tabBarIcon: ({ color, focused }) => (
            <View style={focused ? { transform: [{ scale: 1.05 }] } : undefined}>
              <ArrowLeftRight color={color} size={22} strokeWidth={focused ? 2.2 : 1.8} />
            </View>
          ),
        }}
      />
      <Tabs.Screen
        name="explore"
        options={{
          title: 'Explore',
          tabBarIcon: ({ color, focused }) => (
            <View style={focused ? { transform: [{ scale: 1.05 }] } : undefined}>
              <Compass color={color} size={22} strokeWidth={focused ? 2.2 : 1.8} />
            </View>
          ),
        }}
      />
      <Tabs.Screen
        name="menu"
        options={{
          title: 'Menu',
          tabBarIcon: ({ color, focused }) => (
            <View style={focused ? { transform: [{ scale: 1.05 }] } : undefined}>
              <Menu color={color} size={22} strokeWidth={focused ? 2.2 : 1.8} />
            </View>
          ),
        }}
      />
    </Tabs>
  );
}
