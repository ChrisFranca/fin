# Sistema de Gestão Financeira Doméstica (Django)

Este projeto é um ecossistema completo para gestão de finanças residenciais, focado em previsibilidade, automação e análise visual.

## Como instalar no seu PC

1. **Abra o terminal** na pasta `gestao_financeira`.
2. **Crie um ambiente virtual**:
   ```bash
   python -m venv venv
   .\venv\Scripts\activate
   ```
3. **Instale as dependências**:
   ```bash
   pip install django django-crispy-forms crispy-bootstrap5 pandas xhtml2pdf ofxparse python-dateutil
   ```
4. **Prepare o Banco de Dados**:
   ```bash
   python manage.py makemigrations financas
   python manage.py migrate
   ```
5. **Crie seu usuário de acesso**:
   ```bash
   python manage.py createsuperuser
   ```
6. **Inicie o sistema**:
   ```bash
   python manage.py runserver
   ```

## Funcionalidades Premium Incluídas
- **Previsão de Saldo (Forecasting)**: Dashboard inteligente que projeta quanto de dinheiro você terá no fim do mês baseado nas contas pendentes.
- **Módulo de Transferências**: Mova dinheiro entre as suas contas (ex: Corrente -> Poupança) sem que isso afete os seus gráficos de despesa ou receita.
- **Notificações Inteligentes**: Alertas em tempo real (Toasts) informando sobre sucesso de operações ou avisos de "Orçamento no Limite" (> 80%).
- **Importação com Machine Learning**: O sistema conta com a funcionalidade de `Regras de Importação`. Ele memoriza padrões do seu banco (ex: "UBER") e já aplica a categoria correta no momento da leitura do .OFX/.CSV.
- **Dashboards Dinâmicos**: Gráficos de linha que mostram a evolução do fluxo de caixa nos últimos 6 meses e comparativo de gastos com o ano passado.
- **Gestão de Orçamentos (Budgets)**: Defina metas de gastos mensais por categoria e acompanhe o progresso com alertas visuais (Verde/Amarelo/Vermelho).
- **Calendário Financeiro**: Visualização dinâmica de ganhos e gastos por dia.
- **Ações Rápidas**: Confirme pagamentos ou exclua transações com um clique na listagem.
- **Gestão de Cartão**: Controle de limites, datas de fechamento e vencimento.
- **Parcelamentos e Recorrências**: Geração automática de parcelas futuras e despesas mensais fixas.
- **Relatórios em PDF**: Documentos formatados para conferência offline.
- **Dark Mode Moderno**: Interface elegante adaptável para maior conforto visual.

## Estrutura de Documentação (3 Níveis)
1. **Nível Usuário (README)**: Funcionalidades gerais descritas acima.
2. **Nível Operacional (Central de Aprendizado)**: Menu "Ajuda" interno no sistema, reformulado em formato de grid com Cards explicativos sobre cada módulo de negócio (Fluxo, Orçamentos, Importação).
3. **Nível Desenvolvedor (Código Fonte)**: Funções críticas do sistema (`dashboard()`, `processar_recorrencias()`) estão fartamente documentadas com *docstrings* Python explicando os cálculos financeiros que ocorrem nos bastidores. Modelos contêm `help_text` explicativos.
