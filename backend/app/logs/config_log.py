import sys
from loguru import logger

def configurar_logging():
    """
    Configura o sistema de logs da aplicação.
    Define o formato, nível de saída e destinos (console e arquivo).
    """
    # Remove o logger padrão do Loguru
    logger.remove()

    # Adiciona saída no console com cores
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="INFO",
        colorize=True
    )

    # Adiciona saída em arquivo para persistência e auditoria
    logger.add(
        "logs/app.log",
        rotation="10 MB",
        retention="10 days",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="DEBUG",
        compression="zip"
    )

    logger.info("Sistema de logging configurado com sucesso.")

# Inicializa a configuração
configurar_logging()
