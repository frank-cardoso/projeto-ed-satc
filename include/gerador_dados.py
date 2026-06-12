import os
import random
from datetime import datetime, timedelta
from dotenv import load_dotenv
from faker import Faker
from pymongo import MongoClient

load_dotenv()

fake = Faker('pt_BR')

MONGO_URI = os.getenv("MONGO_URI")

if not MONGO_URI:
    raise ValueError("A variável MONGO_URI não foi encontrada. Verifique o arquivo .env!")

client = MongoClient(MONGO_URI)
db = client['gearlog_erp']

def gerar_dados():
    print("Iniciando a geração de dados. Isso pode levar alguns minutos...")
    
    # Listas de apoio para contexto automotivo
    especialidades = ["Motor", "Suspensão", "Elétrica", "Projetos JDM", "Câmbio Manual", "Estética Automotiva"]
    pecas_nomes = ["Correia Dentada", "Bico Injetor", "Radiador", "Vela de Ignição", "Filtro de Óleo", "Junta do Cabeçote", "Sensor MAP", "Bomba d'Água", "Disco de Freio", "Amortecedor"]
    marcas_modelos = [
        ("Honda", "Civic LX"), ("Honda", "Civic Si"), ("Toyota", "Corolla"), 
        ("Subaru", "Impreza WRX"), ("Nissan", "Skyline"), ("Mitsubishi", "Lancer Evolution")
    ]
    
    # 1. Tabela: Mecânicos (50 registros)
    mecanicos = [{"_id": i, "nome": fake.name(), "especialidade": random.choice(especialidades)} for i in range(1, 51)]
    db.mecanicos.insert_many(mecanicos)
    
    # 2. Tabela: Fornecedores (100 registros)
    fornecedores = [{"_id": i, "nome": fake.company(), "cnpj": fake.cnpj()} for i in range(1, 101)]
    db.fornecedores.insert_many(fornecedores)
    
    # Preparando as listas para inserção em lote (Bulk Insert é muito mais rápido)
    clientes, veiculos, pecas, ordens, itens, pagamentos, agendamentos, avaliacoes = [], [], [], [], [], [], [], []
    
    # Regra: Distribuição de datas para os últimos 3 anos
    data_inicio = datetime.now() - timedelta(days=3*365) 
    
    # Gerando as massas principais (10.000 linhas)
    for i in range(1, 10001):
        # 3. Tabela: Clientes
        clientes.append({"_id": i, "nome": fake.name(), "cpf": fake.cpf(), "telefone": fake.phone_number()})
        
        # 4. Tabela: Veículos
        marca, modelo = random.choice(marcas_modelos)
        ano = random.randint(1995, 2024)
        if i == 1: 
            marca, modelo, ano = "Honda", "Civic LX", 2000
            
        veiculos.append({"_id": i, "id_cliente": i, "marca": marca, "modelo": modelo, "ano": ano, "placa": fake.license_plate()})
        
        # 5. Tabela: Peças no Estoque
        pecas.append({"_id": i, "id_fornecedor": random.randint(1, 100), "nome": random.choice(pecas_nomes), "preco": round(random.uniform(50.0, 1500.0), 2), "quantidade_estoque": random.randint(0, 50)})
        
        # 6. Tabela: Ordens de Serviço (Fato principal)
        data_os = data_inicio + timedelta(days=random.randint(0, 3*365))
        ordens.append({"_id": i, "id_veiculo": i, "id_mecanico": random.randint(1, 50), "data_entrada": data_os, "status": random.choice(["Concluído", "Em Andamento", "Aguardando Peças"])})
        
        # 7. Tabela: Itens da Ordem de Serviço
        itens.append({"_id": i, "id_os": i, "id_peca": random.randint(1, 10000), "quantidade": random.randint(1, 4)})
        
        # 8. Tabela: Pagamentos
        pagamentos.append({"_id": i, "id_os": i, "valor_total": round(random.uniform(200.0, 5000.0), 2), "metodo": random.choice(["PIX", "Cartão de Crédito", "Dinheiro"])})
        
        # 9. Tabela: Agendamentos
        agendamentos.append({"_id": i, "id_cliente": i, "data_agendada": data_os - timedelta(days=random.randint(1, 15)), "servico_solicitado": "Revisão Geral"})
        
        # 10. Tabela: Avaliações
        avaliacoes.append({"_id": i, "id_os": i, "nota": random.randint(1, 5), "comentario": fake.text(max_nb_chars=50)})
        
        if i % 2000 == 0:
            print(f"Progresso: {i} registros processados...")
            
    # Executando a gravação final no Atlas
    db.clientes.insert_many(clientes)
    db.veiculos.insert_many(veiculos)
    db.pecas_estoque.insert_many(pecas)

    db.ordens_servico.insert_many(ordens)
    db.itens_os.insert_many(itens)
    db.pagamentos.insert_many(pagamentos)
    db.agendamentos.insert_many(agendamentos)
    db.avaliacoes.insert_many(avaliacoes)

    print("🚀 Sucesso absoluto! 10 tabelas populadas com as regras de negócio no MongoDB Atlas.")

# === ESTE BLOCO FICA ENCOSTADO NA MARGEM ESQUERDA ===
if __name__ == "__main__":
    gerar_dados()