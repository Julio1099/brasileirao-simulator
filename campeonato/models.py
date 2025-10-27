# campeonato/models.py

from django.db import models


class Time(models.Model):
    nome = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.nome


class Partida(models.Model):
    rodada = models.IntegerField(db_index=True)

    mandante = models.ForeignKey(
        Time, on_delete=models.CASCADE, related_name="partidas_como_mandante"
    )
    visitante = models.ForeignKey(
        Time, on_delete=models.CASCADE, related_name="partidas_como_visitante"
    )
    gols_mandante = models.IntegerField(null=True, blank=True)
    gols_visitante = models.IntegerField(null=True, blank=True)

    cartoes_amarelos_mandante = models.IntegerField(default=0)
    cartoes_vermelhos_mandante = models.IntegerField(default=0)
    cartoes_amarelos_visitante = models.IntegerField(default=0)
    cartoes_vermelhos_visitante = models.IntegerField(default=0)


    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["mandante", "visitante"], name="partida_unica"
            )
        ]

    def __str__(self):
        return f"Rodada {self.rodada}: {self.mandante} vs {self.visitante}"

    @property
    def finalizada(self):
        return self.gols_mandante is not None and self.gols_visitante is not None


class Classificacao(models.Model):
    time = models.ForeignKey(
        Time, on_delete=models.CASCADE, related_name="classificacoes"
    )
    rodada = models.IntegerField()
    pontos = models.IntegerField(default=0)
    vitorias = models.IntegerField(default=0)
    empates = models.IntegerField(default=0)
    derrotas = models.IntegerField(default=0)
    gols_marcados = models.IntegerField(default=0)
    gols_sofridos = models.IntegerField(default=0)
    saldo_gols = models.IntegerField(default=0)
    cartoes_amarelos = models.IntegerField(default=0)
    cartoes_vermelhos = models.IntegerField(default=0)

    class Meta:
        ordering = [  # ordem dos critérios de desempate
            "rodada",
            "-pontos",         # 1. Mais Pontos
            "-vitorias",       # 2. Mais Vitórias
            "-saldo_gols",     # 3. Maior Saldo de Gols
            "-gols_marcados",  # 4. Mais Gols Marcados
            "cartoes_vermelhos", # 5. Menor Nº de Cartões Vermelhos
            "cartoes_amarelos", # 6. Menor Nº de Cartões Amarelos
            "time__nome",      # Critério final: Ordem alfabética
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["time", "rodada"], name="classificacao_unica_por_rodada"
            )
        ]

    def __str__(self):
        return f"{self.time.nome} (Rodada {self.rodada}) - {self.pontos} Pts"
