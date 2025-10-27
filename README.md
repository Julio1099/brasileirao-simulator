# Simulador do Campeonato Brasileiro 2025 (TPPE - Trabalho Prático 1)

Projeto desenvolvido para a disciplina de **Técnicas de Programação em Plataformas Emergentes (TPPE)**, implementado com o framework **Django**.

A aplicação simula uma temporada completa do Campeonato Brasileiro (Série A), desde a criação dos times e geração do calendário de jogos (turno e returno) até a simulação de placares para as 38 rodadas e o cálculo da tabela de classificação em tempo real, respeitando os critérios de pontuação e desempate.

---

## Funcionalidades Principais

* **Geração de Calendário**: Criação automática das 380 partidas (38 rodadas) do campeonato, garantindo que cada time jogue contra todos os outros duas vezes (mandante e visitante), sem duplicidade de confrontos.
* **Simulação de Partidas**: Geração de resultados aleatórios (placares) para cada um dos 380 jogos.
* **Cálculo de Classificação**: Atualização da tabela de classificação ao final de cada rodada, calculando pontos (3 por vitória, 1 por empate), vitórias, saldo de gols e gols marcados.
* **Critérios de Desempate**: A classificação final obedece ao critério de desempate principal por número de vitórias.
* **Testes Unitários**: O projeto inclui uma suíte de testes (executada com `manage.py test`) para validar as regras de negócio essenciais (cálculo de pontos, desempate, etc.).

---

## Tecnologias Utilizadas

* Python 3.12
* Django 5.2+
* SQLite3 (Banco de dados padrão do Django)

---

## Instalação e Configuração

Siga os passos abaixo para configurar o ambiente de desenvolvimento.

### 1. Clone o repositório:

```bash
git clone <url-do-repositorio>
cd trabalho1-tppe
```

### 2. Crie e ative um ambiente virtual (venv):

**No Windows:**

```bash
python -m venv venv
.\venv\Scripts\activate
```

**No macOS/Linux:**

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Instale as dependências do projeto:

```bash
pip install -r requirements.txt
```

### 4. Aplique as migrações do banco de dados:

*(Isso criará o arquivo `db.sqlite3` e as tabelas necessárias)*

```bash
python manage.py migrate
python manage.py makemigrations campeonato
```

---

## Modo de Uso

O projeto possui três comandos principais: **simulação**, **testes** e **visualização**.

### 1. Executando a Simulação

```bash
python manage.py simular_campeonato
```

O comando irá:

* Limpar o banco de dados de simulações anteriores.
* Criar os 20 times da Série A.
* Gerar o calendário completo de 38 rodadas.
* Simular o placar de todas as 380 partidas.
* Calcular a classificação final e imprimi-la no console.
* Salvar todos os resultados no banco de dados.

### 2. Executando os Testes Unitários

```bash
python manage.py test
```

Este comando executa a **suíte AllTests** e valida funcionalidades como o cálculo de pontos, o critério de desempate por vitórias e a geração do calendário.

### 3. Visualizando os Resultados no Admin

1. Crie um superusuário (administrador):

```bash
python manage.py createsuperuser
```

2. Inicie o servidor de desenvolvimento:

```bash
python manage.py runserver
```
3. Tabela de Classificação (Front-end): http://127.0.0.1:8000/

```bash
Nesta tela, você pode navegar entre as 38 rodadas, ver a classificação, os placares de cada rodada e a variação de posição dos times.
```

4. Acesse o painel de admin: [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)

```bash
Faça login com as credenciais criadas. No painel, você poderá navegar, filtrar e inspecionar todos os **Times**, **Partidas (com placares)** e **Classificações (rodada a rodada)**.
```
