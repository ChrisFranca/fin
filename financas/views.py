from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Sum, Q
from django.db import models
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from .models import Transacao, Categoria, Conta, MetaEconomia, Orcamento, MembroFamilia, Recorrencia, RegraImportacao, Tag, RelatorioPersonalizado
from .forms import TransacaoForm, TransferenciaForm, CategoriaForm, ContaForm, MembroFamiliaForm, TagForm, RelatorioPersonalizadoForm
import requests
from datetime import datetime, date
import pandas as pd
import json
from xhtml2pdf import pisa
from django.template.loader import get_template
from io import BytesIO
from ofxparse import OfxParser
import google.generativeai as genai
import markdown
from django.conf import settings

from dateutil.relativedelta import relativedelta
import calendar

def processar_recorrencias():
    """
    Verifica e gera transações para recorrências ativas que ainda não foram 
    lançadas no mês atual, caso o dia de vencimento já tenha passado.
    """
    hoje = datetime.now()
    recorrencias = Recorrencia.objects.filter(ativa=True)
    for r in recorrencias:
        try:
            data_vencimento = date(hoje.year, hoje.month, r.dia_vencimento)
        except ValueError:
            ultimo_dia = calendar.monthrange(hoje.year, hoje.month)[1]
            data_vencimento = date(hoje.year, hoje.month, ultimo_dia)
            
        existe = Transacao.objects.filter(
            descricao=f"{r.descricao} (Recorrente)",
            data__month=hoje.month,
            data__year=hoje.year,
            conta=r.conta
        ).exists()
        
        if not existe and data_vencimento <= hoje.date():
            Transacao.objects.create(
                descricao=f"{r.descricao} (Recorrente)",
                valor=r.valor,
                data=data_vencimento,
                categoria=r.categoria,
                conta=r.conta,
                membro=r.membro,
                status='P',
                recorrente=True
            )

def dashboard(request):
    """
    View principal que processa dados financeiros para exibição de indicadores,
    gráficos dinâmicos e comparativo de orçamentos.
    """
    processar_recorrencias()
    hoje = datetime.now()
    mes_sel = int(request.GET.get('mes', hoje.month))
    ano_sel = int(request.GET.get('ano', hoje.year))
    membro_id = request.GET.get('membro')

    # Dados do mês selecionado (exclui transferências do fluxo geral para não distorcer gráficos)
    transacoes_mes = Transacao.objects.filter(data__month=mes_sel, data__year=ano_sel, eh_transferencia=False)
    if membro_id: transacoes_mes = transacoes_mes.filter(membro_id=membro_id)

    receitas = transacoes_mes.filter(categoria__tipo='R').aggregate(Sum('valor'))['valor__sum'] or 0
    despesas = transacoes_mes.filter(categoria__tipo='D').aggregate(Sum('valor'))['valor__sum'] or 0
    gastos_categoria = transacoes_mes.filter(categoria__tipo='D').values('categoria__nome').annotate(total=Sum('valor')).order_by('-total')
    
    # Orçamentos do mês selecionado
    orcamentos = Orcamento.objects.filter(mes=mes_sel, ano=ano_sel)
    status_orcamentos = []
    for o in orcamentos:
        gasto = o.gasto_atual()
        porcentagem = (gasto / o.valor_limite * 100) if o.valor_limite > 0 else 0
        if porcentagem >= 80 and o.mes == hoje.month and o.ano == hoje.year:
            messages.warning(request, f"Atenção: Orçamento de '{o.categoria.nome}' está em {porcentagem:.0f}%!")
        status_orcamentos.append({
            'categoria': o.categoria.nome,
            'limite': o.valor_limite,
            'gasto': gasto,
            'porcentagem': min(float(porcentagem), 100),
            'cor': 'danger' if porcentagem > 100 else 'warning' if porcentagem > 80 else 'success'
        })

    # Gráfico de Linha (Fluxo de Caixa Dinâmico dos últimos 6 meses)
    labels_linha = []
    data_receita = []
    data_despesa = []
    
    for i in range(5, -1, -1):
        data_aux = hoje - relativedelta(months=i)
        mes_aux = data_aux.month
        ano_aux = data_aux.year
        
        meses_nomes = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
        labels_linha.append(meses_nomes[mes_aux-1])
        
        trans_mes_aux = Transacao.objects.filter(data__month=mes_aux, data__year=ano_aux, eh_transferencia=False)
        if membro_id: trans_mes_aux = trans_mes_aux.filter(membro_id=membro_id)
        
        rec_aux = trans_mes_aux.filter(categoria__tipo='R').aggregate(Sum('valor'))['valor__sum'] or 0
        desp_aux = trans_mes_aux.filter(categoria__tipo='D').aggregate(Sum('valor'))['valor__sum'] or 0
        
        data_receita.append(float(rec_aux))
        data_despesa.append(float(desp_aux))

    # Previsão de Saldo e Comparativo Anual
    saldo_atual_total = sum([c.saldo_atual() for c in Conta.objects.all()])
    receitas_pendentes = Transacao.objects.filter(categoria__tipo='R', status='P', data__month=hoje.month, data__year=hoje.year).aggregate(Sum('valor'))['valor__sum'] or 0
    despesas_pendentes = Transacao.objects.filter(categoria__tipo='D', status='P', data__month=hoje.month, data__year=hoje.year).aggregate(Sum('valor'))['valor__sum'] or 0
    saldo_projetado = saldo_atual_total + receitas_pendentes - despesas_pendentes

    despesas_ano_passado = Transacao.objects.filter(categoria__tipo='D', data__month=mes_sel, data__year=ano_sel-1, eh_transferencia=False).aggregate(Sum('valor'))['valor__sum'] or 0

    context = {
        'mes_selecionado': mes_sel, 'ano_selecionado': ano_sel, 'meses': range(1, 13), 'anos': range(hoje.year - 2, hoje.year + 2),
        'membros': MembroFamilia.objects.all(), 'membro_selecionado': int(membro_id) if membro_id else None,
        'receitas': receitas, 'despesas': despesas, 'saldo_mes': receitas - despesas,
        'saldo_total': saldo_atual_total,
        'saldo_projetado': saldo_projetado,
        'despesas_ano_passado': despesas_ano_passado,
        'contas': Conta.objects.all(), 'metas': MetaEconomia.objects.all(),
        'status_orcamentos': status_orcamentos,
        'labels_pizza': json.dumps([item['categoria__nome'] for item in gastos_categoria]),
        'data_pizza': json.dumps([float(item['total']) for item in gastos_categoria]),
        'labels_linha': json.dumps(labels_linha),
        'data_receita': json.dumps(data_receita),
        'data_despesa': json.dumps(data_despesa),
        'ultimas_transacoes': Transacao.objects.filter(data__month=mes_sel, data__year=ano_sel).order_by('-data')[:10],
    }
    return render(request, 'financas/dashboard.html', context)

