
import os
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
from datetime import datetime
from dateutil.relativedelta import relativedelta
from supabase import create_client, Client
import hashlib

st.set_page_config(page_title="Contas a Pagar", page_icon="💸", layout="wide")

# Sistema de Autenticação
def hash_password(password):
    """Cria hash da senha para armazenamento seguro"""
    return hashlib.sha256(password.encode()).hexdigest()

def load_users():
    """Carrega usuários do arquivo de configuração"""
    try:
        # Tenta carregar do arquivo users.json
        import json
        with open('users.json', 'r', encoding='utf-8') as f:
            content = f.read().strip()
            if not content:
                raise ValueError("Arquivo vazio")
            return json.loads(content)
    except (FileNotFoundError, ValueError, json.JSONDecodeError):
        # Se não existir ou estiver vazio, cria com usuários padrão
        default_users = {
            "admin": hash_password("admin123"),
            "usuario": hash_password("user123"),
            "financeiro": hash_password("fin123")
        }
        try:
            save_users(default_users)
        except Exception:
            # Se não conseguir salvar, retorna os usuários padrão mesmo assim
            pass
        return default_users

def save_users(users):
    """Salva usuários no arquivo de configuração"""
    import json
    with open('users.json', 'w', encoding='utf-8') as f:
        json.dump(users, f, indent=2, ensure_ascii=False)

def check_credentials(username, password):
    """Verifica credenciais de login"""
    users = load_users()
    
    if username in users:
        return users[username] == hash_password(password)
    return False

def add_user(username, password):
    """Adiciona novo usuário"""
    users = load_users()
    users[username] = hash_password(password)
    save_users(users)
    return True

def remove_user(username):
    """Remove usuário"""
    users = load_users()
    if username in users and username != "admin":  # Não permite remover admin
        del users[username]
        save_users(users)
        return True
    return False

def list_users():
    """Lista todos os usuários"""
    users = load_users()
    return list(users.keys())

def login_page():
    """Página de login"""
    st.title("🔐 Sistema de Contas a Pagar")
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("### Acesso ao Sistema")
        
        with st.form("login_form"):
            username = st.text_input("👤 Usuário", placeholder="Digite seu usuário")
            password = st.text_input("🔒 Senha", type="password", placeholder="Digite sua senha")
            
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                login_button = st.form_submit_button("🚀 Entrar", use_container_width=True)
            with col_btn2:
                if st.form_submit_button("❌ Cancelar", use_container_width=True):
                    st.stop()
            
            if login_button:
                if check_credentials(username, password):
                    st.session_state['authenticated'] = True
                    st.session_state['username'] = username
                    st.success("✅ Login realizado com sucesso!")
                    st.rerun()
                else:
                    st.error("❌ Usuário ou senha incorretos!")
        
        st.markdown("---")
        st.markdown("### 👥 Usuários Cadastrados:")
        users = list_users()
        for user in users:
            st.markdown(f"- **{user}**")

def logout():
    """Função para logout"""
    st.session_state['authenticated'] = False
    st.session_state['username'] = None
    st.rerun()

def env_get(key: str):
    """Lê primeiro st.secrets, depois credenciais hardcoded como fallback."""
    # 1) st.secrets (protegido)
    try:
        return st.secrets[key]
    except Exception:
        # 2) Credenciais hardcoded como fallback
        if key == "SUPABASE_URL":
            return "https://ikmubzpieogvheefejjz.supabase.co"
        elif key == "SUPABASE_ANON_KEY":
            return "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlrbXVienBpZW9ndmhlZWZlamp6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY5MzM3MDksImV4cCI6MjA3MjUwOTcwOX0.W_TpmjMvmhnIoUd1L2HzoBkN9VxuJ14RQ2vMD7ofvOw"
        return None

@st.cache_resource
def get_client() -> Client:
    url = env_get("SUPABASE_URL")
    key = env_get("SUPABASE_ANON_KEY")
    if not url or not key:
        st.error(
            "⚠️ Não encontrei SUPABASE_URL / SUPABASE_ANON_KEY.\n"
            "Defina no arquivo .env (mesma pasta do app) ou em .streamlit/secrets.toml."
        )
        st.stop()
    return create_client(url, key)

sb = get_client()

# Verificação de autenticação
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False

if not st.session_state['authenticated']:
    login_page()
    st.stop()
    
def to_float(x):
    try: 
        # Remove espaços e converte string
        s = str(x).strip()
        # Se está vazio, retorna 0
        if not s:
            return 0.0
        
        # Verifica se é negativo
        is_negative = s.startswith('-')
        if is_negative:
            s = s[1:]  # Remove o sinal de negativo temporariamente
        
        # Remove pontos de milhares (apenas se não for o último ponto)
        if '.' in s and ',' in s:
            # Formato brasileiro: 1.500,50 -> 1500.50
            s = s.replace(".", "").replace(",", ".")
        elif ',' in s:
            # Apenas vírgula decimal: 1500,50 -> 1500.50
            s = s.replace(",", ".")
        
        # Converte para float
        result = float(s)
        
        # Aplica o sinal negativo se necessário
        return -result if is_negative else result
        
    except: 
        return 0.0

def fetch_table(table, select="*", order=None, eq=None):
    try:
        q = sb.table(table).select(select)
        if eq:
            for k,v in eq.items(): q = q.eq(k, v)
        if order: q = q.order(order, desc=True)
        return pd.DataFrame(q.execute().data or [])
    except Exception as e:
        st.warning(f"⚠️ Erro de conexão com o banco de dados: {str(e)[:100]}...")
        return pd.DataFrame()

def upsert(table, payload): 
    try:
        # Para contas, só atualiza campos específicos sem sobrescrever campos obrigatórios
        if table == "contas" and "id" in payload:
            # Busca o registro atual primeiro
            current = sb.table(table).select("*").eq("id", payload["id"]).execute()
            if current.data:
                # Mescla apenas os campos fornecidos com os existentes
                existing = current.data[0]
                for key, value in payload.items():
                    if key != "id":  # Não sobrescreve o ID
                        existing[key] = value
                return sb.table(table).update(existing).eq("id", payload["id"]).execute()
        return sb.table(table).upsert(payload).execute()
    except Exception as e:
        st.error(f"Erro ao salvar dados: {str(e)[:100]}...")
        return None

def insert(table, payload): 
    try:
        return sb.table(table).insert(payload).execute()
    except Exception as e:
        st.error(f"Erro ao inserir dados: {str(e)[:100]}...")
        return None

def delete_conta(conta_id):
    """Exclui uma conta e todos os registros relacionados (aprovacoes, pagamentos)"""
    try:
        # Exclui pagamentos relacionados
        sb.table("pagamentos").delete().eq("conta_id", conta_id).execute()
        # Exclui aprovações relacionadas
        sb.table("aprovacoes").delete().eq("conta_id", conta_id).execute()
        # Exclui a conta
        result = sb.table("contas").delete().eq("id", conta_id).execute()
        return result
    except Exception as e:
        st.error(f"Erro ao excluir conta: {e}")
        return None

def ensure_categoria(nome):
    df = fetch_table("categorias", eq={"nome": nome})
    if df.empty:
        insert("categorias", {"nome": nome})
        df = fetch_table("categorias", eq={"nome": nome})
    return int(df.iloc[0]["id"])

def ensure_fornecedor(nome, cnpj=None, email=None, telefone=None):
    df = fetch_table("fornecedores")
    if not df.empty:
        # Busca por nome ou CNPJ
        hit = df[(df["nome"].str.lower() == nome.lower()) | (df["cnpj"] == cnpj)]
        if not hit.empty: 
            # Atualiza dados se CNPJ foi fornecido
            if cnpj and hit.iloc[0]["cnpj"] != cnpj:
                sb.table("fornecedores").update({"cnpj": cnpj, "email": email, "telefone": telefone}).eq("id", hit.iloc[0]["id"]).execute()
            return int(hit.iloc[0]["id"])
    insert("fornecedores", {"nome": nome, "cnpj": cnpj, "email": email, "telefone": telefone})
    df2 = fetch_table("fornecedores")
    hit2 = df2[df2["nome"].str.lower() == nome.lower()]
    return int(hit2.iloc[0]["id"]) if not hit2.empty else None

