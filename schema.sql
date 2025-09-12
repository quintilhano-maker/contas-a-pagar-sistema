
create table if not exists public.fornecedores (id bigserial primary key, nome text not null, cnpj text, email text, telefone text, criado_em timestamptz default now());
create table if not exists public.categorias (id bigserial primary key, nome text unique not null, criado_em timestamptz default now());
create table if not exists public.contas (id bigserial primary key, fornecedor_id bigint references public.fornecedores(id) on delete set null, categoria_id bigint references public.categorias(id) on delete set null, descricao text, competencia date, vencimento date not null, valor_previsto numeric(14,2) not null, status text not null default 'provisionado' check (status in ('provisionado','aprovado','pago','cancelado')), empresa text, numero_documento text, criado_em timestamptz default now());
create index if not exists contas_vencimento_idx on public.contas (vencimento);
create index if not exists contas_status_idx on public.contas (status);
create table if not exists public.aprovacoes (id bigserial primary key, conta_id bigint not null references public.contas(id) on delete cascade, aprovado_por text not null, data_aprovacao date not null, observacao text, criado_em timestamptz default now());
create table if not exists public.pagamentos (id bigserial primary key, conta_id bigint not null references public.contas(id) on delete cascade, data_pagamento date not null, valor_pago numeric(14,2) not null, forma_pagamento text, comprovante_url text, conciliado boolean default false, criado_em timestamptz default now());
create table if not exists public.extrato (id bigserial primary key, data date not null, historico text, valor numeric(14,2) not null, origem text default 'upload_csv', criado_em timestamptz default now());
