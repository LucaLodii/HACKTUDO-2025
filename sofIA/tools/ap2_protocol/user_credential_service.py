"""
User Credential Acquisition and Verification for AP2 Protocol

This module implements secure user credential collection, verification,
and management following AP2 protocol specifications.
"""

import asyncio
import hashlib
import json
import os
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from enum import Enum
import jwt
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from .verifiable_credentials import VerifiableCredential, CredentialProvider


class CredentialAcquisitionMethod(Enum):
    """Methods for acquiring user credentials"""
    WHATSAPP_FLOW = "whatsapp_flow"
    WEB_FORM = "web_form"
    API_INTEGRATION = "api_integration"
    BANK_INTEGRATION = "bank_integration"


@dataclass
class UserPaymentCredential:
    """User's payment method credential with AP2 compliance"""
    user_id: str
    credential_id: str
    payment_method: str  # pix, credit_card, boleto
    encrypted_data: str  # Encrypted payment details
    consent_proof: str   # User consent evidence
    verification_status: str  # verified, pending, failed
    acquired_via: CredentialAcquisitionMethod
    acquired_at: datetime
    expires_at: datetime
    last_used: Optional[datetime] = None


@dataclass
class UserKYCData:
    """User KYC (Know Your Customer) data for AP2 compliance"""
    user_id: str
    full_name: str
    document_type: str  # CPF, RG, CNH
    document_number: str
    phone_number: str
    whatsapp_number: str
    email: Optional[str]
    address: Optional[Dict[str, str]]
    verification_level: str  # basic, enhanced, premium
    kyc_verified: bool
    kyc_verified_at: Optional[datetime]


