from django.contrib import admin
from .models import Time, Partida, Classificacao
from django.http import HttpResponseRedirect
from django.urls import reverse

class RodadaFilter(admin.SimpleListFilter):
    title = 'por rodada'
    parameter_name = 'rodada'

    def lookups(self, request, model_admin):
        rodadas = Classificacao.objects.values_list(
            'rodada', flat=True
        ).distinct().order_by('rodada')
        
        return [(r, f'Rodada {r}') for r in rodadas]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(rodada=self.value())
        return queryset


class TimeAdmin(admin.ModelAdmin):
    list_display = ('nome',)
    search_fields = ('nome',)
    ordering = ('nome',)

class PartidaAdmin(admin.ModelAdmin):
    list_display = ('rodada', 'mandante', 'gols_mandante', 'gols_visitante', 'visitante')
    list_filter = (RodadaFilter, 'mandante', 'visitante') 
    search_fields = ('mandante__nome', 'visitante__nome')
    
    list_per_page = 25 

class ClassificacaoAdmin(admin.ModelAdmin):
    list_display = ('posicao_formatada', 'rodada', 'time', 'pontos', 'vitorias', 'saldo_gols', 'gols_marcados')
    list_filter = (RodadaFilter, 'time') 
    
    def changelist_view(self, request, extra_context=None):
        if not request.GET:
            latest_rodada = Classificacao.objects.order_by(
                '-rodada'
            ).values_list('rodada', flat=True).first()
            
            if latest_rodada:
                changelist_url = reverse(
                    'admin:campeonato_classificacao_changelist'
                )
                return HttpResponseRedirect(
                    f"{changelist_url}?rodada={latest_rodada}"
                )
        
        return super().changelist_view(request, extra_context)

    def get_sortable_by(self, request):
        return []


    def posicao_formatada(self, obj):
        qs = Classificacao.objects.filter(rodada=obj.rodada)
        
        try:
            lista_classificacao = list(qs)
            posicao = lista_classificacao.index(obj) + 1
            return f"{posicao}º"
        except ValueError:
            return "-"

    posicao_formatada.short_description = "Posição"
    posicao_formatada.admin_order_field = None 

admin.site.register(Time, TimeAdmin)
admin.site.register(Partida, PartidaAdmin)
admin.site.register(Classificacao, ClassificacaoAdmin)