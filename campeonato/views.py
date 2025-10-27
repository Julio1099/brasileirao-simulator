from django.shortcuts import render, get_object_or_404
from .models import Classificacao, Partida, Time
from django.db.models import Q, Max 


def tabela_classificacao(request, rodada_num=None):

    rodadas_disponiveis = (
        Classificacao.objects.order_by("rodada")
        .values_list("rodada", flat=True)
        .distinct()
    )

    if not rodadas_disponiveis.exists():
        return render(request, "campeonato/tabela.html", {"tabela": None})

    if rodada_num:
        rodada_selecionada = int(rodada_num)
    else:
        rodada_selecionada = rodadas_disponiveis.last()

    tabela_atual = list(
        Classificacao.objects.filter(rodada=rodada_selecionada).select_related("time")
    )

    partidas_da_rodada = (
        Partida.objects.filter(rodada=rodada_selecionada)
        .select_related("mandante", "visitante")
        .order_by("id")
    )

    tabela_enriquecida = []

    if rodada_selecionada > 1:
        tabela_anterior = list(
            Classificacao.objects.filter(rodada=rodada_selecionada - 1)
        )

        mapa_posicao_anterior = {
            item.time_id: (idx + 1) for idx, item in enumerate(tabela_anterior)
        }

        for idx, item in enumerate(tabela_atual):
            posicao_atual = idx + 1
            posicao_anterior = mapa_posicao_anterior.get(item.time_id, posicao_atual)

            item.variacao = posicao_anterior - posicao_atual
            tabela_enriquecida.append(item)

    else:
        for item in tabela_atual:
            item.variacao = 0 
            tabela_enriquecida.append(item)

    contexto = {
        "tabela": tabela_enriquecida, 
        "partidas_da_rodada": partidas_da_rodada, 
        "rodada_selecionada": rodada_selecionada,
        "todas_rodadas": rodadas_disponiveis,
    }

    return render(request, "campeonato/tabela.html", contexto)


def detalhes_time(request, time_id):
    time = get_object_or_404(Time, id=time_id)

    partidas_db = (
        Partida.objects.filter(Q(mandante=time) | Q(visitante=time))
        .order_by("rodada")
        .select_related("mandante", "visitante")
    )

    partidas_processadas = []
    for partida in partidas_db:
        if partida.gols_mandante is None or partida.gols_visitante is None:
            continue
            
        eh_mandante = partida.mandante == time

        if (eh_mandante and partida.gols_mandante > partida.gols_visitante) or (
            not eh_mandante and partida.gols_visitante > partida.gols_mandante
        ):
            resultado_cor = "bg-green-600"
            resultado_texto = "V"
        elif (eh_mandante and partida.gols_mandante < partida.gols_visitante) or (
            not eh_mandante and partida.gols_visitante < partida.gols_mandante
        ):
            resultado_cor = "bg-red-600"
            resultado_texto = "D"
        else:
            resultado_cor = "bg-yellow-600"
            resultado_texto = "E"

        partidas_processadas.append({
            'partida': partida,
            'eh_mandante': eh_mandante,
            'resultado_cor': resultado_cor,
            'resultado_texto': resultado_texto,
        })

    contexto = {
        "time": time,
        "partidas_processadas": partidas_processadas 
    }
    return render(request, "campeonato/detalhes_time.html", contexto)