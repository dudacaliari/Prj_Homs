from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import get_user_model
import pandas as pd
from .models import Imovel
from django.core.paginator import Paginator
from django.db.models import Q
import json

def count_imoveis():
    total_imoveis = Imovel.objects.count()
    print(f"Total de imóveis cadastrados: {total_imoveis}")

User = get_user_model()

def login_view(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']
        user = authenticate(request, username=email, password=password)
        if user is not None:
            login(request, user)
            return redirect('index')  # Redireciona para 'index' ao invés de 'consulta'
        else:
            return render(request, 'login.html', {'error': 'Invalid credentials'})
    return render(request, 'login.html')

def cadastro_view(request):
    if request.method == 'POST':
        nome = request.POST['nome']
        email = request.POST['email']
        password = request.POST['password']
        codigo_acesso = request.POST['codigo_acesso']

        if User.objects.filter(email=email).exists():
            return render(request, 'cadastro.html', {'error': 'Este e-mail já está em uso.'})

        tipo_usuario = User.ADMINISTRADOR if codigo_acesso == 'admin123' else User.COMUM

        user = User(
            email=email,
            nome=nome,
            tipo_usuario=tipo_usuario
        )
        user.set_password(password)
        user.save()

        return redirect('login_view')
    
    return render(request, 'cadastro.html')

@login_required
def index_view(request):
    return render(request, 'index.html')

@login_required
@user_passes_test(lambda user: user.tipo_usuario == User.ADMINISTRADOR)
# Função para processar um Novo CSV
def processar_csv(request):
    if request.method == 'POST' and request.FILES.get('csv_file'):
        csv_file = request.FILES['csv_file']

        try:
            # Lendo o arquivo CSV em chunks
            chunk_size = 1000
            reader = pd.read_csv(csv_file, delimiter=';', chunksize=chunk_size)

            for chunk in reader:
                chunk = chunk.rename(columns={
                    'NUMERO DO CONTRIBUINTE': 'numero_contribuinte',
                    'ANO DO EXERCICIO': 'ano_exercicio',
                    'CODLOG DO IMOVEL': 'codlog_imovel',
                    'NOME DE LOGRADOURO DO IMOVEL': 'nome_logradouro',
                    'NUMERO DO IMOVEL': 'numero_imovel',
                    'COMPLEMENTO DO IMOVEL': 'complemento',
                    'BAIRRO DO IMOVEL': 'bairro',
                    'CEP DO IMOVEL': 'cep',
                    'AREA DO TERRENO': 'area_terreno',
                    'AREA CONSTRUIDA': 'area_construida',
                    'AREA OCUPADA': 'area_ocupada',
                    'VALOR DO M2 DO TERRENO': 'valor_m2_terreno',
                    'VALOR DO M2 DE CONSTRUCAO': 'valor_m2_construcao',
                    'ANO DA CONSTRUCAO CORRIGIDO': 'ano_construcao_corrigido',
                    'QUANTIDADE DE PAVIMENTOS': 'pavimentos',
                    'TIPO DE USO DO IMOVEL': 'tipo_uso_imovel',
                    'FATOR DE OBSOLESCENCIA': 'fator_obsolescencia'
                })

                colunas_relevantes = [
                    'numero_contribuinte', 'ano_exercicio', 'codlog_imovel', 'nome_logradouro', 'numero_imovel',
                    'complemento', 'bairro', 'cep', 'area_terreno', 'area_construida', 'area_ocupada',
                    'valor_m2_terreno', 'valor_m2_construcao', 'ano_construcao_corrigido', 'pavimentos',
                    'tipo_uso_imovel', 'fator_obsolescencia'
                ]
                chunk = chunk[colunas_relevantes]

                # Coletar todos os numero_contribuinte no chunk atual
                contribuintes_chunk = chunk['numero_contribuinte'].tolist()

                # Buscar apenas os contribuintes que já existem no banco de dados
                contribuintes_existentes = set(Imovel.objects.filter(numero_contribuinte__in=contribuintes_chunk)
                                               .values_list('numero_contribuinte', flat=True))

                imoveis = []
                for index, row in chunk.iterrows():
                    numero_contribuinte = row['numero_contribuinte']
                    if numero_contribuinte in contribuintes_existentes:
                        continue  # Se já existe, pula para o próximo

                    # Tratamento de valores vazios ou ausentes
                    imovel_data = {key: value if pd.notnull(value) else None for key, value in row.items()}
                    imovel_data['numero_imovel'] = int(imovel_data['numero_imovel']) if pd.notnull(imovel_data['numero_imovel']) else None
                    imovel_data['area_terreno'] = float(imovel_data['area_terreno']) if pd.notnull(imovel_data['area_terreno']) else None
                    imovel_data['area_construida'] = float(imovel_data['area_construida']) if pd.notnull(imovel_data['area_construida']) else None
                    imovel_data['area_ocupada'] = float(imovel_data['area_ocupada']) if pd.notnull(imovel_data['area_ocupada']) else None
                    imovel_data['valor_m2_terreno'] = float(imovel_data['valor_m2_terreno']) if pd.notnull(imovel_data['valor_m2_terreno']) else None
                    imovel_data['valor_m2_construcao'] = float(imovel_data['valor_m2_construcao']) if pd.notnull(imovel_data['valor_m2_construcao']) else None
                    imovel_data['ano_construcao_corrigido'] = int(imovel_data['ano_construcao_corrigido']) if pd.notnull(imovel_data['ano_construcao_corrigido']) else None
                    imovel_data['pavimentos'] = int(imovel_data['pavimentos']) if pd.notnull(imovel_data['pavimentos']) else None
                    imovel_data['fator_obsolescencia'] = float(imovel_data['fator_obsolescencia']) if pd.notnull(imovel_data['fator_obsolescencia']) else None

                    imoveis.append(Imovel(**imovel_data))

                Imovel.objects.bulk_create(imoveis)

            return render(request, 'index.html')
        except Exception as e:
            print("Erro durante o processamento do CSV:", str(e))
            return render(request, 'processar_csv.html')
    else:
        return render(request, 'processar_csv.html')

# Função de Retorno de Pesquisa
def index_view(request):
    query = request.GET.get('q', '')
    selected_filter = request.GET.get('filter', 'numero_contribuinte')
    imoveis = Imovel.objects.all()

    if query:
        if selected_filter == 'endereco':
            # Divide a query em termos separados por vírgula e remove espaços
            termos = [termo.strip() for termo in query.split(',')]
            q_objects = Q()
            for termo in termos:
                q_objects &= (
                    Q(nome_logradouro__icontains=termo) |
                    Q(bairro__icontains=termo) |
                    Q(complemento__icontains=termo) |
                    Q(numero_imovel__icontains=termo)
                )
            imoveis = imoveis.filter(q_objects)
        else:
            filtro_dict = {
                'numero_contribuinte': 'numero_contribuinte__icontains',
                'ano_exercicio': 'ano_exercicio__icontains',
                'codlog_imovel': 'codlog_imovel__icontains',
                'nome_logradouro': 'nome_logradouro__icontains',
                'numero_imovel': 'numero_imovel__icontains',
                'complemento': 'complemento__icontains',
                'bairro': 'bairro__icontains',
                'cep': 'cep__icontains',
                'area_terreno': 'area_terreno__icontains',
                'area_construida': 'area_construida__icontains',
                'area_ocupada': 'area_ocupada__icontains',
                'valor_m2_terreno': 'valor_m2_terreno__icontains',
                'valor_m2_construcao': 'valor_m2_construcao__icontains',
                'ano_construcao_corrigido': 'ano_construcao_corrigido__icontains',
                'pavimentos': 'pavimentos__icontains',
                'tipo_uso_imovel': 'tipo_uso_imovel__icontains',
                'fator_obsolescencia': 'fator_obsolescencia__icontains',
            }
            if selected_filter in filtro_dict:
                imoveis = imoveis.filter(**{filtro_dict[selected_filter]: query})

    paginator = Paginator(imoveis, 10)  # Mostra 10 imóveis por página
    page_number = request.GET.get('page')
    imoveis = paginator.get_page(page_number)

    return render(request, 'index.html', {
        'imoveis': imoveis,
        'query': query,
        'selected_filter': selected_filter
    })