def money(x):
    try: return f"R$ {float(x):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except: return x

st.sidebar.title("💸 Contas a Pagar")

# Informações do usuário logado
if st.session_state.get('username'):
    st.sidebar.markdown(f"👤 **Usuário:** {st.session_state['username']}")
    st.sidebar.markdown("---")

page = st.sidebar.radio("Navegar", ["Lançar Contas", "Aprovações", "Pagamentos/Conciliação", "Dashboard", "ETL/Importação", "Gerenciar Usuários"], index=0)

# Botão de logout
st.sidebar.markdown("---")
if st.sidebar.button("🚪 Sair", use_container_width=True):
    logout()

if page == "Lançar Contas":
    st.header("Lançamento / Provisionamento de Contas")
    with st.form("form_conta"):
        # Primeira linha: Empresa e Fornecedor
        cols = st.columns(2)
        empresa = cols[0].text_input("Empresa *", placeholder="Ex: Empresa A, Empresa B, etc.")
        fornecedor = cols[1].text_input("Fornecedor *", placeholder="Nome do fornecedor")
        
        # Segunda linha: CNPJ e Categoria
        cols2 = st.columns(2)
        cnpj_fornecedor = cols2[0].text_input("CNPJ do Fornecedor", placeholder="00.000.000/0000-00")
        categoria = cols2[1].text_input("Categoria *", value="Geral")
        
        # Terceira linha: Descrição e Número do Documento
        cols3 = st.columns(2)
        descricao = cols3[0].text_input("Descrição", placeholder="Descrição da conta")
        numero_documento = cols3[1].text_input("Número do Documento", placeholder="Ex: NF 123, Boleto 456, etc.")
        
        # Quarta linha: Datas e Valor
        cols4 = st.columns(3)
        competence_month = cols4[0].date_input("Competência (mês)", value=datetime.today().replace(day=1))
        vencimento = cols4[1].date_input("Vencimento *", value=datetime.today())
        valor_previsto = cols4[2].text_input("Valor previsto (ex: 1234,56) *", placeholder="1234,56")
        
        submitted = st.form_submit_button("Salvar Provisionamento")
        if submitted:
            if not fornecedor or not categoria or not valor_previsto or not vencimento or not empresa:
                st.error("Preencha os campos obrigatórios (*)")
            else:
                fornecedor_id = ensure_fornecedor(fornecedor, cnpj=cnpj_fornecedor)
                categoria_id = ensure_categoria(categoria)
                vp = to_float(valor_previsto)
                if vp is None:
                    st.error("Valor inválido")
                else:
                    insert("contas", {
                        "fornecedor_id": fornecedor_id,
                        "categoria_id": categoria_id,
                        "descricao": descricao,
                        "competencia": competence_month.strftime("%Y-%m-%d"),
                        "vencimento": vencimento.strftime("%Y-%m-%d"),
                        "valor_previsto": vp,
                        "status": "provisionado",
                        "empresa": empresa,
                        "numero_documento": numero_documento,
                    })
                    st.success("Conta provisionada com sucesso!")
    df = fetch_table("contas", order="criado_em")
    if not df.empty:
        # Prepara dados para exibição
        df_display = df.copy()
        df_display["valor_previsto"] = df_display["valor_previsto"].apply(money)
        
        # Busca nomes dos fornecedores e categorias
        fornecedores = fetch_table("fornecedores")
        categorias = fetch_table("categorias")
        
        if not fornecedores.empty:
            fornecedor_map = dict(zip(fornecedores["id"], fornecedores["nome"]))
            df_display["fornecedor_nome"] = df_display["fornecedor_id"].map(fornecedor_map)
        
        if not categorias.empty:
            categoria_map = dict(zip(categorias["id"], categorias["nome"]))
            df_display["categoria_nome"] = df_display["categoria_id"].map(categoria_map)
        
        # Filtros para a tabela de contas
        st.subheader("🔍 Filtros de Pesquisa")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Filtro por empresa
            empresas_unicas = ["Todos"] + sorted(df_display["empresa"].dropna().unique().tolist())
            empresa_filtro = st.selectbox("Empresa", empresas_unicas)
            
            # Filtro por status
            status_unicos = ["Todos"] + sorted(df_display["status"].dropna().unique().tolist())
            status_filtro = st.selectbox("Status", status_unicos)
        
        with col2:
            # Filtro por fornecedor
            fornecedores_unicos = ["Todos"] + sorted(df_display["fornecedor_nome"].dropna().unique().tolist())
            fornecedor_filtro = st.selectbox("Fornecedor", fornecedores_unicos)
            
            # Filtro por categoria
            categorias_unicas = ["Todos"] + sorted(df_display["categoria_nome"].dropna().unique().tolist())
            categoria_filtro = st.selectbox("Categoria", categorias_unicas)
        
        with col3:
            # Filtro por valor mínimo
            valor_min = st.number_input("Valor Mínimo (R$)", min_value=0.0, value=0.0, step=0.01)
            
            # Filtro por valor máximo
            # Converte valores monetários para float para calcular o máximo
            if not df_display.empty:
                valores_numericos = df_display["valor_previsto"].str.replace("R$", "").str.replace(".", "").str.replace(",", ".").astype(float)
                valor_max_default = float(valores_numericos.max())
            else:
                valor_max_default = 0.0
            valor_max = st.number_input("Valor Máximo (R$)", min_value=0.0, value=valor_max_default, step=0.01)
        
        # Filtro de busca por texto
        st.write("**🔍 Busca por Texto:**")
        col_busca1, col_busca2 = st.columns(2)
        
        with col_busca1:
            busca_descricao = st.text_input("Buscar na Descrição", placeholder="Digite parte da descrição...")
        
        with col_busca2:
            busca_documento = st.text_input("Buscar no Número do Documento", placeholder="Digite o número do documento...")
        
        # Botão para limpar filtros
        col_limpar, col_espaco = st.columns([1, 4])
        with col_limpar:
            if st.button("🗑️ Limpar Filtros", type="secondary"):
                st.rerun()
        
        # Aplicar filtros
        df_filtrado = df_display.copy()
        
        if empresa_filtro != "Todos":
            df_filtrado = df_filtrado[df_filtrado["empresa"] == empresa_filtro]
        
        if status_filtro != "Todos":
            df_filtrado = df_filtrado[df_filtrado["status"] == status_filtro]
        
        if fornecedor_filtro != "Todos":
            df_filtrado = df_filtrado[df_filtrado["fornecedor_nome"] == fornecedor_filtro]
        
        if categoria_filtro != "Todos":
            df_filtrado = df_filtrado[df_filtrado["categoria_nome"] == categoria_filtro]
        
        if valor_min > 0 or valor_max > 0:
            # Converte valores monetários para float para comparação
            valores_numericos = df_filtrado["valor_previsto"].str.replace("R$", "").str.replace(".", "").str.replace(",", ".").astype(float)
            
            if valor_min > 0:
                df_filtrado = df_filtrado[valores_numericos >= valor_min]
            
            if valor_max > 0:
                df_filtrado = df_filtrado[valores_numericos <= valor_max]
        
        # Aplicar filtros de busca por texto
        if busca_descricao:
            df_filtrado = df_filtrado[df_filtrado["descricao"].astype(str).str.contains(busca_descricao, case=False, na=False)]
        
        if busca_documento:
            df_filtrado = df_filtrado[df_filtrado["numero_documento"].astype(str).str.contains(busca_documento, case=False, na=False)]
        
        # Mostrar resultados filtrados
        st.write(f"**📊 Resultados encontrados: {len(df_filtrado)} contas**")
        
        # Seleciona colunas para exibição
        cols_to_show = ["id", "empresa", "fornecedor_nome", "categoria_nome", "descricao", "numero_documento", "competencia", "vencimento", "valor_previsto", "status", "criado_em"]
        available_cols = [col for col in cols_to_show if col in df_filtrado.columns]
        
        st.dataframe(df_filtrado[available_cols], use_container_width=True)
        
        # Seção de exclusão de contas
        st.subheader("🗑️ Excluir Conta")
        if not df.empty:
            # Cria opções para exclusão
            df["label"] = df.apply(lambda r: f'#{int(r["id"])} - {r.get("empresa","N/A")} | {r.get("fornecedor_nome","N/A")} | Venc: {r.get("vencimento","")} | {money(r.get("valor_previsto",0))} | Status: {r.get("status","")}', axis=1)
            
            col1, col2 = st.columns([3, 1])
            with col1:
                conta_excluir = st.selectbox("Selecione a conta para excluir", options=df["id"], format_func=lambda x: df.loc[df["id"]==x, "label"].values[0])
            
            with col2:
                st.write("")  # Espaçamento
                st.write("")  # Espaçamento
                if st.button("🗑️ Excluir", type="secondary"):
                    if conta_excluir:
                        # Exclui aprovações relacionadas
                        sb.table("aprovacoes").delete().eq("conta_id", int(conta_excluir)).execute()
                        # Exclui pagamentos relacionados  
                        sb.table("pagamentos").delete().eq("conta_id", int(conta_excluir)).execute()
                        # Exclui a conta
                        sb.table("contas").delete().eq("id", int(conta_excluir)).execute()
                        st.success("Conta excluída com sucesso!")
                        st.rerun()

