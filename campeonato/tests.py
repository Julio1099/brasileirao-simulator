from django.test import TestCase
from .models import Time, Partida, Classificacao
from .services import gerar_calendario, calcular_classificacao_rodada


class RequisitosCampeonatoTests(TestCase):

    def setUp(self):
        Time.objects.all().delete()
        Partida.objects.all().delete()
        Classificacao.objects.all().delete()
        self.time_a = Time.objects.create(nome="Time Alpha") 
        self.time_b = Time.objects.create(nome="Time Beta") 

    def test_requisito_1_e_2_gerar_calendario(self):
        Time.objects.all().delete() 
        for i in range(20):
            Time.objects.create(nome=f"Time Teste {i}")

        gerar_calendario()

        total_times = Time.objects.count()
        total_partidas = Partida.objects.count()

        self.assertEqual(total_times, 20)
        self.assertEqual(total_partidas, 380) 

        rodadas = Partida.objects.values_list('rodada', flat=True).distinct()
        self.assertEqual(len(rodadas), 38)
        self.assertEqual(min(rodadas), 1)
        self.assertEqual(max(rodadas), 38)

        time_exemplo = Time.objects.first()
        jogos_mandante = Partida.objects.filter(mandante=time_exemplo).count()
        jogos_visitante = Partida.objects.filter(visitante=time_exemplo).count()

        self.assertEqual(jogos_mandante, 19)
        self.assertEqual(jogos_visitante, 19)

        combinacoes = set()
        for partida in Partida.objects.all():
            combinacao = (partida.mandante.id, partida.visitante.id)
            self.assertNotIn(combinacao, combinacoes, f"Jogo duplicado encontrado: {partida}")
            combinacoes.add(combinacao)

    def test_requisito_3_pontuacao_vitoria_mandante(self):
        Partida.objects.create(
            rodada=1,
            mandante=self.time_a,
            visitante=self.time_b,
            gols_mandante=3,
            gols_visitante=0,
        )

        calcular_classificacao_rodada(numero_rodada=1)

        class_a = Classificacao.objects.get(time=self.time_a, rodada=1)
        class_b = Classificacao.objects.get(time=self.time_b, rodada=1)

        self.assertEqual(class_a.pontos, 3)
        self.assertEqual(class_b.pontos, 0)

    def test_requisito_3_pontuacao_empate(self):
        Partida.objects.create(
            rodada=1,
            mandante=self.time_a,
            visitante=self.time_b,
            gols_mandante=1,
            gols_visitante=1,
        )

        calcular_classificacao_rodada(numero_rodada=1)

        class_a = Classificacao.objects.get(time=self.time_a, rodada=1)
        class_b = Classificacao.objects.get(time=self.time_b, rodada=1)

        self.assertEqual(class_a.pontos, 1)
        self.assertEqual(class_b.pontos, 1)

    def test_requisito_4_calculo_stats(self):
        Partida.objects.create(
            rodada=1,
            mandante=self.time_a,
            visitante=self.time_b,
            gols_mandante=5,
            gols_visitante=2,
            cartoes_amarelos_mandante=2, cartoes_vermelhos_mandante=0,
            cartoes_amarelos_visitante=3, cartoes_vermelhos_visitante=1
        )

        calcular_classificacao_rodada(numero_rodada=1)

        class_a = Classificacao.objects.get(time=self.time_a, rodada=1)
        self.assertEqual(class_a.vitorias, 1)
        self.assertEqual(class_a.empates, 0)
        self.assertEqual(class_a.derrotas, 0)
        self.assertEqual(class_a.gols_marcados, 5)
        self.assertEqual(class_a.gols_sofridos, 2)
        self.assertEqual(class_a.saldo_gols, 3) 
        self.assertEqual(class_a.cartoes_amarelos, 2)
        self.assertEqual(class_a.cartoes_vermelhos, 0)


        class_b = Classificacao.objects.get(time=self.time_b, rodada=1)
        self.assertEqual(class_b.vitorias, 0)
        self.assertEqual(class_b.derrotas, 1)
        self.assertEqual(class_b.gols_marcados, 2)
        self.assertEqual(class_b.gols_sofridos, 5)
        self.assertEqual(class_b.saldo_gols, -3) 
        self.assertEqual(class_b.cartoes_amarelos, 3)
        self.assertEqual(class_b.cartoes_vermelhos, 1)


    def test_requisito_5_desempate_por_vitorias(self):
        Classificacao.objects.create(
            time=self.time_a, rodada=1, pontos=3, vitorias=1, saldo_gols=1, gols_marcados=1,
            cartoes_vermelhos=0, cartoes_amarelos=0 
        )
        Classificacao.objects.create(
            time=self.time_b, rodada=1, pontos=3, vitorias=0, saldo_gols=2, gols_marcados=5,
            cartoes_vermelhos=0, cartoes_amarelos=0
        )

        tabela = list(Classificacao.objects.filter(rodada=1))

        self.assertEqual(len(tabela), 2)
        self.assertEqual(tabela[0].time, self.time_a) 
        self.assertEqual(tabela[1].time, self.time_b) 

    def test_desempate_saldo_gols(self):
        Classificacao.objects.create(
            time=self.time_a, rodada=1, pontos=3, vitorias=1, saldo_gols=2, gols_marcados=3,
            cartoes_vermelhos=0, cartoes_amarelos=0
        )
        Classificacao.objects.create(
            time=self.time_b, rodada=1, pontos=3, vitorias=1, saldo_gols=1, gols_marcados=4, 
            cartoes_vermelhos=0, cartoes_amarelos=0
        )

        tabela = list(Classificacao.objects.filter(rodada=1))

        self.assertEqual(len(tabela), 2)
        self.assertEqual(tabela[0].time, self.time_a) 
        self.assertEqual(tabela[1].time, self.time_b)

    def test_desempate_gols_marcados(self):
        Classificacao.objects.create(
            time=self.time_a, rodada=1, pontos=3, vitorias=1, saldo_gols=1, gols_marcados=3,
            cartoes_vermelhos=0, cartoes_amarelos=0
        )
        Classificacao.objects.create(
            time=self.time_b, rodada=1, pontos=3, vitorias=1, saldo_gols=1, gols_marcados=2,
            cartoes_vermelhos=0, cartoes_amarelos=0
        )

        tabela = list(Classificacao.objects.filter(rodada=1))

        self.assertEqual(len(tabela), 2)
        self.assertEqual(tabela[0].time, self.time_a) 
        self.assertEqual(tabela[1].time, self.time_b)

    def test_desempate_cartoes_vermelhos(self):
        Classificacao.objects.create(
            time=self.time_a, rodada=1, pontos=3, vitorias=1, saldo_gols=1, gols_marcados=3,
            cartoes_vermelhos=1, cartoes_amarelos=5 
        )
        Classificacao.objects.create(
            time=self.time_b, rodada=1, pontos=3, vitorias=1, saldo_gols=1, gols_marcados=3,
            cartoes_vermelhos=2, cartoes_amarelos=3 
        )

        tabela = list(Classificacao.objects.filter(rodada=1))

        self.assertEqual(len(tabela), 2)
        self.assertEqual(tabela[0].time, self.time_a) 
        self.assertEqual(tabela[1].time, self.time_b)

    def test_desempate_cartoes_amarelos(self):
        Classificacao.objects.create(
            time=self.time_a, rodada=1, pontos=3, vitorias=1, saldo_gols=1, gols_marcados=3,
            cartoes_vermelhos=1, cartoes_amarelos=3 
        )
        Classificacao.objects.create(
            time=self.time_b, rodada=1, pontos=3, vitorias=1, saldo_gols=1, gols_marcados=3,
            cartoes_vermelhos=1, cartoes_amarelos=5
        )

        tabela = list(Classificacao.objects.filter(rodada=1))

        self.assertEqual(len(tabela), 2)
        self.assertEqual(tabela[0].time, self.time_a) 
        self.assertEqual(tabela[1].time, self.time_b)

    def test_desempate_ordem_alfabetica(self):
        Classificacao.objects.create(
            time=self.time_b, rodada=1, pontos=3, vitorias=1, saldo_gols=1, gols_marcados=3,
            cartoes_vermelhos=1, cartoes_amarelos=3 
        )
        Classificacao.objects.create(
            time=self.time_a, rodada=1, pontos=3, vitorias=1, saldo_gols=1, gols_marcados=3,
            cartoes_vermelhos=1, cartoes_amarelos=3 
        )

        tabela = list(Classificacao.objects.filter(rodada=1))

        self.assertEqual(len(tabela), 2)
        self.assertEqual(tabela[0].time, self.time_a)
        self.assertEqual(tabela[1].time, self.time_b)