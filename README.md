# 💸 Sistema de Contas a Pagar

Sistema completo de gestão de contas a pagar desenvolvido em Streamlit com integração ao Supabase.

## 🚀 Funcionalidades

- **Lançamento de Contas**: Cadastro e provisionamento de contas
- **Aprovações**: Sistema de aprovação com data de agendamento bancário
- **Pagamentos/Conciliação**: Registro de pagamentos e conciliação automática
- **Dashboard Executivo**: Visão geral com gráficos e métricas
- **ETL/Importação**: Importação de planilhas CSV/Excel
- **Gerenciamento de Usuários**: Sistema de autenticação e controle de acesso

## 🛠️ Tecnologias

- **Frontend**: Streamlit
- **Backend**: Supabase (PostgreSQL)
- **Linguagem**: Python 3.12
- **Visualização**: Matplotlib

## 📋 Pré-requisitos

- Python 3.8+
- Conta no Supabase
- Conta no GitHub (para deploy)

## 🚀 Como executar localmente

1. Clone o repositório:
```bash
git clone <seu-repositorio>
cd contas_a_pagar_streamlit_supabase_full
```

2. Instale as dependências:
```bash
pip install -r requirements.txt
```

3. Configure as variáveis de ambiente (NÃO commitá segredos):

   Opção A) `.streamlit/secrets.toml` (recomendado para produção/Streamlit Cloud)
   ```toml
   SUPABASE_URL = "sua_url_do_supabase"
   SUPABASE_ANON_KEY = "sua_chave_publica_anon"
   ADMIN_INITIAL_PASSWORD = "senha_inicial_admin_forte"
   DEBUG = false
   ```

   Opção B) `.env` (somente local; o app carrega automaticamente)
   ```env
   SUPABASE_URL=
   SUPABASE_ANON_KEY=
   ADMIN_INITIAL_PASSWORD=
   DEBUG=false
   ```

4. Execute o aplicativo:
```bash
streamlit run app.py
```

## 🌐 Deploy na Nuvem

### Streamlit Cloud (Recomendado)

1. Faça upload do código para o GitHub
2. Acesse [share.streamlit.io](https://share.streamlit.io)
3. Conecte sua conta GitHub
4. Selecione o repositório
5. Configure as variáveis de ambiente no Streamlit Cloud (.streamlit/secrets)
6. Deploy automático!

## 📊 Estrutura do Banco

O sistema utiliza as seguintes tabelas no Supabase:
- `contas`: Contas a pagar
- `categorias`: Categorias de gastos
- `fornecedores`: Fornecedores
- `aprovacoes`: Aprovações de contas
- `pagamentos`: Registro de pagamentos

## 🔧 Configuração do Supabase

Execute o script SQL fornecido no arquivo `schema.sql` no seu banco Supabase para criar as tabelas necessárias.

## 🔒 Boas práticas de segurança

- Nunca commit suas chaves reais. Este repositório inclui `.gitignore` para ignorar `.env` e `.streamlit/secrets.toml`.
- Se você já publicou chaves no histórico, gere novas no Supabase (revogue as antigas) e atualize seus segredos.
- O usuário `admin` é criado no primeiro boot usando `ADMIN_INITIAL_PASSWORD`. Altere a senha após o primeiro login.

## 📝 Licença

Este projeto é de uso interno da empresa.
