import React, { useState } from 'react';
import {
  StyleSheet,
  Text,
  View,
  TouchableOpacity,
  ScrollView,
  TextInput,
  Alert,
  SafeAreaView,
  ActivityIndicator,
  Platform,
} from 'react-native';
import { StatusBar } from 'expo-status-bar';

// Configuración API
const API_URL = Platform.select({
  ios: 'http://localhost:8000',
  android: 'http://10.0.2.2:8000',
  default: 'http://localhost:8000',
});

// Tipos
interface User {
  id: number;
  email: string;
  name: string;
  organization_name: string;
}

interface Client {
  id: number;
  name: string;
  phone: string;
  email?: string;
  balance: number;
  total_debt: number;
}

export default function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [user, setUser] = useState<User | null>(null);
  const [clients, setClients] = useState<Client[]>([]);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('dashboard');

  // Estados del formulario de login
  const [email, setEmail] = useState('demo@clienteos.mx');
  const [password, setPassword] = useState('demo123');

  // Login
  const handleLogin = async () => {
    setLoading(true);
    try {
      // Por ahora simulamos el login
      setUser({
        id: 1,
        email: email,
        name: 'Usuario Demo',
        organization_name: 'Consultorio Demo',
      });
      setIsLoggedIn(true);
      loadClients();
    } catch (error) {
      Alert.alert('Error', 'No se pudo iniciar sesión');
    }
    setLoading(false);
  };

  // Cargar clientes
  const loadClients = async () => {
    // Datos de ejemplo
    setClients([
      {
        id: 1,
        name: 'Juan Pérez',
        phone: '+525512345678',
        email: 'juan@email.com',
        balance: 0,
        total_debt: 1500,
      },
      {
        id: 2,
        name: 'María García',
        phone: '+525587654321',
        email: 'maria@email.com',
        balance: 500,
        total_debt: 0,
      },
      {
        id: 3,
        name: 'Carlos López',
        phone: '+525511223344',
        balance: 0,
        total_debt: 3200,
      },
    ]);
  };

  // Pantalla de Login
  const LoginScreen = () => (
    <View style={styles.loginContainer}>
      <Text style={styles.logo}>ClienteOS</Text>
      <Text style={styles.subtitle}>Gestión inteligente para tu negocio</Text>
      
      <View style={styles.form}>
        <TextInput
          style={styles.input}
          placeholder="Email"
          value={email}
          onChangeText={setEmail}
          keyboardType="email-address"
          autoCapitalize="none"
        />
        <TextInput
          style={styles.input}
          placeholder="Contraseña"
          value={password}
          onChangeText={setPassword}
          secureTextEntry
        />
        
        <TouchableOpacity
          style={styles.button}
          onPress={handleLogin}
          disabled={loading}
        >
          {loading ? (
            <ActivityIndicator color="white" />
          ) : (
            <Text style={styles.buttonText}>Iniciar Sesión</Text>
          )}
        </TouchableOpacity>
        
        <Text style={styles.helpText}>
          Demo: demo@clienteos.mx / demo123
        </Text>
      </View>
    </View>
  );

  // Dashboard
  const DashboardScreen = () => (
    <ScrollView style={styles.screenContainer}>
      <View style={styles.header}>
        <Text style={styles.welcomeText}>Hola, {user?.name}</Text>
        <Text style={styles.orgText}>{user?.organization_name}</Text>
      </View>

      <View style={styles.statsGrid}>
        <View style={styles.statCard}>
          <Text style={styles.statValue}>12</Text>
          <Text style={styles.statLabel}>Clientes</Text>
        </View>
        <View style={styles.statCard}>
          <Text style={styles.statValue}>$4,700</Text>
          <Text style={styles.statLabel}>Por Cobrar</Text>
        </View>
        <View style={styles.statCard}>
          <Text style={styles.statValue}>3</Text>
          <Text style={styles.statLabel}>Citas Hoy</Text>
        </View>
        <View style={styles.statCard}>
          <Text style={styles.statValue}>85%</Text>
          <Text style={styles.statLabel}>Cobrado</Text>
        </View>
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Acciones Rápidas</Text>
        
        <TouchableOpacity style={styles.actionButton}>
          <Text style={styles.actionText}>📱 Enviar Recordatorio</Text>
        </TouchableOpacity>
        
        <TouchableOpacity style={styles.actionButton}>
          <Text style={styles.actionText}>💳 Crear Link de Pago</Text>
        </TouchableOpacity>
        
        <TouchableOpacity style={styles.actionButton}>
          <Text style={styles.actionText}>📅 Agendar Cita</Text>
        </TouchableOpacity>
        
        <TouchableOpacity style={styles.actionButton}>
          <Text style={styles.actionText}>👥 Nuevo Cliente</Text>
        </TouchableOpacity>
      </View>
    </ScrollView>
  );

  // Pantalla de Clientes
  const ClientsScreen = () => (
    <ScrollView style={styles.screenContainer}>
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Clientes ({clients.length})</Text>
        
        {clients.map((client) => (
          <TouchableOpacity key={client.id} style={styles.clientCard}>
            <View style={styles.clientInfo}>
              <Text style={styles.clientName}>{client.name}</Text>
              <Text style={styles.clientPhone}>{client.phone}</Text>
            </View>
            <View style={styles.clientBalance}>
              {client.total_debt > 0 ? (
                <Text style={styles.debtAmount}>
                  Debe: ${client.total_debt.toFixed(2)}
                </Text>
              ) : (
                <Text style={styles.paidText}>Al corriente</Text>
              )}
            </View>
          </TouchableOpacity>
        ))}
      </View>
    </ScrollView>
  );

  // Pantalla de Cobros
  const PaymentsScreen = () => (
    <ScrollView style={styles.screenContainer}>
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Cobros Pendientes</Text>
        
        <View style={styles.paymentCard}>
          <View style={styles.paymentInfo}>
            <Text style={styles.paymentClient}>Juan Pérez</Text>
            <Text style={styles.paymentDescription}>Consulta general</Text>
            <Text style={styles.paymentDate}>Vence: 20 Ene 2025</Text>
          </View>
          <View style={styles.paymentActions}>
            <Text style={styles.paymentAmount}>$1,500</Text>
            <TouchableOpacity style={styles.smallButton}>
              <Text style={styles.smallButtonText}>Cobrar</Text>
            </TouchableOpacity>
          </View>
        </View>

        <View style={styles.paymentCard}>
          <View style={styles.paymentInfo}>
            <Text style={styles.paymentClient}>Carlos López</Text>
            <Text style={styles.paymentDescription}>Tratamiento dental</Text>
            <Text style={[styles.paymentDate, styles.overdueText]}>
              Vencido hace 5 días
            </Text>
          </View>
          <View style={styles.paymentActions}>
            <Text style={styles.paymentAmount}>$3,200</Text>
            <TouchableOpacity style={styles.smallButton}>
              <Text style={styles.smallButtonText}>Cobrar</Text>
            </TouchableOpacity>
          </View>
        </View>
      </View>
    </ScrollView>
  );

  // Pantalla Principal con Tabs
  const MainScreen = () => (
    <SafeAreaView style={styles.container}>
      <StatusBar style="auto" />
      
      {/* Content */}
      <View style={styles.content}>
        {activeTab === 'dashboard' && <DashboardScreen />}
        {activeTab === 'clients' && <ClientsScreen />}
        {activeTab === 'payments' && <PaymentsScreen />}
      </View>

      {/* Bottom Navigation */}
      <View style={styles.tabBar}>
        <TouchableOpacity
          style={[styles.tab, activeTab === 'dashboard' && styles.activeTab]}
          onPress={() => setActiveTab('dashboard')}
        >
          <Text style={styles.tabText}>🏠</Text>
          <Text style={styles.tabLabel}>Inicio</Text>
        </TouchableOpacity>
        
        <TouchableOpacity
          style={[styles.tab, activeTab === 'clients' && styles.activeTab]}
          onPress={() => setActiveTab('clients')}
        >
          <Text style={styles.tabText}>👥</Text>
          <Text style={styles.tabLabel}>Clientes</Text>
        </TouchableOpacity>
        
        <TouchableOpacity
          style={[styles.tab, activeTab === 'payments' && styles.activeTab]}
          onPress={() => setActiveTab('payments')}
        >
          <Text style={styles.tabText}>💰</Text>
          <Text style={styles.tabLabel}>Cobros</Text>
        </TouchableOpacity>
        
        <TouchableOpacity
          style={styles.tab}
          onPress={() => {
            Alert.alert(
              'Cerrar Sesión',
              '¿Estás seguro?',
              [
                { text: 'Cancelar', style: 'cancel' },
                { text: 'Salir', onPress: () => setIsLoggedIn(false) },
              ]
            );
          }}
        >
          <Text style={styles.tabText}>⚙️</Text>
          <Text style={styles.tabLabel}>Más</Text>
        </TouchableOpacity>
      </View>
    </SafeAreaView>
  );

  return isLoggedIn ? <MainScreen /> : <LoginScreen />;
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  content: {
    flex: 1,
  },
  loginContainer: {
    flex: 1,
    justifyContent: 'center',
    padding: 20,
    backgroundColor: '#fff',
  },
  logo: {
    fontSize: 36,
    fontWeight: 'bold',
    textAlign: 'center',
    color: '#2563eb',
    marginBottom: 10,
  },
  subtitle: {
    fontSize: 16,
    textAlign: 'center',
    color: '#666',
    marginBottom: 40,
  },
  form: {
    width: '100%',
  },
  input: {
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 8,
    padding: 15,
    marginBottom: 15,
    fontSize: 16,
  },
  button: {
    backgroundColor: '#2563eb',
    padding: 15,
    borderRadius: 8,
    alignItems: 'center',
    marginTop: 10,
  },
  buttonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: 'bold',
  },
  helpText: {
    textAlign: 'center',
    color: '#666',
    marginTop: 20,
    fontSize: 14,
  },
  screenContainer: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  header: {
    padding: 20,
    backgroundColor: 'white',
    borderBottomWidth: 1,
    borderBottomColor: '#e5e5e5',
  },
  welcomeText: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#333',
  },
  orgText: {
    fontSize: 14,
    color: '#666',
    marginTop: 5,
  },
  statsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    padding: 10,
  },
  statCard: {
    width: '48%',
    backgroundColor: 'white',
    padding: 20,
    margin: '1%',
    borderRadius: 8,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
  },
  statValue: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#2563eb',
  },
  statLabel: {
    fontSize: 14,
    color: '#666',
    marginTop: 5,
  },
  section: {
    padding: 20,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 15,
    color: '#333',
  },
  actionButton: {
    backgroundColor: 'white',
    padding: 15,
    borderRadius: 8,
    marginBottom: 10,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
  },
  actionText: {
    fontSize: 16,
    color: '#333',
  },
  clientCard: {
    backgroundColor: 'white',
    padding: 15,
    borderRadius: 8,
    marginBottom: 10,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
  },
  clientInfo: {
    flex: 1,
  },
  clientName: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333',
  },
  clientPhone: {
    fontSize: 14,
    color: '#666',
    marginTop: 5,
  },
  clientBalance: {
    alignItems: 'flex-end',
  },
  debtAmount: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#ef4444',
  },
  paidText: {
    fontSize: 14,
    color: '#10b981',
  },
  paymentCard: {
    backgroundColor: 'white',
    padding: 15,
    borderRadius: 8,
    marginBottom: 10,
    flexDirection: 'row',
    justifyContent: 'space-between',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
  },
  paymentInfo: {
    flex: 1,
  },
  paymentClient: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333',
  },
  paymentDescription: {
    fontSize: 14,
    color: '#666',
    marginTop: 2,
  },
  paymentDate: {
    fontSize: 12,
    color: '#999',
    marginTop: 5,
  },
  overdueText: {
    color: '#ef4444',
  },
  paymentActions: {
    alignItems: 'flex-end',
  },
  paymentAmount: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 10,
  },
  smallButton: {
    backgroundColor: '#2563eb',
    paddingHorizontal: 20,
    paddingVertical: 8,
    borderRadius: 6,
  },
  smallButtonText: {
    color: 'white',
    fontSize: 14,
    fontWeight: 'bold',
  },
  tabBar: {
    flexDirection: 'row',
    backgroundColor: 'white',
    borderTopWidth: 1,
    borderTopColor: '#e5e5e5',
    paddingBottom: 20,
  },
  tab: {
    flex: 1,
    alignItems: 'center',
    paddingVertical: 10,
  },
  activeTab: {
    borderTopWidth: 2,
    borderTopColor: '#2563eb',
  },
  tabText: {
    fontSize: 24,
  },
  tabLabel: {
    fontSize: 12,
    color: '#666',
    marginTop: 2,
  },
});
