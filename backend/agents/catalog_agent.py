"""
Agente de Catálogo IQ - Convierte PDFs en catálogos vendibles
"""
import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import logging
from difflib import SequenceMatcher
import json

logger = logging.getLogger(__name__)

@dataclass
class Product:
    """Producto normalizado del catálogo"""
    sku: str
    name: str
    description: Optional[str]
    unit: str
    price: float
    brand: Optional[str]
    category: Optional[str]
    aliases: List[str] = None
    
    def __post_init__(self):
        if self.aliases is None:
            self.aliases = []

class CatalogAgent:
    """
    Agente inteligente para procesar catálogos PDF y responder consultas
    Especializado en ferreterías, refaccionarias y consultorios
    """
    
    def __init__(self):
        # Patrones comunes en catálogos mexicanos
        self.patterns = {
            'sku': [
                r'^[A-Z]{2,4}[-\s]?\d{3,6}',  # TUB-001, CEM001
                r'^\d{6,13}$',  # EAN/UPC
                r'^[A-Z0-9]{4,12}$'  # Códigos mixtos
            ],
            'price': [
                r'\$?\s*[\d,]+\.?\d{0,2}',  # $1,234.56 o 1234.56
                r'MXN\s*[\d,]+\.?\d{0,2}',
                r'[\d,]+\.?\d{0,2}\s*(?:pesos|MXN)'
            ],
            'unit': [
                r'\b(?:pza?|pieza|unidad|kg|gr?|lt?|ml|mt?|cm|mm|pulg|")\b',
                r'\b(?:caja|bolsa|paquete|rollo|galón|litro|metro)\b',
                r'\b(?:par|docena|ciento|millar)\b'
            ]
        }
        
        # Sinónimos comunes en ferretería/refacciones
        self.synonyms = {
            'tubo': ['tubo', 'tuberia', 'caño', 'ducto'],
            'pvc': ['pvc', 'p.v.c.', 'plastico', 'cpvc'],
            '1/2': ['1/2', 'media', '0.5', 'medio', '12mm', '½'],
            '3/4': ['3/4', 'tres cuartos', '0.75', '19mm', '¾'],
            '1': ['1', 'una', 'pulgada', '25mm', '1"'],
            'tornillo': ['tornillo', 'pija', 'tirafondo'],
            'tuerca': ['tuerca', 'rosca', 'hembra'],
            'rondana': ['rondana', 'arandela', 'washer'],
            'cemento': ['cemento', 'mortero', 'concreto'],
            'pintura': ['pintura', 'esmalte', 'barniz', 'laca']
        }
        
        # Cache de productos procesados
        self.product_cache = {}
        
    def extract_from_pdf(self, pdf_content: str) -> List[Dict]:
        """
        Extrae productos de un PDF parseado
        """
        lines = pdf_content.split('\n')
        products = []
        
        for line in lines:
            if len(line.strip()) < 10:  # Skip líneas muy cortas
                continue
                
            product = self._parse_line(line)
            if product:
                products.append(product)
        
        # Normalizar y deduplicar
        normalized = self._normalize_products(products)
        
        logger.info(f"Extraídos {len(normalized)} productos únicos de {len(products)} líneas")
        return normalized
    
    def _parse_line(self, line: str) -> Optional[Dict]:
        """
        Parsea una línea del catálogo
        """
        # Buscar SKU
        sku = None
        for pattern in self.patterns['sku']:
            match = re.search(pattern, line)
            if match:
                sku = match.group()
                break
        
        # Buscar precio
        price = None
        for pattern in self.patterns['price']:
            match = re.search(pattern, line)
            if match:
                price_str = match.group()
                price = self._clean_price(price_str)
                break
        
        if not price:
            return None
        
        # Buscar unidad
        unit = 'PZA'  # Default
        for pattern in self.patterns['unit']:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                unit = match.group().upper()
                break
        
        # El resto es descripción
        description = line
        if sku:
            description = description.replace(sku, '')
        if price:
            description = re.sub(self.patterns['price'][0], '', description)
        
        description = ' '.join(description.split())  # Clean whitespace
        
        return {
            'sku': sku or f"AUTO_{hash(description) % 100000:05d}",
            'description': description,
            'price': price,
            'unit': unit
        }
    
    def _clean_price(self, price_str: str) -> float:
        """Limpia y convierte string de precio a float"""
        price_str = re.sub(r'[^\d.,]', '', price_str)
        price_str = price_str.replace(',', '')
        try:
            return float(price_str)
        except:
            return 0.0
    
    def _normalize_products(self, products: List[Dict]) -> List[Dict]:
        """
        Normaliza y deduplica productos
        """
        normalized = {}
        
        for product in products:
            # Generar clave única
            key = self._generate_key(product['description'])
            
            if key in normalized:
                # Si ya existe, promediar precios
                existing = normalized[key]
                existing['price'] = (existing['price'] + product['price']) / 2
                existing['aliases'].append(product['description'])
            else:
                normalized[key] = {
                    **product,
                    'canonical_name': self._canonicalize(product['description']),
                    'aliases': [product['description']],
                    'key': key
                }
        
        return list(normalized.values())
    
    def _generate_key(self, description: str) -> str:
        """
        Genera clave única para deduplicación
        """
        # Normalizar texto
        text = description.lower()
        text = re.sub(r'[^\w\s]', '', text)
        
        # Extraer tokens importantes
        tokens = []
        for word in text.split():
            # Buscar en sinónimos
            for canonical, syns in self.synonyms.items():
                if word in syns:
                    tokens.append(canonical)
                    break
            else:
                if len(word) > 2:  # Skip palabras muy cortas
                    tokens.append(word)
        
        return '_'.join(sorted(tokens))
    
    def _canonicalize(self, description: str) -> str:
        """
        Genera nombre canónico limpio
        """
        # Capitalizar primeras letras
        words = description.split()
        canonical = []
        
        for word in words:
            if word.upper() in ['PVC', 'CPVC', 'PPR', 'HG', 'HD']:
                canonical.append(word.upper())
            elif word[0].isdigit():
                canonical.append(word)
            else:
                canonical.append(word.capitalize())
        
        return ' '.join(canonical)
    
    def search_products(self, query: str, catalog: List[Dict]) -> List[Dict]:
        """
        Busca productos en el catálogo con fuzzy matching
        """
        query_lower = query.lower()
        query_tokens = set(query_lower.split())
        
        results = []
        
        for product in catalog:
            score = 0
            
            # Buscar en nombre canónico
            if query_lower in product['canonical_name'].lower():
                score += 10
            
            # Buscar en aliases
            for alias in product['aliases']:
                if query_lower in alias.lower():
                    score += 5
            
            # Buscar tokens individuales
            product_tokens = set(product['canonical_name'].lower().split())
            matching_tokens = query_tokens & product_tokens
            score += len(matching_tokens) * 2
            
            # Buscar con sinónimos
            for token in query_tokens:
                for canonical, syns in self.synonyms.items():
                    if token in syns and canonical in product['canonical_name'].lower():
                        score += 3
            
            # Fuzzy matching
            similarity = SequenceMatcher(None, query_lower, product['canonical_name'].lower()).ratio()
            score += similarity * 5
            
            if score > 3:  # Threshold mínimo
                results.append({
                    **product,
                    'score': score
                })
        
        # Ordenar por score
        results.sort(key=lambda x: x['score'], reverse=True)
        
        return results[:5]  # Top 5
    
    def extract_quantity_from_message(self, message: str) -> Tuple[Optional[int], str]:
        """
        Extrae cantidad del mensaje de WhatsApp
        """
        # Patrones para detectar cantidad
        patterns = [
            r'(\d+)\s*(?:piezas?|unidades?|pza?s?)',
            r'(\d+)\s*(?:kilos?|kg)',
            r'(\d+)\s*(?:metros?|mts?)',
            r'(\d+)\s*(?:litros?|lts?)',
            r'necesito\s*(\d+)',
            r'quiero\s*(\d+)',
            r'(\d+)\s*(?:de|del|dela)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                quantity = int(match.group(1))
                # Limpiar mensaje
                clean_message = re.sub(pattern, '', message, flags=re.IGNORECASE)
                return quantity, clean_message.strip()
        
        return 1, message  # Default 1 pieza
    
    def generate_whatsapp_response(self, products: List[Dict], quantity: int = 1) -> str:
        """
        Genera respuesta formateada para WhatsApp
        """
        if not products:
            return ("No encontré ese producto 😕\n"
                   "¿Podrías ser más específico?\n"
                   "Por ejemplo: 'tubo pvc 3/4' o 'cemento gris'")
        
        response = f"Encontré estas opciones para ti:\n\n"
        
        for i, product in enumerate(products[:3], 1):
            unit_price = product['price']
            total = unit_price * quantity
            
            response += f"*{i}. {product['canonical_name']}*\n"
            response += f"   SKU: {product['sku']}\n"
            response += f"   Precio unitario: ${unit_price:,.2f} {product['unit']}\n"
            
            if quantity > 1:
                response += f"   📦 {quantity} unidades = *${total:,.2f}*\n"
            
            response += "\n"
        
        response += "💳 *¿Cómo quieres pagar?*\n"
        response += "• Tarjeta de crédito/débito\n"
        response += "• OXXO (efectivo)\n"
        response += "• Transferencia SPEI\n\n"
        response += "Responde con el número del producto que quieres (1, 2 o 3)"
        
        return response
    
    def detect_price_changes(self, old_catalog: List[Dict], new_catalog: List[Dict]) -> Dict:
        """
        Detecta cambios de precio entre catálogos
        """
        changes = {
            'increased': [],
            'decreased': [],
            'new_products': [],
            'removed_products': []
        }
        
        old_by_sku = {p['sku']: p for p in old_catalog}
        new_by_sku = {p['sku']: p for p in new_catalog}
        
        # Buscar cambios
        for sku, new_product in new_by_sku.items():
            if sku in old_by_sku:
                old_price = old_by_sku[sku]['price']
                new_price = new_product['price']
                
                if new_price > old_price:
                    changes['increased'].append({
                        'sku': sku,
                        'name': new_product['canonical_name'],
                        'old_price': old_price,
                        'new_price': new_price,
                        'increase_pct': ((new_price - old_price) / old_price) * 100
                    })
                elif new_price < old_price:
                    changes['decreased'].append({
                        'sku': sku,
                        'name': new_product['canonical_name'],
                        'old_price': old_price,
                        'new_price': new_price,
                        'decrease_pct': ((old_price - new_price) / old_price) * 100
                    })
            else:
                changes['new_products'].append(new_product)
        
        # Productos removidos
        for sku in old_by_sku:
            if sku not in new_by_sku:
                changes['removed_products'].append(old_by_sku[sku])
        
        return changes