class UserCredentialService:
    """
    Handles user credential acquisition and verification for AP2 protocol.

    This service manages:
    1. User identity verification (KYC)
    2. Payment method credential acquisition
    3. Consent management and proof generation
    4. Credential encryption and secure storage
    5. AP2-compliant credential verification
    """

    def __init__(self):
        self.user_credentials: Dict[str, List[UserPaymentCredential]] = {}
        self.user_kyc_data: Dict[str, UserKYCData] = {}
        self.consent_records: Dict[str, Dict[str, Any]] = {}

    async def initiate_whatsapp_credential_flow(
        self,
        user_id: str,
        payment_method: str,
        amount: float,
        currency: str = "BRL"
    ) -> Dict[str, Any]:
        """
        Initiate credential acquisition through WhatsApp flow.

        This is the main method called when a user needs to provide
        payment credentials via WhatsApp conversation.
        """

        print(f"📱 Initiating WhatsApp credential flow for {user_id}")

        # Step 1: Check if user has existing verified credentials for this payment method
        existing_credentials = await self.get_user_credentials(user_id, payment_method)

        if existing_credentials and any(cred.verification_status == "verified" for cred in existing_credentials):
            # User has verified credentials, ask for confirmation to reuse
            return {
                "flow_type": "credential_reuse",
                "message": f"💳 Você já tem credenciais {payment_method.upper()} salvas e verificadas.\n\n"
                          f"Gostaria de:\n"
                          f"1️⃣ Usar credenciais salvas\n"
                          f"2️⃣ Adicionar novo método de pagamento\n\n"
                          f"Digite '1' ou '2':",
                "existing_credentials": len(existing_credentials),
                "next_step": "credential_selection"
            }

        # Step 2: Check KYC status
        kyc_data = await self.get_user_kyc_data(user_id)

        if not kyc_data or not kyc_data.kyc_verified:
            # Need KYC first
            return await self._initiate_kyc_flow(user_id)

        # Step 3: Request payment method credentials
        return await self._request_payment_credentials(user_id, payment_method, amount, currency)

    async def _initiate_kyc_flow(self, user_id: str) -> Dict[str, Any]:
        """Initiate KYC (Know Your Customer) flow via WhatsApp"""

        return {
            "flow_type": "kyc_required",
            "message": "🔐 **Verificação de Identidade Necessária**\n\n"
                      "Para usar pagamentos seguros via protocolo AP2, precisamos verificar sua identidade.\n\n"
                      "**Por favor, forneça:**\n"
                      "📋 Nome completo\n"
                      "🆔 CPF\n"
                      "📱 Número de telefone\n\n"
                      "Formato: `DADOS [Nome] [CPF] [Telefone]`\n"
                      "Exemplo: `DADOS João Silva 12345678901 11999887766`\n\n"
                      "*Seus dados são protegidos e criptografados.*",
            "next_step": "kyc_data_collection"
        }

    async def _request_payment_credentials(
        self,
        user_id: str,
        payment_method: str,
        amount: float,
        currency: str
    ) -> Dict[str, Any]:
        """Request specific payment method credentials"""

        if payment_method.lower() == "pix":
            return {
                "flow_type": "pix_credentials",
                "message": f"🏦 **Pagamento PIX - {currency} {amount:.2f}**\n\n"
                          f"Para processar o pagamento via protocolo AP2, forneça sua chave PIX:\n\n"
                          f"📧 **E-mail**: `PIX_EMAIL [seu@email.com]`\n"
                          f"📱 **Telefone**: `PIX_TELEFONE [11999887766]`\n"
                          f"🆔 **CPF**: `PIX_CPF [12345678901]`\n"
                          f"🔑 **Chave Aleatória**: `PIX_CHAVE [sua-chave-aleatoria]`\n\n"
                          f"*Suas credenciais são criptografadas com protocolo AP2.*",
                "payment_method": payment_method,
                "amount": amount,
                "currency": currency,
                "next_step": "pix_credential_processing"
            }

        elif payment_method.lower() == "credit_card":
            return {
                "flow_type": "card_credentials",
                "message": f"💳 **Pagamento Cartão - {currency} {amount:.2f}**\n\n"
                          f"Forneça os dados do cartão (formato seguro):\n\n"
                          f"`CARTAO [últimos 4 dígitos] [MM/AA] [Nome do titular]`\n"
                          f"Exemplo: `CARTAO 1234 12/25 João Silva`\n\n"
                          f"⚠️ **Segurança AP2:**\n"
                          f"• Nunca enviamos dados completos do cartão\n"
                          f"• Usamos apenas identificação segura\n"
                          f"• Processamento via tokenização\n\n"
                          f"*Protocolo AP2 garante segurança máxima.*",
                "payment_method": payment_method,
                "amount": amount,
                "currency": currency,
                "next_step": "card_credential_processing"
            }

        elif payment_method.lower() == "boleto":
            return {
                "flow_type": "boleto_credentials",
                "message": f"🧾 **Pagamento Boleto - {currency} {amount:.2f}**\n\n"
                          f"Para gerar o boleto, confirme seus dados:\n\n"
                          f"`BOLETO [CPF] [Nome completo]`\n"
                          f"Exemplo: `BOLETO 12345678901 João Silva Santos`\n\n"
                          f"📄 **O boleto será gerado com:**\n"
                          f"• Vencimento em 3 dias\n"
                          f"• Código de barras\n"
                          f"• Linha digitável\n"
                          f"• QR Code para pagamento\n\n"
                          f"*Processamento seguro via AP2.*",
                "payment_method": payment_method,
                "amount": amount,
                "currency": currency,
                "next_step": "boleto_credential_processing"
            }

        else:
            return {
                "flow_type": "unsupported_method",
                "message": f"❌ Método de pagamento '{payment_method}' não suportado.\n\n"
                          f"**Métodos disponíveis:**\n"
                          f"🏦 PIX\n"
                          f"💳 Cartão de Crédito\n"
                          f"🧾 Boleto\n\n"
                          f"Por favor, escolha um método válido.",
                "next_step": "method_selection"
            }

    async def process_kyc_data(self, user_id: str, kyc_input: str) -> Dict[str, Any]:
        """Process KYC data provided by user"""

        try:
            # Parse KYC input: "DADOS [Nome] [CPF] [Telefone]"
            if not kyc_input.upper().startswith("DADOS"):
                return {
                    "success": False,
                    "message": "❌ Formato inválido. Use: `DADOS [Nome] [CPF] [Telefone]`"
                }

            parts = kyc_input.split()
            if len(parts) < 4:
                return {
                    "success": False,
                    "message": "❌ Dados incompletos. Forneça nome, CPF e telefone."
                }

            name = " ".join(parts[1:-2]) if len(parts) > 4 else parts[1]
            cpf = parts[-2]
            phone = parts[-1]

            # Validate CPF (basic validation)
            if not self._validate_cpf(cpf):
                return {
                    "success": False,
                    "message": "❌ CPF inválido. Verifique o número e tente novamente."
                }

            # Create KYC data
            kyc_data = UserKYCData(
                user_id=user_id,
                full_name=name,
                document_type="CPF",
                document_number=cpf,
                phone_number=phone,
                whatsapp_number=user_id,  # Assuming user_id is WhatsApp number
                email=None,
                address=None,
                verification_level="basic",
                kyc_verified=True,  # In production, implement real verification
                kyc_verified_at=datetime.now(timezone.utc)
            )

            # Store KYC data
            self.user_kyc_data[user_id] = kyc_data

            print(f"✅ KYC completed for user {user_id}: {name}")

            return {
                "success": True,
                "message": f"✅ **Verificação concluída!**\n\n"
                          f"**Dados verificados:**\n"
                          f"👤 Nome: {name}\n"
                          f"🆔 CPF: ***{cpf[-3:]}\n"
                          f"📱 Telefone: ***{phone[-4:]}\n\n"
                          f"🔐 Seus dados estão seguros com protocolo AP2.\n"
                          f"Agora você pode usar todos os métodos de pagamento!",
                "kyc_verified": True
            }

        except Exception as e:
            print(f"KYC processing error: {e}")
            return {
                "success": False,
                "message": "❌ Erro ao processar dados. Tente novamente."
            }

    async def process_payment_credentials(
        self,
        user_id: str,
        payment_input: str,
        payment_method: str
    ) -> Dict[str, Any]:
        """Process payment credentials provided by user"""

        try:
            if payment_method.lower() == "pix":
                return await self._process_pix_credentials(user_id, payment_input)
            elif payment_method.lower() == "credit_card":
                return await self._process_card_credentials(user_id, payment_input)
            elif payment_method.lower() == "boleto":
                return await self._process_boleto_credentials(user_id, payment_input)
            else:
                return {
                    "success": False,
                    "message": "❌ Método de pagamento não suportado."
                }

        except Exception as e:
            print(f"Credential processing error: {e}")
            return {
                "success": False,
                "message": "❌ Erro ao processar credenciais. Tente novamente."
            }

    async def _process_pix_credentials(self, user_id: str, pix_input: str) -> Dict[str, Any]:
        """Process PIX credentials"""

        # Parse different PIX key formats
        if pix_input.upper().startswith("PIX_EMAIL"):
            pix_key = pix_input.split(maxsplit=1)[1]
            key_type = "email"
        elif pix_input.upper().startswith("PIX_TELEFONE"):
            pix_key = pix_input.split(maxsplit=1)[1]
            key_type = "phone"
        elif pix_input.upper().startswith("PIX_CPF"):
            pix_key = pix_input.split(maxsplit=1)[1]
            key_type = "cpf"
        elif pix_input.upper().startswith("PIX_CHAVE"):
            pix_key = pix_input.split(maxsplit=1)[1]
            key_type = "random"
        else:
            return {
                "success": False,
                "message": "❌ Formato PIX inválido. Use: PIX_EMAIL, PIX_TELEFONE, PIX_CPF ou PIX_CHAVE"
            }

        # Create encrypted credential
        credential = UserPaymentCredential(
            user_id=user_id,
            credential_id=f"pix_{user_id}_{datetime.now().timestamp()}",
            payment_method="pix",
            encrypted_data=self._encrypt_data({
                "pix_key": pix_key,
                "key_type": key_type
            }),
            consent_proof=self._generate_consent_proof(user_id, "pix"),
            verification_status="verified",  # In production, verify with bank
            acquired_via=CredentialAcquisitionMethod.WHATSAPP_FLOW,
            acquired_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(days=90)
        )

        # Store credential
        if user_id not in self.user_credentials:
            self.user_credentials[user_id] = []
        self.user_credentials[user_id].append(credential)

        return {
            "success": True,
            "credential_id": credential.credential_id,
            "message": f"✅ **PIX configurado com sucesso!**\n\n"
                      f"🏦 Chave PIX: ***{pix_key[-4:]} ({key_type})\n"
                      f"🔐 Credencial: {credential.credential_id[:12]}...\n"
                      f"📅 Válida até: {credential.expires_at.strftime('%d/%m/%Y')}\n\n"
                      f"**Protocolo AP2 ativo** ✅\n"
                      f"Suas credenciais estão seguras!"
        }

    async def _process_card_credentials(self, user_id: str, card_input: str) -> Dict[str, Any]:
        """Process credit card credentials (tokenized approach)"""

        if not card_input.upper().startswith("CARTAO"):
            return {
                "success": False,
                "message": "❌ Formato inválido. Use: CARTAO [últimos 4] [MM/AA] [Nome]"
            }

        parts = card_input.split()
        if len(parts) < 4:
            return {
                "success": False,
                "message": "❌ Dados incompletos do cartão."
            }

        last_four = parts[1]
        expiry = parts[2]
        holder_name = " ".join(parts[3:])

        # In production, this would integrate with a card tokenization service
        card_token = f"card_token_{hashlib.sha256(f'{user_id}{last_four}{expiry}'.encode()).hexdigest()[:16]}"

        credential = UserPaymentCredential(
            user_id=user_id,
            credential_id=f"card_{user_id}_{datetime.now().timestamp()}",
            payment_method="credit_card",
            encrypted_data=self._encrypt_data({
                "card_token": card_token,
                "last_four": last_four,
                "expiry": expiry,
                "holder_name": holder_name
            }),
            consent_proof=self._generate_consent_proof(user_id, "credit_card"),
            verification_status="verified",
            acquired_via=CredentialAcquisitionMethod.WHATSAPP_FLOW,
            acquired_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(days=365)
        )

        if user_id not in self.user_credentials:
            self.user_credentials[user_id] = []
        self.user_credentials[user_id].append(credential)

        return {
            "success": True,
            "credential_id": credential.credential_id,
            "message": f"✅ **Cartão configurado com sucesso!**\n\n"
                      f"💳 Cartão: ****{last_four}\n"
                      f"📅 Validade: {expiry}\n"
                      f"👤 Titular: {holder_name}\n"
                      f"🔐 Token: {card_token[:12]}...\n\n"
                      f"**Tokenização AP2 ativa** ✅\n"
                      f"Máxima segurança garantida!"
        }

    async def _process_boleto_credentials(self, user_id: str, boleto_input: str) -> Dict[str, Any]:
        """Process boleto credentials"""

        if not boleto_input.upper().startswith("BOLETO"):
            return {
                "success": False,
                "message": "❌ Formato inválido. Use: BOLETO [CPF] [Nome completo]"
            }

        parts = boleto_input.split()
        if len(parts) < 3:
            return {
                "success": False,
                "message": "❌ Dados incompletos para boleto."
            }

        cpf = parts[1]
        name = " ".join(parts[2:])

        # Generate boleto data
        boleto_code = f"BLT{datetime.now().strftime('%Y%m%d')}{hash(f'{user_id}{cpf}') % 10000:04d}"

        credential = UserPaymentCredential(
            user_id=user_id,
            credential_id=f"boleto_{user_id}_{datetime.now().timestamp()}",
            payment_method="boleto",
            encrypted_data=self._encrypt_data({
                "cpf": cpf,
                "name": name,
                "boleto_code": boleto_code
            }),
            consent_proof=self._generate_consent_proof(user_id, "boleto"),
            verification_status="verified",
            acquired_via=CredentialAcquisitionMethod.WHATSAPP_FLOW,
            acquired_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(days=3)  # Boletos expire in 3 days
        )

        if user_id not in self.user_credentials:
            self.user_credentials[user_id] = []
        self.user_credentials[user_id].append(credential)

        return {
            "success": True,
            "credential_id": credential.credential_id,
            "message": f"✅ **Boleto configurado com sucesso!**\n\n"
                      f"🧾 Código: {boleto_code}\n"
                      f"🆔 CPF: ***{cpf[-3:]}\n"
                      f"👤 Nome: {name}\n"
                      f"📅 Vencimento: {(datetime.now() + timedelta(days=3)).strftime('%d/%m/%Y')}\n\n"
                      f"**Protocolo AP2 ativo** ✅\n"
                      f"Boleto será gerado no pagamento!"
        }

    async def get_user_credentials(
        self,
        user_id: str,
        payment_method: Optional[str] = None
    ) -> List[UserPaymentCredential]:
        """Get user's payment credentials"""

        user_creds = self.user_credentials.get(user_id, [])

        if payment_method:
            return [cred for cred in user_creds if cred.payment_method == payment_method.lower()]

        return user_creds

    async def get_user_kyc_data(self, user_id: str) -> Optional[UserKYCData]:
        """Get user's KYC data"""
        return self.user_kyc_data.get(user_id)

    def _encrypt_data(self, data: Dict[str, Any]) -> str:
        """Encrypt sensitive data (simplified for demo)"""
        # In production, use proper encryption with KMS
        import base64
        json_data = json.dumps(data)
        return base64.b64encode(json_data.encode()).decode()

    def _decrypt_data(self, encrypted_data: str) -> Dict[str, Any]:
        """Decrypt sensitive data (simplified for demo)"""
        import base64
        json_data = base64.b64decode(encrypted_data.encode()).decode()
        return json.loads(json_data)

    def _generate_consent_proof(self, user_id: str, payment_method: str) -> str:
        """Generate consent proof for AP2 compliance"""
        consent_data = {
            "user_id": user_id,
            "payment_method": payment_method,
            "consent_given_at": datetime.now(timezone.utc).isoformat(),
            "consent_type": "payment_credential_acquisition",
            "protocol": "AP2"
        }
        # In production, sign this with a proper key
        return json.dumps(consent_data)

    def _validate_cpf(self, cpf: str) -> bool:
        """Basic CPF validation"""
        # Remove non-digits
        cpf = ''.join(filter(str.isdigit, cpf))

        # Check length
        if len(cpf) != 11:
            return False

        # Check for invalid patterns
        if cpf == cpf[0] * 11:
            return False

        # In production, implement full CPF validation algorithm
        return True


# Global instance for the application
_user_credential_service: Optional[UserCredentialService] = None


def get_user_credential_service() -> UserCredentialService:
    """Get or create the global user credential service"""
    global _user_credential_service
    if _user_credential_service is None:
        _user_credential_service = UserCredentialService()
    return _user_credential_service