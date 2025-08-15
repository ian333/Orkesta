"""
💸 Transfer Manager - Modo Separate de Stripe Connect
===================================================

Maneja transfers manuales para modo Separate.
Soporte para multi-split y transfers complejos.
"""

import stripe
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import logging

from .types import Transfer, ChargesMode, ConnectAccount
from .connect import connect_manager

logger = logging.getLogger(__name__)

class TransferManager:
    """Manager para transfers en modo Separate"""
    
    def __init__(self):
        stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
        if not stripe.api_key:
            raise ValueError("STRIPE_SECRET_KEY not found in environment")
        
        # Storage de transfers (en prod usar DB)
        self.transfers: Dict[str, Transfer] = {}
    
    def create_transfer(self, amount: int, destination_account: str,
                       source_transaction: str = None,
                       currency: str = "MXN",
                       description: str = "",
                       metadata: Dict[str, str] = None) -> Transfer:
        """
        Crea un transfer a una cuenta Connect.
        
        Args:
            amount: Monto en centavos
            destination_account: ID de cuenta Connect destino
            source_transaction: ID del charge original (opcional)
            currency: Moneda (MXN por defecto)
            description: Descripción del transfer
            metadata: Metadata adicional
        """
        
        try:
            # Crear transfer en Stripe
            stripe_transfer = stripe.Transfer.create(
                amount=amount,
                currency=currency.lower(),
                destination=destination_account,
                source_transaction=source_transaction,
                description=description,
                metadata=metadata or {}
            )
            
            # Crear registro local
            transfer = Transfer(
                transfer_id=stripe_transfer.id,
                tenant_id=metadata.get("tenant_id", "unknown") if metadata else "unknown",
                connect_account_id=destination_account,
                amount=amount,
                currency=currency,
                source_transaction=source_transaction,
                description=description,
                metadata=metadata or {},
                status="pending"
            )
            
            # Guardar en storage
            self.transfers[stripe_transfer.id] = transfer
            
            logger.info(f"Created transfer {stripe_transfer.id}: {amount/100} {currency} to {destination_account}")
            
            return transfer
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to create transfer: {e}")
            raise Exception(f"Stripe transfer error: {e.user_message}")
    
    def create_multi_split_transfer(self, source_charge_id: str, 
                                  splits: List[Dict[str, Any]],
                                  tenant_id: str) -> List[Transfer]:
        """
        Crea múltiples transfers desde un charge (multi-split).
        
        Args:
            source_charge_id: ID del charge original
            splits: Lista de splits: [
                {
                    "account_id": "acct_vendor1",
                    "amount_pct": 70,  # 70% del total
                    "description": "Vendor payment",
                    "metadata": {"vendor_id": "v1"}
                },
                {
                    "account_id": "acct_delivery",
                    "amount_pct": 20,  # 20% del total
                    "description": "Delivery fee"
                }
                # 10% restante queda en plataforma
            ]
            tenant_id: ID del tenant
        
        Returns:
            Lista de transfers creados
        """
        
        try:
            # Obtener información del charge
            charge = stripe.Charge.retrieve(source_charge_id)
            total_amount = charge.amount  # En centavos
            
            if charge.refunded:
                raise ValueError(f"Cannot split refunded charge: {source_charge_id}")
            
            # Validar splits
            total_pct = sum(split.get("amount_pct", 0) for split in splits)
            if total_pct > 100:
                raise ValueError(f"Split percentages exceed 100%: {total_pct}%")
            
            transfers_created = []
            
            for split in splits:
                account_id = split["account_id"]
                amount_pct = split["amount_pct"]
                
                # Calcular monto exacto
                split_amount = int((total_amount * amount_pct) / 100)
                
                if split_amount <= 0:
                    logger.warning(f"Skipping zero amount split for {account_id}")
                    continue
                
                # Validar que la cuenta existe
                account = connect_manager.get_account(account_id)
                if not account:
                    logger.error(f"Connect account not found: {account_id}")
                    continue
                
                # Crear transfer
                transfer = self.create_transfer(
                    amount=split_amount,
                    destination_account=account_id,
                    source_transaction=source_charge_id,
                    description=split.get("description", f"Split payment {amount_pct}%"),
                    metadata={
                        "tenant_id": tenant_id,
                        "split_type": "multi_split",
                        "original_charge": source_charge_id,
                        "split_percentage": str(amount_pct),
                        **split.get("metadata", {})
                    }
                )
                
                transfers_created.append(transfer)
            
            # Log del resumen
            total_transferred = sum(t.amount for t in transfers_created)
            platform_retained = total_amount - total_transferred
            
            logger.info(f"Multi-split completed: {len(transfers_created)} transfers, "
                       f"${total_transferred/100:.2f} transferred, "
                       f"${platform_retained/100:.2f} retained")
            
            return transfers_created
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to create multi-split: {e}")
            raise Exception(f"Stripe error: {e.user_message}")
    
    def reverse_transfer(self, transfer_id: str, amount: int = None,
                        reason: str = "requested_by_customer") -> Dict[str, Any]:
        """
        Reversa un transfer (total o parcial).
        
        Args:
            transfer_id: ID del transfer a reversar
            amount: Monto a reversar en centavos (None = total)
            reason: Razón de la reversa
        """
        
        try:
            # Crear reversal en Stripe
            reversal = stripe.Transfer.create_reversal(
                transfer_id,
                amount=amount,
                description=f"Transfer reversal: {reason}",
                metadata={
                    "reversal_reason": reason,
                    "reversed_at": datetime.now().isoformat()
                }
            )
            
            # Actualizar estado local
            if transfer_id in self.transfers:
                transfer = self.transfers[transfer_id]
                
                if amount is None or amount >= transfer.amount:
                    transfer.status = "reversed"
                else:
                    transfer.status = "partially_reversed"
            
            logger.info(f"Transfer {transfer_id} reversed: ${(amount or 0)/100:.2f}")
            
            return {
                "reversal_id": reversal.id,
                "amount_reversed": reversal.amount,
                "status": "succeeded",
                "fee": reversal.fee,
                "created": reversal.created
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to reverse transfer: {e}")
            raise Exception(f"Stripe reversal error: {e.user_message}")
    
    def get_transfer_status(self, transfer_id: str) -> Dict[str, Any]:
        """Obtiene estado actual de un transfer desde Stripe"""
        
        try:
            stripe_transfer = stripe.Transfer.retrieve(transfer_id)
            
            # Actualizar estado local
            if transfer_id in self.transfers:
                local_transfer = self.transfers[transfer_id]
                local_transfer.status = stripe_transfer.get("status", "unknown")
            
            return {
                "id": stripe_transfer.id,
                "amount": stripe_transfer.amount,
                "currency": stripe_transfer.currency,
                "destination": stripe_transfer.destination,
                "created": stripe_transfer.created,
                "description": stripe_transfer.description,
                "metadata": stripe_transfer.metadata,
                "reversals": [
                    {
                        "id": rev.id,
                        "amount": rev.amount,
                        "created": rev.created
                    }
                    for rev in stripe_transfer.reversals.data
                ],
                "source_transaction": stripe_transfer.source_transaction,
                "transfer_group": stripe_transfer.transfer_group
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to get transfer status: {e}")
            return {"error": str(e)}
    
    def create_transfer_group(self, group_id: str, transfers: List[Dict[str, Any]],
                            tenant_id: str) -> List[Transfer]:
        """
        Crea un grupo de transfers relacionados.
        Útil para tracking de transfers que pertenecen al mismo pedido.
        
        Args:
            group_id: ID único del grupo
            transfers: Lista de transfers a crear
            tenant_id: ID del tenant
        """
        
        created_transfers = []
        
        for transfer_data in transfers:
            try:
                # Agregar transfer_group a metadata
                metadata = transfer_data.get("metadata", {})
                metadata.update({
                    "tenant_id": tenant_id,
                    "transfer_group": group_id
                })
                
                transfer = self.create_transfer(
                    amount=transfer_data["amount"],
                    destination_account=transfer_data["destination_account"],
                    source_transaction=transfer_data.get("source_transaction"),
                    description=transfer_data.get("description", f"Group transfer {group_id}"),
                    metadata=metadata
                )
                
                created_transfers.append(transfer)
                
            except Exception as e:
                logger.error(f"Failed to create transfer in group {group_id}: {e}")
                # Continuar con los siguientes transfers
        
        logger.info(f"Created transfer group {group_id}: {len(created_transfers)} transfers")
        
        return created_transfers
    
    def calculate_optimal_splits(self, total_amount: int, 
                               participants: List[Dict[str, Any]],
                               platform_fee_pct: float = 5.0) -> List[Dict[str, Any]]:
        """
        Calcula splits óptimos basado en reglas de negocio.
        
        Args:
            total_amount: Monto total en centavos
            participants: Lista de participantes con sus reglas
            platform_fee_pct: Porcentaje que retiene la plataforma
        
        Returns:
            Lista de splits optimizados
        """
        
        # Reservar fee de plataforma
        platform_fee = int(total_amount * platform_fee_pct / 100)
        distributable_amount = total_amount - platform_fee
        
        # Calcular weights totales
        total_weight = sum(p.get("weight", 1) for p in participants)
        
        splits = []
        remaining_amount = distributable_amount
        
        for i, participant in enumerate(participants):
            account_id = participant["account_id"]
            weight = participant.get("weight", 1)
            min_amount = participant.get("min_amount", 0)
            max_amount = participant.get("max_amount", None)
            
            # Calcular monto proporcional
            if i == len(participants) - 1:
                # Último participante recibe el restante
                split_amount = remaining_amount
            else:
                split_amount = int(distributable_amount * weight / total_weight)
            
            # Aplicar límites
            if split_amount < min_amount:
                split_amount = min_amount
            if max_amount and split_amount > max_amount:
                split_amount = max_amount
            
            # Verificar que no excedamos el disponible
            if split_amount > remaining_amount:
                split_amount = remaining_amount
            
            if split_amount > 0:
                split_pct = (split_amount / total_amount) * 100
                
                splits.append({
                    "account_id": account_id,
                    "amount": split_amount,
                    "amount_pct": split_pct,
                    "description": participant.get("description", f"Payment to {account_id}"),
                    "metadata": participant.get("metadata", {})
                })
                
                remaining_amount -= split_amount
        
        return splits
    
    def list_transfers_by_tenant(self, tenant_id: str, 
                               status: str = None,
                               limit: int = 50) -> List[Transfer]:
        """Lista transfers de un tenant con filtros opcionales"""
        
        transfers = [
            t for t in self.transfers.values()
            if t.tenant_id == tenant_id
        ]
        
        if status:
            transfers = [t for t in transfers if t.status == status]
        
        # Ordenar por fecha de creación (más reciente primero)
        transfers.sort(key=lambda x: x.created_at, reverse=True)
        
        return transfers[:limit]
    
    def get_transfer_summary(self, tenant_id: str, 
                           days: int = 30) -> Dict[str, Any]:
        """Genera resumen de transfers para un tenant"""
        
        since = datetime.now() - timedelta(days=days)
        
        tenant_transfers = [
            t for t in self.transfers.values()
            if t.tenant_id == tenant_id and t.created_at > since
        ]
        
        if not tenant_transfers:
            return {
                "tenant_id": tenant_id,
                "period_days": days,
                "total_transfers": 0,
                "total_amount": 0,
                "by_status": {},
                "by_account": {}
            }
        
        # Calcular métricas
        total_amount = sum(t.amount for t in tenant_transfers)
        
        # Agrupar por estado
        by_status = {}
        for transfer in tenant_transfers:
            status = transfer.status
            if status not in by_status:
                by_status[status] = {"count": 0, "amount": 0}
            by_status[status]["count"] += 1
            by_status[status]["amount"] += transfer.amount
        
        # Agrupar por cuenta destino
        by_account = {}
        for transfer in tenant_transfers:
            account_id = transfer.connect_account_id
            if account_id not in by_account:
                by_account[account_id] = {"count": 0, "amount": 0}
            by_account[account_id]["count"] += 1
            by_account[account_id]["amount"] += transfer.amount
        
        return {
            "tenant_id": tenant_id,
            "period_days": days,
            "total_transfers": len(tenant_transfers),
            "total_amount": total_amount,
            "average_transfer": total_amount / len(tenant_transfers),
            "by_status": by_status,
            "by_account": by_account,
            "largest_transfer": max(t.amount for t in tenant_transfers),
            "smallest_transfer": min(t.amount for t in tenant_transfers)
        }

# Instancia global
transfer_manager = TransferManager()

if __name__ == "__main__":
    # Ejemplo de uso del Transfer Manager
    print("💸 Transfer Manager - Test Multi-Split")
    print("=" * 50)
    
    manager = TransferManager()
    
    # Simular participantes para multi-split
    participants = [
        {
            "account_id": "acct_vendor_main",
            "weight": 70,  # 70% del split
            "min_amount": 5000,  # Mínimo $50
            "description": "Main vendor payment",
            "metadata": {"vendor_type": "primary", "vendor_id": "v001"}
        },
        {
            "account_id": "acct_delivery_service", 
            "weight": 20,  # 20% del split
            "min_amount": 1000,  # Mínimo $10
            "max_amount": 5000,  # Máximo $50
            "description": "Delivery service fee",
            "metadata": {"service_type": "delivery"}
        },
        {
            "account_id": "acct_insurance_provider",
            "weight": 10,  # 10% del split
            "description": "Insurance coverage",
            "metadata": {"service_type": "insurance"}
        }
    ]
    
    # Calcular splits óptimos para $1000
    total_amount = 100000  # $1000 en centavos
    
    try:
        splits = manager.calculate_optimal_splits(
            total_amount, 
            participants, 
            platform_fee_pct=3.0  # 3% para la plataforma
        )
        
        print(f"\\n💰 Splits para ${total_amount/100:.2f}:")
        
        platform_retained = total_amount
        
        for split in splits:
            print(f"\\n  {split['account_id']}:")
            print(f"    Monto: ${split['amount']/100:.2f} ({split['amount_pct']:.1f}%)")
            print(f"    Descripción: {split['description']}")
            platform_retained -= split['amount']
        
        print(f"\\n  Plataforma retiene: ${platform_retained/100:.2f} ({(platform_retained/total_amount)*100:.1f}%)")
        
        # Simular creación de multi-split
        print(f"\\n🔄 Simulando multi-split...")
        
        # En un caso real, esto crearía los transfers en Stripe
        print(f"   {len(splits)} transfers serían creados")
        print(f"   Total distribuido: ${sum(s['amount'] for s in splits)/100:.2f}")
        
        print("\\n✅ Test de transfers completado")
        print("💡 Para usar en producción, configura las cuentas Connect reales")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("💡 Configura STRIPE_SECRET_KEY para tests reales")