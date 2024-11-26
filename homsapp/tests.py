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

    def test_filtro_busca_imovel(self):
        Imovel.objects.create(
            numero_contribuinte='123456', nome_logradouro='Rua Teste', bairro='Centro'
        )
        response = self.client.get(reverse('index'), {'q': 'Rua Teste', 'filter': 'endereco'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Rua Teste')

    def test_login_com_credenciais_invalidas(self):
        response = self.client.post(reverse('login_view'), {'email': 'wrong@example.com', 'password': 'wrongpassword'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Invalid credentials')

    def test_paginacao_imoveis(self):
        for i in range(25):
            Imovel.objects.create(numero_contribuinte=f'{i}', nome_logradouro='Rua Teste')
        response = self.client.get(reverse('index') + '?page=2')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Rua Teste', count=10)

    def test_segurança_acesso_csv_sem_permissao(self):
        self.client.login(email='user@example.com', password='user123')
        response = self.client.get(reverse('processar_csv'))
        self.assertEqual(response.status_code, 302)

    def test_upload_csv_admin(self):
        self.client.login(email='admin@example.com', password='admin123')
        csv_file = SimpleUploadedFile("test.csv", b"col1,col2\nval1,val2", content_type="text/csv")
        response = self.client.post(reverse('processar_csv'), {'csv_file': csv_file})
        self.assertEqual(response.status_code, 302)

    def test_upload_csv_sem_permissao(self):
        self.client.login(email='user@example.com', password='user123')
        response = self.client.post(reverse('processar_csv'), {})
        self.assertEqual(response.status_code, 302)

    def test_visualizar_imoveis(self):
        Imovel.objects.create(numero_contribuinte='123456', nome_logradouro='Rua Teste', bairro='Centro')
        response = self.client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Rua Teste')
