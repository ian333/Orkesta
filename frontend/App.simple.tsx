import React from 'react';
import { StatusBar } from 'expo-status-bar';
import { StyleSheet, Text, View, TouchableOpacity, Alert } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';

export default function App() {
  const handleTestPress = () => {
    Alert.alert('🎉 ¡Funciona!', 'La app React Native se está ejecutando correctamente en tu emulador.');
  };

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.content}>
        {/* Logo */}
        <View style={styles.logoContainer}>
          <Ionicons name="analytics" size={80} color="#6366f1" />
          <Text style={styles.title}>Orkesta</Text>
          <Text style={styles.subtitle}>Agentes de Ventas Inteligentes</Text>
        </View>

        {/* Success Message */}
        <View style={styles.successContainer}>
          <Ionicons name="checkmark-circle" size={40} color="#10b981" />
          <Text style={styles.successTitle}>¡Setup Completado!</Text>
          <Text style={styles.successText}>
            Tu app React Native está funcionando correctamente
          </Text>
        </View>

        {/* Test Button */}
        <TouchableOpacity style={styles.testButton} onPress={handleTestPress}>
          <Text style={styles.testButtonText}>Probar Funcionalidad</Text>
        </TouchableOpacity>

        {/* Info Cards */}
        <View style={styles.infoContainer}>
          <View style={styles.infoCard}>
            <Ionicons name="phone-portrait" size={24} color="#6366f1" />
            <Text style={styles.infoText}>Emulador: ✅ Conectado</Text>
          </View>
          
          <View style={styles.infoCard}>
            <Ionicons name="code" size={24} color="#6366f1" />
            <Text style={styles.infoText}>React Native: ✅ Funcionando</Text>
          </View>
          
          <View style={styles.infoCard}>
            <Ionicons name="server" size={24} color="#6366f1" />
            <Text style={styles.infoText}>Expo: ✅ Activo</Text>
          </View>
        </View>

        {/* Next Steps */}
        <View style={styles.nextSteps}>
          <Text style={styles.nextStepsTitle}>Próximos pasos:</Text>
          <Text style={styles.nextStepsText}>
            • ✅ Emulador conectado{'\n'}
            • ✅ App React Native funcionando{'\n'}
            • 🔄 Conectar con backend Orkesta{'\n'}
            • 📱 Desarrollar features específicas
          </Text>
        </View>
      </View>
      <StatusBar style="auto" />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8fafc',
  },
  content: {
    flex: 1,
    padding: 20,
    justifyContent: 'center',
  },
  logoContainer: {
    alignItems: 'center',
    marginBottom: 40,
  },
  title: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#1f2937',
    marginTop: 16,
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 16,
    color: '#6b7280',
    textAlign: 'center',
  },
  successContainer: {
    backgroundColor: 'white',
    borderRadius: 16,
    padding: 24,
    alignItems: 'center',
    marginBottom: 32,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 4,
  },
  successTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#1f2937',
    marginTop: 12,
    marginBottom: 8,
  },
  successText: {
    fontSize: 14,
    color: '#6b7280',
    textAlign: 'center',
  },
  testButton: {
    backgroundColor: '#6366f1',
    borderRadius: 12,
    padding: 16,
    alignItems: 'center',
    marginBottom: 32,
  },
  testButtonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: '600',
  },
  infoContainer: {
    marginBottom: 32,
  },
  infoCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'white',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 2,
  },
  infoText: {
    fontSize: 14,
    color: '#1f2937',
    marginLeft: 12,
    fontWeight: '500',
  },
  nextSteps: {
    backgroundColor: '#eff6ff',
    borderRadius: 12,
    padding: 16,
  },
  nextStepsTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1f2937',
    marginBottom: 8,
  },
  nextStepsText: {
    fontSize: 14,
    color: '#374151',
    lineHeight: 20,
  },
});