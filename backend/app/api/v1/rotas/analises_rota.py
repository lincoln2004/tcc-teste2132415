from typing import List
import os

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import FileResponse, JSONResponse

from app.api.dependencias.autenticacao import obter_usuario_atual
from app.esquemas.analise_esquema import AnaliseCriar, AnaliseResposta
from app.modelos.usuario import Usuario
from app.repositorios.analise_repositorio import AnaliseRepositorio
from app.servicos.analise_servico import AnaliseServico


router = APIRouter()


@router.post("/executar", response_model=AnaliseResposta, status_code=status.HTTP_201_CREATED)
async def executar_analise(
    analise_in: AnaliseCriar,
    usuario_atual: Usuario = Depends(obter_usuario_atual),
) -> AnaliseResposta:
    """
    Cria e dispara a execucao de uma nova analise de anomalias.
    """
    try:
        return await AnaliseServico.criar_e_executar_analise(analise_in, usuario_atual.id)
    except ValueError as erro:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(erro)) from erro
    except Exception as erro:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno ao processar analise: {erro}",
        ) from erro


@router.get("/historico", response_model=List[AnaliseResposta])
async def listar_historico(usuario_atual: Usuario = Depends(obter_usuario_atual)) -> List[AnaliseResposta]:
    """
    Retorna o historico de analises realizadas pelo usuario autenticado.
    """
    return await AnaliseRepositorio.listar_por_usuario(usuario_atual.id)


@router.delete("/historico", status_code=status.HTTP_200_OK)
async def excluir_historico(usuario_atual: Usuario = Depends(obter_usuario_atual)) -> dict[str, int | str]:
    """
    Remove todo o historico de analises do usuario autenticado.
    """
    return await AnaliseServico.excluir_historico_usuario(usuario_atual.id)


@router.get("/{analise_id}", response_model=AnaliseResposta)
async def obter_detalhes_analise(
    analise_id: int,
    usuario_atual: Usuario = Depends(obter_usuario_atual),
) -> AnaliseResposta:
    """
    Obtem os detalhes de uma analise especifica pertencente ao usuario logado.
    """
    analise = await AnaliseRepositorio.obter_por_id_e_usuario(analise_id, usuario_atual.id)
    if not analise:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analise nao encontrada.")
    return analise


@router.get("/{analise_id}/download")
async def baixar_resultado_analise(
    analise_id: int,
    usuario_atual: Usuario = Depends(obter_usuario_atual),
) -> FileResponse:
    """
    Disponibiliza o CSV gerado pela analise concluida para o usuario autenticado.
    """
    analise = await AnaliseRepositorio.obter_por_id_e_usuario(analise_id, usuario_atual.id)
    if not analise:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analise nao encontrada.")
    if not analise.caminho_resultado_csv:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A analise ainda nao possui um arquivo de resultado disponivel.",
        )
    if not os.path.exists(analise.caminho_resultado_csv):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="O arquivo de resultado da analise nao foi encontrado no armazenamento local.",
        )
    return FileResponse(
        analise.caminho_resultado_csv,
        media_type="text/csv",
        filename=f"resultado_analise_{analise.id}.csv",
    )


@router.get("/tipos-relatorios")
async def listar_tipos_relatorios() -> JSONResponse:
    """
    Retorna lista de tipos de relatorios disponiveis para gerar a partir das analises.
    """
    tipos = AnaliseServico.listar_tipos_relatorios()
    return JSONResponse(content={"tipos": tipos})


@router.post("/{analise_id}/gerar-relatorio")
async def gerar_relatorio_analise(
    analise_id: int,
    tipo_relatorio: str = Query(..., description="Tipo de relatorio: pycaret, deepchecks, sweetviz, ydata_profiling"),
    formato_saida: str = Query("html", description="Formato de saida: html ou pdf"),
    usuario_atual: Usuario = Depends(obter_usuario_atual),
) -> dict[str, str]:
    """
    Gera um relatorio especializado (PyCaret, DeepChecks, Sweetviz, YData-Profiling) para uma analise concluida.
    """
    try:
        caminho_arquivo = await AnaliseServico.gerar_relatorio_analise(
            analise_id=analise_id,
            usuario_id=usuario_atual.id,
            tipo_relatorio=tipo_relatorio,
            formato_saida=formato_saida,
        )
        return {
            "mensagem": "Relatorio gerado com sucesso.",
            "caminho_arquivo": caminho_arquivo,
            "tipo_relatorio": tipo_relatorio,
            "formato_saida": formato_saida,
        }
    except ValueError as erro:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(erro)) from erro
    except RuntimeError as erro:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao gerar relatorio: {erro}",
        ) from erro
    except Exception as erro:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno ao gerar relatorio: {erro}",
        ) from erro


@router.get("/{analise_id}/baixar-relatorio")
async def baixar_relatorio_analise(
    analise_id: int,
    tipo_relatorio: str = Query(..., description="Tipo de relatorio: pycaret, deepchecks, sweetviz, ydata_profiling"),
    usuario_atual: Usuario = Depends(obter_usuario_atual),
) -> FileResponse:
    """
    Baixa o relatorio especializado previamente gerado para uma analise.
    """
    # Primeiro, gerar o relatorio se ainda nao existir
    try:
        caminho_arquivo = await AnaliseServico.gerar_relatorio_analise(
            analise_id=analise_id,
            usuario_id=usuario_atual.id,
            tipo_relatorio=tipo_relatorio,
            formato_saida="html",
        )
    except ValueError as erro:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(erro)) from erro
    except Exception as erro:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao gerar relatorio: {erro}",
        ) from erro

    if not os.path.exists(caminho_arquivo):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="O arquivo do relatorio nao foi encontrado.",
        )

    nome_arquivo = f"relatorio_{tipo_relatorio}_analise_{analise_id}.html"
    return FileResponse(
        caminho_arquivo,
        media_type="text/html",
        filename=nome_arquivo,
    )
