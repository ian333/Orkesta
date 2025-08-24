# 📋 SPRINT 01: FOUNDATION - TAREAS DETALLADAS

**Duración**: 1 semana
**Objetivo**: Sentar las bases con PostgreSQL, agentes básicos y comunicación

## 🎯 OBJETIVOS DEL SPRINT

1. ✅ Database setup con PostgreSQL + pgvector
2. ✅ Arquitectura de agentes base
3. ✅ Sistema de mensajería entre agentes
4. ✅ Primer flujo E2E: Pedido simple por WhatsApp
5. ✅ Multi-tenant isolation verificado

## 📊 TAREAS BREAKDOWN

### 🗄️ TASK 1: Database Setup
**Asignado a**: Backend Dev
**Tiempo estimado**: 8 horas
**Dependencias**: Ninguna

#### Subtareas:
```yaml
1.1 Instalar PostgreSQL + pgvector:
    - Docker compose con PostgreSQL 16
    - Extensión pgvector 0.8
    - Extensión pg_trgm para fuzzy search
    - Configurar connection pooling
    
1.2 Crear schema multi-tenant:
    - Tabla master 'tenants'
    - Function create_tenant_schema()
    - Row-level security policies
    - Audit triggers
    
1.3 Crear tablas core:
    - products (con embedding vector)
    - customers
    - orders
    - conversations
    - agent_messages
    
1.4 Seed data para testing:
    - 3 tenants demo
    - 100 productos por tenant
    - 10 clientes por tenant
```

#### Definition of Done:
- [ ] PostgreSQL corriendo en Docker
- [ ] pgvector instalado y funcionando
- [ ] Schema multi-tenant creado
- [ ] Tests de aislamiento pasando
- [ ] Seed data cargada

#### Código de referencia:
```sql
-- Ejemplo de tabla con vector
CREATE TABLE products (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id TEXT NOT NULL,
    sku TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    embedding VECTOR(1536),  -- OpenAI embeddings
    price DECIMAL(10,2),
    stock INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(tenant_id, sku)
);

-- Índice para búsqueda vectorial
CREATE INDEX ON products 
USING hnsw (embedding vector_cosine_ops)
WHERE tenant_id = current_setting('app.current_tenant');
```

---

### 🤖 TASK 2: Base Agent Architecture
**Asignado a**: AI Dev
**Tiempo estimado**: 12 horas
**Dependencias**: Task 1

#### Subtareas:
```yaml
2.1 Implementar BaseAgent class:
    - LLM client (Groq primary, Azure fallback)
    - Message handling
    - Error handling
    - Metrics collection
    
2.2 Implementar AgentMessage protocol:
    - Message structure
    - Serialization/deserialization
    - Validation
    
2.3 Implementar EventBus:
    - Redis pub/sub setup
    - Message routing
    - Persistence en PostgreSQL
    - Retry logic
    
2.4 Implementar OrchestratorAgent:
    - Intent analysis con LLM
    - Routing rules
    - Fallback handling
    - Response aggregation
```

#### Definition of Done:
- [ ] BaseAgent puede llamar a Groq
- [ ] Fallback a Azure funciona
- [ ] EventBus envía/recibe mensajes
- [ ] Orchestrator routea correctamente
- [ ] Tests unitarios pasando

#### Código de referencia:
```python
class BaseAgent:
    async def process_message(self, message: AgentMessage):
        # Pre-processing
        validated = self.validate(message)
        
        # LLM processing
        response = await self.llm.process(validated)
        
        # Post-processing
        enriched = self.enrich(response)
        
        # Send response
        await self.event_bus.publish(enriched)
```

---

### 📱 TASK 3: WhatsApp Integration Mock
**Asignado a**: Backend Dev
**Tiempo estimado**: 6 horas
**Dependencias**: Task 2

#### Subtareas:
```yaml
3.1 WhatsApp Agent básico:
    - Recibir mensajes (mock por ahora)
    - Parsear texto
    - Enviar a Orchestrator
    - Formatear respuestas
    
3.2 Webhook endpoint:
    - POST /webhook/whatsapp
    - Validación de firma (mock)
    - Queue de mensajes
    - Rate limiting
    
3.3 Simulador de WhatsApp:
    - UI simple para testing
    - Enviar mensajes
    - Ver respuestas
    - Simular diferentes usuarios
```

#### Definition of Done:
- [ ] Endpoint recibe mensajes
- [ ] WhatsApp agent procesa texto
- [ ] Respuestas formateadas correctamente
- [ ] Simulador funcionando

---

### 🛍️ TASK 4: Catalog Agent
**Asignado a**: AI Dev
**Tiempo estimado**: 10 horas
**Dependencias**: Task 2

