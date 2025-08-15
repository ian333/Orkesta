"""
🧠 ORKESTA SMART AGENTS - Coreografía Inteligente de Agentes
==========================================================

Agentes que usan el contexto compartido para tomar decisiones
colaborativas. Cada agente tiene especialización pero comparte
el mismo "cerebro" (OrkestaSharedContext).
"""

import os
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
import logging
from dataclasses import asdict
import re
from difflib import SequenceMatcher

# Imports para LLMs
try:
    from groq import Groq
    groq_available = True
except ImportError:
    groq_available = False

try:
    from openai import AzureOpenAI
    azure_available = True
except ImportError:
    azure_available = False

from orkesta_shared_context import (
    get_shared_context, OrkestaSharedContext, Product, Client, 
    OrderStatus, OrderItem, Order, AgentSuggestion
)

logger = logging.getLogger(__name__)

class BaseOrkestaAgent:
    """Agente base con acceso al contexto compartido"""
    
    def __init__(self, name: str):
        self.name = name
        self.confidence_threshold = 0.85
        self.llm_client = self._initialize_llm()
        
    def _initialize_llm(self):
        """Inicializa cliente LLM (Groq preferido, Azure fallback)"""
        
        if groq_available and os.getenv("GROQ_API_KEY"):
            return Groq(api_key=os.getenv("GROQ_API_KEY"))
        elif azure_available and os.getenv("AZURE_OPENAI_KEY"):
            return AzureOpenAI(
                api_key=os.getenv("AZURE_OPENAI_KEY"),
                api_version="2024-02-01",
                azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
            )
        else:
            logger.warning(f"No LLM client available for {self.name}")
            return None
    
    def _call_llm(self, prompt: str, max_tokens: int = 500) -> str:
        """Llama al LLM con manejo de errores"""
        
        if not self.llm_client:
            return "LLM no disponible"
        
        try:
            if isinstance(self.llm_client, Groq):
                response = self.llm_client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=max_tokens,
                    temperature=0.3
                )
                return response.choices[0].message.content
            
            elif hasattr(self.llm_client, 'chat'):
                response = self.llm_client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=max_tokens,
                    temperature=0.3
                )
                return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"LLM call failed for {self.name}: {e}")
            return f"Error en LLM: {e}"
    
    def get_context(self, tenant_id: str) -> OrkestaSharedContext:
        """Obtiene contexto compartido del tenant"""
        return get_shared_context(tenant_id)
    
    def suggest_with_confidence(self, tenant_id: str, suggestion_type: str, 
                               description: str, confidence: float, 
                               data: Dict[str, Any]) -> str:
        """Crea sugerencia en el contexto compartido"""
        
        ctx = self.get_context(tenant_id)
        suggestion_id = ctx.add_agent_suggestion(
            agent_name=self.name,
            suggestion_type=suggestion_type,
            description=description,
            confidence=confidence,
            data=data
        )
        
        logger.info(f"{self.name} suggested {suggestion_type} with confidence {confidence:.2f}")
        return suggestion_id

