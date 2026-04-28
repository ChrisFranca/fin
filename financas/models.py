from django.db import models
from django.db.models import Sum
from datetime import date

class MembroFamilia(models.Model):
    nome = models.CharField(max_length=50)
    cor = models.CharField(max_length=7, default='#007bff', help_text="Cor usada nos gráficos para identificar este membro.")
    def __str__(self): return self.nome

class Categoria(models.Model):
    TIPO_CHOICES = (('R', 'Receita'), ('D', 'Despesa'))
    nome = models.CharField(max_length=100)
    tipo = models.CharField(max_length=1, choices=TIPO_CHOICES)
    pai = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subcategorias', help_text="Selecione se esta for uma subcategoria (ex: Almoço é sub de Alimentação).")
    icone = models.CharField(max_length=50, default='bi-cash-stack', help_text="Ícone do Bootstrap Icons (ex: bi-cart, bi-house).")
    def __str__(self): return f"{self.nome} ({self.get_tipo_display()})"

class Conta(models.Model):
    TIPO_CONTA = (('C', 'Corrente'), ('P', 'Poupança'), ('I', 'Investimento'), ('X', 'Dinheiro'), ('K', 'Cartão de Crédito'))
    nome = models.CharField(max_length=100)
    banco = models.CharField(max_length=50, blank=True)
    tipo = models.CharField(max_length=1, choices=TIPO_CONTA)
    saldo_inicial = models.DecimalField(max_digits=15, decimal_places=2, default=0, help_text="Saldo que você já possui nesta conta hoje.")
    cor = models.CharField(max_length=7, default='#6c757d', help_text="Cor de identificação visual da conta.")
    limite = models.DecimalField(max_digits=15, decimal_places=2, default=0, help_text="Limite total (apenas para Cartões de Crédito).")
    dia_fechamento = models.PositiveSmallIntegerField(null=True, blank=True, help_text="Dia que a fatura do cartão fecha.")
    dia_vencimento = models.PositiveSmallIntegerField(null=True, blank=True, help_text="Dia que a fatura do cartão vence.")
    def __str__(self): return self.nome
    def saldo_atual(self):
        if self.tipo == 'K':
            gastos = Transacao.objects.filter(conta=self, status='C').aggregate(Sum('valor'))['valor__sum'] or 0
            return self.limite - gastos
        receitas = Transacao.objects.filter(conta=self, categoria__tipo='R', status='C').aggregate(Sum('valor'))['valor__sum'] or 0
        despesas = Transacao.objects.filter(conta=self, categoria__tipo='D', status='C').aggregate(Sum('valor'))['valor__sum'] or 0
        return self.saldo_inicial + receitas - despesas

class Tag(models.Model):
    nome = models.CharField(max_length=50)
    def __str__(self): return self.nome

class Transacao(models.Model):
    TIPO_STATUS = (('P', 'Pendente'), ('C', 'Confirmado'))
    descricao = models.CharField(max_length=200)
    valor = models.DecimalField(max_digits=15, decimal_places=2)
    data = models.DateField(default=date.today, help_text="Data da compra ou do recebimento.")
    categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT)
    conta = models.ForeignKey(Conta, on_delete=models.CASCADE, help_text="Conta por onde o dinheiro sairá/entrará.")
    membro = models.ForeignKey(MembroFamilia, on_delete=models.SET_NULL, null=True, blank=True, help_text="Quem realizou esta transação?")
    status = models.CharField(max_length=1, choices=TIPO_STATUS, default='C', help_text="Pendente: ainda não saiu do banco. Confirmado: já conferido no extrato.")
    tags = models.ManyToManyField(Tag, blank=True, help_text="Etiquetas para agrupar (ex: Viagem, Reforma).")
    observacao = models.TextField(blank=True, null=True)
    recorrente = models.BooleanField(default=False)
    parcela_atual = models.PositiveSmallIntegerField(default=1)
    total_parcelas = models.PositiveSmallIntegerField(default=1)
    id_parcelamento = models.CharField(max_length=100, blank=True, null=True)
    eh_transferencia = models.BooleanField(default=False, help_text="Indica se esta transação faz parte de uma transferência entre contas.")
    def __str__(self):
        if self.total_parcelas > 1: return f"{self.descricao} ({self.parcela_atual}/{self.total_parcelas})"
        return self.descricao

class Orcamento(models.Model):
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE)
    valor_limite = models.DecimalField(max_digits=15, decimal_places=2, help_text="Limite máximo de gastos para esta categoria no mês.")
    mes = models.PositiveSmallIntegerField()
    ano = models.PositiveIntegerField()
    def gasto_atual(self):
        return Transacao.objects.filter(categoria=self.categoria, data__month=self.mes, data__year=self.ano, eh_transferencia=False).aggregate(Sum('valor'))['valor__sum'] or 0

class MetaEconomia(models.Model):
    nome = models.CharField(max_length=100)
    valor_objetivo = models.DecimalField(max_digits=15, decimal_places=2, help_text="Quanto você quer juntar?")
    valor_poupado = models.DecimalField(max_digits=15, decimal_places=2, default=0, help_text="Quanto já possui guardado hoje?")
    data_limite = models.DateField(help_text="Data pretendida para realizar o objetivo.")
    def progresso(self):
        if self.valor_objetivo > 0: return int((self.valor_poupado / self.valor_objetivo) * 100)
        return 0
    def valor_restante(self): return self.valor_objetivo - self.valor_poupado

class Recorrencia(models.Model):
    descricao = models.CharField(max_length=200)
    valor = models.DecimalField(max_digits=15, decimal_places=2)
    dia_vencimento = models.PositiveSmallIntegerField(help_text="Dia do mês que esta conta vence (ex: 1 a 31).")
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE)
    conta = models.ForeignKey(Conta, on_delete=models.CASCADE)
    membro = models.ForeignKey(MembroFamilia, on_delete=models.SET_NULL, null=True, blank=True)
    ativa = models.BooleanField(default=True, help_text="Desmarque para parar de gerar esta transação automaticamente.")
    def __str__(self): return f"{self.descricao} (Dia {self.dia_vencimento})"

class RegraImportacao(models.Model):
    descricao_contem = models.CharField(max_length=100, help_text="Texto a buscar na descrição do banco (ex: UBER).")
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE, help_text="Categoria a ser aplicada automaticamente.")
    def __str__(self): return f"'{self.descricao_contem}' -> {self.categoria.nome}"
