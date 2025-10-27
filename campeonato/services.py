# campeonato/services.py

import random
from django.db import transaction
from .models import Time, Partida, Classificacao

def gerar_calendario():
    """
    Gera o calendário completo usando o algoritmo Round-Robin,
    com lógica aprimorada para priorizar a alternância de jogos
    em casa e fora para cada time e corrigindo o número de jogos gerados.
    """
    Partida.objects.all().delete()
    Classificacao.objects.all().delete()

    times = list(Time.objects.all())
    if len(times) != 20:
        raise ValueError("O campeonato deve ter exatamente 20 times cadastrados.")

    # Embaralha os times para garantir um sorteio diferente a cada vez
    random.shuffle(times)

    n = len(times)
    num_rodadas_turno = n - 1
    partidas_por_rodada = {i: [] for i in range(1, (num_rodadas_turno * 2) + 1)}
    ultimo_local = {time.id: None for time in times}

    # Copia a lista para rotação, mantendo a original intacta se necessário
    times_rotacao = times[:] 
    
    # Armazena temporariamente todas as partidas antes de salvar
    todas_partidas_objs = [] 

    for rodada_num in range(1, num_rodadas_turno + 1):
        pares_rodada = []
        # --- CORREÇÃO NA LÓGICA DE PAREAMENTO ---
        metade = n // 2
        # Par 1: Time fixo (índice 0) contra o último time da lista rotacionada
        pares_rodada.append((times_rotacao[0], times_rotacao[-1]))
        # Pares restantes: Simetricamente do início e fim da lista rotacionada
        for i in range(1, metade):
            pares_rodada.append((times_rotacao[i], times_rotacao[n - 1 - i]))
        # --- FIM DA CORREÇÃO ---

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
                 # Fallback: Regra original baseada na rodada/índice
                 # Usamos o índice do par na lista 'pares_rodada'
                 idx_par = pares_rodada.index((t1,t2)) # Acha o índice do par atual
                 if (rodada_num + idx_par) % 2 == 0:
                     mandante, visitante = t1, t2
                 else:
                     mandante, visitante = t2, t1

            # Cria objeto Partida do turno e atualiza último local
            partida_turno = Partida(rodada=rodada_num, mandante=mandante, visitante=visitante)
            todas_partidas_objs.append(partida_turno)
            ultimo_local[mandante.id] = 'home'
            ultimo_local[visitante.id] = 'away'

            # Cria objeto Partida do returno (invertendo mando)
            partida_returno = Partida(rodada=rodada_returno_num, mandante=visitante, visitante=mandante)
            todas_partidas_objs.append(partida_returno)


        # Rotaciona a lista (exceto o primeiro time 'times_rotacao[0]')
        times_rotacao.insert(1, times_rotacao.pop())


    # --- Salva todas as partidas de uma vez após gerar todas ---
    # Embaralha a ordem dos jogos DENTRO de cada rodada ANTES de salvar
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
    # --- Fim da reorganização e salvamento ---

    print(
        f"Calendário com {Partida.objects.count()} jogos em {num_rodadas_turno * 2} rodadas gerado."
    )


