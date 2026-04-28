"""
Configura os recursos necessários no Supabase:
  - Tabela de metadados dos arquivos
  - Bucket público de storage

Uso:
    python setup_supabase.py

Variáveis obrigatórias (.env):
    SUPABASE_URL, SUPABASE_TK, SUPABASE_TABLE, SUPABASE_BUCKET

Variável opcional — necessária apenas para CRIAR a tabela pela primeira vez:
    SUPABASE_PERSONAL_TOKEN  (supabase.com/dashboard/account/tokens)
"""

import os
import re
import sys
import requests
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SUPABASE_URL    = os.getenv("SUPABASE_URL", "")
SUPABASE_TK     = os.getenv("SUPABASE_TK", "")
SUPABASE_TABLE  = os.getenv("SUPABASE_TABLE", "")
SUPABASE_BUCKET = os.getenv("SUPABASE_BUCKET", "")
PERSONAL_TOKEN  = os.getenv("SUPABASE_PERSONAL_TOKEN", "")

# ── Validação das obrigatórias ─────────────────────────────────────────────
missing = [k for k, v in {
    "SUPABASE_URL": SUPABASE_URL,
    "SUPABASE_TK": SUPABASE_TK,
    "SUPABASE_TABLE": SUPABASE_TABLE,
    "SUPABASE_BUCKET": SUPABASE_BUCKET,
}.items() if not v]

if missing:
    print(f"[ERRO] Variáveis faltando no .env: {', '.join(missing)}")
    sys.exit(1)

match = re.search(r"https://([^.]+)\.supabase\.co", SUPABASE_URL)
if not match:
    print(f"[ERRO] SUPABASE_URL inválida: {SUPABASE_URL}")
    sys.exit(1)

PROJECT_REF = match.group(1)
supabase    = create_client(SUPABASE_URL, SUPABASE_TK)


def tabela_existe():
    try:
        supabase.table(SUPABASE_TABLE).select("id").limit(1).execute()
        return True
    except Exception:
        return False


def criar_tabela():
    if not PERSONAL_TOKEN:
        if tabela_existe():
            print(f"[OK]   Tabela '{SUPABASE_TABLE}' já existe.")
            return
        print(
            f"[ERRO] Tabela '{SUPABASE_TABLE}' não existe e SUPABASE_PERSONAL_TOKEN não está definido.\n"
            f"       Adicione o token ao .env para criá-la automaticamente.\n"
            f"       Gere em: https://supabase.com/dashboard/account/tokens"
        )
        sys.exit(1)

    sql = f"""
    create table if not exists public.{SUPABASE_TABLE} (
        id           uuid primary key default gen_random_uuid(),
        filename     text not null,
        storage_path text not null,
        public_url   text not null,
        content_type text,
        size_bytes   integer,
        created_at   timestamptz default now()
    );
    """
    resp = requests.post(
        f"https://api.supabase.com/v1/projects/{PROJECT_REF}/database/query",
        headers={"Authorization": f"Bearer {PERSONAL_TOKEN}", "Content-Type": "application/json"},
        json={"query": sql},
    )
    if resp.status_code in (200, 201):
        print(f"[OK]   Tabela '{SUPABASE_TABLE}' criada (ou já existia).")
    else:
        print(f"[ERRO] Falha ao criar tabela: {resp.status_code} — {resp.text}")
        sys.exit(1)


def criar_bucket():
    try:
        supabase.storage.create_bucket(SUPABASE_BUCKET, options={"public": True})
        print(f"[OK]   Bucket '{SUPABASE_BUCKET}' criado como público.")
    except Exception as e:
        msg = str(e)
        if "already exists" in msg.lower() or "duplicate" in msg.lower():
            print(f"[OK]   Bucket '{SUPABASE_BUCKET}' já existe.")
        else:
            print(f"[ERRO] Falha ao criar bucket: {msg}")
            sys.exit(1)


if __name__ == "__main__":
    print(f"\nConfigurando projeto: {PROJECT_REF}\n")
    criar_tabela()
    criar_bucket()
    print("\nSetup concluído.\n")