def transacao_eventos_json(request):
    transacoes = Transacao.objects.all()
    eventos = []
    for t in transacoes:
        eventos.append({
            'title': f"{'+' if t.categoria.tipo == 'R' else '-'} R$ {t.valor} {t.descricao}",
            'start': t.data.isoformat(),
            'color': '#198754' if t.categoria.tipo == 'R' else '#dc3545',
            'allDay': True
        })
    return JsonResponse(eventos, safe=False)

def calendario(request):
    return render(request, 'financas/calendario.html')

def transacao_confirmar(request, pk):
    t = get_object_or_404(Transacao, pk=pk); t.status = 'C'; t.save()
    messages.success(request, f"Transação '{t.descricao}' confirmada com sucesso!")
    return redirect(request.META.get('HTTP_REFERER', 'transacao_list'))

def transacao_excluir(request, pk):
    t = get_object_or_404(Transacao, pk=pk); t.delete()
    messages.success(request, "Transação excluída.")
    return redirect(request.META.get('HTTP_REFERER', 'transacao_list'))

def ajuda(request): return render(request, 'financas/ajuda.html')

def gerar_relatorio_pdf(request):
    mes = request.GET.get('mes', datetime.now().month); ano = request.GET.get('ano', datetime.now().year)
    transacoes = Transacao.objects.filter(data__month=mes, data__year=ano)
    receitas = transacoes.filter(categoria__tipo='R').aggregate(Sum('valor'))['valor__sum'] or 0
    despesas = transacoes.filter(categoria__tipo='D').aggregate(Sum('valor'))['valor__sum'] or 0
    data = {'transacoes': transacoes, 'receitas': receitas, 'despesas': despesas, 'saldo': receitas - despesas, 'mes': mes, 'ano': ano, 'data_geracao': datetime.now()}
    template = get_template('financas/relatorio_pdf.html'); html = template.render(data)
    result = BytesIO(); pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)
    return HttpResponse(result.getvalue(), content_type='application/pdf')

class TransacaoListView(ListView):
    model = Transacao; template_name = 'financas/transacao_list.html'; context_object_name = 'transacoes'; ordering = ['-data']
    def get_queryset(self):
        qs = super().get_queryset(); q = self.request.GET.get('q'); conta_id = self.request.GET.get('conta')
        if q: qs = qs.filter(Q(descricao__icontains=q) | Q(observacao__icontains=q) | Q(categoria__nome__icontains=q) | Q(membro__nome__icontains=q) | Q(conta__nome__icontains=q))
        if conta_id: qs = qs.filter(conta_id=conta_id)
        return qs