@transaction.atomic
def calcular_classificacao_rodada(numero_rodada):
    """
    Calcula e salva a classificação para todos os times
    APÓS os jogos da rodada 'numero_rodada' terem seus
    resultados preenchidos. Inclui cálculo de cartões.
    """

    # 1. Obter estatísticas da rodada anterior (ou zerar se for a primeira)
    stats_base = {}
    if numero_rodada == 1:
        for time in Time.objects.all():
            stats_base[time.id] = {
                "pontos": 0, "vitorias": 0, "empates": 0, "derrotas": 0,
                "gols_marcados": 0, "gols_sofridos": 0, "saldo_gols": 0,
                "cartoes_amarelos": 0, "cartoes_vermelhos": 0 # Inicializa cartões
            }
    else:
        classificacao_anterior = Classificacao.objects.filter(rodada=numero_rodada - 1)
        # Garante que temos stats base para todos os times, caso algum não esteja na rodada anterior (não deve acontecer)
        all_time_ids = Time.objects.values_list('id', flat=True)
        stats_base = {tid: {
                "pontos": 0, "vitorias": 0, "empates": 0, "derrotas": 0,
                "gols_marcados": 0, "gols_sofridos": 0, "saldo_gols": 0,
                "cartoes_amarelos": 0, "cartoes_vermelhos": 0
            } for tid in all_time_ids}

        for c in classificacao_anterior:
            # Só atualiza se o time existir no stats_base (segurança)
            if c.time_id in stats_base:
                stats_base[c.time_id] = {
                    "pontos": c.pontos, "vitorias": c.vitorias, "empates": c.empates, "derrotas": c.derrotas,
                    "gols_marcados": c.gols_marcados, "gols_sofridos": c.gols_sofridos, "saldo_gols": c.saldo_gols,
                    "cartoes_amarelos": c.cartoes_amarelos, "cartoes_vermelhos": c.cartoes_vermelhos # Carrega cartões
                }

    # 2. Criar ou obter entradas de classificação para a rodada atual
    class_rodada_map = {}
    for time_id, stats in stats_base.items():
         # Tenta buscar, se não existir, cria com os defaults
         obj, created = Classificacao.objects.get_or_create(
             time_id=time_id,
             rodada=numero_rodada,
             defaults=stats # Usa os stats base se for criar
         )
         # Se já existia (não foi criado), reseta para os stats da rodada anterior
         # antes de aplicar os resultados da rodada atual.
         if not created:
             for key, value in stats.items():
                 setattr(obj, key, value)
         class_rodada_map[time_id] = obj


    # 3. Processar os resultados da rodada atual
    partidas_da_rodada = Partida.objects.filter(rodada=numero_rodada).select_related(
        "mandante", "visitante"
    )

    for partida in partidas_da_rodada:
        # Pula partidas sem resultado simulado
        if partida.gols_mandante is None or partida.gols_visitante is None:
            continue

        # Pega os objetos Classificacao corretos do mapa
        # Adiciona verificação se o ID existe no mapa (robustez)
        if partida.mandante_id not in class_rodada_map or partida.visitante_id not in class_rodada_map:
             print(f"Alerta: Time da partida ID {partida.id} não encontrado no mapa de classificação da rodada {numero_rodada}.")
             continue

        class_mandante = class_rodada_map[partida.mandante_id]
        class_visitante = class_rodada_map[partida.visitante_id]


        # REQUISITO 4: Atualiza Gols
        class_mandante.gols_marcados += partida.gols_mandante
        class_mandante.gols_sofridos += partida.gols_visitante
        class_visitante.gols_marcados += partida.gols_visitante
        class_visitante.gols_sofridos += partida.gols_mandante

        # Atualiza Cartões
        class_mandante.cartoes_amarelos += partida.cartoes_amarelos_mandante
        class_mandante.cartoes_vermelhos += partida.cartoes_vermelhos_mandante
        class_visitante.cartoes_amarelos += partida.cartoes_amarelos_visitante
        class_visitante.cartoes_vermelhos += partida.cartoes_vermelhos_visitante

        # REQUISITO 3: Atualiza Pontuação e Vitórias/Empates/Derrotas
        if partida.gols_mandante > partida.gols_visitante:
            class_mandante.pontos += 3
            class_mandante.vitorias += 1
            class_visitante.derrotas += 1
        elif partida.gols_visitante > partida.gols_mandante:
            class_visitante.pontos += 3
            class_visitante.vitorias += 1
            class_mandante.derrotas += 1
        else: # Empate
            class_mandante.pontos += 1
            class_visitante.pontos += 1
            class_mandante.empates += 1
            class_visitante.empates += 1

    # 4. Atualiza Saldo de Gols (Req 4) e salva tudo
    objetos_para_atualizar = []
    campos_para_atualizar = [
            "pontos", "vitorias", "empates", "derrotas",
            "gols_marcados", "gols_sofridos", "saldo_gols",
            "cartoes_amarelos", "cartoes_vermelhos" # Inclui cartões na atualização
        ]

    for class_obj in class_rodada_map.values():
        class_obj.saldo_gols = class_obj.gols_marcados - class_obj.gols_sofridos
        objetos_para_atualizar.append(class_obj)

    # Usa bulk_update para eficiência
    Classificacao.objects.bulk_update(
        objetos_para_atualizar,
        campos_para_atualizar,
    )

