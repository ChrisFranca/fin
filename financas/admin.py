from django.contrib import admin
from .models import MembroFamilia, Categoria, Conta, Transacao, Tag, Orcamento, MetaEconomia

@admin.register(Transacao)
class TransacaoAdmin(admin.ModelAdmin):
    list_display = ('data', 'descricao', 'valor', 'categoria', 'conta', 'status')
    list_filter = ('data', 'status', 'categoria', 'conta')
    search_fields = ('descricao', 'observacao')

admin.site.register(MembroFamilia)
admin.site.register(Categoria)
admin.site.register(Conta)
admin.site.register(Tag)
admin.site.register(Orcamento)
admin.site.register(MetaEconomia)
