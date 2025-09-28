#!/usr/bin/env python3
"""
Teste de Deploy - Mercado Pago Sandbox
=====================================

Este script testa se o sistema deployado está funcionando corretamente
com integração do Mercado Pago sandbox.

Uso:
    python test_deploy_mercadopago.py --url https://seu-projeto.onrender.com
"""

import os
import sys
import json
import time
import requests
import argparse
from datetime import datetime
from typing import Dict, Any, Optional

class DeployTester:
    """Testa o sistema deployado com Mercado Pago"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'sofIA-Deploy-Tester/1.0'
        })
    
    def test_health_check(self) -> Dict[str, Any]:
        """Testa se o agente está funcionando"""
        print("🔍 Testando health check...")
        
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Health check OK: {data}")
                return {"success": True, "data": data}
            else:
                print(f"❌ Health check falhou: {response.status_code}")
                return {"success": False, "error": f"HTTP {response.status_code}"}
                
        except requests.RequestException as e:
            print(f"❌ Erro de conexão: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def test_mercadopago_config(self) -> Dict[str, Any]:
        """Testa se as credenciais do Mercado Pago estão configuradas"""
        print("🔍 Testando configuração do Mercado Pago...")
        
        try:
            # Testa criação de payment intent
            test_data = {
                "operation": "create_payment_intent",
                "merchant_id": "mercadopago_demo_001",
                "amount": 10.00,
                "currency": "BRL",
                "description": "Teste de pagamento via sofIA"
            }
            
            response = self.session.post(
                f"{self.base_url}/test-mercadopago",
                json=test_data,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    print("✅ Mercado Pago configurado corretamente")
                    return {"success": True, "data": data}
                else:
                    print(f"❌ Erro no Mercado Pago: {data.get('error')}")
                    return {"success": False, "error": data.get('error')}
            else:
                print(f"❌ Erro HTTP: {response.status_code}")
                return {"success": False, "error": f"HTTP {response.status_code}"}
                
        except requests.RequestException as e:
            print(f"❌ Erro de conexão: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def test_whatsapp_bridge(self) -> Dict[str, Any]:
        """Testa se o WhatsApp Bridge está funcionando"""
        print("🔍 Testando WhatsApp Bridge...")
        
        try:
            # Tenta acessar o endpoint do bridge
            bridge_url = self.base_url.replace(':8000', ':3001')
            response = self.session.get(f"{bridge_url}/health", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                print("✅ WhatsApp Bridge funcionando")
                return {"success": True, "data": data}
            else:
                print(f"⚠️  WhatsApp Bridge não acessível: {response.status_code}")
                return {"success": False, "error": f"HTTP {response.status_code}"}
                
        except requests.RequestException as e:
            print(f"⚠️  WhatsApp Bridge não acessível: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def test_webhook_endpoint(self) -> Dict[str, Any]:
        """Testa se o webhook está funcionando"""
        print("🔍 Testando webhook do Mercado Pago...")
        
        try:
            webhook_data = {
                "id": 123456789,
                "live_mode": False,
                "type": "payment",
                "date_created": datetime.now().isoformat(),
                "data": {
                    "id": "123456789"
                }
            }
            
            response = self.session.post(
                f"{self.base_url}/webhooks/mercadopago",
                json=webhook_data,
                timeout=10
            )
            
            if response.status_code == 200:
                print("✅ Webhook funcionando")
                return {"success": True}
            else:
                print(f"❌ Webhook falhou: {response.status_code}")
                return {"success": False, "error": f"HTTP {response.status_code}"}
                
        except requests.RequestException as e:
            print(f"❌ Erro no webhook: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def test_payment_flow(self) -> Dict[str, Any]:
        """Testa o fluxo completo de pagamento"""
        print("🔍 Testando fluxo de pagamento...")
        
        try:
            # Simula uma mensagem do WhatsApp
            whatsapp_data = {
                "user_id": "test_user_123",
                "message": "Quero comprar um café por R$ 5,00",
                "phone_number": "+5511999999999",
                "timestamp": datetime.now().isoformat()
            }
            
            response = self.session.post(
                f"{self.base_url}/process-whatsapp-message",
                json=whatsapp_data,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                print("✅ Fluxo de pagamento funcionando")
                return {"success": True, "data": data}
            else:
                print(f"❌ Fluxo de pagamento falhou: {response.status_code}")
                return {"success": False, "error": f"HTTP {response.status_code}"}
                
        except requests.RequestException as e:
            print(f"❌ Erro no fluxo de pagamento: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Executa todos os testes"""
        print(f"🚀 Iniciando testes do deploy: {self.base_url}")
        print("=" * 60)
        
        results = {}
        
        # Teste 1: Health Check
        results["health_check"] = self.test_health_check()
        time.sleep(1)
        
        # Teste 2: Configuração Mercado Pago
        results["mercadopago_config"] = self.test_mercadopago_config()
        time.sleep(1)
        
        # Teste 3: WhatsApp Bridge
        results["whatsapp_bridge"] = self.test_whatsapp_bridge()
        time.sleep(1)
        
        # Teste 4: Webhook
        results["webhook"] = self.test_webhook_endpoint()
        time.sleep(1)
        
        # Teste 5: Fluxo de Pagamento
        results["payment_flow"] = self.test_payment_flow()
        
        # Resumo dos resultados
        print("\n" + "=" * 60)
        print("📊 RESUMO DOS TESTES")
        print("=" * 60)
        
        passed = 0
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ PASSOU" if result["success"] else "❌ FALHOU"
            print(f"{test_name.replace('_', ' ').title()}: {status}")
            if result["success"]:
                passed += 1
        
        print(f"\nResultado: {passed}/{total} testes passaram")
        
        if passed == total:
            print("🎉 Todos os testes passaram! Seu deploy está funcionando perfeitamente!")
        elif passed >= total * 0.8:
            print("⚠️  A maioria dos testes passou. Verifique os que falharam.")
        else:
            print("❌ Muitos testes falharam. Verifique a configuração do deploy.")
        
        return {
            "total_tests": total,
            "passed_tests": passed,
            "results": results,
            "overall_success": passed == total
        }


def main():
    """Função principal"""
    parser = argparse.ArgumentParser(description="Testa o deploy do sofIA com Mercado Pago")
    parser.add_argument(
        "--url", 
        required=True,
        help="URL do deploy (ex: https://seu-projeto.onrender.com)"
    )
    parser.add_argument(
        "--verbose", 
        action="store_true",
        help="Mostra informações detalhadas"
    )
    
    args = parser.parse_args()
    
    # Valida URL
    if not args.url.startswith(('http://', 'https://')):
        args.url = f"https://{args.url}"
    
    # Executa testes
    tester = DeployTester(args.url)
    results = tester.run_all_tests()
    
    # Salva resultados em arquivo
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"deploy_test_results_{timestamp}.json"
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n📄 Resultados salvos em: {filename}")
    
    # Exit code baseado no resultado
    sys.exit(0 if results["overall_success"] else 1)


if __name__ == "__main__":
    main()