elif page == "Aprovações":
    st.header("Registrar Aprovação")
    contas = fetch_table("contas")
    pendentes = contas[contas["status"].isin(["provisionado"])].copy()
    if pendentes.empty:
        st.info("Não há contas pendentes de aprovação.")
    else:
        # Busca nomes dos fornecedores
        fornecedores = fetch_table("fornecedores")
        if not fornecedores.empty:
            fornecedor_map = dict(zip(fornecedores["id"], fornecedores["nome"]))
            pendentes["fornecedor_nome"] = pendentes["fornecedor_id"].map(fornecedor_map)
        
        # Cria label mais informativo
        pendentes["label"] = pendentes.apply(lambda r: f'#{int(r["id"])} - {r.get("empresa","N/A")} | {r.get("fornecedor_nome","N/A")} | Venc: {r.get("vencimento","")} | {money(r.get("valor_previsto",0))}', axis=1)
        escolha = st.selectbox("Conta para aprovar", options=pendentes["id"], format_func=lambda x: pendentes.loc[pendentes["id"]==x, "label"].values[0])
        aprovado_por = st.text_input("Aprovado por *")
        data_aprovacao = st.date_input("Data de aprovação", value=datetime.today())
        obs = st.text_area("Observação")
        if st.button("Confirmar Aprovação"):
            insert("aprovacoes", {
                "conta_id": int(escolha), 
                "aprovado_por": aprovado_por or "Diretoria", 
                "data_aprovacao": data_aprovacao.strftime("%Y-%m-%d"), 
                "observacao": obs
            })
            upsert("contas", {"id": int(escolha), "status": "aprovado"})
            st.success("Aprovação registrada e status atualizado para 'aprovado'.")
    
    # Relatório de aprovações com informações detalhadas
    st.subheader("📋 Relatório de Aprovações")
    aprovacoes = fetch_table("aprovacoes", order="criado_em")
    if not aprovacoes.empty:
        # Busca dados das contas relacionadas
        contas_aprovadas = fetch_table("contas")
        fornecedores = fetch_table("fornecedores")
        
        # Cria DataFrame com informações completas
        relatorio_data = []
        for _, aprov in aprovacoes.iterrows():
            conta_rel = contas_aprovadas[contas_aprovadas["id"] == aprov["conta_id"]]
            if not conta_rel.empty:
                conta = conta_rel.iloc[0]
                fornecedor_nome = "N/A"
                if not fornecedores.empty:
                    fornecedor_info = fornecedores[fornecedores["id"] == conta["fornecedor_id"]]
                    if not fornecedor_info.empty:
                        fornecedor_nome = fornecedor_info.iloc[0]["nome"]
                
                relatorio_data.append({
                    "Empresa": conta.get("empresa", "N/A"),
                    "Fornecedor": fornecedor_nome,
                    "Vencimento": conta.get("vencimento", "N/A"),
                    "Valor": money(conta.get("valor_previsto", 0)),
                    "Aprovado por": aprov.get("aprovado_por", "N/A"),
                    "Data aprovação": aprov.get("data_aprovacao", "N/A"),
                    "Observação": aprov.get("observacao", ""),
                    "Criado em": aprov.get("criado_em", "N/A")
                })
        
        if relatorio_data:
            df_relatorio = pd.DataFrame(relatorio_data)
            st.dataframe(df_relatorio, use_container_width=True)
            
            # Seção de exclusão de aprovações
            st.subheader("🗑️ Excluir Aprovação")
            aprovacoes["label"] = aprovacoes.apply(lambda r: f'#{int(r["id"])} - Conta #{r.get("conta_id","N/A")} | Aprovado por: {r.get("aprovado_por","N/A")} | Data: {r.get("data_aprovacao","N/A")}', axis=1)
            
            col1, col2 = st.columns([3, 1])
            with col1:
                aprov_excluir = st.selectbox("Selecione a aprovação para excluir", options=aprovacoes["id"], format_func=lambda x: aprovacoes.loc[aprovacoes["id"]==x, "label"].values[0])
            
            with col2:
                st.write("")  # Espaçamento
                st.write("")  # Espaçamento
                if st.button("🗑️ Excluir Aprovação", type="secondary"):
                    if aprov_excluir:
                        # Busca a conta relacionada para reverter o status
                        aprov_sel = aprovacoes[aprovacoes["id"] == aprov_excluir].iloc[0]
                        conta_id = aprov_sel["conta_id"]
                        
                        # Exclui a aprovação
                        sb.table("aprovacoes").delete().eq("id", int(aprov_excluir)).execute()
                        
                        # Reverte o status da conta para "provisionado"
                        upsert("contas", {"id": int(conta_id), "status": "provisionado"})
                        
                        st.success("Aprovação excluída e status da conta revertido para 'provisionado'!")
                        st.rerun()
        else:
            st.info("Nenhuma aprovação encontrada.")
    else:
        st.info("Nenhuma aprovação registrada ainda.")

