import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';

import { useConversations } from '../../hooks/useApi';
import { Conversation } from '../../types';

const ConversationsScreen: React.FC = () => {
  const { data: conversations, isLoading, refetch } = useConversations();

  const getStageIcon = (stage: Conversation['stage']) => {
    switch (stage) {
      case 'greeting':
        return 'hand-left-outline';
      case 'discovery':
        return 'search-outline';
      case 'quote':
        return 'calculator-outline';
      case 'closing':
        return 'checkmark-circle-outline';
      case 'completed':
        return 'checkmark-done-outline';
      default:
        return 'chatbubble-outline';
    }
  };

  const getStageText = (stage: Conversation['stage']) => {
    switch (stage) {
      case 'greeting':
        return 'Saludo';
      case 'discovery':
        return 'Descubrimiento';
      case 'quote':
        return 'Cotización';
      case 'closing':
        return 'Cierre';
      case 'completed':
        return 'Completada';
      default:
        return 'Iniciando';
    }
  };

  const getSentimentColor = (sentiment: Conversation['sentiment']) => {
    switch (sentiment) {
      case 'positive':
        return '#10b981';
      case 'negative':
        return '#ef4444';
      default:
        return '#f59e0b';
    }
  };

  const getSentimentIcon = (sentiment: Conversation['sentiment']) => {
    switch (sentiment) {
      case 'positive':
        return 'happy-outline';
      case 'negative':
        return 'sad-outline';
      default:
        return 'remove-outline';
    }
  };

  const renderConversation = ({ item }: { item: Conversation }) => (
    <TouchableOpacity style={styles.conversationCard}>
      <View style={styles.conversationHeader}>
        <View style={styles.stageContainer}>
          <Ionicons 
            name={getStageIcon(item.stage)} 
            size={16} 
            color="#6366f1" 
          />
          <Text style={styles.stageText}>{getStageText(item.stage)}</Text>
        </View>
        <View style={styles.sentimentContainer}>
          <Ionicons 
            name={getSentimentIcon(item.sentiment)} 
            size={16} 
            color={getSentimentColor(item.sentiment)} 
          />
        </View>
      </View>
      
      <Text style={styles.clientPhone}>{item.client_phone}</Text>
      <Text style={styles.intent}>Intent: {item.intent}</Text>
      
      <View style={styles.conversationDetails}>
        <Text style={styles.messageCount}>
          {item.messages.length} mensajes
        </Text>
        <View style={styles.healthScore}>
          <Text style={styles.healthScoreText}>
            Salud: {(item.health_score * 100).toFixed(0)}%
          </Text>
        </View>
      </View>
      
      <Text style={styles.conversationDate}>
        {new Date(item.updated_at).toLocaleString()}
      </Text>
    </TouchableOpacity>
  );

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Conversaciones</Text>
        <TouchableOpacity style={styles.addButton}>
          <Ionicons name="add" size={24} color="white" />
        </TouchableOpacity>
      </View>

      <FlatList
        data={conversations}
        renderItem={renderConversation}
        keyExtractor={(item) => item.conversation_id}
        contentContainerStyle={styles.list}
        refreshing={isLoading}
        onRefresh={refetch}
        ListEmptyComponent={
          <View style={styles.emptyState}>
            <Ionicons name="chatbubbles-outline" size={48} color="#6b7280" />
            <Text style={styles.emptyText}>No hay conversaciones activas</Text>
            <TouchableOpacity style={styles.startButton}>
              <Text style={styles.startButtonText}>Iniciar Conversación</Text>
            </TouchableOpacity>
          </View>
        }
      />
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8fafc',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 20,
    backgroundColor: 'white',
    borderBottomWidth: 1,
    borderBottomColor: '#e5e7eb',
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#1f2937',
  },
  addButton: {
    backgroundColor: '#6366f1',
    borderRadius: 8,
    width: 40,
    height: 40,
    justifyContent: 'center',
    alignItems: 'center',
  },
  list: {
    padding: 16,
  },
  conversationCard: {
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
  conversationHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  stageContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  stageText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#6366f1',
    marginLeft: 4,
  },
  sentimentContainer: {
    padding: 4,
  },
  clientPhone: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1f2937',
    marginBottom: 4,
  },
  intent: {
    fontSize: 14,
    color: '#6b7280',
    marginBottom: 8,
  },
  conversationDetails: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  messageCount: {
    fontSize: 14,
    color: '#6b7280',
  },
  healthScore: {
    backgroundColor: '#f3f4f6',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
  },
  healthScoreText: {
    fontSize: 12,
    color: '#374151',
    fontWeight: '600',
  },
  conversationDate: {
    fontSize: 12,
    color: '#9ca3af',
  },
  emptyState: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 60,
  },
  emptyText: {
    fontSize: 16,
    color: '#6b7280',
    marginTop: 12,
    marginBottom: 24,
    textAlign: 'center',
  },
  startButton: {
    backgroundColor: '#6366f1',
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 8,
  },
  startButtonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: '600',
  },
});

export default ConversationsScreen;