import oracledb

# Defina suas credenciais e informações de conexão aqui
username = "ADMIN"
password = "M2g2imoveis*"  # Substitua pela sua senha do ADB
dsn = "homsdata_low"

# Tente conectar ao banco de dados
try:
    connection = oracledb.connect(user=username, password=password, dsn=dsn)
    print("Conexão bem-sucedida!")
    connection.close()
except oracledb.DatabaseError as e:
    error, = e.args
    print("Erro ao conectar ao banco de dados:")
    print("Código de erro:", error.code)
    print("Mensagem de erro:", error.message)
except Exception as e:
    print("Erro geral:", str(e))