class TransacaoCreateView(CreateView):
 
    model = Transacao; form_class = TransacaoForm; template_name = 'financas/form_generico.html'; success_url = reverse_lazy('transacao_list')
    def form_valid(self, form):
        messages.success(self.request, "Transação criada com sucesso!")
        return super().form_valid(form)

class ContaListView(ListView): model = Conta; template_name = 'financas/conta_list.html'; context_object_name = 'contas'
class ContaCreateView(CreateView): model = Conta; form_class = ContaForm; template_name = 'financas/form_generico.html'; success_url = reverse_lazy('conta_list')
class ContaUpdateView(UpdateView): model = Conta; form_class = ContaForm; template_name = 'financas/form_generico.html'; success_url = reverse_lazy('conta_list')
class ContaDeleteView(DeleteView): model = Conta; template_name = 'financas/confirm_delete.html'; success_url = reverse_lazy('conta_list')

class MetaListView(ListView): model = MetaEconomia; template_name = 'financas/meta_list.html'; context_object_name = 'metas'
class MetaCreateView(CreateView): model = MetaEconomia; fields = ['nome', 'valor_objetivo', 'valor_poupado', 'data_limite']; template_name = 'financas/form_generico.html'; success_url = reverse_lazy('meta_list')
class MetaUpdateView(UpdateView): model = MetaEconomia; fields = ['nome', 'valor_objetivo', 'valor_poupado', 'data_limite']; template_name = 'financas/form_generico.html'; success_url = reverse_lazy('meta_list')
class MetaDeleteView(DeleteView): model = MetaEconomia; template_name = 'financas/confirm_delete.html'; success_url = reverse_lazy('meta_list')

class CategoriaListView(ListView): model = Categoria; template_name = 'financas/categoria_list.html'; context_object_name = 'categorias'
class CategoriaCreateView(CreateView): model = Categoria; form_class = CategoriaForm; template_name = 'financas/form_generico.html'; success_url = reverse_lazy('categoria_list')
class CategoriaUpdateView(UpdateView): model = Categoria; form_class = CategoriaForm; template_name = 'financas/form_generico.html'; success_url = reverse_lazy('categoria_list')
class CategoriaDeleteView(DeleteView): model = Categoria; template_name = 'financas/confirm_delete.html'; success_url = reverse_lazy('categoria_list')

class MembroListView(ListView): model = MembroFamilia; template_name = 'financas/membro_list.html'; context_object_name = 'membros'
class MembroCreateView(CreateView): model = MembroFamilia; form_class = MembroFamiliaForm; template_name = 'financas/form_generico.html'; success_url = reverse_lazy('membro_list')
class MembroUpdateView(UpdateView): model = MembroFamilia; form_class = MembroFamiliaForm; template_name = 'financas/form_generico.html'; success_url = reverse_lazy('membro_list')
class MembroDeleteView(DeleteView): model = MembroFamilia; template_name = 'financas/confirm_delete.html'; success_url = reverse_lazy('membro_list')

class TagListView(ListView): model = Tag; template_name = 'financas/tag_list.html'; context_object_name = 'tags'
class TagCreateView(CreateView): model = Tag; form_class = TagForm; template_name = 'financas/form_generico.html'; success_url = reverse_lazy('tag_list')
class TagUpdateView(UpdateView): model = Tag; form_class = TagForm; template_name = 'financas/form_generico.html'; success_url = reverse_lazy('tag_list')
class TagDeleteView(DeleteView): model = Tag; template_name = 'financas/confirm_delete.html'; success_url = reverse_lazy('tag_list')

class OrcamentoListView(ListView):
 model = Orcamento; template_name = 'financas/orcamento_list.html'; context_object_name = 'orcamentos'
class OrcamentoCreateView(CreateView): model = Orcamento; fields = ['categoria', 'valor_limite', 'mes', 'ano']; template_name = 'financas/form_generico.html'; success_url = reverse_lazy('dashboard')

class RecorrenciaListView(ListView):
 model = Recorrencia; template_name = 'financas/recorrencia_list.html'; context_object_name = 'recorrencias'
class RecorrenciaCreateView(CreateView): model = Recorrencia; fields = ['descricao', 'valor', 'dia_vencimento', 'categoria', 'conta', 'membro', 'ativa']; template_name = 'financas/form_generico.html'; success_url = reverse_lazy('recorrencia_list')

def sugestao_categoria(descricao):
    # Regras Inteligentes
    regras = RegraImportacao.objects.all()
    for r in regras:
        if r.descricao_contem.lower() in descricao.lower():
            return r.categoria
    
    ultima = Transacao.objects.filter(descricao__icontains=descricao).order_by('-id').first()
    return ultima.categoria if ultima else Categoria.objects.get_or_create(nome='Geral', tipo='D')[0]

