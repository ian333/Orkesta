import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity, Alert } from 'react-native';

export default function App() {
  const handlePress = () => {
    Alert.alert('🎉 ¡Funciona!', 'React Native está funcionando en tu emulador');
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>🚀 Orkesta</Text>
      <Text style={styles.subtitle}>¡Conectado exitosamente!</Text>
      
      <TouchableOpacity style={styles.button} onPress={handlePress}>
        <Text style={styles.buttonText}>Probar</Text>
      </TouchableOpacity>
      
      <Text style={styles.info}>
        ✅ Emulador Android{'\n'}
        ✅ React Native{'\n'}
        ✅ Expo funcionando
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#f0f0f0',
    padding: 20,
  },
  title: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 10,
  },
  subtitle: {
    fontSize: 18,
    color: '#666',
    marginBottom: 30,
    textAlign: 'center',
  },
  button: {
    backgroundColor: '#007AFF',
    paddingHorizontal: 30,
    paddingVertical: 15,
    borderRadius: 10,
    marginBottom: 30,
  },
  buttonText: {
    color: 'white',
    fontSize: 18,
    fontWeight: '600',
  },
  info: {
    fontSize: 16,
    color: '#333',
    textAlign: 'center',
    lineHeight: 24,
  },
});