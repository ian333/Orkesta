# 🧪 ORKESTA TEST SUITE - IA-DRIVEN TESTING

## 📂 ESTRUCTURA DE TESTS

```
tests/
├── user_stories/          # Tests basados en historias de usuario
│   ├── test_us_1_onboarding.py     # Epic 1: Onboarding inteligente
│   ├── test_us_2_ventas_autonomas.py # Epic 2: Ventas con IA
│   ├── test_us_3_cobranza.py       # Epic 3: Cobranza inteligente
│   └── test_us_4_verificacion.py   # Epic 4: Verificación continua
│
├── unit/                  # Tests unitarios por componente
│   ├── test_shared_context.py      # Contexto compartido
│   ├── test_agents.py              # Agentes individuales
│   ├── test_stripe_integration.py  # Stripe Connect
│   └── test_conversation_flow.py   # Motor de conversación
│
├── integration/           # Tests de integración
│   ├── test_agent_collaboration.py # Agentes trabajando juntos
│   ├── test_payment_flow.py       # Flujo completo de pago
│   ├── test_order_lifecycle.py    # Ciclo de vida de orden
│   └── test_multi_tenant.py       # Aislamiento multi-tenant
│
├── e2e/                   # Tests end-to-end
│   ├── test_complete_sale.py      # Venta completa con IA
│   ├── test_catalog_import.py     # Importación inteligente
│   ├── test_dunning_cycle.py      # Ciclo completo de cobranza
│   └── test_autonomous_operation.py # Operación autónoma 24/7
│
├── performance/           # Tests de rendimiento
│   ├── orkesta_simulation_lab.py  # Laboratorio de simulación
│   ├── test_load.py              # Pruebas de carga
│   ├── test_concurrent_agents.py  # Agentes concurrentes
│   └── test_scale.py             # Escalabilidad
│
├── fixtures/              # Datos de prueba
│   ├── catalogs/                 # Catálogos de ejemplo
│   ├── conversations/            # Conversaciones de prueba
│   ├── transactions/             # Transacciones mock
│   └── clients/                  # Clientes de prueba
│
├── test_orkesta_quick.py         # Test rápido del sistema
└── orkesta_comprehensive_test_suite.py # Suite completa
```

## 🎯 FILOSOFÍA DE TESTING

### La IA también verifica los tests
- Cada test es verificado por IA antes de ejecutarse
- Los resultados son analizados por IA para detectar patrones
- La IA sugiere nuevos tests basados en gaps detectados

### Principios:
1. **Test-Driven by User Stories**: Cada test mapea a un caso de uso real
2. **AI-First Testing**: La IA no es mock, es parte del test
3. **Continuous Verification**: Tests corriendo 24/7 con datos reales
4. **Self-Healing Tests**: La IA corrige tests que fallan por cambios menores

## 🚀 EJECUTAR TESTS

### Test Rápido (30 segundos)
```bash
# Verificación básica del sistema
python tests/test_orkesta_quick.py
```

### Tests por Epic
```bash
# Onboarding inteligente
python -m pytest tests/user_stories/test_us_1_onboarding.py -v

# Ventas autónomas
python -m pytest tests/user_stories/test_us_2_ventas_autonomas.py -v

# Cobranza inteligente
python -m pytest tests/user_stories/test_us_3_cobranza.py -v

# Verificación continua
python -m pytest tests/user_stories/test_us_4_verificacion.py -v
```

### Suite Completa
```bash
# Todos los tests (10-15 minutos)
python tests/orkesta_comprehensive_test_suite.py

# Con reporte detallado
python -m pytest tests/ --html=report.html --self-contained-html
```

### Tests de Performance
```bash
# Simulación de carga real
python tests/performance/orkesta_simulation_lab.py

# Test de estrés (cuidado: usa recursos)
python tests/performance/test_load.py --users=1000 --duration=600
```

## 📊 COBERTURA ACTUAL

| Componente | Unit | Integration | E2E | Performance |
|------------|------|-------------|-----|-------------|
| Shared Context | 85% | 75% | 70% | ✅ |
| Agentes IA | 70% | 65% | 60% | ✅ |
| Stripe Connect | 90% | 85% | 80% | ✅ |
| Conversaciones | 75% | 70% | 65% | ⚠️ |
| Verificaciones | 60% | 55% | 50% | 🔄 |

**Leyenda**: ✅ Completo | ⚠️ Parcial | 🔄 En desarrollo | ❌ Pendiente

## 🤖 TESTS CON IA REAL

### Configuración de LLMs para tests
```python
# tests/conftest.py
import pytest
import os

@pytest.fixture
def ai_client():
    """Cliente de IA para tests"""
    if os.getenv("USE_MOCK_AI") == "true":
        return MockAIClient()  # Para CI/CD
    else:
        return RealAIClient()  # Para tests reales

@pytest.fixture
def conversation_ai():
    """IA de conversación para tests"""
    return ConversationAI(
        model="groq/llama-3.1-8b",
        temperature=0.7,
        test_mode=True
    )
```

