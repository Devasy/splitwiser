import { View, ScrollView } from 'react-native';
import { ThemedText, ThemedButton, ThemedView } from '../components/Themed';
import { NeoCard } from '../components/NeoCard';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Wallet, PieChart, TrendingUp, ArrowRight } from 'lucide-react-native';

export default function HomeScreen() {
  return (
    <ThemedView className="flex-1">
      <SafeAreaView className="flex-1">
        <ScrollView contentContainerStyle={{ padding: 20 }}>

          {/* Header */}
          <View className="mb-8">
            <ThemedText type="title" className="mb-2">Hello, Jules!</ThemedText>
            <ThemedText className="text-gray-600">Welcome back to Splitwiser.</ThemedText>
          </View>

          {/* Balance Card */}
          <NeoCard className="bg-neo-main mb-8">
            <View className="flex-row justify-between items-center mb-4">
              <ThemedText className="text-neo-white font-mono-bold">TOTAL BALANCE</ThemedText>
              <Wallet color="white" size={24} />
            </View>
            <ThemedText type="title" className="text-neo-white text-5xl mb-4">$1,234.56</ThemedText>
            <View className="flex-row gap-4">
               <View className="bg-white/20 px-3 py-1 rounded-full border border-white">
                 <ThemedText className="text-white text-xs font-mono-bold">+2.4% this month</ThemedText>
               </View>
            </View>
          </NeoCard>

          {/* Quick Actions */}
          <View className="flex-row gap-4 mb-8">
            <ThemedButton
              title="Add Expense"
              className="flex-1"
              variant="secondary"
              onPress={() => console.log('Add Expense')}
            />
             <ThemedButton
              title="Settle Up"
              className="flex-1"
              variant="accent"
              onPress={() => console.log('Settle Up')}
            />
          </View>

          {/* Recent Activity */}
          <View className="mb-4 flex-row justify-between items-end">
            <ThemedText type="subtitle">Recent Activity</ThemedText>
            <ThemedText type="link">View All</ThemedText>
          </View>

          <View className="gap-4">
            <NeoCard className="flex-row items-center justify-between p-4">
              <View className="flex-row items-center gap-4">
                <View className="w-10 h-10 bg-neo-second border-2 border-neo-dark items-center justify-center">
                   <TrendingUp color="black" size={20} />
                </View>
                <View>
                  <ThemedText type="defaultSemiBold">Grocery Run</ThemedText>
                  <ThemedText className="text-xs text-gray-500">Yesterday</ThemedText>
                </View>
              </View>
              <ThemedText className="font-mono-bold text-red-500">-$45.00</ThemedText>
            </NeoCard>

             <NeoCard className="flex-row items-center justify-between p-4">
              <View className="flex-row items-center gap-4">
                <View className="w-10 h-10 bg-neo-accent border-2 border-neo-dark items-center justify-center">
                   <PieChart color="black" size={20} />
                </View>
                <View>
                  <ThemedText type="defaultSemiBold">Movie Night</ThemedText>
                  <ThemedText className="text-xs text-gray-500">2 days ago</ThemedText>
                </View>
              </View>
              <ThemedText className="font-mono-bold text-green-600">+$12.50</ThemedText>
            </NeoCard>

             <NeoCard className="flex-row items-center justify-between p-4">
              <View className="flex-row items-center gap-4">
                <View className="w-10 h-10 bg-neo-main border-2 border-neo-dark items-center justify-center">
                   <Wallet color="white" size={20} />
                </View>
                <View>
                  <ThemedText type="defaultSemiBold">Rent Payment</ThemedText>
                  <ThemedText className="text-xs text-gray-500">Oct 1</ThemedText>
                </View>
              </View>
              <ThemedText className="font-mono-bold text-red-500">-$800.00</ThemedText>
            </NeoCard>
          </View>

        </ScrollView>
      </SafeAreaView>
    </ThemedView>
  );
}