elif page == "Pagamentos/Conciliação":
    st.header("Pagamentos e Conciliação de Extrato")
    st.subheader("Registrar Pagamento")
    contas = fetch_table("contas")
    aprovadas = contas[contas["status"].isin(["aprovado","provisionado"])].copy()
    if aprovadas.empty:
        st.info("Não há contas aprovadas/provisionadas para pagar.")
    else:
        # Busca nomes dos fornecedores
        fornecedores = fetch_table("fornecedores")
        if not fornecedores.empty:
            fornecedor_map = dict(zip(fornecedores["id"], fornecedores["nome"]))
            aprovadas["fornecedor_nome"] = aprovadas["fornecedor_id"].map(fornecedor_map)
        
        # Cria label mais informativo com empresa, fornecedor, vencimento e valor
        aprovadas["label"] = aprovadas.apply(lambda r: f'#{int(r["id"])} - {r.get("empresa","N/A")} | {r.get("fornecedor_nome","N/A")} | Venc: {r.get("vencimento","")} | {money(r.get("valor_previsto",0))}', axis=1)
        escolha = st.selectbox("Conta a pagar", options=aprovadas["id"], format_func=lambda x: aprovadas.loc[aprovadas["id"]==x, "label"].values[0])
        data_pag = st.date_input("Data do pagamento", value=datetime.today())
        valor_pago = st.text_input("Valor pago (ex: 1234,56) *")
        forma = st.selectbox("Forma de pagamento", ["TED", "PIX", "Boleto", "Cartão", "Dinheiro", "Outro"], index=1)
        if st.button("Registrar Pagamento"):
            vp = to_float(valor_pago)
            if vp is None:
                st.error("Valor inválido.")
            else:
                insert("pagamentos", {"conta_id": int(escolha), "data_pagamento": data_pag.strftime("%Y-%m-%d"), "valor_pago": vp, "forma_pagamento": forma})
                upsert("contas", {"id": int(escolha), "status": "pago"})
                st.success("Pagamento registrado e conta marcada como 'pago'.")
    st.subheader("Importar Extrato (CSV)")
    up = st.file_uploader("Envie um CSV com colunas: data, historico, valor (negativo = saída)", type=["csv"])
    if up is not None:
        # Tenta diferentes codificações e delimitadores
        df_csv = None
        for encoding in ['utf-8', 'latin-1', 'cp1252']:
            for sep in [';', ',', '\t']:  # Ponto e vírgula primeiro (formato brasileiro)
                try:
                    df_csv = pd.read_csv(up, encoding=encoding, sep=sep, header=0)
                    if df_csv is not None and len(df_csv.columns) >= 3:  # Verifica se tem pelo menos 3 colunas
                        st.info(f"✅ Arquivo lido com sucesso! Encoding: {encoding}, Delimitador: '{sep}', Colunas: {len(df_csv.columns)}")
                        break  # Sai do loop de delimitadores se conseguir ler
                except (UnicodeDecodeError, pd.errors.ParserError):
                    continue  # Tenta a próxima combinação
            if df_csv is not None:  # Se df foi lido com sucesso, sai do loop de encodings
                break
        if df_csv is None:  # Se não conseguiu ler com nenhuma combinação
            st.error("Não foi possível ler o arquivo CSV com as codificações e delimitadores testados.")
        else:
            # Mapeia colunas com variações de nomes
            cols = {c.lower().strip(): c for c in df_csv.columns}
            col_mapping = {}
            
            # Mapeia colunas obrigatórias com variações
            variations = {
                "data": ["data", "date", "dt", "data_movimento", "data_mov", "data_transacao"],
                "historico": ["historico", "histórico", "history", "descricao", "descrição", "description", "desc", "detalhes", "obs", "observacao", "observação"],
                "valor": ["valor", "value", "vlr", "amount", "montante", "total", "preco", "preço"]
            }
            
            # Primeiro tenta mapeamento exato
            for col_type, possible_names in variations.items():
                found = False
                for name in possible_names:
                    if name in cols:
                        col_mapping[col_type] = cols[name]
                        found = True
                        break
                if not found:
                    # Tenta busca parcial (apenas se não encontrou exato)
                    for col in cols.keys():
                        if any(partial in col for partial in possible_names):
                            col_mapping[col_type] = cols[col]
                            found = True
                            break
            
            # Se ainda não encontrou todas as colunas, tenta mapeamento por posição
            if len(col_mapping) < 3:
                st.warning("⚠️ Mapeamento automático falhou. Tentando mapeamento por posição...")
                col_names = list(df_csv.columns)
                if len(col_names) >= 3:
                    col_mapping = {
                        "data": col_names[0],      # Primeira coluna = data
                        "historico": col_names[1], # Segunda coluna = historico  
                        "valor": col_names[2]      # Terceira coluna = valor
                    }
                    st.info(f"📋 Mapeamento por posição: data='{col_names[0]}', historico='{col_names[1]}', valor='{col_names[2]}'")
            
            # Debug: Mostra o mapeamento encontrado
            st.write("🔍 **Debug - Mapeamento de colunas:**")
            for key, value in col_mapping.items():
                st.write(f"- {key}: '{value}'")
            
            # Debug: Mostra as primeiras linhas do CSV original
            st.write("🔍 **Debug - Primeiras 3 linhas do CSV original:**")
            st.write(df_csv.head(3))
            
            # Mostra o mapeamento encontrado
            st.write("**Mapeamento de colunas encontrado:**")
            for col_type, col_name in col_mapping.items():
                st.write(f"- {col_type}: '{col_name}'")
            
            if len(col_mapping) == 3:
                try:
                    df_csv_norm = pd.DataFrame({
                        "data": pd.to_datetime(df_csv[col_mapping["data"]], errors="coerce", dayfirst=True).dt.date, 
                        "historico": df_csv[col_mapping["historico"]].astype(str), 
                        "valor": df_csv[col_mapping["valor"]].apply(to_float)
                    }).dropna(subset=["data","valor"])
                    
                    # Mostra estatísticas dos valores encontrados
                    st.info(f"📊 Estatísticas do arquivo: {len(df_csv_norm)} linhas processadas")
                    st.info(f"💰 Valores encontrados: Min: {df_csv_norm['valor'].min():.2f}, Max: {df_csv_norm['valor'].max():.2f}")
                    
                    # Debug: Mostra alguns valores para análise
                    st.write("🔍 **Debug - Primeiros 5 valores encontrados:**")
                    st.write(df_csv_norm[['data', 'historico', 'valor']].head())
                    
                    # Conta valores negativos e positivos
                    negativos = df_csv_norm[df_csv_norm['valor'] < 0]
                    positivos = df_csv_norm[df_csv_norm['valor'] > 0]
                    st.info(f"📈 Valores negativos: {len(negativos)} | Valores positivos: {len(positivos)}")
                    
                    # Filtra apenas valores negativos (saídas)
                    df_csv_norm = df_csv_norm[df_csv_norm["valor"] < 0]
                    
                    if not df_csv_norm.empty:
                        for _, r in df_csv_norm.iterrows():
                            insert("extrato", {"data": str(r["data"]), "historico": r["historico"], "valor": float(r["valor"])})
                        st.success(f"✅ {len(df_csv_norm)} movimentações de saída importadas para 'extrato'.")
                    else:
                        st.warning("⚠️ Nenhuma movimentação de saída encontrada no arquivo.")
                        st.info("💡 Dica: O sistema procura por valores negativos. Verifique se os valores de saída estão com sinal negativo.")
                        
                except Exception as e:
                    st.error(f"Erro ao processar o arquivo: {str(e)}")
            else:
                missing = [col for col in ["data", "historico", "valor"] if col not in col_mapping]
                st.error(f"❌ Colunas obrigatórias não encontradas: {', '.join(missing)}")
                st.write("**Colunas disponíveis no arquivo:**", list(df_csv.columns))
                st.write("**Tentativas de mapeamento:**", col_mapping)
    st.subheader("Conciliação automática (valor + data ±3 dias)")
    extrato = fetch_table("extrato", order="data")
    to_match = extrato.copy()
    contas_df = fetch_table("contas")
    
    # Sempre mostra os filtros, mesmo sem dados
    st.write("**Filtros para Conciliação:**")
    col1, col2 = st.columns(2)
    
    # Filtro por empresa
    empresas_disponiveis = contas_df["empresa"].dropna().unique().tolist() if not contas_df.empty else []
    if empresas_disponiveis:
        empresa_filtro = col1.selectbox("Filtrar por Empresa", ["Todas"] + empresas_disponiveis)
    else:
        empresa_filtro = "Todas"
        col1.info("Nenhuma empresa encontrada")
    
    # Filtro por fornecedor
    fornecedores = fetch_table("fornecedores")
    if not fornecedores.empty:
        fornecedor_map = dict(zip(fornecedores["id"], fornecedores["nome"]))
        contas_df["fornecedor_nome"] = contas_df["fornecedor_id"].map(fornecedor_map)
        fornecedores_disponiveis = contas_df["fornecedor_nome"].dropna().unique().tolist()
        if fornecedores_disponiveis:
            fornecedor_filtro = col2.selectbox("Filtrar por Fornecedor", ["Todos"] + fornecedores_disponiveis)
        else:
            fornecedor_filtro = "Todos"
            col2.info("Nenhum fornecedor encontrado")
    else:
        fornecedor_filtro = "Todos"
        col2.info("Nenhum fornecedor encontrado")
    
    janela = st.slider("Janela de dias para casar data", 0, 10, 3)
    
    # Mostra informações sobre os critérios de conciliação
    st.info(f"🔍 **Critérios de Conciliação:**")
    st.info(f"• **Tolerância de valor:** R$ 0,01 (1 centavo)")
    st.info(f"• **Tolerância de data:** {janela + 2} dias (janela + 2 dias extras)")
    st.info(f"• **Prioridade:** Data primeiro, depois valor")
    
    if not to_match.empty:
        # Aplica filtros
        candidatos = contas_df[contas_df["status"].isin(["aprovado","provisionado"])].copy()
        
        # Filtro por empresa
        if empresa_filtro != "Todas":
            candidatos = candidatos[candidatos["empresa"] == empresa_filtro]
        
        # Filtro por fornecedor
        if fornecedor_filtro != "Todos":
            candidatos = candidatos[candidatos["fornecedor_nome"] == fornecedor_filtro]
        
        # Mostra quantas contas estão sendo consideradas
        st.info(f"🔍 Considerando {len(candidatos)} contas para conciliação (Empresa: {empresa_filtro}, Fornecedor: {fornecedor_filtro})")
        
        for col in ["vencimento","competencia"]:
            if col in candidatos.columns:
                try: candidatos[col] = pd.to_datetime(candidatos[col]).dt.date
                except: pass
        if "valor_previsto" in candidatos.columns:
            candidatos["valor_previsto"] = candidatos["valor_previsto"].astype(float)
        
        matches = []
        for _, mov in to_match.iterrows():
            val = float(mov.get("valor", 0))
            if val >= 0: continue
            alvo = abs(val)
            
            # Calcula diferenças de valor e data
            candidatos["diff_valor"] = (candidatos["valor_previsto"] - alvo).abs()
            candidatos["diff_data"] = candidatos["vencimento"].apply(lambda d: abs((pd.to_datetime(d) - pd.to_datetime(mov["data"])).days) if pd.notnull(d) else 9999)
            
            # Critérios mais flexíveis para conciliação
            tolerancia_valor = 0.01  # 1 centavo de tolerância
            tolerancia_data = janela + 2  # Janela + 2 dias extras
            
            # Filtra candidatos que atendem aos critérios
            candidatos_validos = candidatos[
                (candidatos["diff_valor"] <= tolerancia_valor) & 
                (candidatos["diff_data"] <= tolerancia_data)
            ].copy()
            
            if not candidatos_validos.empty:
                # Ordena por proximidade de data primeiro, depois por valor
                candidatos_validos = candidatos_validos.sort_values(["diff_data", "diff_valor"])
                
                # Pega o melhor candidato
                melhor = candidatos_validos.iloc[0]
                
                matches.append({
                    "extrato_id": mov["id"], 
                    "extrato_data": mov["data"], 
                    "extrato_hist": mov.get("historico",""), 
                    "extrato_valor": val, 
                    "conta_id": melhor["id"], 
                    "conta_empresa": melhor.get("empresa", "N/A"),
                    "conta_fornecedor": melhor.get("fornecedor_nome", "N/A"),
                    "conta_desc": melhor.get("descricao",""), 
                    "conta_venc": melhor.get("vencimento",""), 
                    "conta_valor": melhor.get("valor_previsto",0.0), 
                    "diff_valor": melhor["diff_valor"], 
                    "diff_data": melhor["diff_data"]
                })
        
        if matches:
            df_match = pd.DataFrame(matches)
            
            # Mostra informações dos matches encontrados
            st.write(f"**📊 Encontrados {len(df_match)} possíveis conciliações:**")
            
            # Reorganiza colunas para melhor visualização
            colunas_exibir = ["extrato_id", "extrato_data", "extrato_hist", "extrato_valor", 
                            "conta_id", "conta_empresa", "conta_fornecedor", "conta_desc", 
                            "conta_venc", "conta_valor", "diff_valor", "diff_data"]
            
            # Renomeia colunas para exibição
            df_exibir = df_match[colunas_exibir].copy()
            df_exibir.columns = ["ID Extrato", "Data Extrato", "Histórico", "Valor Extrato", 
                               "ID Conta", "Empresa", "Fornecedor", "Descrição", 
                               "Vencimento", "Valor Conta", "Diferença Valor", "Diferença Dias"]
            
            # Formata valores monetários
            df_exibir["Valor Extrato"] = df_exibir["Valor Extrato"].apply(lambda x: money(abs(x)))
            df_exibir["Valor Conta"] = df_exibir["Valor Conta"].apply(money)
            df_exibir["Diferença Valor"] = df_exibir["Diferença Valor"].apply(money)
            
            st.dataframe(df_exibir.head(30), use_container_width=True)
            
            if st.button("Confirmar conciliação para o melhor match por movimento"):
                best = df_match.sort_values(["extrato_id","diff_valor","diff_data"]).drop_duplicates("extrato_id", keep="first")
                count = 0
                for _, row in best.iterrows():
                    insert("pagamentos", {"conta_id": int(row["conta_id"]), "data_pagamento": str(row["extrato_data"]), "valor_pago": float(abs(row["extrato_valor"])), "forma_pagamento": "Extrato/Conciliação", "conciliado": True})
                    upsert("contas", {"id": int(row["conta_id"]), "status": "pago"})
                    count += 1
                st.success(f"Conciliação registrada para {count} movimentações.")
        else:
            st.info("Nenhum candidato para conciliação automática no momento com os filtros aplicados.")
    else:
        st.info("Importe um extrato para conciliar.")
    
    st.subheader("🗑️ Excluir Contas")
    st.write("**Atenção:** Esta ação excluirá permanentemente a conta e todos os registros relacionados (aprovacoes, pagamentos).")
    
    # Opção para excluir todas as contas
    st.write("**⚠️ Exclusão em Massa:**")
    col_excluir_todas, col_cancelar = st.columns([1, 1])
    
    with col_excluir_todas:
        if st.button("🗑️ EXCLUIR TODAS AS CONTAS", type="secondary", help="Esta ação excluirá TODAS as contas do sistema"):
            if st.session_state.get('confirm_delete_all', False):
                # Confirmação dupla
                todas_contas = fetch_table("contas")
                if not todas_contas.empty:
                    # Exclui todas as aprovações
                    sb.table("aprovacoes").delete().neq("id", 0).execute()
                    # Exclui todos os pagamentos
                    sb.table("pagamentos").delete().neq("id", 0).execute()
                    # Exclui todas as contas
                    sb.table("contas").delete().neq("id", 0).execute()
                    st.success(f"✅ {len(todas_contas)} contas excluídas com sucesso!")
                    st.session_state['confirm_delete_all'] = False
                    st.rerun()
                else:
                    st.info("Nenhuma conta encontrada para excluir.")
            else:
                st.session_state['confirm_delete_all'] = True
                st.warning("⚠️ Clique novamente para confirmar a exclusão de TODAS as contas!")
    
    with col_cancelar:
        if st.session_state.get('confirm_delete_all', False):
            if st.button("❌ Cancelar Exclusão"):
                st.session_state['confirm_delete_all'] = False
                st.rerun()
    
    if st.session_state.get('confirm_delete_all', False):
        st.error("⚠️ **CONFIRMAÇÃO NECESSÁRIA:** Clique novamente em 'EXCLUIR TODAS AS CONTAS' para confirmar!")
    
    st.write("---")
    st.write("**🔍 Exclusão Individual:**")
    
    # Busca contas para exclusão
    todas_contas = fetch_table("contas", order="criado_em")
    if not todas_contas.empty:
        # Mostra apenas contas pagas ou aprovadas
        contas_excluir = todas_contas[todas_contas["status"].isin(["pago", "aprovado"])].copy()
        
        if not contas_excluir.empty:
            contas_excluir["label"] = contas_excluir.apply(lambda r: f'#{int(r["id"])} - {r.get("descricao","")} / Venc.: {r.get("vencimento","")} / Prev.: {money(r.get("valor_previsto",0))} / Status: {r.get("status","")}', axis=1)
            
            col1, col2 = st.columns([3, 1])
            with col1:
                conta_excluir = st.selectbox("Selecione a conta para excluir", options=contas_excluir["id"], format_func=lambda x: contas_excluir.loc[contas_excluir["id"]==x, "label"].values[0])
            
            with col2:
                st.write("")  # Espaçamento
                st.write("")  # Espaçamento
                if st.button("🗑️ Excluir Conta", type="secondary"):
                    if conta_excluir:
                        # Confirmação adicional
                        if st.session_state.get('confirm_delete', False):
                            result = delete_conta(int(conta_excluir))
                            if result:
                                st.success(f"Conta #{conta_excluir} excluída com sucesso!")
                                st.session_state['confirm_delete'] = False
                                st.rerun()
                        else:
                            st.session_state['confirm_delete'] = True
                            st.warning("⚠️ Clique novamente para confirmar a exclusão!")
                    else:
                        st.error("Selecione uma conta para excluir.")
            
            # Mostra detalhes da conta selecionada
            if conta_excluir:
                conta_detalhes = contas_excluir[contas_excluir["id"] == conta_excluir].iloc[0]
                
                st.write("**Detalhes da Conta Selecionada:**")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.write(f"**ID:** #{int(conta_detalhes['id'])}")
                    st.write(f"**Status:** {conta_detalhes['status']}")
                    st.write(f"**Valor:** {money(conta_detalhes['valor_previsto'])}")
                with col2:
                    st.write(f"**Vencimento:** {conta_detalhes['vencimento']}")
                    st.write(f"**Competência:** {conta_detalhes['competencia']}")
                    st.write(f"**Descrição:** {conta_detalhes.get('descricao', 'N/A')}")
                with col3:
                    # Busca fornecedor e categoria
                    fornecedor = fetch_table("fornecedores", eq={"id": conta_detalhes['fornecedor_id']})
                    categoria = fetch_table("categorias", eq={"id": conta_detalhes['categoria_id']})
                    st.write(f"**Fornecedor:** {fornecedor.iloc[0]['nome'] if not fornecedor.empty else 'N/A'}")
                    st.write(f"**Categoria:** {categoria.iloc[0]['nome'] if not categoria.empty else 'N/A'}")
                
                # Mostra pagamentos relacionados
                pagamentos_conta = fetch_table("pagamentos", eq={"conta_id": conta_excluir})
                if not pagamentos_conta.empty:
                    st.write("**Pagamentos Relacionados:**")
                    for _, pag in pagamentos_conta.iterrows():
                        st.write(f"- {pag['data_pagamento']} | {money(pag['valor_pago'])} | {pag['forma_pagamento']}")
                
                # Mostra aprovações relacionadas
                aprovacoes_conta = fetch_table("aprovacoes", eq={"conta_id": conta_excluir})
                if not aprovacoes_conta.empty:
                    st.write("**Aprovações Relacionadas:**")
                    for _, apr in aprovacoes_conta.iterrows():
                        st.write(f"- {apr['data_aprovacao']} | Aprovado por: {apr['aprovado_por']}")
                        if apr.get('observacao'):
                            st.write(f"  Observação: {apr['observacao']}")
        else:
            st.info("Não há contas pagas ou aprovadas para excluir.")
    else:
        st.info("Não há contas cadastradas.")

