# 🚀 Resumo: Configuração do Deploy com Mercado Pago

## ✅ O que foi criado para você:

1. **📋 Guia completo**: `DEPLOY_MERCADOPAGO_SETUP.md`
2. **🧪 Script de teste**: `test_deploy_mercadopago.py`
3. **⚙️ Arquivo de configuração**: `env.deploy.example`
4. **🔧 Endpoint de teste**: Adicionado em `app.py`

## 🎯 Passo a Passo para Configurar:

### 1. Obter Credenciais do Mercado Pago

1. Acesse: https://www.mercadopago.com.br/developers
2. Crie uma aplicação
3. Copie as credenciais **SANDBOX** (começam com TEST-)

### 2. Configurar Variáveis de Ambiente no Deploy

No seu provedor de deploy (Render/Railway/Heroku), adicione:

```bash
# OBRIGATÓRIAS
GOOGLE_API_KEY=sua_google_api_key
MERCADOPAGO_ACCESS_TOKEN=TEST-sua_access_token_sandbox
MERCADOPAGO_PUBLIC_KEY=TEST-sua_public_key_sandbox
MERCADOPAGO_CLIENT_ID=seu_client_id_sandbox
MERCADOPAGO_CLIENT_SECRET=seu_client_secret_sandbox
MERCADOPAGO_ENVIRONMENT=sandbox
MERCADOPAGO_USE_MOCK=false
MERCADOPAGO_WEBHOOK_URL=https://seu-projeto.onrender.com/webhooks/mercadopago

# CONFIGURAÇÕES BÁSICAS
HOST=0.0.0.0
PORT=8000
ENVIRONMENT=production
DEBUG=false
```

### 3. Configurar Webhook no Mercado Pago

1. No painel do Mercado Pago
2. Vá em "Webhooks"
3. Adicione: `https://seu-projeto.onrender.com/webhooks/mercadopago`
4. Selecione os eventos de pagamento

### 4. Reiniciar o Deploy

1. Faça redeploy do seu projeto
2. Aguarde completar
3. Verifique os logs

### 5. Testar o Sistema

```bash
# Execute o script de teste
python test_deploy_mercadopago.py --url https://seu-projeto.onrender.com

# Ou teste manualmente
curl https://seu-projeto.onrender.com/health
```

## 🧪 Como Testar:

### Teste 1: Health Check

```bash
curl https://seu-projeto.onrender.com/health
```

### Teste 2: Mercado Pago

```bash
curl -X POST https://seu-projeto.onrender.com/test-mercadopago \
  -H "Content-Type: application/json" \
  -d '{
    "operation": "create_payment_intent",
    "merchant_id": "mercadopago_demo_001",
    "amount": 10.00,
    "currency": "BRL",
    "description": "Teste de pagamento"
  }'
```

### Teste 3: WhatsApp

1. Conecte o WhatsApp (escaneie QR Code)
2. Envie: "Quero comprar um café por R$ 5,00"
3. Verifique se sofIA responde

## 🎯 Cartões de Teste do Mercado Pago:

```
✅ Aprovado:
Número: 4509 9535 6623 3704
CVV: 123
Vencimento: 11/2025
Nome: APRO

❌ Recusado (Saldo Insuficiente):
Número: 4013 5406 8274 6260
CVV: 123
Vencimento: 11/2025
Nome: OTHE
```

## 🚨 Solução de Problemas:

### "Invalid credentials"

- Verifique se está usando credenciais SANDBOX (TEST-)
- Confirme `MERCADOPAGO_ENVIRONMENT=sandbox`

### "Webhook not working"

- Verifique se a URL está correta
- Teste se retorna 200 OK
- Confirme se está configurado no Mercado Pago

### "WhatsApp not connecting"

- Verifique logs do WhatsApp Bridge
- Escaneie QR Code novamente
- Limpe sessão se necessário

## 📊 Verificação Final:

- [ ] ✅ Deploy funcionando (health check OK)
- [ ] ✅ Credenciais Mercado Pago configuradas
- [ ] ✅ Webhook configurado e testado
- [ ] ✅ WhatsApp conectado
- [ ] ✅ sofIA responde mensagens
- [ ] ✅ Pagamentos processados com sucesso

## 🎉 Próximos Passos:

1. **Teste todos os métodos**: PIX, cartão, boleto
2. **Teste parcelamentos**: 2x, 3x, 6x, 12x
3. **Teste cenários de erro**: cartão recusado, dados inválidos
4. **Configure monitoramento**: logs, alertas, métricas
5. **Prepare para produção**: quando estiver satisfeito

## 📞 Suporte:

Se encontrar problemas:

1. Verifique os logs do deploy
2. Execute o script de teste
3. Consulte o guia completo em `DEPLOY_MERCADOPAGO_SETUP.md`
4. Use os cartões de teste fornecidos

**Seu sistema sofIA está pronto para processar pagamentos via WhatsApp! 🚀**
