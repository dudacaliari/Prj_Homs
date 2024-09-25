import pyodbc

try:
    conn = pyodbc.connect(
        'DRIVER={ODBC Driver 17 for SQL Server};'
        'SERVER=server-homs.database.windows.net;'
        'DATABASE=homsdb;'
        'UID=dinizc;'
        'PWD=@dmin123',
        timeout=60  # Adicionando um tempo limite para a conexão
    )
    print("Conexão bem-sucedida!")
except Exception as e:
    print(f"Erro de conexão: {e}")