def importar_extrato(request):
    if request.method == 'POST' and request.FILES.get('arquivo'):
        arquivo = request.FILES['arquivo']; conta = Conta.objects.get(id=request.POST.get('conta'))
        count = 0
        if arquivo.name.endswith('.ofx'):
            ofx = OfxParser.parse(arquivo)
            for t in ofx.account.statement.transactions: 
                obj, created = Transacao.objects.get_or_create(descricao=t.memo, valor=abs(t.amount), data=t.date.date(), conta=conta, defaults={'categoria': sugestao_categoria(t.memo), 'status': 'C'})
                if created: count += 1
        elif arquivo.name.endswith('.csv'):
            df = pd.read_csv(arquivo)
            for _, row in df.iterrows(): 
                obj, created = Transacao.objects.get_or_create(descricao=row['descricao'], valor=abs(row['valor']), data=pd.to_datetime(row['data']).date(), conta=conta, defaults={'categoria': sugestao_categoria(row['descricao']), 'status': 'C'})
                if created: count += 1
        messages.success(request, f"{count} transações importadas com sucesso!")
        return redirect('dashboard')
    return render(request, 'financas/importar.html', {'contas': Conta.objects.all()})

def transferencia_create(request):
    if request.method == 'POST':
        form = TransferenciaForm(request.POST)
        if form.valid():
            origem = form.cleaned_data['conta_origem']
            destino = form.cleaned_data['conta_destino']
            valor = form.cleaned_data['valor']
            data = form.cleaned_data['data']
            obs = form.cleaned_data['observacao']
            
            cat_despesa = Categoria.objects.get_or_create(nome='Transferência Saída', tipo='D')[0]
            cat_receita = Categoria.objects.get_or_create(nome='Transferência Entrada', tipo='R')[0]
            
            Transacao.objects.create(descricao=f"Transf. para {destino.nome}", valor=valor, data=data, categoria=cat_despesa, conta=origem, status='C', observacao=obs, eh_transferencia=True)
            Transacao.objects.create(descricao=f"Transf. de {origem.nome}", valor=valor, data=data, categoria=cat_receita, conta=destino, status='C', observacao=obs, eh_transferencia=True)
            
            messages.success(request, "Transferência realizada com sucesso!")
            return redirect('dashboard')
    else:
        form = TransferenciaForm()
    return render(request, 'financas/form_generico.html', {'form': form, 'titulo': 'Nova Transferência'})

class RelatorioListView(ListView):
    model = RelatorioPersonalizado
    template_name = 'financas/relatorio_list.html'
    context_object_name = 'relatorios'

class RelatorioCreateView(CreateView):
    model = RelatorioPersonalizado
    form_class = RelatorioPersonalizadoForm
    template_name = 'financas/form_generico.html'
    success_url = reverse_lazy('relatorio_list')

def gerar_relatorio_ia(request, pk):
    relatorio = get_object_or_404(RelatorioPersonalizado, pk=pk)
    
    # Busca transações para contexto (últimos 3 meses por padrão)
    tres_meses_atras = date.today() - relativedelta(months=3)
    transacoes = Transacao.objects.filter(data__gte=tres_meses_atras).order_by('data')
    
    if relatorio.query_base:
        transacoes = transacoes.filter(Q(descricao__icontains=relatorio.query_base) | Q(categoria__nome__icontains=relatorio.query_base))

    # Formata contexto para a IA
    contexto_transacoes = "Transações recentes:\n"
    for t in transacoes:
        contexto_transacoes += f"- {t.data}: {t.descricao} ({t.categoria.nome}) - R$ {t.valor}\n"

    # Configura Gemini
    api_key = getattr(settings, 'GEMINI_API_KEY', None)
    if not api_key or api_key == 'sua_chave_aqui':
        return render(request, 'financas/relatorio_ia_resultado.html', {
            'relatorio': relatorio,
            'resultado': "Erro: Chave de API do Gemini não configurada no arquivo .env."
        })

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-pro')
        
        prompt = f"""
        Você é um consultor financeiro pessoal experiente. 
        Analise os dados abaixo e gere um relatório baseado no seguinte objetivo: {relatorio.descricao}
        
        Dados de Transações:
        {contexto_transacoes}
        
        Instruções Adicionais:
        - Use um tom profissional mas acolhedor.
        - Se o tipo for 'I' (IA Analítico), foque em insights profundos e sugestões práticas.
        - Formate a resposta em Markdown (use títulos, listas e negrito).
        - Responda em Português do Brasil.
        """
        
        response = model.generate_content(prompt)
        resultado_html = markdown.markdown(response.text)
        
    except Exception as e:
        resultado_html = f"<p class='text-danger'>Erro ao chamar a API do Gemini: {str(e)}</p>"

    return render(request, 'financas/relatorio_ia_resultado.html', {
        'relatorio': relatorio,
        'resultado': resultado_html
    })
