import random
from django.core.management.base import BaseCommand
from campeonato.models import Time, Partida, Classificacao
from campeonato.services import GeradorDeCalendarioService, calcular_classificacao_rodada

LISTA_TIMES = [
    "Atlético Mineiro", "Bahia", "Bragantino", "Botafogo", "Ceará",
    "Corinthians", "Cruzeiro", "Flamengo", "Fluminense", "Fortaleza",
    "Grêmio", "Internacional", "Juventude", "Mirassol", "Palmeiras",
    "Santos", "São Paulo", "Sport", "Vasco da Gama", "Vitória",
]

LARGURA_NOME_TIME = max(len(nome) for nome in LISTA_TIMES) + 1


class Command(BaseCommand):
    help = "Simula a temporada completa do Campeonato Brasileiro 2025."

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS("--- Iniciando Simulação do Brasileirão 2025 ---")
        )

        self.stdout.write("Limpando dados da temporada anterior...")
        Partida.objects.all().delete()
        Classificacao.objects.all().delete()
        Time.objects.all().delete()

        self.stdout.write(f"Criando os 20 times da Série A 2025...")
        for nome_time in LISTA_TIMES:
            Time.objects.get_or_create(nome=nome_time)
        self.stdout.write(f"{Time.objects.count()} times criados com sucesso.")

        self.stdout.write("Gerando calendário (Requisitos 1 e 2)...")
        try:
            GeradorDeCalendarioService().executar()
        except ValueError as e:
            self.stderr.write(self.style.ERROR(f"Erro ao gerar calendário: {e}"))
            return

        self.stdout.write(f"Calendário com {Partida.objects.count()} jogos gerado.")

        self.stdout.write(
            self.style.SUCCESS(
                "\n--- IMPRIMINDO CALENDÁRIO GERADO (Verificação Reqs. 1 e 2) ---"
            )
        )
        try:
            numeros_rodadas = (
                Partida.objects.values_list("rodada", flat=True)
                .distinct()
                .order_by("rodada")
            )
            if not numeros_rodadas:
                self.stdout.write(self.style.ERROR("Nenhum jogo foi gerado."))
            for rodada_num in numeros_rodadas:
                self.stdout.write(f"\n--- Rodada {rodada_num} ---")
                partidas_da_rodada = Partida.objects.filter(
                    rodada=rodada_num
                ).order_by("id")
                for partida in partidas_da_rodada:
                    mandante_nome = partida.mandante.nome.ljust(LARGURA_NOME_TIME)
                    vs = " vs ".center(9)
                    visitante_nome = partida.visitante.nome
                    self.stdout.write(f"  {mandante_nome}{vs}{visitante_nome}")
        except AttributeError:
            self.stderr.write(self.style.ERROR("Erro ao imprimir calendário."))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Erro inesperado: {e}"))
        self.stdout.write(
            self.style.SUCCESS("\n--- FIM DA VERIFICAÇÃO DO CALENDÁRIO ---\n")
        )

        self.stdout.write(
            "Iniciando simulação das 38 rodadas (Requisitos 3, 4, 5)..."
        )

        for i in range(1, 39):
            self.stdout.write(f"\n--- Processando Rodada {i} ---")
            partidas_da_rodada = Partida.objects.filter(
                rodada=i, gols_mandante__isnull=True
            ).order_by("id")

            for partida in partidas_da_rodada:
                partida.gols_mandante = random.randint(0, 4)
                partida.gols_visitante = random.randint(0, 4)

                partida.cartoes_amarelos_mandante = random.randint(0, 5)
                partida.cartoes_amarelos_visitante = random.randint(0, 5)
                partida.cartoes_vermelhos_mandante = random.choice([0, 0, 0, 0, 1])
                partida.cartoes_vermelhos_visitante = random.choice([0, 0, 0, 0, 1])

                partida.save()

                mandante_nome_str = partida.mandante.nome.ljust(LARGURA_NOME_TIME)
                visitante_nome_str = partida.visitante.nome
                placar_str = f" {partida.gols_mandante} x {partida.gols_visitante} ".center(9)

                if partida.gols_mandante > partida.gols_visitante:
                    mandante_nome = self.style.SUCCESS(mandante_nome_str)
                    placar = self.style.SUCCESS(placar_str)
                    visitante_nome = self.style.ERROR(visitante_nome_str)
                elif partida.gols_visitante > partida.gols_mandante:
                    mandante_nome = self.style.ERROR(mandante_nome_str)
                    placar = self.style.ERROR(placar_str)
                    visitante_nome = self.style.SUCCESS(visitante_nome_str)
                else:
                    mandante_nome = self.style.WARNING(mandante_nome_str)
                    placar = self.style.WARNING(placar_str)
                    visitante_nome = self.style.WARNING(visitante_nome_str)
                self.stdout.write(f"  {mandante_nome}{placar}{visitante_nome}")

            calcular_classificacao_rodada(numero_rodada=i)

        self.stdout.write(self.style.SUCCESS("\n--- Simulação Concluída ---"))

        self.stdout.write(self.style.SUCCESS("--- Classificação Final (Rodada 38) ---"))
        nome_ljust = LARGURA_NOME_TIME
        self.stdout.write(
            "Pos | " + "Time".ljust(nome_ljust) + " | Pts | V   | SG   | GM  | CV | CA"
        )
        self.stdout.write(
            "----|-" + "-" * nome_ljust + "-|-----|-----|------|-----|----|----"
        )

        tabela_final = Classificacao.objects.filter(rodada=38)

        for i, classif in enumerate(tabela_final):
            pos = f"{(i+1):>2}º".ljust(3)
            nome = classif.time.nome.ljust(nome_ljust)
            pts = str(classif.pontos).ljust(3)
            v = str(classif.vitorias).ljust(3)
            sg = str(classif.saldo_gols).ljust(4)
            gm = str(classif.gols_marcados).ljust(3)
            cv = str(classif.cartoes_vermelhos).ljust(2)
            ca = str(classif.cartoes_amarelos).ljust(2)

            self.stdout.write(f"{pos} | {nome} | {pts} | {v} | {sg} | {gm} | {cv} | {ca}")