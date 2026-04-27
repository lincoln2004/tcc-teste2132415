import uuid, io, csv, os
from fastapi import APIRouter, UploadFile, File, HTTPException
from ..models.database import supabase
from ..models.file import FileInfoResponse
import pandas as pd
from dotenv import load_dotenv
from datetime import datetime, timezone, timedelta

load_dotenv()

router = APIRouter(prefix="/files", tags=["files"])

def delete_old_files(minutes: int = 10):
    """
    Deleta arquivos do banco e do storage que foram criados há mais dez 'minutes' minutos.
    Retorna a quantidade de arquivos deletados.
    """
    try:
        # Calcula o timestamp limite (UTC)
        cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=minutes)
        
        # Busca arquivos criados antes do cutoff_time
        # Assumindo que a tabela tem uma coluna 'created_at' ou 'inserted_at'
        # Se não tiver, podemos usar o id (UUID v1 tem timestamp) ou adicionar coluna
        result = (
            supabase.table(os.getenv("SUPABASE_TABLE"))
            .select("id, storage_path")
            .lt("created_at", cutoff_time.isoformat())
            .execute()
        )
        
        old_files = result.data
        if not old_files:
            return 0
        
        deleted_count = 0
        for file in old_files:
            try:
                # Deleta do storage
                supabase.storage.from_(os.getenv("SUPABASE_BUCKET")).remove([file["storage_path"]])
                # Deleta do banco
                supabase.table(os.getenv("SUPABASE_TABLE")).delete().eq("id", file["id"]).execute()
                deleted_count += 1
                print(f"🗑️ Arquivo deletado: {file['id']} - {file['storage_path']}")
            except Exception as e:
                print(f"❌ Erro ao deletar arquivo {file['id']}: {str(e)}")
        
        return deleted_count
        
    except Exception as e:
        print(f"⚠️ Erro na limpeza de arquivos antigos: {str(e)}")
        return 0

@router.post("/upload")
async def upload_file(documento: UploadFile = File(...)):
    content = await documento.read()
    
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="Arquivo vazio")
    
    delete_old_files(minutes=10)
    
    extension = documento.filename.rsplit(".", 1)[-1].lower() if "." in documento.filename else ""
    unique_id = str(uuid.uuid4())
    storage_path = f"{unique_id}/{documento.filename}"

    try:
        supabase.storage.from_(os.getenv("SUPABASE_BUCKET")).upload(
            path=storage_path,
            file=content,
            file_options={"content-type": documento.content_type or "application/octet-stream"},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    public_url = supabase.storage.from_(os.getenv("SUPABASE_BUCKET")).get_public_url(storage_path)

    row = {
        "filename": documento.filename,
        "storage_path": storage_path,
        "public_url": public_url,
        "content_type": documento.content_type,
        "size_bytes": len(content),
    }
    result = supabase.table(os.getenv("SUPABASE_TABLE")).insert(row).execute()
    if not result.data:
        raise HTTPException(status_code=500, detail="Falha ao salvar no banco.")

    record = result.data[0]
    columns = []

    if extension == "csv":
        try:
            # Estratégia 1: O Pandas com sep=None e engine='python' detecta o separador automaticamente
            # Usamos BytesIO para evitar problemas de tipos
            df = pd.read_csv(
                io.BytesIO(content),
                sep=None, 
                engine='python',
                on_bad_lines='skip',
                encoding='utf-8-sig' # utf-8-sig lida com arquivos Excel/Windows (BOM)
            )
        except Exception:
            # Estratégia 2: Fallback simples para vírgula caso o detector falhe
            try:
                df = pd.read_csv(io.BytesIO(content), sep=',', on_bad_lines='skip')
            except Exception as e:
                raise HTTPException(status_code=422, detail=f"Erro ao processar CSV: {str(e)}")

        if df.empty:
            raise HTTPException(status_code=422, detail="Arquivo CSV sem dados.")

        num_cols = df.select_dtypes(include=["number"]).columns.tolist()
        cat_cols = df.select_dtypes(exclude=["number"]).columns.tolist()
        
        columns = (
            [{"column": c, "type": "numerico"} for c in num_cols]
            + [{"column": c, "type": "categorico"} for c in cat_cols]
        )

    return {"key": record.get("id"), "columns": columns}


@router.get("/{file_id}", response_model=FileInfoResponse)
async def get_file(file_id: str):
    
    delete_old_files(10)
    
    result = (
        supabase.table(os.getenv("SUPABASE_TABLE"))
        .select("*")
        .eq("id", file_id)
        .single()
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="Arquivo não encontrado.")
    return FileInfoResponse(**result.data)


@router.delete("/{file_id}")
async def delete_file(file_id: str):
    record = (
        supabase.table(os.getenv("SUPABASE_TABLE"))
        .select("storage_path")
        .eq("id", file_id)
        .single()
        .execute()
    )
    if not record.data:
        raise HTTPException(status_code=404, detail="Arquivo não encontrado.")
    supabase.storage.from_(os.getenv("SUPABASE_BUCKET")).remove([record.data["storage_path"]])
    supabase.table(os.getenv("SUPABASE_TABLE")).delete().eq("id", file_id).execute()
    return {"deleted": file_id}