from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from .models import Imovel

User = get_user_model()

class CadastroLoginCSVTestCase(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(
            email='admin@example.com', nome='Admin', password='admin123'
        )
        self.comum = User.objects.create_user(
            email='user@example.com', nome='User', password='user123'
        )

    def print_detailed_result(self, test_name, etapas):
        """
        Função para imprimir o resultado dos testes de maneira detalhada.
        """
        print(f"\nTeste: {test_name}")
        for idx, (descricao, resultado) in enumerate(etapas, 1):
            status = "OK" if resultado else "FALHOU"
            print(f"{idx}. {descricao} - {status}")
        if all(resultado for _, resultado in etapas):
            print("Resultado Final: OK!\n")
        else:
            print("Resultado Final: FALHOU!\n")

    def test_cadastro_usuario(self):
        """
        Testa o cadastro de usuários com validação de administrador e mensagens no terminal.
        """
        etapas = []

        # Pré-condição: A página de cadastro deve estar acessível
        response_get = self.client.get(reverse('cadastro_view'))
        etapas.append(("Acessar a página de cadastro de usuários.", response_get.status_code == 200))

        # Teste 1: Cadastro de usuário comum
        response_post_user = self.client.post(reverse('cadastro_view'), {
            'nome': 'Novo Usuario',
            'email': 'novo_usuario@example.com',
            'password': 'senha123',
            'codigo_acesso': ''  # Sem código de acesso, será usuário comum
        })
        user_created = User.objects.filter(email='novo_usuario@example.com').exists()
        etapas.append(("Preencher os campos obrigatórios e enviar o formulário (usuário comum).", user_created))
        etapas.append(("Verificar redirecionamento para a página de login (usuário comum).", response_post_user.status_code == 302))

        # Teste 2: Cadastro de administrador
        response_post_admin = self.client.post(reverse('cadastro_view'), {
            'nome': 'Novo Admin',
            'email': 'novo_admin@example.com',
            'password': 'senha123',
            'codigo_acesso': 'admin123'  # Código de acesso para administrador
        })
        admin_created = User.objects.filter(email='novo_admin@example.com', tipo_usuario=User.ADMINISTRADOR).exists()
        etapas.append(("Preencher os campos obrigatórios e enviar o formulário (administrador).", admin_created))
        etapas.append(("Verificar redirecionamento para a página de login (administrador).", response_post_admin.status_code == 302))

        # Teste 3: Cadastro com e-mail já existente
        response_post_duplicate = self.client.post(reverse('cadastro_view'), {
            'nome': 'Usuario Duplicado',
            'email': 'novo_usuario@example.com',  # E-mail já cadastrado
            'password': 'senha123',
            'codigo_acesso': ''
        })
        etapas.append(("Tentar cadastrar com e-mail já existente.", response_post_duplicate.status_code == 200))

        self.print_detailed_result('cadastro_usuario', etapas)

        # Validações finais
        self.assertTrue(user_created)
        self.assertTrue(admin_created)
        self.assertEqual(response_post_user.status_code, 302)
        self.assertEqual(response_post_admin.status_code, 302)
        self.assertEqual(response_post_duplicate.status_code, 200)

    def test_filtro_busca_imovel(self):
        Imovel.objects.create(
            numero_contribuinte='123456', nome_logradouro='Rua Teste', bairro='Centro'
        )
        response = self.client.get(reverse('index'), {'q': 'Rua Teste', 'filter': 'endereco'})
        etapas = [
            ("Criar um imóvel no banco de dados para teste.",
             Imovel.objects.filter(nome_logradouro='Rua Teste').exists()),
            ("Enviar requisição GET para buscar o imóvel pelo nome logradouro.",
             response.status_code == 200),
            ("Verificar se o imóvel buscado está na resposta.",
             'Rua Teste' in response.content.decode())
        ]
        self.print_detailed_result('filtro_busca_imovel', etapas)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Rua Teste')

    def test_login_com_credenciais_invalidas(self):
        response = self.client.post(reverse('login_view'), {'email': 'wrong@example.com', 'password': 'wrongpassword'})
        etapas = [
            ("Enviar requisição POST com e-mail e senha inválidos.",
             response.status_code == 200),
            ("Verificar se a mensagem 'Invalid credentials' está presente.",
             'Invalid credentials' in response.content.decode())
        ]
        self.print_detailed_result('login_com_credenciais_invalidas', etapas)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Invalid credentials')

    def test_paginacao_imoveis(self):
        for i in range(25):
            Imovel.objects.create(numero_contribuinte=f'{i}', nome_logradouro='Rua Teste')
        response = self.client.get(reverse('index') + '?page=2')
        etapas = [
            ("Criar 25 imóveis no banco de dados para teste de paginação.",
             Imovel.objects.count() == 25),
            ("Enviar requisição GET para a segunda página de resultados.",
             response.status_code == 200),
            ("Verificar se há exatamente 10 itens na página de resposta.",
             response.content.decode().count('Rua Teste') == 10)
        ]
        self.print_detailed_result('paginacao_imoveis', etapas)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Rua Teste', count=10)

    def test_segurança_acesso_csv_sem_permissao(self):
        self.client.login(email='user@example.com', password='user123')
        response = self.client.get(reverse('processar_csv'))
        etapas = [
            ("Logar no sistema como um usuário comum.",
             self.client.session['_auth_user_id'] == str(self.comum.id)),
            ("Tentar acessar a página de upload de CSV sem permissões de administrador.",
             response.status_code == 302)
        ]
        self.print_detailed_result('segurança_acesso_csv_sem_permissao', etapas)
        self.assertEqual(response.status_code, 302)

    def test_upload_csv_admin(self):
        self.client.login(email='admin@example.com', password='admin123')
        csv_file = SimpleUploadedFile("test.csv", b"col1,col2\nval1,val2", content_type="text/csv")
        response = self.client.post(reverse('processar_csv'), {'csv_file': csv_file})
        etapas = [
            ("Logar no sistema como administrador.",
             self.client.session['_auth_user_id'] == str(self.admin.id)),
            ("Enviar um arquivo CSV válido para upload.",
             response.status_code == 302),
            ("Verificar se o sistema redirecionou após o upload.",
             response.url is not None)
        ]
        self.print_detailed_result('upload_csv_admin', etapas)
        self.assertEqual(response.status_code, 302)

    def test_upload_csv_sem_permissao(self):
        self.client.login(email='user@example.com', password='user123')
        response = self.client.post(reverse('processar_csv'), {})
        etapas = [
            ("Logar no sistema como um usuário comum.",
             self.client.session['_auth_user_id'] == str(self.comum.id)),
            ("Tentar enviar um arquivo CSV sem permissões de administrador.",
             response.status_code == 302)
        ]
        self.print_detailed_result('upload_csv_sem_permissao', etapas)
        self.assertEqual(response.status_code, 302)

    def test_visualizar_imoveis(self):
        Imovel.objects.create(numero_contribuinte='123456', nome_logradouro='Rua Teste', bairro='Centro')
        response = self.client.get(reverse('index'))
        etapas = [
            ("Criar um imóvel no banco de dados para teste.",
             Imovel.objects.filter(nome_logradouro='Rua Teste').exists()),
            ("Enviar requisição GET para visualizar imóveis cadastrados.",
             response.status_code == 200),
            ("Verificar se o imóvel está presente na resposta.",
             'Rua Teste' in response.content.decode())
        ]
        self.print_detailed_result('visualizar_imoveis', etapas)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Rua Teste')
