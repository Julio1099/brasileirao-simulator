import random
from django.db import transaction
from .models import Time, Partida, Classificacao

def gerar_calendario():
    Partida.objects.all().delete()
    Classificacao.objects.all().delete()

    times = list(Time.objects.all())
    if len(times) != 20:
        raise ValueError("O campeonato deve ter exatamente 20 times cadastrados.")

    random.shuffle(times)

    n = len(times)
    num_rodadas_turno = n - 1
    partidas_por_rodada = {i: [] for i in range(1, (num_rodadas_turno * 2) + 1)}
    ultimo_local = {time.id: None for time in times}

    times_rotacao = times[:]
    
    todas_partidas_objs = []

    for rodada_num in range(1, num_rodadas_turno + 1):
        pares_rodada = []
        metade = n // 2
        pares_rodada.append((times_rotacao[0], times_rotacao[-1]))
        for i in range(1, metade):
            pares_rodada.append((times_rotacao[i], times_rotacao[n - 1 - i]))

        jogos_rodada_atual_turno = []
        rodada_returno_num = rodada_num + num_rodadas_turno
        jogos_rodada_atual_returno = []

        for t1, t2 in pares_rodada:
            t1_pode_casa = ultimo_local[t1.id] != 'home'
            t2_pode_fora = ultimo_local[t2.id] != 'away'
            t2_pode_casa = ultimo_local[t2.id] != 'home'
            t1_pode_fora = ultimo_local[t1.id] != 'away'

            mandante, visitante = None, None

            if t1_pode_casa and t2_pode_fora:
                mandante, visitante = t1, t2
            elif t2_pode_casa and t1_pode_fora:
                mandante, visitante = t2, t1
            else:
                idx_par = pares_rodada.index((t1,t2))
                if (rodada_num + idx_par) % 2 == 0:
                    mandante, visitante = t1, t2
                else:
                    mandante, visitante = t2, t1

            partida_turno = Partida(rodada=rodada_num, mandante=mandante, visitante=visitante)
            todas_partidas_objs.append(partida_turno)
            ultimo_local[mandante.id] = 'home'
            ultimo_local[visitante.id] = 'away'

            partida_returno = Partida(rodada=rodada_returno_num, mandante=visitante, visitante=mandante)
            todas_partidas_objs.append(partida_returno)


        times_rotacao.insert(1, times_rotacao.pop())


    partidas_organizadas = {}
    for p in todas_partidas_objs:
        if p.rodada not in partidas_organizadas:
            partidas_organizadas[p.rodada] = []
        partidas_organizadas[p.rodada].append(p)

    partidas_finais_para_salvar = []
    for rodada_num in sorted(partidas_organizadas.keys()):
        jogos_da_rodada = partidas_organizadas[rodada_num]
        random.shuffle(jogos_da_rodada)
        partidas_finais_para_salvar.extend(jogos_da_rodada)
        
    Partida.objects.bulk_create(partidas_finais_para_salvar)

    print(
        f"Calendário com {Partida.objects.count()} jogos em {num_rodadas_turno * 2} rodadas gerado."
    )


@transaction.atomic
def calcular_classificacao_rodada(numero_rodada):

    stats_base = {}
    if numero_rodada == 1:
        for time in Time.objects.all():
            stats_base[time.id] = {
                "pontos": 0, "vitorias": 0, "empates": 0, "derrotas": 0,
                "gols_marcados": 0, "gols_sofridos": 0, "saldo_gols": 0,
                "cartoes_amarelos": 0, "cartoes_vermelhos": 0
            }
    else:
        classificacao_anterior = Classificacao.objects.filter(rodada=numero_rodada - 1)
        all_time_ids = Time.objects.values_list('id', flat=True)
        stats_base = {tid: {
                "pontos": 0, "vitorias": 0, "empates": 0, "derrotas": 0,
                "gols_marcados": 0, "gols_sofridos": 0, "saldo_gols": 0,
                "cartoes_amarelos": 0, "cartoes_vermelhos": 0
            } for tid in all_time_ids}

        for c in classificacao_anterior:
            if c.time_id in stats_base:
                stats_base[c.time_id] = {
                    "pontos": c.pontos, "vitorias": c.vitorias, "empates": c.empates, "derrotas": c.derrotas,
                    "gols_marcados": c.gols_marcados, "gols_sofridos": c.gols_sofridos, "saldo_gols": c.saldo_gols,
                    "cartoes_amarelos": c.cartoes_amarelos, "cartoes_vermelhos": c.cartoes_vermelhos
                }

    class_rodada_map = {}
    for time_id, stats in stats_base.items():
          obj, created = Classificacao.objects.get_or_create(
              time_id=time_id,
              rodada=numero_rodada,
              defaults=stats
          )
          if not created:
              for key, value in stats.items():
                  setattr(obj, key, value)
          class_rodada_map[time_id] = obj


    partidas_da_rodada = Partida.objects.filter(rodada=numero_rodada).select_related(
        "mandante", "visitante"
    )

    for partida in partidas_da_rodada:
        if partida.gols_mandante is None or partida.gols_visitante is None:
            continue

        if partida.mandante_id not in class_rodada_map or partida.visitante_id not in class_rodada_map:
             print(f"Alerta: Time da partida ID {partida.id} não encontrado no mapa de classificação da rodada {numero_rodada}.")
             continue

        class_mandante = class_rodada_map[partida.mandante_id]
        class_visitante = class_rodada_map[partida.visitante_id]


        class_mandante.gols_marcados += partida.gols_mandante
        class_mandante.gols_sofridos += partida.gols_visitante
        class_visitante.gols_marcados += partida.gols_visitante
        class_visitante.gols_sofridos += partida.gols_mandante

        class_mandante.cartoes_amarelos += partida.cartoes_amarelos_mandante
        class_mandante.cartoes_vermelhos += partida.cartoes_vermelhos_mandante
        class_visitante.cartoes_amarelos += partida.cartoes_amarelos_visitante
        class_visitante.cartoes_vermelhos += partida.cartoes_vermelhos_visitante

        if partida.gols_mandante > partida.gols_visitante:
            class_mandante.pontos += 3
            class_mandante.vitorias += 1
            class_visitante.derrotas += 1
        elif partida.gols_visitante > partida.gols_mandante:
            class_visitante.pontos += 3
            class_visitante.vitorias += 1
            class_mandante.derrotas += 1
        else:
            class_mandante.pontos += 1
            class_visitante.pontos += 1
            class_mandante.empates += 1
            class_visitante.empates += 1

    objetos_para_atualizar = []
    campos_para_atualizar = [
                "pontos", "vitorias", "empates", "derrotas",
                "gols_marcados", "gols_sofridos", "saldo_gols",
                "cartoes_amarelos", "cartoes_vermelhos"
            ]

    for class_obj in class_rodada_map.values():
        class_obj.saldo_gols = class_obj.gols_marcados - class_obj.gols_sofridos
        objetos_para_atualizar.append(class_obj)

    Classificacao.objects.bulk_update(
        objetos_para_atualizar,
        campos_para_atualizar,
    )