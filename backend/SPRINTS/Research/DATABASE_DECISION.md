# 🗄️ DECISIÓN DE BASE DE DATOS - ORKESTA

## 📊 ANÁLISIS Y JUSTIFICACIÓN

### CONTEXTO DEL PROBLEMA
Orkesta necesita una base de datos que pueda:
1. **Almacenar embeddings vectoriales** para búsqueda semántica
2. **Datos transaccionales** (órdenes, pagos, inventario)
3. **Contexto conversacional** (historial de chats)
4. **Escalar horizontalmente** con multi-tenancy
5. **Búsquedas híbridas** (SQL + Vector)

## 🔍 INVESTIGACIÓN DE OPCIONES (2024-2025)

### Opción 1: PostgreSQL + pgvector ✅ RECOMENDADO

**Ventajas:**
- **30 años de madurez**: ACID compliance, backups, replicación
- **Todo en un lugar**: No necesitas múltiples DBs
- **pgvector 0.8.0** soporta:
  - Hasta 64,000 dimensiones para bit vectors
  - Sparse vectors con 1,000 elementos no-zero
  - 9.4x mejora en latencia (13.1ms vs 123.3ms)
- **SQL + Vector**: Queries híbridas poderosas
- **Gratis y open source**

**Desventajas:**
- No tan optimizado como DBs vectoriales puras
- Requiere tuning para escala masiva

### Opción 2: MongoDB Atlas

**Ventajas:**
- Flexible para datos no estructurados
- Puede almacenar vectors junto con documentos
- Bueno para catálogos con estructura variable

**Desventajas:**
- No es vector-first
- Más caro que PostgreSQL
- Menos maduro para vectors

### Opción 3: Pinecone (Vector puro)

**Ventajas:**
- Optimizado para billones de vectores
- Managed service, zero ops
- Búsquedas ultra-rápidas

**Desventajas:**
- **Caro**: $70-$2000/mes
- Solo vectores, necesitas otra DB para transacciones
- Vendor lock-in

### Opción 4: ChromaDB

**Ventajas:**
- Open source y gratis
- Diseñado para LLMs
- Simple de usar

**Desventajas:**
- Menos maduro
- No maneja datos transaccionales
- Comunidad más pequeña

## 🎯 DECISIÓN FINAL: PostgreSQL + pgvector

### Justificación:

1. **Simplicidad Arquitectural**
   - Una sola DB para todo
   - Menos puntos de falla
   - Backup/restore unificado

2. **Costo-Efectivo**
   - Open source
   - No fees por vector
   - Hosting barato ($20-100/mes)

3. **Capacidades Híbridas**
   ```sql
   -- Query ejemplo: Buscar productos similares Y en stock
   SELECT 
     p.name, 
     p.price,
     p.embedding <=> query_embedding as similarity
   FROM products p
   WHERE 
     p.stock > 0 
     AND p.tenant_id = 'tenant-123'
     AND p.embedding <=> query_embedding < 0.5
   ORDER BY similarity
   LIMIT 10;
   ```

4. **Multi-tenant Nativo**
   - Row-level security
   - Partitioning por tenant
   - Isolation garantizado

## 📐 ARQUITECTURA PROPUESTA

```yaml
Database: PostgreSQL 16 + pgvector 0.8
Schema:
  public:
    - tenants (master table)
  
  tenant_specific: (schema per tenant)
    - products
      - id, name, sku, price
      - embedding VECTOR(1536)  # OpenAI embeddings
      - search_vector tsvector   # Full-text search
    
    - conversations
      - id, customer_id, channel
      - messages JSONB
      - context_embedding VECTOR(1536)
    
    - orders
      - Traditional OLTP tables
      - Foreign keys, constraints
    
    - agents_memory
      - agent_id, memory_type
      - embedding VECTOR(1536)
      - metadata JSONB

Indexes:
  - HNSW for vector similarity
  - GIN for JSONB
  - B-tree for lookups
```

## 🚀 PLAN DE IMPLEMENTACIÓN

### Fase 1: Setup Básico (Sprint 1)
```bash
# 1. Instalar PostgreSQL + pgvector
docker run -d \
  --name orkesta-db \
  -e POSTGRES_PASSWORD=orkesta \
  -p 5432:5432 \
  ankane/pgvector:latest

# 2. Crear extensión
CREATE EXTENSION vector;
CREATE EXTENSION pg_trgm;  -- Para fuzzy search
```

### Fase 2: Schema Multi-tenant (Sprint 1)
```sql
-- Tabla master de tenants
CREATE TABLE tenants (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  settings JSONB DEFAULT '{}'
);

-- Function para crear schema por tenant
CREATE OR REPLACE FUNCTION create_tenant_schema(tenant_id TEXT)
RETURNS void AS $$
BEGIN
  EXECUTE format('CREATE SCHEMA IF NOT EXISTS tenant_%s', tenant_id);
  -- Crear tablas dentro del schema
END;
$$ LANGUAGE plpgsql;
```

### Fase 3: Embeddings Integration (Sprint 2)
```python
# Generar embeddings con OpenAI
from openai import OpenAI
import psycopg2
from pgvector.psycopg2 import register_vector

def store_product_with_embedding(product):
    # Generar embedding
    embedding = openai.embeddings.create(
        input=f"{product['name']} {product['description']}",
        model="text-embedding-3-small"
    )
    
    # Guardar en PostgreSQL
    conn.execute("""
        INSERT INTO products (name, embedding)
        VALUES (%s, %s)
    """, (product['name'], embedding))
```

### Fase 4: Optimización (Sprint 3)
- Índices HNSW para búsquedas rápidas
- Partitioning por fecha para conversations
- Materialized views para dashboards
- Connection pooling con pgBouncer

## 📊 MÉTRICAS DE ÉXITO

| Métrica | Target | Medición |
|---------|--------|----------|
| Query latency (p95) | < 50ms | pgBadger |
| Similarity search | < 100ms | Custom metrics |
| Concurrent queries | > 1000/s | pgbench |
| Storage per tenant | < 1GB | pg_database_size |
| Backup time | < 5 min | pg_dump timing |

## 🔄 PLAN DE MIGRACIÓN FUTURA

Si necesitamos escalar más allá de PostgreSQL:

1. **Corto plazo**: Read replicas para queries
2. **Mediano plazo**: Citus para sharding horizontal
3. **Largo plazo**: Hybrid con vector DB especializada
   - PostgreSQL: Transacciones
   - Pinecone/Milvus: Vectores

## ⚠️ RIESGOS Y MITIGACIÓN

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------------|---------|------------|
| Performance degrada con escala | Media | Alto | Monitoring + índices |
| Embeddings muy grandes | Baja | Medio | Compression + pruning |
| Vendor lock-in pgvector | Baja | Bajo | Abstraction layer |

## ✅ DECISIÓN APROBADA

**PostgreSQL + pgvector** es la elección correcta para Orkesta porque:
1. Simplifica la arquitectura
2. Reduce costos operativos
3. Provee todas las features necesarias
4. Permite crecimiento gradual
5. Tiene comunidad masiva

**Fecha de decisión**: 2024-08-24
**Revisión próxima**: Sprint 4