elif page == "Dashboard":
    st.title("📊 Dashboard Executivo")
    st.markdown("---")
    
    contas = fetch_table("contas")
    pagamentos = fetch_table("pagamentos")
    categorias = fetch_table("categorias")
    
    if contas.empty:
        st.info("📭 Nenhuma conta encontrada.")
    else:
        contas["vencimento"] = pd.to_datetime(contas["vencimento"], errors="coerce")
        contas["competencia"] = pd.to_datetime(contas["competencia"], errors="coerce")
        contas["valor_previsto"] = pd.to_numeric(contas["valor_previsto"], errors="coerce").fillna(0.0)
        
        total_previsto = contas["valor_previsto"].sum()
        contas_pagas = contas[contas["status"] == "pago"]
        total_pago = contas_pagas["valor_previsto"].sum()
        em_aberto = contas[~contas["status"].isin(["pago","cancelado"])]["valor_previsto"].sum()
        
        # Percentual pago
        percentual_pago = (total_pago / total_previsto * 100) if total_previsto > 0 else 0
        
        # Métricas principais com design melhorado
        st.subheader("💰 Resumo Financeiro")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="💵 Total Previsto",
                value=money(total_previsto),
                help="Valor total de todas as contas cadastradas"
            )
        
        with col2:
            st.metric(
                label="✅ Total Pago",
                value=money(total_pago),
                delta=f"{percentual_pago:.1f}%",
                delta_color="normal",
                help="Valor total das contas já pagas"
            )
        
        with col3:
            st.metric(
                label="⏳ Em Aberto",
                value=money(em_aberto),
                delta=f"{100-percentual_pago:.1f}%",
                delta_color="inverse",
                help="Valor total das contas pendentes"
            )
        
        with col4:
            st.metric(
                label="📊 Total de Contas",
                value=f"{len(contas)}",
                help="Número total de contas cadastradas"
            )
        
        # Barra de progresso
        st.markdown("### 📈 Progresso de Pagamentos")
        progress = percentual_pago / 100
        st.progress(progress)
        st.caption(f"**{percentual_pago:.1f}%** das contas foram pagas")
        
        # Gráficos em duas colunas
        col_graf1, col_graf2 = st.columns(2)
        
        with col_graf1:
            st.markdown("### 📊 Status das Contas")
            status_counts = contas["status"].value_counts()
            
            # Cores personalizadas para cada status
            cores_status = {
                'provisionado': '#FF6B6B',
                'aprovado': '#4ECDC4', 
                'pago': '#45B7D1',
                'vencido': '#96CEB4',
                'cancelado': '#FFEAA7'
            }
            
            fig1, ax1 = plt.subplots(figsize=(8, 6))
            wedges, texts, autotexts = ax1.pie(
                status_counts.values, 
                labels=status_counts.index,
                autopct='%1.1f%%', 
                startangle=90,
                colors=[cores_status.get(status, '#95A5A6') for status in status_counts.index],
                explode=[0.05] * len(status_counts)
            )
            
            # Melhorar aparência dos textos
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontweight('bold')
                autotext.set_fontsize(10)
            
            ax1.set_title("Distribuição por Status", fontsize=14, fontweight='bold', pad=20)
            plt.tight_layout()
            st.pyplot(fig1)
        
        with col_graf2:
            st.markdown("### 📅 Contas por Mês")
            hoje = pd.Timestamp.today().normalize()
            futuro_6m = hoje + relativedelta(months=6)
            mask = (contas["vencimento"] >= hoje) & (contas["vencimento"] <= futuro_6m)
            por_mes = contas.loc[mask].copy()
            
            if not por_mes.empty:
                por_mes["ano_mes"] = por_mes["vencimento"].dt.to_period("M").astype(str)
                s = por_mes.groupby("ano_mes")["valor_previsto"].sum().sort_index()
                
                fig2, ax2 = plt.subplots(figsize=(8, 6))
                bars = ax2.bar(range(len(s)), s.values, 
                              color='#3498DB', alpha=0.8, edgecolor='#2980B9', linewidth=2)
                
                # Adicionar valores nas barras
                for i, bar in enumerate(bars):
                    height = bar.get_height()
                    ax2.text(bar.get_x() + bar.get_width()/2., height + height*0.01,
                            f'R$ {height:,.0f}'.replace(',', '.'),
                            ha='center', va='bottom', fontweight='bold')
                
                ax2.set_xlabel('Mês', fontweight='bold')
                ax2.set_ylabel('Valor (R$)', fontweight='bold')
                ax2.set_title('Evolução dos Gastos por Mês', fontsize=14, fontweight='bold', pad=20)
                ax2.set_xticks(range(len(s)))
                ax2.set_xticklabels(s.index, rotation=45)
                ax2.grid(True, alpha=0.3)
                plt.tight_layout()
                st.pyplot(fig2)
        
        # Gráfico de gastos por categoria
        st.markdown("### 🏷️ Gastos por Categoria (Últimos 90 dias)")
        ult_90 = hoje - pd.Timedelta(days=90)
        recorte = contas[(contas["vencimento"] >= ult_90) & (contas["vencimento"] <= hoje)].copy()
        
        if not recorte.empty:
            s2 = recorte.groupby("categoria_id")["valor_previsto"].sum().sort_values(ascending=True)
            if not categorias.empty:
                cat_map = dict(zip(categorias["id"], categorias["nome"]))
                s2.index = s2.index.map(lambda i: cat_map.get(i, f"Cat {i}"))
                
                fig3, ax3 = plt.subplots(figsize=(10, 6))
                bars = ax3.barh(s2.index, s2.values, color='#E74C3C', alpha=0.8, edgecolor='#C0392B', linewidth=1)
                
                # Adicionar valores nas barras
                for i, bar in enumerate(bars):
                    width = bar.get_width()
                    ax3.text(width + width*0.01, bar.get_y() + bar.get_height()/2,
                            f'R$ {width:,.0f}'.replace(',', '.'),
                            ha='left', va='center', fontweight='bold')
                
                ax3.set_xlabel('Valor (R$)', fontweight='bold')
                ax3.set_title('Gastos por Categoria (90 dias)', fontsize=14, fontweight='bold', pad=20)
                ax3.grid(True, alpha=0.3, axis='x')
                plt.tight_layout()
                st.pyplot(fig3)
        
        # Cards informativos
        st.markdown("### 📋 Resumo Detalhado")
        
        col_info1, col_info2, col_info3 = st.columns(3)
        
        with col_info1:
            st.markdown("""
            <div style="background-color: #E8F5E8; padding: 20px; border-radius: 10px; border-left: 5px solid #27AE60;">
                <h4 style="color: #27AE60; margin: 0;">✅ Contas Pagas</h4>
                <p style="margin: 5px 0; font-size: 18px; font-weight: bold; color: #27AE60;">{}</p>
                <p style="margin: 0; color: #666;">{} contas</p>
            </div>
            """.format(money(total_pago), len(contas_pagas)), unsafe_allow_html=True)
        
        with col_info2:
            vencidas = contas[(contas["vencimento"] < hoje) & (~contas["status"].isin(["pago","cancelado"]))]
            st.markdown("""
            <div style="background-color: #FDF2E9; padding: 20px; border-radius: 10px; border-left: 5px solid #E67E22;">
                <h4 style="color: #E67E22; margin: 0;">⚠️ Contas Vencidas</h4>
                <p style="margin: 5px 0; font-size: 18px; font-weight: bold; color: #E67E22;">{}</p>
                <p style="margin: 0; color: #666;">{} contas</p>
            </div>
            """.format(money(vencidas["valor_previsto"].sum()), len(vencidas)), unsafe_allow_html=True)
        
        with col_info3:
            contas_aprovadas = contas[contas["status"] == "aprovado"]
            st.markdown("""
            <div style="background-color: #EBF3FD; padding: 20px; border-radius: 10px; border-left: 5px solid #3498DB;">
                <h4 style="color: #3498DB; margin: 0;">📋 Aguardando Pagamento</h4>
                <p style="margin: 5px 0; font-size: 18px; font-weight: bold; color: #3498DB;">{}</p>
                <p style="margin: 0; color: #666;">{} contas</p>
            </div>
            """.format(money(contas_aprovadas["valor_previsto"].sum()), len(contas_aprovadas)), unsafe_allow_html=True)
        
        # Tabela de contas vencidas
        if not vencidas.empty:
            st.markdown("### ⚠️ Contas Vencidas - Ação Necessária")
            st.dataframe(
                vencidas[["id","descricao","vencimento","valor_previsto","status"]], 
                use_container_width=True,
                column_config={
                    "id": "ID",
                    "descricao": "Descrição",
                    "vencimento": "Vencimento",
                    "valor_previsto": st.column_config.NumberColumn("Valor", format="R$ %.2f"),
                    "status": "Status"
                }
            )

