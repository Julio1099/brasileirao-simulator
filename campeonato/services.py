import random
from django.db import transaction
from .models import Time, Partida, Classificacao

class GeradorDeCalendario:
    def __init__(self, times):
        self.times = times
        self.n = len(times)
        self.num_rodadas_turno = self.n - 1
        self.times_rotacao = self.times[:]
        self.ultimo_local = {time.id: None for time in times}
        self.todas_partidas_objs = []
        self.partidas_organizadas = {}

    def _gerar_pares_e_locais(self, rodada_num):
        metade = self.n // 2
        pares_rodada = []
        pares_rodada.append((self.times_rotacao[0], self.times_rotacao[-1]))
        for i in range(1, metade):
            pares_rodada.append((self.times_rotacao[i], self.times_rotacao[self.n - 1 - i]))

        rodada_returno_num = rodada_num + self.num_rodadas_turno

        for idx_par, (t1, t2) in enumerate(pares_rodada):
            
            t1_pode_casa = self.ultimo_local[t1.id] != 'home'
            t2_pode_fora = self.ultimo_local[t2.id] != 'away'
            t2_pode_casa = self.ultimo_local[t2.id] != 'home'
            t1_pode_fora = self.ultimo_local[t1.id] != 'away'

            mandante, visitante = None, None

            if t1_pode_casa and t2_pode_fora:
                mandante, visitante = t1, t2
            elif t2_pode_casa and t1_pode_fora:
                mandante, visitante = t2, t1
            else:
                if (rodada_num + idx_par) % 2 == 0:
                    mandante, visitante = t1, t2
                else:
                    mandante, visitante = t2, t1

            partida_turno = Partida(rodada=rodada_num, mandante=mandante, visitante=visitante)
            self.todas_partidas_objs.append(partida_turno)
            
            self.ultimo_local[mandante.id] = 'home'
            self.ultimo_local[visitante.id] = 'away'

            partida_returno = Partida(rodada=rodada_returno_num, mandante=visitante, visitante=mandante)
            self.todas_partidas_objs.append(partida_returno)

    def executar(self):
        if self.n != 20:
            raise ValueError("O campeonato deve ter exatamente 20 times cadastrados.")

        random.shuffle(self.times)
        
        for rodada_num in range(1, self.num_rodadas_turno + 1):
            self._gerar_pares_e_locais(rodada_num)
            
            self.times_rotacao.insert(1, self.times_rotacao.pop())
            
        for p in self.todas_partidas_objs:
            if p.rodada not in self.partidas_organizadas:
                self.partidas_organizadas[p.rodada] = []
            self.partidas_organizadas[p.rodada].append(p)

        partidas_finais_para_salvar = []
        for rodada_num in sorted(self.partidas_organizadas.keys()):
            jogos_da_rodada = self.partidas_organizadas[rodada_num]
            random.shuffle(jogos_da_rodada)
            partidas_finais_para_salvar.extend(jogos_da_rodada)
            
        return partidas_finais_para_salvar, self.num_rodadas_turno * 2

class GeradorDeCalendarioService:
    def __init__(self):
        pass

    def executar(self):
        Partida.objects.all().delete()
        Classificacao.objects.all().delete()

        times = list(Time.objects.all())

        gerador = GeradorDeCalendario(times)
        partidas_finais_para_salvar, total_rodadas = gerador.executar()
            
        Partida.objects.bulk_create(partidas_finais_para_salvar)

        print(
            f"Calendário com {Partida.objects.count()} jogos em {total_rodadas} rodadas gerado."
        )

