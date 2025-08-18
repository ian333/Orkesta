import React from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  RefreshControl,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { useDashboardOverview, useDashboardAgents, useDashboardStripe } from '../../hooks/useApi';

const DashboardScreen: React.FC = () => {
  const { 
    data: overviewData, 
    isLoading: overviewLoading, 
    refetch: refetchOverview 
  } = useDashboardOverview();
  
  const { 
    data: agentsData, 
    isLoading: agentsLoading, 
    refetch: refetchAgents 
  } = useDashboardAgents();
  
  const { 
    data: stripeData, 
    isLoading: stripeLoading, 
    refetch: refetchStripe 
  } = useDashboardStripe();

  const isLoading = overviewLoading || agentsLoading || stripeLoading;

  const onRefresh = async () => {
    await Promise.all([
      refetchOverview(),
      refetchAgents(),
      refetchStripe(),
    ]);
  };

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView
        style={styles.scrollView}
        refreshControl={
          <RefreshControl refreshing={isLoading} onRefresh={onRefresh} />
        }
      >
        {/* Header */}
        <View style={styles.header}>
          <Text style={styles.title}>Dashboard Orkesta</Text>
          <Text style={styles.subtitle}>Agentes de Ventas Inteligentes</Text>
        </View>

        {/* Overview Metrics */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Resumen General</Text>
          <View style={styles.metricsGrid}>
            <View style={styles.metricCard}>
              <Text style={styles.metricValue}>
                ${overviewData?.total_revenue?.toLocaleString() || '0'}
              </Text>
              <Text style={styles.metricLabel}>Revenue Total</Text>
            </View>
            <View style={styles.metricCard}>
              <Text style={styles.metricValue}>
                {overviewData?.total_orders || 0}
              </Text>
              <Text style={styles.metricLabel}>Órdenes</Text>
            </View>
            <View style={styles.metricCard}>
              <Text style={styles.metricValue}>
                {overviewData?.active_conversations || 0}
              </Text>
              <Text style={styles.metricLabel}>Conversaciones</Text>
            </View>
            <View style={styles.metricCard}>
              <Text style={styles.metricValue}>
                {((overviewData?.conversion_rate || 0) * 100).toFixed(1)}%
              </Text>
              <Text style={styles.metricLabel}>Conversión</Text>
            </View>
          </View>
        </View>

        {/* Agents Metrics */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>🤖 Agentes Inteligentes</Text>
          <View style={styles.metricsGrid}>
            <View style={styles.metricCard}>
              <Text style={styles.metricValue}>
                {agentsData?.total_suggestions || 0}
              </Text>
              <Text style={styles.metricLabel}>Sugerencias</Text>
            </View>
            <View style={styles.metricCard}>
              <Text style={styles.metricValue}>
                {agentsData?.approved_suggestions || 0}
              </Text>
              <Text style={styles.metricLabel}>Aprobadas</Text>
            </View>
            <View style={styles.metricCard}>
              <Text style={styles.metricValue}>
                {((agentsData?.confidence_avg || 0) * 100).toFixed(0)}%
              </Text>
              <Text style={styles.metricLabel}>Confianza</Text>
            </View>
            <View style={styles.metricCard}>
              <Text style={styles.metricValue}>
                {(agentsData?.response_time_avg || 0).toFixed(1)}s
              </Text>
              <Text style={styles.metricLabel}>Tiempo Resp.</Text>
            </View>
          </View>
        </View>

        {/* Stripe Metrics */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>💳 Stripe Connect</Text>
          <View style={styles.metricsGrid}>
            <View style={styles.metricCard}>
              <Text style={styles.metricValue}>
                ${stripeData?.total_processed?.toLocaleString() || '0'}
              </Text>
              <Text style={styles.metricLabel}>Procesado</Text>
            </View>
            <View style={styles.metricCard}>
              <Text style={styles.metricValue}>
                ${stripeData?.fees_collected?.toLocaleString() || '0'}
              </Text>
              <Text style={styles.metricLabel}>Fees</Text>
            </View>
            <View style={styles.metricCard}>
              <Text style={styles.metricValue}>
                {stripeData?.active_accounts || 0}
              </Text>
              <Text style={styles.metricLabel}>Cuentas</Text>
            </View>
            <View style={styles.metricCard}>
              <Text style={styles.metricValue}>
                ${stripeData?.payout_pending?.toLocaleString() || '0'}
              </Text>
              <Text style={styles.metricLabel}>Pendientes</Text>
            </View>
          </View>
        </View>

        {/* Quick Actions */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Acciones Rápidas</Text>
          <View style={styles.quickActions}>
            <View style={styles.actionCard}>
              <Text style={styles.actionIcon}>🛒</Text>
              <Text style={styles.actionText}>Nueva Orden</Text>
            </View>
            <View style={styles.actionCard}>
              <Text style={styles.actionIcon}>👥</Text>
              <Text style={styles.actionText}>Nuevo Cliente</Text>
            </View>
            <View style={styles.actionCard}>
              <Text style={styles.actionIcon}>💬</Text>
              <Text style={styles.actionText}>Chat Agente</Text>
            </View>
            <View style={styles.actionCard}>
              <Text style={styles.actionIcon}>📊</Text>
              <Text style={styles.actionText}>Reportes</Text>
            </View>
          </View>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8fafc',
  },
  scrollView: {
    flex: 1,
  },
  header: {
    padding: 20,
    backgroundColor: 'white',
    borderBottomWidth: 1,
    borderBottomColor: '#e5e7eb',
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#1f2937',
  },
  subtitle: {
    fontSize: 16,
    color: '#6b7280',
    marginTop: 4,
  },
  section: {
    margin: 16,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#374151',
    marginBottom: 12,
  },
  metricsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  metricCard: {
    backgroundColor: 'white',
    borderRadius: 12,
    padding: 16,
    width: '48%',
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 2,
  },
  metricValue: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#1f2937',
    marginBottom: 4,
  },
  metricLabel: {
    fontSize: 14,
    color: '#6b7280',
  },
  quickActions: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  actionCard: {
    backgroundColor: 'white',
    borderRadius: 12,
    padding: 16,
    width: '48%',
    marginBottom: 12,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 2,
  },
  actionIcon: {
    fontSize: 32,
    marginBottom: 8,
  },
  actionText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#374151',
    textAlign: 'center',
  },
});

export default DashboardScreen;