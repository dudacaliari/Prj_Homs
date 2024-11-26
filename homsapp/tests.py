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

    def print_result(self, test_name, expected, result):
        """
        Função para imprimir o resultado dos testes de maneira detalhada.
        """
        print(f"\nTeste: {test_name}")
        print(f"Esperado: {expected}")
        print(f"Resultado: {result}")
        if expected == result:
            print("OK!\n")
        else:
            print("Falhou!\n")

    def test_filtro_busca_imovel(self):
        Imovel.objects.create(
            numero_contribuinte='123456', nome_logradouro='Rua Teste', bairro='Centro'
        )
        response = self.client.get(reverse('index'), {'q': 'Rua Teste', 'filter': 'endereco'})
        # Esperado é a presença do texto 'Rua Teste' na resposta
        expected = 'Rua Teste'
        # O resultado será a mesma coisa, se a busca for bem-sucedida
        result = 'Rua Teste' if response.status_code == 200 and 'Rua Teste' in response.content.decode() else None
        self.print_result('filtro_busca_imovel', expected, result)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Rua Teste')

    def test_login_com_credenciais_invalidas(self):
        response = self.client.post(reverse('login_view'), {'email': 'wrong@example.com', 'password': 'wrongpassword'})
        # Esperado é a mensagem de 'Invalid credentials'
        expected = 'Invalid credentials'
        # O resultado será a mesma mensagem, se ela estiver presente na resposta
        result = 'Invalid credentials' if response.status_code == 200 and 'Invalid credentials' in response.content.decode() else None
        self.print_result('login_com_credenciais_invalidas', expected, result)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Invalid credentials')

    def test_paginacao_imoveis(self):
        for i in range(25):
            Imovel.objects.create(numero_contribuinte=f'{i}', nome_logradouro='Rua Teste')
        response = self.client.get(reverse('index') + '?page=2')
        # Esperado é que a resposta contenha 'Rua Teste' (pelo menos 10 vezes por página)
        expected = 'Rua Teste'
        # O resultado será 'Rua Teste', se estiver presente na página
        result = 'Rua Teste' if response.status_code == 200 and 'Rua Teste' in response.content.decode() else None
        self.print_result('paginacao_imoveis', expected, result)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Rua Teste', count=10)

    def test_segurança_acesso_csv_sem_permissao(self):
        self.client.login(email='user@example.com', password='user123')
        response = self.client.get(reverse('processar_csv'))
        # Esperado é que o usuário seja redirecionado
        expected = '/accounts/login/'
        # O resultado será o URL de redirecionamento se o código de status for 302
        result = '/accounts/login/' if response.status_code == 302 else None
        self.print_result('segurança_acesso_csv_sem_permissao', expected, result)
        self.assertEqual(response.status_code, 302)

    def test_upload_csv_admin(self):
        self.client.login(email='admin@example.com', password='admin123')
        csv_file = SimpleUploadedFile("test.csv", b"col1,col2\nval1,val2", content_type="text/csv")
        response = self.client.post(reverse('processar_csv'), {'csv_file': csv_file})
        # Esperado é que o upload do CSV seja bem-sucedido e redirecione
        expected = 'Redirecionamento após upload de CSV'
        # O resultado será 'Redirecionamento após upload de CSV', se o código de status for 302
        result = 'Redirecionamento após upload de CSV' if response.status_code == 302 else None
        self.print_result('upload_csv_admin', expected, result)
        self.assertEqual(response.status_code, 302)

    def test_upload_csv_sem_permissao(self):
        self.client.login(email='user@example.com', password='user123')
        response = self.client.post(reverse('processar_csv'), {})
        # Esperado é que o usuário sem permissão seja redirecionado
        expected = '/accounts/login/'
        # O resultado será o URL de redirecionamento se o código de status for 302
        result = '/accounts/login/' if response.status_code == 302 else None
        self.print_result('upload_csv_sem_permissao', expected, result)
        self.assertEqual(response.status_code, 302)

    def test_visualizar_imoveis(self):
        Imovel.objects.create(numero_contribuinte='123456', nome_logradouro='Rua Teste', bairro='Centro')
        response = self.client.get(reverse('index'))
        # Esperado é que a resposta contenha 'Rua Teste'
        expected = 'Rua Teste'
        # O resultado será 'Rua Teste', se estiver presente na resposta
        result = 'Rua Teste' if response.status_code == 200 and 'Rua Teste' in response.content.decode() else None
        self.print_result('visualizar_imoveis', expected, result)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Rua Teste')
