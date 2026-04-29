from django import forms
from .models import Transacao, Conta, Categoria, MembroFamilia, Tag, Orcamento, RelatorioPersonalizado
import uuid
from datetime import date
from dateutil.relativedelta import relativedelta

class TransacaoForm(forms.ModelForm):
    total_parcelas = forms.IntegerField(min_value=1, initial=1, label="Total de Parcelas")

    class Meta:
        model = Transacao
        fields = ['descricao', 'valor', 'data', 'categoria', 'conta', 'membro', 'status', 'tags', 'observacao', 'comprovante']
        widgets = {
            'data': forms.DateInput(attrs={'type': 'date'}),
            'tags': forms.CheckboxSelectMultiple(),
            'observacao': forms.Textarea(attrs={'rows': 3}),
        }

    def save(self, commit=True):
        instance = super().save(commit=False)
        total = self.cleaned_data.get('total_parcelas', 1)
        
        if total > 1:
            id_grupo = str(uuid.uuid4())
            instance.id_parcelamento = id_grupo
            instance.total_parcelas = total
            instance.parcela_atual = 1
            instance.save() 
            
            for i in range(2, total + 1):
                Transacao.objects.create(
                    descricao=instance.descricao,
                    valor=instance.valor,
                    data=instance.data + relativedelta(months=i-1),
                    categoria=instance.categoria,
                    conta=instance.conta,
                    membro=instance.membro,
                    status='P',
                    id_parcelamento=id_grupo,
                    total_parcelas=total,
                    parcela_atual=i
                )
            return instance
        
        if commit:
            instance.save()
        return instance

class TransferenciaForm(forms.Form):
    conta_origem = forms.ModelChoiceField(queryset=Conta.objects.all(), label="Conta de Origem")
    conta_destino = forms.ModelChoiceField(queryset=Conta.objects.all(), label="Conta de Destino")
    valor = forms.DecimalField(max_digits=15, decimal_places=2, label="Valor da Transferência")
    data = forms.DateField(initial=date.today, widget=forms.DateInput(attrs={'type': 'date'}), label="Data da Transferência")
    observacao = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 2}), label="Observação")

    def clean(self):
        cleaned_data = super().clean()
        origem = cleaned_data.get("conta_origem")
        destino = cleaned_data.get("conta_destino")
        if origem and destino and origem == destino:
            raise forms.ValidationError("A conta de origem não pode ser a mesma que a de destino.")
        return cleaned_data

class CategoriaForm(forms.ModelForm):
    ICONES_CHOICES = [
        ('bi-cash-stack', 'Dinheiro'),
        ('bi-cart', 'Compras'),
        ('bi-house', 'Moradia'),
        ('bi-car-front', 'Transporte'),
        ('bi-heart-pulse', 'Saúde'),
        ('bi-mortarboard', 'Educação'),
        ('bi-controller', 'Lazer'),
        ('bi-lightning', 'Energia/Utilidades'),
        ('bi-phone', 'Comunicação'),
        ('bi-briefcase', 'Trabalho'),
        ('bi-gift', 'Presentes'),
        ('bi-cup-hot', 'Alimentação'),
        ('bi-airplane', 'Viagens'),
        ('bi-piggy-bank', 'Investimentos'),
    ]
    
    icone = forms.ChoiceField(choices=ICONES_CHOICES, widget=forms.Select(attrs={'class': 'form-select'}))

    class Meta:
        model = Categoria
        fields = ['nome', 'tipo', 'classe_abc', 'pai', 'icone']

class ContaForm(forms.ModelForm):
    class Meta:
        model = Conta
        fields = ['nome', 'banco', 'tipo', 'saldo_inicial', 'cor', 'limite', 'dia_fechamento', 'dia_vencimento']
        widgets = {
            'cor': forms.TextInput(attrs={'type': 'color', 'class': 'form-control form-control-color'}),
        }

class MembroFamiliaForm(forms.ModelForm):
    class Meta:
        model = MembroFamilia
        fields = ['nome', 'cor']
        widgets = {
            'cor': forms.TextInput(attrs={'type': 'color', 'class': 'form-control form-control-color'}),
        }

class TagForm(forms.ModelForm):
    class Meta:
        model = Tag
        fields = ['nome']

class RelatorioPersonalizadoForm(forms.ModelForm):
    class Meta:
        model = RelatorioPersonalizado
        fields = ['nome', 'descricao', 'tipo', 'query_base']