elif page == "Gerenciar Usuários":
    st.header("👥 Gerenciamento de Usuários")
    
    # Verificar se é admin
    if st.session_state.get('username') != 'admin':
        st.error("❌ Apenas o usuário 'admin' pode gerenciar usuários!")
        st.stop()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("➕ Adicionar Novo Usuário")
        with st.form("add_user_form"):
            new_username = st.text_input("👤 Nome do Usuário", placeholder="Digite o nome do usuário")
            new_password = st.text_input("🔒 Senha", type="password", placeholder="Digite a senha")
            confirm_password = st.text_input("🔒 Confirmar Senha", type="password", placeholder="Confirme a senha")
            
            if st.form_submit_button("➕ Adicionar Usuário", use_container_width=True):
                if not new_username or not new_password:
                    st.error("❌ Preencha todos os campos!")
                elif new_password != confirm_password:
                    st.error("❌ As senhas não coincidem!")
                elif new_username in list_users():
                    st.error("❌ Usuário já existe!")
                else:
                    add_user(new_username, new_password)
                    st.success(f"✅ Usuário '{new_username}' adicionado com sucesso!")
                    st.rerun()
    
    with col2:
        st.subheader("🗑️ Remover Usuário")
        users = list_users()
        if len(users) > 1:  # Se há mais de um usuário
            user_to_remove = st.selectbox("Selecione o usuário para remover", 
                                        options=[u for u in users if u != 'admin'])
            
            if st.button("🗑️ Remover Usuário", type="secondary", use_container_width=True):
                if user_to_remove and user_to_remove != 'admin':
                    remove_user(user_to_remove)
                    st.success(f"✅ Usuário '{user_to_remove}' removido com sucesso!")
                    st.rerun()
        else:
            st.info("ℹ️ Não há usuários para remover (mínimo de 1 usuário)")
    
    st.markdown("---")
    st.subheader("📋 Lista de Usuários Cadastrados")
    users = list_users()
    
    if users:
        for i, user in enumerate(users, 1):
            col_user, col_type = st.columns([3, 1])
            with col_user:
                st.write(f"{i}. **{user}**")
            with col_type:
                if user == 'admin':
                    st.markdown("**👑 Administrador**")
                else:
                    st.markdown("**👤 Usuário**")
    else:
        st.info("ℹ️ Nenhum usuário cadastrado")
    
    st.markdown("---")
    st.info("💡 **Dica:** O usuário 'admin' não pode ser removido e tem acesso total ao sistema.")