class ClassificacaoProcessor:
    
    DEFAULT_STATS = {
        "pontos": 0, "vitorias": 0, "empates": 0, "derrotas": 0,
        "gols_marcados": 0, "gols_sofridos": 0, "saldo_gols": 0,
        "cartoes_amarelos": 0, "cartoes_vermelhos": 0
    }

    def __init__(self, numero_rodada):
        self.numero_rodada = numero_rodada
        self.class_rodada_map = {}
        self.objetos_para_atualizar = []
        self._carregar_stats_base()
        self._processar_partidas()
        self._finalizar_e_salvar()

    def _carregar_stats_base(self):
        stats_base = {}
        all_time_ids = Time.objects.values_list('id', flat=True)

        if self.numero_rodada == 1:
            stats_base = {tid: self.DEFAULT_STATS.copy() for tid in all_time_ids}
        else:
            stats_base = {tid: self.DEFAULT_STATS.copy() for tid in all_time_ids}
            
            classificacao_anterior = Classificacao.objects.filter(rodada=self.numero_rodada - 1)

            for c in classificacao_anterior:
                if c.time_id in stats_base:
                    stats_base[c.time_id] = {
                        "pontos": c.pontos, "vitorias": c.vitorias, "empates": c.empates, "derrotas": c.derrotas,
                        "gols_marcados": c.gols_marcados, "gols_sofridos": c.gols_sofridos, "saldo_gols": c.saldo_gols,
                        "cartoes_amarelos": c.cartoes_amarelos, "cartoes_vermelhos": c.cartoes_vermelhos
                    }
        
        for time_id, stats in stats_base.items():
            obj, created = Classificacao.objects.get_or_create(
                time_id=time_id,
                rodada=self.numero_rodada,
                defaults=stats
            )
            if not created:
                for key, value in stats.items():
                    setattr(obj, key, value)
            self.class_rodada_map[time_id] = obj


    def _atualizar_estatisticas(self, classificacao_obj, gols_marcados, gols_sofridos, cartoes_amarelos, cartoes_vermelhos):
        classificacao_obj.gols_marcados += gols_marcados
        classificacao_obj.gols_sofridos += gols_sofridos

        classificacao_obj.cartoes_amarelos += cartoes_amarelos
        classificacao_obj.cartoes_vermelhos += cartoes_vermelhos

        if gols_marcados > gols_sofridos:
            classificacao_obj.pontos += 3
            classificacao_obj.vitorias += 1
        elif gols_marcados == gols_sofridos:
            classificacao_obj.pontos += 1
            classificacao_obj.empates += 1


    def _processar_partidas(self):
        partidas_da_rodada = Partida.objects.filter(rodada=self.numero_rodada).select_related(
            "mandante", "visitante"
        )
        
        for partida in partidas_da_rodada:
            if partida.gols_mandante is None or partida.gols_visitante is None:
                continue

            if partida.mandante_id not in self.class_rodada_map or partida.visitante_id not in self.class_rodada_map:
                print(f"Alerta: Time da partida ID {partida.id} não encontrado no mapa de classificação da rodada {self.numero_rodada}.")
                continue

            class_mandante = self.class_rodada_map[partida.mandante_id]
            class_visitante = self.class_rodada_map[partida.visitante_id]

            self._atualizar_estatisticas(
                classificacao_obj=class_mandante,
                gols_marcados=partida.gols_mandante,
                gols_sofridos=partida.gols_visitante,
                cartoes_amarelos=partida.cartoes_amarelos_mandante,
                cartoes_vermelhos=partida.cartoes_vermelhos_mandante
            )

            self._atualizar_estatisticas(
                classificacao_obj=class_visitante,
                gols_marcados=partida.gols_visitante,
                gols_sofridos=partida.gols_mandante,
                cartoes_amarelos=partida.cartoes_amarelos_visitante,
                cartoes_vermelhos=partida.cartoes_vermelhos_visitante
            )

            if partida.gols_mandante > partida.gols_visitante:
                class_visitante.derrotas += 1
            elif partida.gols_visitante > partida.gols_mandante:
                class_mandante.derrotas += 1
        
        self.objetos_para_atualizar = list(self.class_rodada_map.values())
        
    
    def _finalizar_e_salvar(self):
        campos_para_atualizar = [
            "pontos", "vitorias", "empates", "derrotas",
            "gols_marcados", "gols_sofridos", "saldo_gols",
            "cartoes_amarelos", "cartoes_vermelhos"
        ]

        for class_obj in self.objetos_para_atualizar:
            class_obj.saldo_gols = class_obj.gols_marcados - class_obj.gols_sofridos

        Classificacao.objects.bulk_update(
            self.objetos_para_atualizar,
            campos_para_atualizar,
        )

@transaction.atomic
def calcular_classificacao_rodada(numero_rodada):
    ClassificacaoProcessor(numero_rodada)