#### Subtareas:
```yaml
4.1 Búsqueda de productos:
    - Búsqueda por texto exacto
    - Búsqueda fuzzy
    - Búsqueda vectorial
    - Ranking de resultados
    
4.2 Normalización con IA:
    - Entender variaciones ("tubo"/"tubería")
    - Mapear unidades ("1/2 pulgada"/"media")
    - Detectar cantidades
    
4.3 Generación de embeddings:
    - Integración con OpenAI
    - Batch processing
    - Cache de embeddings
    
4.4 Respuestas inteligentes:
    - Formato según contexto
    - Sugerencias alternativas
    - Manejo de "no encontrado"
```

#### Definition of Done:
- [ ] Busca productos por texto
- [ ] Entiende variaciones
- [ ] Embeddings funcionando
- [ ] Tests S01 y S02 pasando

#### Código de referencia:
```python
class CatalogAgent(BaseAgent):
    async def search_products(self, query: str, tenant_id: str):
        # 1. Búsqueda exacta
        exact = await self.db.search_exact(query, tenant_id)
        if exact:
            return exact
        
        # 2. Búsqueda fuzzy
        fuzzy = await self.db.search_fuzzy(query, tenant_id)
        if fuzzy and fuzzy.score > 0.7:
            return fuzzy
        
        # 3. Búsqueda vectorial
        embedding = await self.generate_embedding(query)
        similar = await self.db.search_vector(embedding, tenant_id)
        
        return similar
```

---

### 📝 TASK 5: Order Agent
**Asignado a**: Backend Dev
**Tiempo estimado**: 8 horas
**Dependencias**: Task 4

#### Subtareas:
```yaml
5.1 Crear órdenes:
    - Validar productos
    - Calcular totales
    - Aplicar impuestos
    - Generar ID único
    
5.2 Estado de órdenes:
    - State machine
    - Transiciones válidas
    - Audit log
    
5.3 Integración con catálogo:
    - Verificar stock
    - Reservar productos
    - Actualizar disponibilidad
```

#### Definition of Done:
- [ ] Crea órdenes válidas
- [ ] Maneja estados correctamente
- [ ] Integrado con catálogo
- [ ] Test S01 completo pasando

---

### 🧪 TASK 6: Integration Testing
**Asignado a**: QA Dev
**Tiempo estimado**: 8 horas
**Dependencias**: Tasks 1-5

#### Subtareas:
```yaml
6.1 Setup testing environment:
    - Docker compose para tests
    - Fixtures y mocks
    - CI/CD pipeline
    
6.2 Implementar scenarios S01 y S02:
    - Pedido simple
    - Pedido ambiguo
    - Verificaciones E2E
    
6.3 Multi-tenant testing (S09):
    - Crear múltiples tenants
    - Verificar aislamiento
    - Tests de seguridad
    
6.4 Performance baseline:
    - Medir latencias
    - Throughput máximo
    - Memory usage
```

#### Definition of Done:
- [ ] S01 pasando E2E
- [ ] S02 pasando E2E
- [ ] S09 verificado
- [ ] Métricas baseline documentadas

---

## 📈 MÉTRICAS DE ÉXITO DEL SPRINT

| Métrica | Target | Actual | Status |
|---------|--------|--------|--------|
| Tareas completadas | 6/6 | 0/6 | 🔄 |
| Tests pasando | S01, S02, S09 | - | 🔄 |
| Cobertura de código | > 70% | - | 🔄 |
| Performance (P95) | < 500ms | - | 🔄 |
| Bugs críticos | 0 | - | 🔄 |

## 🚀 ENTREGABLES

1. **Database**: PostgreSQL con pgvector funcionando
2. **Agents**: Base, Orchestrator, Catalog, Order
3. **Communication**: EventBus con Redis
4. **Tests**: S01, S02, S09 pasando
5. **Docs**: Arquitectura documentada

## ⚠️ RIESGOS

| Riesgo | Impacto | Probabilidad | Mitigación |
|--------|---------|--------------|------------|
| Groq API límites | Alto | Media | Azure fallback listo |
| pgvector performance | Medio | Baja | Índices optimizados |
| Multi-tenant bugs | Alto | Media | Tests exhaustivos |
| Integration issues | Alto | Alta | Testing continuo |

## 📅 DAILY STANDUP TOPICS

### Lunes
- Database setup status
- Bloqueadores?

### Martes  
- Agent architecture review
- LLM integration working?

### Miércoles
- WhatsApp mock status
- Catalog search working?

### Jueves
- Order flow E2E
- Integration issues?

### Viernes
- Testing results
- Sprint review prep

## ✅ DEFINITION OF DONE DEL SPRINT

- [ ] Todos los tests (S01, S02, S09) pasando
- [ ] Código reviewed y mergeado
- [ ] Documentación actualizada
- [ ] Demo preparada
- [ ] Métricas collected
- [ ] Retrospectiva completada

---

**🎯 RECORDAR**: No escribir código sin que los tests estén definidos primero!