class CatalogMapperAgent(BaseOrkestaAgent):
    """
    Agente que mapea imports de catálogos (PDF/Excel/Foto).
    Detecta columnas automáticamente y sugiere mapeos.
    """
    
    def __init__(self):
        super().__init__("CatalogMapper")
    
    def analyze_import_structure(self, tenant_id: str, file_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analiza estructura de un archivo importado y sugiere mapeo.
        
        Args:
            file_data: {
                "filename": "catalogo.xlsx",
                "columns": ["codigo", "descripcion", "precio", "stock"],
                "sample_rows": [...]
            }
        """
        
        ctx = self.get_context(tenant_id)
        
        # Analizar columnas con LLM
        prompt = f"""
        Analiza estas columnas de un catálogo importado y mapea a nuestro esquema:
        
        Archivo: {file_data.get('filename', 'unknown')}
        Columnas: {file_data.get('columns', [])}
        Datos ejemplo: {json.dumps(file_data.get('sample_rows', [])[:3], ensure_ascii=False)}
        
        Esquema objetivo:
        - sku: Código único del producto
        - name: Nombre/descripción del producto  
        - price: Precio en MXN
        - unit: Unidad (pieza, metro, kilo, etc)
        - brand: Marca (opcional)
        - stock: Cantidad disponible
        
        Responde en JSON:
        {{
            "mapping": {{"columna_origen": "campo_destino"}},
            "confidence": 0.95,
            "issues": ["lista de problemas detectados"],
            "suggestions": ["lista de mejoras"]
        }}
        """
        
        llm_response = self._call_llm(prompt, max_tokens=800)
        
        try:
            mapping_result = json.loads(llm_response)
        except:
            # Fallback manual
            mapping_result = self._fallback_column_mapping(file_data.get('columns', []))
        
        # Validar mapeo
        validation = self._validate_mapping(file_data, mapping_result.get("mapping", {}))
        
        # Crear sugerencia si confidence es alta
        if mapping_result.get("confidence", 0) > self.confidence_threshold:
            suggestion_id = self.suggest_with_confidence(
                tenant_id=tenant_id,
                suggestion_type="catalog_mapping",
                description=f"Mapeo automático para {file_data.get('filename')}",
                confidence=mapping_result.get("confidence", 0),
                data={
                    "filename": file_data.get("filename"),
                    "mapping": mapping_result.get("mapping"),
                    "validation": validation,
                    "estimated_rows": len(file_data.get('sample_rows', []))
                }
            )
        else:
            suggestion_id = None
        
        return {
            "mapping": mapping_result.get("mapping", {}),
            "confidence": mapping_result.get("confidence", 0),
            "validation": validation,
            "suggestion_id": suggestion_id,
            "issues": mapping_result.get("issues", []),
            "recommendations": mapping_result.get("suggestions", [])
        }
    
    def _fallback_column_mapping(self, columns: List[str]) -> Dict[str, Any]:
        """Mapeo de columnas manual si LLM falla"""
        
        mapping = {}
        confidence = 0.5
        
        # Patrones comunes
        patterns = {
            "sku": ["codigo", "sku", "clave", "id", "ref"],
            "name": ["nombre", "descripcion", "desc", "producto", "item"],
            "price": ["precio", "costo", "cost", "price"],
            "unit": ["unidad", "unit", "medida", "um"],
            "stock": ["stock", "existencia", "inventario", "qty", "cantidad"],
            "brand": ["marca", "brand", "fabricante"]
        }
        
        columns_lower = [col.lower() for col in columns]
        
        for target_field, keywords in patterns.items():
            for keyword in keywords:
                matches = [col for col in columns_lower if keyword in col]
                if matches:
                    # Tomar la primera coincidencia
                    original_col = columns[columns_lower.index(matches[0])]
                    mapping[original_col] = target_field
                    confidence += 0.1
                    break
        
        return {
            "mapping": mapping,
            "confidence": min(confidence, 0.8),  # Máximo 0.8 para fallback
            "issues": ["Mapeo automático por patrones - revisar manualmente"],
            "suggestions": ["Verificar que los campos mapeados sean correctos"]
        }
    
    def _validate_mapping(self, file_data: Dict[str, Any], mapping: Dict[str, str]) -> Dict[str, Any]:
        """Valida el mapeo propuesto"""
        
        validation = {
            "required_fields_mapped": True,
            "data_type_issues": [],
            "missing_required": [],
            "data_quality_score": 0.0
        }
        
        required_fields = ["sku", "name", "price"]
        mapped_fields = set(mapping.values())
        
        # Verificar campos requeridos
        for field in required_fields:
            if field not in mapped_fields:
                validation["missing_required"].append(field)
                validation["required_fields_mapped"] = False
        
        # Verificar tipos de datos en sample
        sample_rows = file_data.get("sample_rows", [])
        if sample_rows and mapping:
            columns = file_data.get("columns", [])
            
            for orig_col, target_field in mapping.items():
                if orig_col in columns:
                    col_index = columns.index(orig_col)
                    
                    # Analizar valores de la columna
                    values = [row[col_index] for row in sample_rows if len(row) > col_index]
                    
                    if target_field == "price":
                        # Verificar que precios sean numéricos
                        numeric_count = 0
                        for value in values:
                            try:
                                float(str(value).replace(",", ""))
                                numeric_count += 1
                            except:
                                pass
                        
                        if numeric_count / len(values) < 0.8:
                            validation["data_type_issues"].append(f"Columna {orig_col} contiene valores no numéricos")
        
        # Calcular score de calidad
        quality_factors = [
            validation["required_fields_mapped"],
            len(validation["data_type_issues"]) == 0,
            len(mapping) >= 3  # Al menos 3 campos mapeados
        ]
        
        validation["data_quality_score"] = sum(quality_factors) / len(quality_factors)
        
        return validation

class AliasNormalizerAgent(BaseOrkestaAgent):
    """
    Agente que detecta productos duplicados y normaliza aliases.
    Sugiere merges de SKUs similares.
    """
    
    def __init__(self):
        super().__init__("AliasNormalizer")
    
    def detect_duplicates(self, tenant_id: str) -> List[Dict[str, Any]]:
        """Detecta productos potencialmente duplicados"""
        
        ctx = self.get_context(tenant_id)
        products = list(ctx.catalog["products"].values())
        
        duplicates = []
        processed = set()
        
        for i, product1 in enumerate(products):
            if product1.product_id in processed:
                continue
            
            potential_duplicates = []
            
            for j, product2 in enumerate(products[i+1:], i+1):
                if product2.product_id in processed:
                    continue
                
                similarity = self._calculate_similarity(product1, product2)
                
                if similarity["overall_score"] > 0.75:
                    potential_duplicates.append({
                        "product": product2,
                        "similarity": similarity
                    })
                    processed.add(product2.product_id)
            
            if potential_duplicates:
                # Analizar con LLM para confirmación
                llm_analysis = self._analyze_duplicates_with_llm(product1, potential_duplicates)
                
                duplicates.append({
                    "primary_product": product1,
                    "duplicates": potential_duplicates,
                    "llm_analysis": llm_analysis,
                    "confidence": llm_analysis.get("confidence", 0.0),
                    "recommended_action": llm_analysis.get("action", "review_manually")
                })
                
                processed.add(product1.product_id)
        
        # Crear sugerencias para duplicados con alta confianza
        for duplicate_group in duplicates:
            if duplicate_group["confidence"] > self.confidence_threshold:
                self.suggest_with_confidence(
                    tenant_id=tenant_id,
                    suggestion_type="merge_duplicates",
                    description=f"Merge {len(duplicate_group['duplicates'])} productos similares",
                    confidence=duplicate_group["confidence"],
                    data={
                        "primary_product_id": duplicate_group["primary_product"].product_id,
                        "duplicate_product_ids": [d["product"].product_id for d in duplicate_group["duplicates"]],
                        "similarity_scores": [d["similarity"] for d in duplicate_group["duplicates"]],
                        "recommended_action": duplicate_group["recommended_action"]
                    }
                )
        
        return duplicates
    
    def _calculate_similarity(self, product1: Product, product2: Product) -> Dict[str, float]:
        """Calcula similitud entre dos productos"""
        
        # Similitud de nombres
        name_sim = SequenceMatcher(None, product1.name.lower(), product2.name.lower()).ratio()
        
        # Similitud de SKUs
        sku_sim = SequenceMatcher(None, product1.sku.lower(), product2.sku.lower()).ratio()
        
        # Similitud de aliases
        alias_sim = 0.0
        if product1.aliases and product2.aliases:
            all_aliases1 = [alias.lower() for alias in product1.aliases]
            all_aliases2 = [alias.lower() for alias in product2.aliases]
            
            max_alias_sim = 0.0
            for alias1 in all_aliases1:
                for alias2 in all_aliases2:
                    sim = SequenceMatcher(None, alias1, alias2).ratio()
                    max_alias_sim = max(max_alias_sim, sim)
            
            alias_sim = max_alias_sim
        
        # Similitud de atributos
        attr_sim = 0.0
        if product1.attributes and product2.attributes:
            common_attrs = set(product1.attributes.keys()) & set(product2.attributes.keys())
            if common_attrs:
                matching_values = 0
                for attr in common_attrs:
                    if product1.attributes[attr].lower() == product2.attributes[attr].lower():
                        matching_values += 1
                attr_sim = matching_values / len(common_attrs)
        
        # Diferencia de precios (inversa - similar precio = mayor similitud)
        price_sim = 0.0
        price1 = product1.pricing.lists.get("lista_base", {}).get("MXN", 0)
        price2 = product2.pricing.lists.get("lista_base", {}).get("MXN", 0)
        
        if price1 > 0 and price2 > 0:
            price_diff = abs(price1 - price2) / max(price1, price2)
            price_sim = max(0, 1 - price_diff)
        
        # Score general ponderado
        overall_score = (
            name_sim * 0.4 +
            sku_sim * 0.2 + 
            alias_sim * 0.2 +
            attr_sim * 0.1 +
            price_sim * 0.1
        )
        
        return {
            "name_similarity": name_sim,
            "sku_similarity": sku_sim,
            "alias_similarity": alias_sim,
            "attributes_similarity": attr_sim,
            "price_similarity": price_sim,
            "overall_score": overall_score
        }
    
    def _analyze_duplicates_with_llm(self, primary: Product, duplicates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analiza duplicados potenciales con LLM"""
        
        prompt = f"""
        Analiza si estos productos son duplicados que deben combinarse:
        
        PRODUCTO PRINCIPAL:
        SKU: {primary.sku}
        Nombre: {primary.name}
        Aliases: {primary.aliases}
        Atributos: {primary.attributes}
        
        PRODUCTOS SIMILARES:
        """
        
        for i, dup in enumerate(duplicates, 1):
            product = dup["product"]
            prompt += f"""
        {i}. SKU: {product.sku}
           Nombre: {product.name}
           Aliases: {product.aliases}
           Similitud: {dup["similarity"]["overall_score"]:.2f}
        """
        
        prompt += """
        
        Responde en JSON:
        {
            "are_duplicates": true/false,
            "confidence": 0.95,
            "action": "merge_all|merge_some|keep_separate|review_manually",
            "reasoning": "explicación de tu decisión",
            "suggested_master": "sku_del_producto_principal",
            "aliases_to_merge": ["alias1", "alias2"]
        }
        """
        
        llm_response = self._call_llm(prompt, max_tokens=600)
        
        try:
            return json.loads(llm_response)
        except:
            return {
                "are_duplicates": False,
                "confidence": 0.3,
                "action": "review_manually",
                "reasoning": "Error en análisis LLM",
                "suggested_master": primary.sku,
                "aliases_to_merge": []
            }
    
    def normalize_units(self, tenant_id: str) -> Dict[str, Any]:
        """Normaliza unidades de medida en el catálogo"""
        
        ctx = self.get_context(tenant_id)
        products = list(ctx.catalog["products"].values())
        
        # Mapeo de unidades comunes
        unit_mappings = {
            "pz": "pieza", "pza": "pieza", "pc": "pieza", "unidad": "pieza",
            "m": "metro", "mts": "metro", "metros": "metro",
            "kg": "kilogramo", "kilo": "kilogramo", "kilos": "kilogramo",
            "l": "litro", "lt": "litro", "lts": "litro",
            "cj": "caja", "cajas": "caja",
            "rl": "rollo", "rollos": "rollo"
        }
        
        normalization_suggestions = []
        unit_frequency = {}
        
        # Analizar unidades actuales
        for product in products:
            unit = product.unit.lower().strip()
            unit_frequency[unit] = unit_frequency.get(unit, 0) + 1
        
        # Generar sugerencias de normalización
        for original_unit, count in unit_frequency.items():
            normalized = unit_mappings.get(original_unit, original_unit)
            
            if normalized != original_unit:
                normalization_suggestions.append({
                    "original_unit": original_unit,
                    "normalized_unit": normalized,
                    "affected_products": count,
                    "confidence": 0.9
                })
        
        # Crear sugerencia en contexto
        if normalization_suggestions:
            suggestion_id = self.suggest_with_confidence(
                tenant_id=tenant_id,
                suggestion_type="normalize_units",
                description=f"Normalizar {len(normalization_suggestions)} tipos de unidades",
                confidence=0.9,
                data={
                    "normalizations": normalization_suggestions,
                    "total_affected_products": sum(s["affected_products"] for s in normalization_suggestions)
                }
            )
        else:
            suggestion_id = None
        
        return {
            "suggestions": normalization_suggestions,
            "current_units": unit_frequency,
            "suggestion_id": suggestion_id
        }

class PriceResolverAgent(BaseOrkestaAgent):
    """
    Agente que resuelve precios según cliente y políticas.
    Aplica descuentos, overrides y promociones.
    """
    
    def __init__(self):
        super().__init__("PriceResolver")
    
    def resolve_price(self, tenant_id: str, product_id: str, client_id: str, 
                     quantity: int = 1, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Resuelve precio final para un producto y cliente específico.
        
        Returns:
            {
                "final_price": 125.50,
                "list_price": 150.00,
                "discount_applied": 24.50,
                "discount_reason": "Cliente VIP",
                "pricing_rule": "override_client_vip",
                "valid_until": "2025-08-15",
                "quantity_breaks": {...}
            }
        """
        
        ctx = self.get_context(tenant_id)
        
        # Obtener producto y cliente
        if product_id not in ctx.catalog["products"]:
            return {"error": f"Producto {product_id} no encontrado"}
        
        product = ctx.catalog["products"][product_id]
        client = ctx.clients.get(client_id)
        
        # Precio base
        list_price = ctx.get_product_price(product_id)
        if list_price is None:
            return {"error": f"No hay precio configurado para {product_id}"}
        
        # Resolver precio con reglas de negocio
        pricing_result = self._apply_pricing_rules(
            product, client, list_price, quantity, context or {}
        )
        
        # Analizar con LLM si hay contexto especial
        if context and context.get("special_request"):
            llm_analysis = self._analyze_pricing_with_llm(
                product, client, pricing_result, context
            )
            
            if llm_analysis.get("suggested_adjustment"):
                # Crear sugerencia para ajuste de precio
                suggestion_id = self.suggest_with_confidence(
                    tenant_id=tenant_id,
                    suggestion_type="price_adjustment",
                    description=f"Ajuste de precio sugerido para {product.name}",
                    confidence=llm_analysis.get("confidence", 0.5),
                    data={
                        "product_id": product_id,
                        "client_id": client_id,
                        "current_price": pricing_result["final_price"],
                        "suggested_price": llm_analysis["suggested_price"],
                        "reasoning": llm_analysis["reasoning"],
                        "context": context
                    }
                )
                
                pricing_result["llm_suggestion"] = {
                    "suggested_price": llm_analysis["suggested_price"],
                    "reasoning": llm_analysis["reasoning"],
                    "suggestion_id": suggestion_id
                }
        
        return pricing_result
    
    def _apply_pricing_rules(self, product: Product, client: Optional[Client], 
                           list_price: float, quantity: int, 
                           context: Dict[str, Any]) -> Dict[str, Any]:
        """Aplica reglas de pricing business"""
        
        final_price = list_price
        discount_applied = 0.0
        discount_reason = ""
        pricing_rule = "list_price"
        
        # 1. Cliente específico overrides
        if client:
            for override in product.pricing.overrides:
                if override.get("client_id") == client.client_id:
                    override_price = override.get("MXN", list_price)
                    if override_price < list_price:
                        discount_applied = list_price - override_price
                        final_price = override_price
                        discount_reason = "Precio especial cliente"
                        pricing_rule = "client_override"
                    break
        
        # 2. Descuentos por etiquetas de cliente
        if client and "vip" in client.tags:
            vip_discount = list_price * 0.05  # 5% VIP
            if vip_discount > discount_applied:
                discount_applied = vip_discount
                final_price = list_price - vip_discount
                discount_reason = "Descuento VIP 5%"
                pricing_rule = "vip_discount"
        
        # 3. Descuentos por volumen
        if quantity >= 10:
            volume_discount = list_price * 0.03  # 3% por volumen
            if volume_discount > discount_applied:
                discount_applied = volume_discount
                final_price = list_price - volume_discount
                discount_reason = f"Descuento por volumen ({quantity} unidades)"
                pricing_rule = "volume_discount"
        
        # 4. Descuentos por categoría (ejemplo: construcción)
        if client and "construccion" in client.tags:
            if "construction" in product.attributes.get("category", "").lower():
                construction_discount = list_price * 0.04  # 4% construcción
                if construction_discount > discount_applied:
                    discount_applied = construction_discount
                    final_price = list_price - construction_discount
                    discount_reason = "Descuento sector construcción"
                    pricing_rule = "category_discount"
        
        # 5. Descuentos por temporada/promoción
        if context.get("promotion_code"):
            promo_discount = list_price * 0.10  # 10% promocional
            if promo_discount > discount_applied:
                discount_applied = promo_discount
                final_price = list_price - promo_discount
                discount_reason = f"Promoción {context['promotion_code']}"
                pricing_rule = "promotion"
        
        # Calcular quantity breaks
        quantity_breaks = self._calculate_quantity_breaks(list_price, quantity)
        
        return {
            "final_price": round(final_price, 2),
            "list_price": list_price,
            "discount_applied": round(discount_applied, 2),
            "discount_percentage": round((discount_applied / list_price) * 100, 1) if list_price > 0 else 0,
            "discount_reason": discount_reason,
            "pricing_rule": pricing_rule,
            "quantity": quantity,
            "quantity_breaks": quantity_breaks,
            "valid_until": (datetime.now() + timedelta(days=7)).isoformat()
        }
    
    def _calculate_quantity_breaks(self, list_price: float, current_qty: int) -> Dict[str, Any]:
        """Calcula descuentos por cantidad"""
        
        breaks = {
            "10+": {"discount_pct": 3, "price": list_price * 0.97, "savings": list_price * 0.03},
            "25+": {"discount_pct": 5, "price": list_price * 0.95, "savings": list_price * 0.05},
            "50+": {"discount_pct": 8, "price": list_price * 0.92, "savings": list_price * 0.08},
            "100+": {"discount_pct": 12, "price": list_price * 0.88, "savings": list_price * 0.12}
        }
        
        # Marcar el break actual
        for break_qty, break_info in breaks.items():
            min_qty = int(break_qty.replace("+", ""))
            break_info["is_current"] = current_qty >= min_qty
            break_info["units_to_unlock"] = max(0, min_qty - current_qty)
        
        return breaks
    
    def _analyze_pricing_with_llm(self, product: Product, client: Optional[Client],
                                 current_pricing: Dict[str, Any], 
                                 context: Dict[str, Any]) -> Dict[str, Any]:
        """Analiza pricing con LLM para casos especiales"""
        
        client_info = f"""
        Cliente: {client.name if client else 'Anónimo'}
        Tags: {client.tags if client else []}
        """ if client else "Cliente no identificado"
        
        prompt = f"""
        Analiza esta situación de pricing y sugiere ajustes si es necesario:
        
        PRODUCTO:
        {product.name} - SKU: {product.sku}
        Precio lista: ${current_pricing['list_price']:.2f}
        Precio actual: ${current_pricing['final_price']:.2f}
        Descuento aplicado: {current_pricing['discount_reason']}
        
        {client_info}
        
        CONTEXTO ESPECIAL:
        {json.dumps(context, ensure_ascii=False)}
        
        PREGUNTA: ¿Debería ajustarse el precio considerando el contexto?
        
        Responde en JSON:
        {{
            "should_adjust": true/false,
            "suggested_price": 125.50,
            "confidence": 0.85,
            "reasoning": "explicación del ajuste sugerido",
            "risk_level": "low|medium|high"
        }}
        """
        
        llm_response = self._call_llm(prompt, max_tokens=400)
        
        try:
            analysis = json.loads(llm_response)
            return {
                "suggested_adjustment": analysis.get("should_adjust", False),
                "suggested_price": analysis.get("suggested_price", current_pricing["final_price"]),
                "confidence": analysis.get("confidence", 0.5),
                "reasoning": analysis.get("reasoning", "Análisis LLM"),
                "risk_level": analysis.get("risk_level", "medium")
            }
        except:
            return {
                "suggested_adjustment": False,
                "confidence": 0.3,
                "reasoning": "Error en análisis LLM"
            }

class QuoteBuilderAgent(BaseOrkestaAgent):
    """
    Agente que construye cotizaciones desde conversaciones de chat.
    Extrae items, cantidades y genera cotizaciones completas.
    """
    
    def __init__(self):
        super().__init__("QuoteBuilder")
        self.price_resolver = PriceResolverAgent()
    
    def build_quote_from_chat(self, tenant_id: str, chat_messages: List[Dict[str, str]],
                             client_id: str) -> Dict[str, Any]:
        """
        Construye cotización desde mensajes de chat.
        
        Args:
            chat_messages: [
                {"role": "user", "content": "Necesito 20 tubos PVC de 3/4"},
                {"role": "assistant", "content": "Encontré tubos PVC..."},
                {"role": "user", "content": "También 5 codos de 90 grados"}
            ]
        """
        
        ctx = self.get_context(tenant_id)
        
        # Extraer productos solicitados con LLM
        extraction_result = self._extract_products_from_chat(chat_messages)
        
        if not extraction_result.get("products"):
            return {"error": "No se pudieron extraer productos de la conversación"}
        
        # Crear orden nueva
        order_id = ctx.create_order(client_id, agent_name=self.name)
        
        quote_items = []
        total_amount = 0.0
        
        for item_request in extraction_result["products"]:
            # Buscar producto en catálogo
            search_results = ctx.find_products(item_request["description"], limit=3)
            
            if not search_results:
                # Producto no encontrado - crear sugerencia
                self.suggest_with_confidence(
                    tenant_id=tenant_id,
                    suggestion_type="missing_product",
                    description=f"Producto solicitado no encontrado: {item_request['description']}",
                    confidence=0.9,
                    data=item_request
                )
                continue
            
            # Usar el primer resultado (más relevante)
            product = search_results[0]
            quantity = item_request.get("quantity", 1)
            
            # Resolver precio
            pricing = self.price_resolver.resolve_price(
                tenant_id=tenant_id,
                product_id=product.product_id,
                client_id=client_id,
                quantity=quantity,
                context={"source": "chat_quote"}
            )
            
            if "error" in pricing:
                continue
            
            # Agregar item a la orden
            success = ctx.add_item_to_order(
                order_id=order_id,
                product_id=product.product_id,
                quantity=quantity,
                client_id=client_id
            )
            
            if success:
                quote_items.append({
                    "product": {
                        "id": product.product_id,
                        "sku": product.sku,
                        "name": product.name,
                        "unit": product.unit
                    },
                    "quantity": quantity,
                    "unit_price": pricing["final_price"],
                    "list_price": pricing["list_price"],
                    "discount": pricing["discount_applied"],
                    "total_price": pricing["final_price"] * quantity,
                    "pricing_rule": pricing["pricing_rule"]
                })
                
                total_amount += pricing["final_price"] * quantity
        
        # Obtener orden actualizada
        order = ctx.orders[order_id]
        
        # Analizar cotización con LLM para completeness
        analysis = self._analyze_quote_completeness(chat_messages, quote_items)
        
        quote_result = {
            "order_id": order_id,
            "items": quote_items,
            "subtotal": order.subtotal,
            "tax_amount": order.tax_amount,
            "total_amount": order.total_amount,
            "currency": "MXN",
            "valid_until": (datetime.now() + timedelta(days=7)).isoformat(),
            "extraction_confidence": extraction_result.get("confidence", 0.0),
            "analysis": analysis,
            "chat_summary": extraction_result.get("summary", ""),
            "missing_items": analysis.get("missing_items", []),
            "recommendations": analysis.get("recommendations", [])
        }
        
        # Actualizar estado de orden
        ctx.update_order_status(order_id, OrderStatus.QUOTED)
        
        return quote_result
    
    def _extract_products_from_chat(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """Extrae productos solicitados desde mensajes de chat"""
        
        # Concatenar mensajes del usuario
        user_messages = [msg["content"] for msg in messages if msg["role"] == "user"]
        conversation_text = "\\n".join(user_messages)
        
        prompt = f"""
        Extrae los productos solicitados de esta conversación de chat:
        
        CONVERSACIÓN:
        {conversation_text}
        
        Identifica cada producto mencionado con su cantidad.
        
        Responde en JSON:
        {{
            "products": [
                {{
                    "description": "tubos PVC 3/4 pulgada",
                    "quantity": 20,
                    "unit": "pieza",
                    "specifications": ["3/4 pulgada", "PVC"],
                    "confidence": 0.95
                }}
            ],
            "confidence": 0.90,
            "summary": "Cliente solicita materiales de plomería",
            "notes": ["Cliente mencionó urgencia", "Posible descuento por volumen"]
        }}
        """
        
        llm_response = self._call_llm(prompt, max_tokens=800)
        
        try:
            return json.loads(llm_response)
        except:
            # Fallback con regex simple
            return self._fallback_product_extraction(conversation_text)
    
    def _fallback_product_extraction(self, text: str) -> Dict[str, Any]:
        """Extracción de productos con regex si LLM falla"""
        
        # Patrones simples
        patterns = [
            r"(\d+)\s+(.*?)(tubo|cable|cemento|varilla|pintura)",
            r"necesito\s+(\d*)\s*(.*)",
            r"quiero\s+(\d*)\s*(.*)"
        ]
        
        products = []
        
        for pattern in patterns:
            matches = re.finditer(pattern, text.lower(), re.IGNORECASE)
            for match in matches:
                try:
                    quantity = int(match.group(1)) if match.group(1) else 1
                    description = match.group(2).strip()
                    
                    if len(description) > 3:  # Filtrar matches muy cortos
                        products.append({
                            "description": description,
                            "quantity": quantity,
                            "unit": "pieza",
                            "specifications": [],
                            "confidence": 0.6
                        })
                except:
                    continue
        
        return {
            "products": products[:5],  # Máximo 5 productos
            "confidence": 0.6,
            "summary": "Extracción automática por patrones",
            "notes": ["Revisar productos extraídos"]
        }
    
    def _analyze_quote_completeness(self, messages: List[Dict[str, str]], 
                                   quote_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analiza si la cotización está completa vs la conversación"""
        
        conversation_text = "\\n".join([msg["content"] for msg in messages])
        items_summary = "\\n".join([f"- {item['product']['name']} x{item['quantity']}" for item in quote_items])
        
        prompt = f"""
        Analiza si esta cotización cubre todos los productos mencionados en la conversación:
        
        CONVERSACIÓN ORIGINAL:
        {conversation_text}
        
        ITEMS EN COTIZACIÓN:
        {items_summary}
        
        Responde en JSON:
        {{
            "completeness_score": 0.85,
            "missing_items": ["item que falta"],
            "recommendations": ["sugerir productos complementarios"],
            "concerns": ["productos mencionados pero no cotizados"],
            "confidence": 0.90
        }}
        """
        
        llm_response = self._call_llm(prompt, max_tokens=600)
        
        try:
            return json.loads(llm_response)
        except:
            return {
                "completeness_score": 0.8,
                "missing_items": [],
                "recommendations": ["Revisar cotización manualmente"],
                "concerns": [],
                "confidence": 0.5
            }

# ==================== ORCHESTRATOR PRINCIPAL ====================

class OrkestaAgentOrchestrator:
    """Orquestador que coordina todos los agentes inteligentes"""
    
    def __init__(self):
        self.agents = {
            "catalog_mapper": CatalogMapperAgent(),
            "alias_normalizer": AliasNormalizerAgent(),
            "price_resolver": PriceResolverAgent(),
            "quote_builder": QuoteBuilderAgent()
        }
    
    def process_catalog_import(self, tenant_id: str, file_data: Dict[str, Any]) -> Dict[str, Any]:
        """Flujo completo de importación de catálogo"""
        
        results = {}
        
        # 1. Mapear columnas
        mapping_result = self.agents["catalog_mapper"].analyze_import_structure(tenant_id, file_data)
        results["mapping"] = mapping_result
        
        # 2. Si el mapeo es exitoso, detectar duplicados
        if mapping_result.get("confidence", 0) > 0.7:
            duplicates = self.agents["alias_normalizer"].detect_duplicates(tenant_id)
            results["duplicates"] = duplicates
            
            # 3. Normalizar unidades
            normalization = self.agents["alias_normalizer"].normalize_units(tenant_id)
            results["normalization"] = normalization
        
        return results
    
    def process_quote_request(self, tenant_id: str, chat_messages: List[Dict[str, str]], 
                            client_id: str) -> Dict[str, Any]:
        """Flujo completo de generación de cotización"""
        
        # Construir cotización
        quote = self.agents["quote_builder"].build_quote_from_chat(
            tenant_id, chat_messages, client_id
        )
        
        return quote
    
    def get_pending_suggestions(self, tenant_id: str) -> List[Dict[str, Any]]:
        """Obtiene todas las sugerencias pendientes de aprobación"""
        
        ctx = get_shared_context(tenant_id)
        suggestions = ctx.get_pending_suggestions()
        
        return [
            {
                "suggestion_id": s.suggestion_id,
                "agent_name": s.agent_name,
                "type": s.suggestion_type,
                "description": s.description,
                "confidence": s.confidence,
                "data": s.data,
                "created_at": s.created_at.isoformat()
            }
            for s in suggestions
        ]

# Instancia global
orchestrator = OrkestaAgentOrchestrator()

if __name__ == "__main__":
    # Ejemplo de uso de los agentes inteligentes
    print("🧠 Orkesta Smart Agents - Test de Coreografía")
    print("=" * 60)
    
    # Crear contexto demo
    tenant_id = "demo-smart-agents"
    ctx = get_shared_context(tenant_id)
    
    # Configurar productos demo
    from orkesta_shared_context import Product, ProductPricing, Client
    
    # Productos con posibles duplicados
    products = [
        Product(
            product_id="p_tubo_001",
            sku="TUB-PVC-19-6M",
            aliases=["tubo pvc 3/4", "tubo 19mm", "pvc 3/4 pulgada"],
            name="Tubo PVC 19mm (3/4) x 6m",
            brand="AquaFlow",
            unit="pieza",
            attributes={"diametro": "19mm", "longitud": "6m", "material": "PVC"},
            pricing=ProductPricing(
                lists={"lista_base": {"MXN": 85.00, "iva_pct": 16}},
                overrides=[]
            ),
            stock={"default": 150, "reorder_point": 30}
        ),
        Product(
            product_id="p_tubo_002",
            sku="TUBO-PVC-3/4-6MTS",
            aliases=["tubo pvc 3/4 pulgada", "tubo 19 mm", "pvc tube 3/4"],
            name="Tubo de PVC 3/4 pulgada 6 metros",
            brand="FlowMaster",
            unit="pza",
            attributes={"diametro": "3/4 pulgada", "longitud": "6 metros", "material": "PVC"},
            pricing=ProductPricing(
                lists={"lista_base": {"MXN": 82.00, "iva_pct": 16}},
                overrides=[]
            ),
            stock={"default": 200, "reorder_point": 40}
        )
    ]
    
    for product in products:
        ctx.add_product(product)
    
    # Cliente demo
    client = Client(
        client_id="c_demo_vip",
        name="Constructora Demo VIP",
        phones=["+5255123456789"],
        tags=["vip", "construccion"]
    )
    ctx.add_client(client)
    
    print(f"✅ Contexto demo creado: {len(ctx.catalog['products'])} productos, {len(ctx.clients)} clientes")
    
    # Test 1: Detectar duplicados
    print("\\n🔍 Detectando productos duplicados...")
    duplicates = orchestrator.agents["alias_normalizer"].detect_duplicates(tenant_id)
    
    if duplicates:
        for dup_group in duplicates:
            print(f"   📦 Posible duplicado: {dup_group['primary_product'].name}")
            print(f"      Similares: {len(dup_group['duplicates'])}")
            print(f"      Confianza: {dup_group['confidence']:.2f}")
    else:
        print("   ✅ No se detectaron duplicados")
    
    # Test 2: Resolver precios
    print("\\n💰 Resolviendo precios...")
    for product in products:
        pricing = orchestrator.agents["price_resolver"].resolve_price(
            tenant_id=tenant_id,
            product_id=product.product_id,
            client_id=client.client_id,
            quantity=15  # Cantidad para descuento por volumen
        )
        
        print(f"   {product.name}:")
        print(f"      Lista: ${pricing['list_price']:.2f}")
        print(f"      Final: ${pricing['final_price']:.2f}")
        print(f"      Descuento: {pricing['discount_reason']}")
    
    # Test 3: Construir cotización desde chat
    print("\\n💬 Construyendo cotización desde chat...")
    chat_messages = [
        {"role": "user", "content": "Hola, necesito cotización"},
        {"role": "assistant", "content": "¡Hola! Con gusto te ayudo. ¿Qué productos necesitas?"},
        {"role": "user", "content": "Necesito 25 tubos PVC de 3/4 pulgada para una obra"},
        {"role": "assistant", "content": "Perfecto, tengo tubos PVC disponibles"},
        {"role": "user", "content": "También me harían falta 10 codos de 90 grados"},
        {"role": "user", "content": "¿Hay descuento por la cantidad?"}
    ]
    
    quote = orchestrator.agents["quote_builder"].build_quote_from_chat(
        tenant_id=tenant_id,
        chat_messages=chat_messages,
        client_id=client.client_id
    )
    
    if "error" not in quote:
        print(f"   ✅ Cotización generada: {len(quote['items'])} items")
        print(f"      Total: ${quote['total_amount']:.2f}")
        print(f"      Orden ID: {quote['order_id']}")
    else:
        print(f"   ❌ Error: {quote['error']}")
    
    # Test 4: Sugerencias pendientes
    print("\\n📋 Sugerencias de agentes...")
    suggestions = orchestrator.get_pending_suggestions(tenant_id)
    
    if suggestions:
        for suggestion in suggestions:
            print(f"   🤖 {suggestion['agent_name']}: {suggestion['description']}")
            print(f"      Tipo: {suggestion['type']}, Confianza: {suggestion['confidence']:.2f}")
    else:
        print("   ✅ No hay sugerencias pendientes")
    
    print("\\n" + "=" * 60)
    print("🎯 Test de agentes inteligentes completado")
    print("💡 Los agentes colaboran usando el contexto compartido")
    print("=" * 60)