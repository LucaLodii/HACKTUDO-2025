# 🚀 Configuração do Deploy - Mercado Pago Sandbox

Este guia te ajudará a configurar seu projeto deployado para testar pagamentos com Mercado Pago na versão sandbox.

## 📋 Pré-requisitos

- ✅ Projeto deployado (sofIA Agent + WhatsApp Bridge)
- ✅ Acesso ao painel do Mercado Pago
- ✅ URL do seu deploy (ex: https://seu-projeto.onrender.com)

## 🔧 Passo 1: Configurar Credenciais do Mercado Pago

### 1.1 Criar Conta no Mercado Pago

1. Acesse: https://www.mercadopago.com.br/
2. Clique em "Criar conta"
3. Escolha "Pessoa Física" (para testes) ou "Pessoa Jurídica" (para produção)
4. Complete o cadastro com seus dados

### 1.2 Obter Credenciais Sandbox

1. Acesse: https://www.mercadopago.com.br/developers
2. Clique em "Suas integrações"
3. Clique em "Criar aplicação"
4. Preencha:

   - **Nome**: sofIA WhatsApp Payment Agent
   - **Descrição**: AI payment agent for WhatsApp transactions
   - **Modelo**: Pagamentos
   - **Tipo de integração**: Pagamentos online

5. Após criar, vá em "Credenciais"
6. **COPIE as credenciais SANDBOX** (começam com TEST-)

## 🔧 Passo 2: Configurar Variáveis de Ambiente

### 2.1 No seu provedor de deploy (Render/Railway/Heroku)

Adicione estas variáveis de ambiente:

```bash
# =============================================================================
# CONFIGURAÇÕES OBRIGATÓRIAS
# =============================================================================

# Google AI (obrigatório)
GOOGLE_API_KEY=sua_google_api_key_aqui

# Mercado Pago Sandbox (obrigatório)
MERCADOPAGO_ACCESS_TOKEN=TEST-sua_access_token_sandbox_aqui
MERCADOPAGO_PUBLIC_KEY=TEST-sua_public_key_sandbox_aqui
MERCADOPAGO_CLIENT_ID=seu_client_id_sandbox_aqui
MERCADOPAGO_CLIENT_SECRET=seu_client_secret_sandbox_aqui

# Ambiente Mercado Pago
MERCADOPAGO_ENVIRONMENT=sandbox
MERCADOPAGO_USE_MOCK=false

# URL do webhook (substitua pela sua URL de deploy)
MERCADOPAGO_WEBHOOK_URL=https://seu-projeto.onrender.com/webhooks/mercadopago

# =============================================================================
# CONFIGURAÇÕES DO SERVIDOR
# =============================================================================

# Configurações básicas
HOST=0.0.0.0
PORT=8000
ENVIRONMENT=production
DEBUG=false

# WhatsApp Bridge
WHATSAPP_BRIDGE_URL=http://localhost:3001

# =============================================================================
# CONFIGURAÇÕES OPCIONAIS
# =============================================================================

# AP2 Protocol
AGENT_ID=sofia-whatsapp-agent
MERCHANT_ID=sofia-merchant

# Configurações de negócio
DEFAULT_CURRENCY=BRL
DEFAULT_TIMEZONE=America/Sao_Paulo
DEFAULT_LANGUAGE=pt-BR

# Configurações de segurança
JWT_SECRET=sua_jwt_secret_aqui
ENCRYPTION_KEY=sua_encryption_key_aqui
```

### 2.2 Exemplo de Configuração no Render

1. Acesse seu projeto no Render
2. Vá em "Environment"
3. Adicione cada variável:

```
GOOGLE_API_KEY = AIzaSyC... (sua chave do Google AI)
MERCADOPAGO_ACCESS_TOKEN = TEST-1234567890123456-112233-abcdef...
MERCADOPAGO_PUBLIC_KEY = TEST-abcdef12-3456-7890-abcd-ef1234567890
MERCADOPAGO_CLIENT_ID = 1234567890123456
MERCADOPAGO_CLIENT_SECRET = abcdefghijklmnopqrstuvwxyz123456
MERCADOPAGO_ENVIRONMENT = sandbox
MERCADOPAGO_USE_MOCK = false
MERCADOPAGO_WEBHOOK_URL = https://seu-projeto.onrender.com/webhooks/mercadopago
HOST = 0.0.0.0
PORT = 8000
ENVIRONMENT = production
DEBUG = false
```

## 🔧 Passo 3: Configurar Webhook no Mercado Pago

### 3.1 No Painel do Mercado Pago

1. Acesse sua aplicação no Mercado Pago
2. Vá em "Webhooks" ou "Notificações"
3. Adicione a URL: `https://seu-projeto.onrender.com/webhooks/mercadopago`
4. Selecione os eventos:
   - ✅ Payment status changes
   - ✅ Payment updates
   - ✅ Refund notifications
   - ✅ Chargeback notifications

### 3.2 Verificar Webhook

O webhook deve retornar HTTP 200 OK. Teste com:

```bash
curl -X POST https://seu-projeto.onrender.com/webhooks/mercadopago \
  -H "Content-Type: application/json" \
  -d '{"test": "webhook"}'
```

## 🔧 Passo 4: Reiniciar o Deploy

### 4.1 No Render/Railway/Heroku

1. Vá em "Deploy" ou "Releases"
2. Clique em "Redeploy" ou "Restart"
3. Aguarde o deploy completar
4. Verifique os logs para erros

### 4.2 Verificar Logs

```bash
# No Render, vá em "Logs" e procure por:
# ✅ "sofIA WhatsApp Payment Agent initialized"
# ✅ "Mercado Pago processor initialized"
# ✅ "WhatsApp Bridge connected"
```

## 🔧 Passo 5: Testar o Sistema

### 5.1 Teste de Conectividade

```bash
# Teste se o agente está funcionando
curl https://seu-projeto.onrender.com/health

# Resposta esperada:
# {"status": "healthy", "service": "sofIA WhatsApp Payment Agent", "ap2_ready": true}
```

### 5.2 Teste de Pagamento via WhatsApp

1. **Conecte o WhatsApp**:

   - Acesse os logs do WhatsApp Bridge
   - Escaneie o QR Code com seu celular
   - Aguarde "WhatsApp client is ready!"

2. **Envie mensagem de teste**:

   ```
   Olá sofIA! Quero comprar um café por R$ 5,00
   ```

3. **Verifique o fluxo**:
   - sofIA deve responder
   - Deve criar um payment intent
   - Deve mostrar opções de pagamento

### 5.3 Teste com Cartão Sandbox

Use estes dados de teste do Mercado Pago:

```
Cartão Aprovado:
Número: 4509 9535 6623 3704
CVV: 123
Vencimento: 11/2025
Nome: APRO

Cartão Recusado (Saldo Insuficiente):
Número: 4013 5406 8274 6260
CVV: 123
Vencimento: 11/2025
Nome: OTHE
```

## 🔧 Passo 6: Monitoramento e Debug

### 6.1 Verificar Logs em Tempo Real

```bash
# No Render, vá em "Logs" e monitore:
# - Mensagens do WhatsApp sendo processadas
# - Criação de payment intents
# - Processamento de pagamentos
# - Webhooks recebidos
```

### 6.2 Testar Webhook Manualmente

```bash
# Simular notificação do Mercado Pago
curl -X POST https://seu-projeto.onrender.com/webhooks/mercadopago \
  -H "Content-Type: application/json" \
  -H "X-Signature: sha256=test" \
  -d '{
    "id": 123456789,
    "live_mode": false,
    "type": "payment",
    "date_created": "2024-01-01T00:00:00Z",
    "data": {
      "id": "123456789"
    }
  }'
```

## 🚨 Solução de Problemas

### Problema 1: "Invalid credentials"

**Solução**:

- Verifique se está usando credenciais SANDBOX (começam com TEST-)
- Confirme se `MERCADOPAGO_ENVIRONMENT=sandbox`
- Verifique se não há espaços extras nas credenciais

### Problema 2: "Webhook not receiving notifications"

**Solução**:

- Verifique se a URL do webhook está correta
- Confirme se o webhook está configurado no Mercado Pago
- Teste se a URL retorna 200 OK
- Verifique os logs do servidor

### Problema 3: "Payment processing failed"

**Solução**:

- Use cartões de teste do Mercado Pago
- Verifique se está no ambiente sandbox
- Confirme se as credenciais estão corretas
- Verifique os logs para erros específicos

### Problema 4: "WhatsApp not connecting"

**Solução**:

- Verifique se o WhatsApp Bridge está rodando
- Escaneie o QR Code novamente
- Limpe a sessão do WhatsApp se necessário
- Verifique os logs do bridge

## 📊 Verificação Final

### Checklist de Funcionamento

- [ ] ✅ Deploy funcionando (health check OK)
- [ ] ✅ Credenciais Mercado Pago configuradas
- [ ] ✅ Webhook configurado e testado
- [ ] ✅ WhatsApp conectado
- [ ] ✅ sofIA responde mensagens
- [ ] ✅ Payment intents sendo criados
- [ ] ✅ Pagamentos processados com sucesso
- [ ] ✅ Webhooks recebendo notificações

### Teste Completo

1. **Envie**: "Quero comprar um produto por R$ 10,00"
2. **sofIA deve**: Responder e criar payment intent
3. **Escolha**: Cartão de crédito
4. **Use**: Cartão de teste (4509 9535 6623 3704)
5. **Resultado**: Pagamento aprovado

## 🎯 Próximos Passos

1. **Teste todos os métodos de pagamento** (PIX, boleto, débito)
2. **Teste parcelamentos** (2x, 3x, 6x, 12x)
3. **Teste cenários de erro** (cartão recusado, dados inválidos)
4. **Configure monitoramento** (logs, alertas, métricas)
5. **Prepare para produção** (quando estiver satisfeito com os testes)

## 📞 Suporte

Se encontrar problemas:

1. **Verifique os logs** do deploy
2. **Teste as credenciais** do Mercado Pago
3. **Confirme a configuração** do webhook
4. **Use os cartões de teste** fornecidos
5. **Consulte a documentação** do Mercado Pago

Seu sistema sofIA está pronto para processar pagamentos via WhatsApp! 🚀
