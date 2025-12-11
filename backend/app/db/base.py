from sqlalchemy.orm import DeclarativeBase # Importa a classe base declarativa do SQLAlchemy

class Base(DeclarativeBase):
    """
    Classe base para todos os modelos do banco de dados.
    Qualquer classe que herdar de 'Base' será transformada em uma tabela SQL.
    """
    pass