elif page == "ETL/Importação":
    st.header("Importação de Planilha (XLSX/CSV) → contas")
    st.write("**Formato mínimo:** fornecedor, categoria, descricao, vencimento (AAAA-MM-DD), valor_previsto")
    st.write("**Campos opcionais:** empresa, cnpj, numero_documento")
    st.info("💡 **Dica:** A competência será calculada automaticamente como o primeiro dia do mês de vencimento.")
    up = st.file_uploader("Envie XLSX ou CSV", type=["xlsx","csv"])
    if up is not None:
        try:
            import pandas as pd
            if up.name.lower().endswith(".xlsx"): 
                df = pd.read_excel(up)
            else: 
                # Tenta diferentes codificações e delimitadores
                df = None
                used_encoding = None
                used_sep = None
                
                # Primeiro tenta com ponto e vírgula (mais comum em CSVs brasileiros)
                for encoding in ['utf-8', 'latin-1', 'cp1252']:
                    for sep in [';', ',', '\t']:
                        try:
                            # Reset do ponteiro do arquivo para cada tentativa
                            up.seek(0)
                            
                            # Tenta ler o CSV
                            temp_df = pd.read_csv(up, encoding=encoding, sep=sep, header=0)
                            
                            # Verifica se conseguiu separar em múltiplas colunas
                            if len(temp_df.columns) >= 3:  # Pelo menos 3 colunas
                                # Verifica se as colunas fazem sentido
                                if not any("Sem nome" in str(col) or "Unnamed" in str(col) for col in temp_df.columns):
                                    df = temp_df
                                    used_encoding = encoding
                                    used_sep = sep
                                    break
                        except (UnicodeDecodeError, pd.errors.ParserError, Exception):
                            continue  # Tenta a próxima combinação
                    if df is not None:  # Se df foi lido com sucesso, sai do loop de encodings
                        break
                if df is None:  # Se não conseguiu ler com nenhuma combinação
                    raise Exception("Não foi possível ler o arquivo CSV com as codificações e delimitadores testados.")
                
                # Mostra informações sobre a leitura
                st.info(f"✅ Arquivo lido com sucesso! Codificação: {used_encoding}, Delimitador: '{used_sep}'")
                
                # Mostra as primeiras linhas para debug
                st.write("**Primeiras 3 linhas do arquivo:**")
                st.write(df.head(3))
                
                # Debug: Mostra informações sobre o DataFrame
                st.write(f"**Debug - Shape do DataFrame:** {df.shape}")
                st.write(f"**Debug - Colunas detectadas:** {list(df.columns)}")
                st.write(f"**Debug - Tipos de dados:** {df.dtypes.to_dict()}")
                
            req = ["fornecedor","categoria","descricao","vencimento","valor_previsto"]
            opt = ["empresa","cnpj","numero_documento"]
            
            # Mostra as colunas encontradas para debug
            st.write("**Colunas encontradas no arquivo:**")
            st.write(list(df.columns))
            
            # Mapeia colunas com variações de nomes (remove acentos e converte para minúsculo)
            import unicodedata
            def remove_accents(text):
                return unicodedata.normalize('NFD', text).encode('ascii', 'ignore').decode('ascii')
            
            # Cria mapeamento normalizado (sem acentos, minúsculo)
            normalized_cols = {}
            for col in df.columns:
                normalized = remove_accents(col.lower().strip())
                normalized_cols[normalized] = col
            
            col_mapping = {}
            
            # Mapeia colunas obrigatórias com variações
            for req_col in req:
                found = False
                req_normalized = remove_accents(req_col.lower())
                
                # Primeiro tenta correspondência exata
                if req_normalized in normalized_cols:
                    col_mapping[req_col] = normalized_cols[req_normalized]
                    found = True
                else:
                    # Tenta correspondência parcial
                    for norm_col, orig_col in normalized_cols.items():
                        if req_normalized in norm_col or norm_col in req_normalized:
                            col_mapping[req_col] = orig_col
                            found = True
                            break
                
                if not found:
                    # Tenta variações específicas
                    variations = {
                        "fornecedor": ["fornecedor", "fornecedores", "supplier", "provedor"],
                        "categoria": ["categoria", "categorias", "category", "tipo"],
                        "descricao": ["descricao", "descricao", "description", "desc", "detalhes"],
                        "competencia": ["competencia", "competencia", "compet", "mes_competencia", "periodo"],
                        "vencimento": ["vencimento", "venc", "data_vencimento", "due_date", "vencto"],
                        "valor_previsto": ["valor_previsto", "valor", "vlr_previsto", "amount", "preco", "preco"]
                    }
                    for variation in variations.get(req_col, []):
                        variation_normalized = remove_accents(variation.lower())
                        if variation_normalized in normalized_cols:
                            col_mapping[req_col] = normalized_cols[variation_normalized]
                            found = True
                            break
            
            # Mapeia colunas opcionais
            for opt_col in opt:
                opt_normalized = remove_accents(opt_col.lower())
                if opt_normalized in normalized_cols:
                    col_mapping[opt_col] = normalized_cols[opt_normalized]
                else:
                    for norm_col, orig_col in normalized_cols.items():
                        if opt_normalized in norm_col or norm_col in opt_normalized:
                            col_mapping[opt_col] = orig_col
                            break
            
            # Debug: Mostra o mapeamento encontrado
            st.write("**🔍 Mapeamento de colunas encontrado:**")
            for key, value in col_mapping.items():
                st.write(f"- {key}: '{value}'")
            
            if not all(c in col_mapping for c in req):
                missing = [c for c in req if c not in col_mapping]
                st.error(f"❌ Colunas obrigatórias não encontradas: {', '.join(missing)}")
                st.write("**Colunas disponíveis no arquivo:**", list(df.columns))
                st.write("**Colunas normalizadas:**", list(normalized_cols.keys()))
            else:
                inserted = 0
                for _, r in df.iterrows():
                    # Busca CNPJ se disponível
                    cnpj_val = str(r[col_mapping["cnpj"]]) if "cnpj" in col_mapping and pd.notna(r[col_mapping["cnpj"]]) else None
                    fornecedor_id = ensure_fornecedor(str(r[col_mapping["fornecedor"]]), cnpj=cnpj_val)
                    categoria_id = ensure_categoria(str(r[col_mapping["categoria"]]))
                    
                    # Prepara dados da conta
                    vencimento_date = pd.to_datetime(r[col_mapping["vencimento"]], errors="coerce", dayfirst=True).date()
                    # Usa a data de vencimento como competência (primeiro dia do mês)
                    competencia_date = vencimento_date.replace(day=1) if vencimento_date else None
                    
                    # Limpa o valor monetário (formato brasileiro)
                    valor_str = str(r[col_mapping["valor_previsto"]])
                    # Remove R$, espaços e caracteres especiais
                    valor_limpo = valor_str.replace("R$", "").replace(" ", "").strip()
                    
                    # Trata formato brasileiro: 1.234,56 -> 1234.56
                    if '.' in valor_limpo and ',' in valor_limpo:
                        # Formato: 1.234,56 (ponto como milhares, vírgula como decimal)
                        valor_limpo = valor_limpo.replace(".", "").replace(",", ".")
                    elif ',' in valor_limpo:
                        # Formato: 1234,56 (apenas vírgula como decimal)
                        valor_limpo = valor_limpo.replace(",", ".")
                    
                    try:
                        valor_float = float(valor_limpo)
                    except ValueError:
                        st.error(f"Erro ao converter valor: '{valor_str}' -> '{valor_limpo}'")
                        continue
                    
                    conta_data = {
                        "fornecedor_id": fornecedor_id, 
                        "categoria_id": categoria_id, 
                        "descricao": str(r[col_mapping["descricao"]]), 
                        "competencia": str(competencia_date), 
                        "vencimento": str(vencimento_date), 
                        "valor_previsto": valor_float, 
                        "status": "provisionado"
                    }
                    
                    # Adiciona campos opcionais se disponíveis
                    if "empresa" in col_mapping and pd.notna(r[col_mapping["empresa"]]):
                        conta_data["empresa"] = str(r[col_mapping["empresa"]])
                    if "numero_documento" in col_mapping and pd.notna(r[col_mapping["numero_documento"]]):
                        conta_data["numero_documento"] = str(r[col_mapping["numero_documento"]])
                    
                    insert("contas", conta_data)
                    inserted += 1
                st.success(f"Importação concluída: {inserted} linhas inseridas.")
        except Exception as e:
            st.exception(e)
