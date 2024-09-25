from background_task import background
import requests
from .models import Imovel

@background(schedule=0)
def geocode_imoveis():
    batch_size = 100  # Define o tamanho do lote
    offset = 0

    while True:
        imoveis_batch = Imovel.objects.filter(latitude__isnull=True, longitude__isnull=True)[offset:offset + batch_size]
        if not imoveis_batch:
            break

        for imovel in imoveis_batch:
            address_parts = [
                imovel.nome_logradouro,
                str(imovel.numero_imovel),  # Converte para string
                imovel.bairro,
                imovel.cep,
                'São Paulo',
                'SP',
                'Brasil'
            ]
            address = ', '.join(part for part in address_parts if part)
            geocode_url = f'https://nominatim.openstreetmap.org/search?format=json&q={address}&addressdetails=1'

            try:
                response = requests.get(geocode_url)
                data = response.json()
                if data:
                    lat = data[0].get('lat')
                    lon = data[0].get('lon')
                    if lat and lon:
                        imovel.latitude = float(lat)
                        imovel.longitude = float(lon)
                        imovel.save()
            except Exception as e:
                print(f"Erro ao geocodificar o imóvel {imovel.id}: {str(e)}")

        offset += batch_size