### Ejemplo de test con IA real
```python
def test_ai_understands_ambiguous_order(conversation_ai):
    """Test que la IA entiende pedidos ambiguos"""
    
    # Mensaje ambiguo real
    message = "necesito 3 de los que me vendiste ayer pero más grandes"
    
    # La IA real debe procesarlo
    response = conversation_ai.process(message)
    
    # Verificaciones
    assert response.confidence > 0.6
    assert response.needs_clarification or response.has_product_match
    assert response.suggested_action in ["clarify", "confirm", "proceed"]
```

## 📈 MÉTRICAS DE TESTING

### Dashboard de Tests
```
┌─────────────────────────────────────────────┐
│          TEST EXECUTION SUMMARY              │
├─────────────────────────────────────────────┤
│                                             │
│ Last Run: 2024-08-24 10:30:00             │
│ Duration: 12m 34s                          │
│                                             │
│ Results:                                    │
│ ├─ Passed: 234 ✅ (92%)                   │
│ ├─ Failed: 15 ❌ (6%)                      │
│ ├─ Skipped: 5 ⏭️ (2%)                      │
│ └─ Total: 254                              │
│                                             │
│ Coverage:                                   │
│ ├─ Statements: 78%                         │
│ ├─ Branches: 65%                           │
│ ├─ Functions: 82%                          │
│ └─ Lines: 76%                              │
│                                             │
│ AI Verifications:                          │
│ ├─ Total AI calls: 1,234                   │
│ ├─ Avg response time: 234ms                │
│ ├─ Accuracy: 94.5%                         │
│ └─ Cost: $0.47                             │
│                                             │
└─────────────────────────────────────────────┘
```

## 🔄 CI/CD PIPELINE

### GitHub Actions
```yaml
name: Orkesta AI Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Setup Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-cov pytest-html
    
    - name: Run quick tests
      run: python tests/test_orkesta_quick.py
    
    - name: Run unit tests
      run: pytest tests/unit/ -v --cov
    
    - name: Run integration tests
      run: pytest tests/integration/ -v
      
    - name: Run E2E tests (if main branch)
      if: github.ref == 'refs/heads/main'
      run: pytest tests/e2e/ -v
      
    - name: Upload coverage
      uses: codecov/codecov-action@v2
```

## 🐛 DEBUGGING TESTS

### Modo verbose
```bash
# Ver detalles de cada test
pytest tests/ -vvv

# Ver print statements
pytest tests/ -s

# Parar en el primer fallo
pytest tests/ -x

# Modo debug con pdb
pytest tests/ --pdb
```

### Logs de IA
```python
# Activar logs detallados de IA
import logging
logging.getLogger("orkesta.ai").setLevel(logging.DEBUG)

# Ver decisiones de la IA
os.environ["AI_EXPLAIN_DECISIONS"] = "true"

# Guardar conversaciones de test
os.environ["SAVE_TEST_CONVERSATIONS"] = "true"
```

## 📝 ESCRIBIR NUEVOS TESTS

### Template para User Story
```python
"""
USER STORY X: [Título]
Como [usuario]
Quiero [acción]
Para [beneficio]
"""

class TestUserStoryX:
    
    def test_acceptance_criteria_1(self):
        """
        GIVEN [contexto]
        WHEN [acción]
        THEN [resultado esperado]
        """
        # Arrange
        
        # Act
        
        # Assert
        
    def test_edge_case(self):
        """Casos límite que la IA debe manejar"""
        pass
    
    def test_ai_decision(self):
        """Verificar que la IA toma la decisión correcta"""
        pass
```

## 🚨 TESTS FALLANDO?

### Checklist de debugging
1. ✅ ¿El servidor está corriendo? (`python run_orkesta.py`)
2. ✅ ¿Las API keys están configuradas? (`.env`)
3. ✅ ¿La base de datos existe? (`orkesta.db`)
4. ✅ ¿Los agentes tienen LLM client? (Groq/Azure)
5. ✅ ¿El test está usando el tenant correcto?

### Errores comunes
- `No LLM client available`: Configurar `GROQ_API_KEY`
- `ModuleNotFoundError`: Verificar imports y paths
- `Connection refused`: Levantar el servidor
- `Timeout`: Aumentar timeout o usar mock

## 🎯 ROADMAP DE TESTING

### Sprint Actual
- [x] Estructura de tests organizada
- [x] User stories documentadas
- [x] Tests de onboarding
- [x] Tests de ventas autónomas
- [ ] Tests de cobranza inteligente
- [ ] Tests de verificación continua

### Próximo Sprint
- [ ] Tests de performance bajo carga
- [ ] Tests de seguridad y penetración
- [ ] Tests de disaster recovery
- [ ] Tests de integración con WhatsApp real
- [ ] Tests de multi-idioma
- [ ] Tests de edge cases extremos

---

**🎯 RECORDAR: Los tests no validan features, validan que la IA está tomando decisiones correctas.**