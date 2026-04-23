from pydantic import BaseModel, UUID4
from datetime import datetime
from typing import Optional

class FileUploadResponse(BaseModel):
    """Retornado ao frontend após upload bem-sucedido."""
    id: UUID4                  # o ID aleatório que o frontend vai guardar
    filename: str
    content_type: Optional[str]
    size_bytes: Optional[int]
    created_at: datetime

class FileInfoResponse(BaseModel):
    """Retornado quando o frontend consulta pelo ID."""
    id: UUID4
    filename: str
    public_url: str            # URL real do Supabase Storage
    content_type: Optional[str]
    size_bytes: Optional[int]
    created_at: datetime