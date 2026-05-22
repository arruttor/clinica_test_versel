import json
from datetime import timedelta, datetime
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .models import Marcacao, ListaEspera, ClinicaOdonto, Paciente, Anamnese, DocumentoPaciente, Evolucao, Professor, Academico, DuplaOdonto, LogAlteracaoEvolucao, Colaborador, Box, Clinica, ItemEstoque, MovimentacaoEstoque
from .forms import ListaEsperaForm, ClinicaOdontoForm, PacienteForm, AnamneseForm, DocumentoPacienteForm, EvolucaoForm, ProfessorForm, AcademicoForm, AprovacaoEvolucaoForm, DuplaOdontoForm, AlteracaoEvolucaoForm, MarcacaoForm, ColaboradorForm, BoxForm, ClinicaForm, ItemEstoqueForm, MovimentacaoEstoqueForm

@login_required
def dashboard(request):
    from django.db.models import Count, Avg, F, ExpressionWrapper, DurationField
    hoje = timezone.now().date()
    trinta_dias_atras = hoje - timedelta(days=30)
    
    # Monta a data extensa em formato brasileiro perfeitamente
    meses_pt = {
        1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril', 5: 'Maio', 6: 'Junho',
        7: 'Julho', 8: 'Agosto', 9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
    }
    dias_semana_pt = {
        0: 'Segunda-feira', 1: 'Terça-feira', 2: 'Quarta-feira', 3: 'Quinta-feira', 
        4: 'Sexta-feira', 5: 'Sábado', 6: 'Domingo'
    }
    data_extensa = f"{dias_semana_pt[hoje.weekday()]}, {hoje.day:02d} de {meses_pt[hoje.month]} de {hoje.year}"
    
    # Resgata todas para listagem geral 
    todas_listas = ListaEspera.objects.all().order_by('-data_hora_marcacao')
    
    # Aplica filtro se selecionado
    filtro_clinica = request.GET.get('clinica')
    if filtro_clinica:
        todas_listas = todas_listas.filter(clinica__nome=filtro_clinica)
        
    listas_hoje = todas_listas.filter(data_hora_marcacao__date=hoje).order_by('data_hora_marcacao')
    
    # Contadores para os Cards
    total_dia = listas_hoje.count()
    aguardando = listas_hoje.filter(status='AGUARDANDO').count()
    agendados = listas_hoje.filter(status='AGENDADO').count()
    concluidos = listas_hoje.filter(status='CONCLUÍDO').count()
    cancelados = listas_hoje.filter(status='CANCELADO').count()

    # ── MÉTRICAS DE RETENÇÃO E ABSENTEÍSMO ────────────────────────────────────

    # 1. Taxa de cancelamento global (base completa, sem filtro de clínica)
    total_geral = ListaEspera.objects.count()
    total_cancelados_geral = ListaEspera.objects.filter(status='CANCELADO').count()
    taxa_cancelamento = round((total_cancelados_geral / total_geral * 100), 1) if total_geral > 0 else 0

    # 2. Top 5 pacientes com mais faltas (nome na lista de espera)
    top_faltas = (
        ListaEspera.objects
        .filter(status='CANCELADO')
        .values('pessoa')
        .annotate(total_faltas=Count('id_marcacao'))
        .order_by('-total_faltas')[:5]
    )

    # 3. Tempo médio (em dias) entre entrada na lista de espera e criação da marcação
    #    Usa entradas que têm agendamento vinculado e data_create preenchida
    esperas_com_agendamento = ListaEspera.objects.filter(
        agendamento__isnull=False,
        date_create__isnull=False,
        agendamento__date_create__isnull=False,
    ).select_related('agendamento')

    deltas = []
    for entrada in esperas_com_agendamento:
        delta = entrada.agendamento.date_create - entrada.date_create
        if delta.total_seconds() >= 0:
            deltas.append(delta.days + delta.seconds / 86400)

    if deltas:
        tempo_medio_espera = round(sum(deltas) / len(deltas), 1)
        deltas_sorted = sorted(deltas)
        meio = len(deltas_sorted) // 2
        if len(deltas_sorted) % 2 == 0:
            tempo_mediano_espera = round((deltas_sorted[meio - 1] + deltas_sorted[meio]) / 2, 1)
        else:
            tempo_mediano_espera = round(deltas_sorted[meio], 1)
        total_calculados = len(deltas)
    else:
        tempo_medio_espera = None
        tempo_mediano_espera = None
        total_calculados = 0

    # 4. Volume de atendimentos concluídos por clínica nos últimos 30 dias
    CLINICA_META = {
        'OD': {'nome': 'Odontologia', 'icone': 'ph-tooth',      'cor': 'teal'},
        'PS': {'nome': 'Psicologia',   'icone': 'ph-brain',      'cor': 'purple'},
        'FI': {'nome': 'Fisioterapia', 'icone': 'ph-activity',   'cor': 'orange'},
        'EN': {'nome': 'Enfermagem',   'icone': 'ph-heartbeat',  'cor': 'rose'},
    }
    atendimentos_qs = (
        Marcacao.objects
        .filter(status='CONCLUIDO', data_hora__date__gte=trinta_dias_atras)
        .values('clinica__nome')
        .annotate(total=Count('id'))
        .order_by('-total')
    )
    max_atendimentos = atendimentos_qs[0]['total'] if atendimentos_qs else 1
    atendimentos_por_clinica = []
    for row in atendimentos_qs:
        codigo = row['clinica__nome']
        meta = CLINICA_META.get(codigo, {'nome': codigo, 'icone': 'ph-hospital', 'cor': 'indigo'})
        pct = round(row['total'] / max_atendimentos * 100) if max_atendimentos else 0
        media_diaria = round(row['total'] / 30, 1)
        atendimentos_por_clinica.append({
            'codigo': codigo,
            'nome': meta['nome'],
            'icone': meta['icone'],
            'cor': meta['cor'],
            'total': row['total'],
            'pct': pct,
            'media_diaria': media_diaria,
        })

    # ── DASHBOARD APRIMORADO: ALERTAS INTELIGENTES ────────────────────────────

    # 5. Evoluções aguardando aprovação do supervisor (alerta global)
    evolucoes_aguardando_count = Evolucao.objects.filter(status='AGUARDANDO').count()

    # 6. Itens de estoque abaixo do mínimo (alerta global)
    itens_criticos_count = ItemEstoque.objects.filter(
        estoque_atual__lte=F('estoque_minimo'), ativo=True
    ).count()

    # ── DASHBOARD APRIMORADO: MARCAÇÕES REAIS DE HOJE ─────────────────────────

    # 7. Status real das Marcações de hoje (diferente da Lista de Espera)
    marcacoes_hoje_qs = Marcacao.objects.filter(data_hora__date=hoje)
    if filtro_clinica:
        marcacoes_hoje_qs = marcacoes_hoje_qs.filter(clinica__nome=filtro_clinica)
    marcacoes_total_hoje     = marcacoes_hoje_qs.count()
    marcacoes_confirmadas    = marcacoes_hoje_qs.filter(status='CONFIRMADO').count()
    marcacoes_em_atendimento = marcacoes_hoje_qs.filter(status='EM_ATENDIMENTO').count()
    marcacoes_aguardando_sup = marcacoes_hoje_qs.filter(status='AGUARDANDO_SUPERVISOR').count()
    marcacoes_concluidas_hoje = marcacoes_hoje_qs.filter(status='CONCLUIDO').count()

    # ── DASHBOARD APRIMORADO: NOTA MÉDIA POR CLÍNICA (MÊS ATUAL) ─────────────

    # 8. Média de notas das evoluções aprovadas no mês corrente, agrupada por clínica
    primeiro_dia_mes = hoje.replace(day=1)
    nota_media_qs = (
        Evolucao.objects
        .filter(status='APROVADO', date_create__date__gte=primeiro_dia_mes, nota__isnull=False)
        .values('clinica__nome')
        .annotate(media=Avg('nota'), total_avaliacoes=Count('id'))
        .order_by('-media')
    )
    notas_clinica = []
    for row in nota_media_qs:
        codigo = row['clinica__nome']
        if codigo:
            meta = CLINICA_META.get(codigo, {'nome': codigo, 'icone': 'ph-hospital', 'cor': 'indigo'})
            notas_clinica.append({
                'codigo': codigo,
                'nome': meta['nome'],
                'icone': meta['icone'],
                'cor': meta['cor'],
                'media': round(float(row['media']), 1),
                'total': row['total_avaliacoes'],
            })

    context = {
        'filtro_clinica': filtro_clinica,
        'data_extensa': data_extensa,
        'total_dia': total_dia,
        'aguardando': aguardando,
        'agendados': agendados,
        'concluidos': concluidos,
        'cancelados': cancelados,
        'listas_hoje': listas_hoje,
        'todas_listas': todas_listas[:10],
        # Métricas de retenção
        'taxa_cancelamento': taxa_cancelamento,
        'taxa_cancelamento_restante': round(100 - taxa_cancelamento, 1),
        'total_cancelados_geral': total_cancelados_geral,
        'total_geral': total_geral,
        'top_faltas': top_faltas,
        'tempo_medio_espera': tempo_medio_espera,
        'tempo_mediano_espera': tempo_mediano_espera,
        'total_calculados': total_calculados,
        'atendimentos_por_clinica': atendimentos_por_clinica,
        # Alertas inteligentes
        'evolucoes_aguardando_count': evolucoes_aguardando_count,
        'itens_criticos_count': itens_criticos_count,
        # Marcações reais de hoje
        'marcacoes_total_hoje': marcacoes_total_hoje,
        'marcacoes_confirmadas': marcacoes_confirmadas,
        'marcacoes_em_atendimento': marcacoes_em_atendimento,
        'marcacoes_aguardando_sup': marcacoes_aguardando_sup,
        'marcacoes_concluidas_hoje': marcacoes_concluidas_hoje,
        # Nota média acadêmica
        'notas_clinica': notas_clinica,
        'mes_atual': meses_pt[hoje.month],
    }
    return render(request, 'clinica_core/dashboard.html', context)

@login_required
def lista_espera_list(request):
    from django.db.models import Q
    busca = request.GET.get('q', '').strip()
    cadastros = ListaEspera.objects.all().order_by('-data_hora_marcacao')
    if busca:
        cadastros = cadastros.filter(
            Q(pessoa__icontains=busca) | Q(celular__icontains=busca)
        )
    return render(request, 'clinica_core/lista_espera_list.html', {
        'cadastros': cadastros,
        'busca': busca,
        'total_resultados': cadastros.count() if busca else None,
    })

@login_required
def lista_espera_create(request):
    if request.method == 'POST':
        form = ListaEsperaForm(request.POST)
        if form.is_valid():
            es_novo = form.save(commit=False)
            if request.user.is_authenticated:
                es_novo.user_create = request.user
                es_novo.atendente = request.user
            else:
                from django.contrib.auth.models import User
                primeiro_usuario = User.objects.first()
                if primeiro_usuario:
                    es_novo.atendente = primeiro_usuario
                    
            es_novo.save()
            return redirect('lista_espera_list')
    else:
        initial_data = {}
        if request.user.is_authenticated:
            initial_data['atendente'] = request.user
        form = ListaEsperaForm(initial=initial_data)
        
    return render(request, 'clinica_core/lista_espera_form.html', {'form': form, 'titulo': 'Nova Marcação', 'btn_texto': 'Registrar Atendimento'})

@login_required
def lista_espera_update(request, pk):
    cadastro = get_object_or_404(ListaEspera, pk=pk)
    if request.method == 'POST':
        form = ListaEsperaForm(request.POST, instance=cadastro)
        if form.is_valid():
            es_edit = form.save(commit=False)
            if request.user.is_authenticated:
                es_edit.user_update = request.user
            es_edit.save()
            return redirect('lista_espera_list')
    else:
        form = ListaEsperaForm(instance=cadastro)
        
    return render(request, 'clinica_core/lista_espera_form.html', {'form': form, 'titulo': 'Editar Marcação', 'btn_texto': 'Salvar Alterações', 'cadastro': cadastro})

@login_required
def clinica_odonto_list(request):
    clinicas = ClinicaOdonto.objects.all().order_by('nome')
    return render(request, 'clinica_core/clinica_odonto_list.html', {'clinicas': clinicas})

@login_required
def clinica_odonto_create(request):
    if request.method == 'POST':
        form = ClinicaOdontoForm(request.POST)
        if form.is_valid():
            es_novo = form.save(commit=False)
            if request.user.is_authenticated:
                es_novo.user_create = request.user
            es_novo.save()
            return redirect('clinica_odonto_list')
    else:
        form = ClinicaOdontoForm()
        
    return render(request, 'clinica_core/clinica_odonto_form.html', {'form': form, 'titulo': 'Nova Clínica Odonto', 'btn_texto': 'Registrar'})

@login_required
def clinica_odonto_update(request, pk):
    clinica = get_object_or_404(ClinicaOdonto, pk=pk)
    if request.method == 'POST':
        form = ClinicaOdontoForm(request.POST, instance=clinica)
        if form.is_valid():
            es_edit = form.save(commit=False)
            if request.user.is_authenticated:
                es_edit.user_update = request.user
            es_edit.save()
            return redirect('clinica_odonto_list')
    else:
        form = ClinicaOdontoForm(instance=clinica)
        
    return render(request, 'clinica_core/clinica_odonto_form.html', {'form': form, 'titulo': 'Editar Clínica Odonto', 'btn_texto': 'Salvar Variáveis', 'clinica': clinica})

@login_required
def clinica_odonto_delete(request, pk):
    clinica = get_object_or_404(ClinicaOdonto, pk=pk)
    if request.method == 'POST':
        clinica.delete()
        return redirect('clinica_odonto_list')
    return render(request, 'clinica_core/clinica_odonto_confirm_delete.html', {'clinica': clinica})

@login_required
def paciente_list(request):
    from django.db.models import Q
    busca = request.GET.get('q', '').strip()
    pacientes = Paciente.objects.all().order_by('nome')
    if busca:
        pacientes = pacientes.filter(
            Q(nome__icontains=busca) | Q(celular__icontains=busca)
        )
    return render(request, 'clinica_core/paciente_list.html', {
        'pacientes': pacientes,
        'busca': busca,
        'total_resultados': pacientes.count() if busca else None,
    })

@login_required
def paciente_check_cpf(request):
    import re
    cpf_input = request.GET.get('cpf', '').strip()
    exclude_id = request.GET.get('exclude_id', '').strip()
    
    cpf_cleaned = re.sub(r'[^0-9]', '', cpf_input)
    if not cpf_cleaned:
        return JsonResponse({'exists': False})
    
    cpf_formatado = cpf_cleaned
    if len(cpf_cleaned) == 11:
        cpf_formatado = f"{cpf_cleaned[:3]}.{cpf_cleaned[3:6]}.{cpf_cleaned[6:9]}-{cpf_cleaned[9:]}"
        
    qs = Paciente.objects.filter(cpf=cpf_formatado)
    if exclude_id and exclude_id.isdigit():
        qs = qs.exclude(pk=int(exclude_id))
        
    exists = qs.exists()
    if not exists:
        qs_cru = Paciente.objects.filter(cpf=cpf_cleaned)
        if exclude_id and exclude_id.isdigit():
            qs_cru = qs_cru.exclude(pk=int(exclude_id))
        exists = qs_cru.exists()
        
    return JsonResponse({'exists': exists})

@login_required
def paciente_create(request):
    if request.method == 'POST':
        form = PacienteForm(request.POST)
        if form.is_valid():
            es_novo = form.save(commit=False)
            if request.user.is_authenticated:
                es_novo.user_create = request.user
            es_novo.save()
            return redirect('paciente_list')
    else:
        form = PacienteForm()
        
    return render(request, 'clinica_core/paciente_form.html', {'form': form, 'titulo': 'Novo Paciente', 'btn_texto': 'Registrar Paciente'})

@login_required
def paciente_update(request, pk):
    paciente = get_object_or_404(Paciente, pk=pk)
    if request.method == 'POST':
        form = PacienteForm(request.POST, instance=paciente)
        if form.is_valid():
            es_edit = form.save(commit=False)
            if request.user.is_authenticated:
                es_edit.user_update = request.user
            es_edit.save()
            return redirect('paciente_list')
    else:
        form = PacienteForm(instance=paciente)
        
    return render(request, 'clinica_core/paciente_form.html', {'form': form, 'titulo': 'Editar Paciente', 'btn_texto': 'Salvar Alterações', 'paciente': paciente})

@login_required
def paciente_delete(request, pk):
    paciente = get_object_or_404(Paciente, pk=pk)
    if request.method == 'POST':
        paciente.delete()
        return redirect('paciente_list')
    return render(request, 'clinica_core/paciente_confirm_delete.html', {'paciente': paciente})

@login_required
def anamnese_update(request, paciente_id):
    from django.db import IntegrityError
    paciente = get_object_or_404(Paciente, pk=paciente_id)
    clinica_usuario = get_user_clinica(request.user)
    
    if clinica_usuario:
        anamnese, created = Anamnese.objects.get_or_create(paciente=paciente, clinica=clinica_usuario)
    else:
        anamnese_id = request.GET.get('id')
        if anamnese_id:
            anamnese = get_object_or_404(Anamnese, pk=anamnese_id, paciente=paciente)
            created = False
        else:
            anamnese = Anamnese.objects.filter(paciente=paciente).first()
            created = anamnese is None
            
    if request.method == 'POST':
        form = AnamneseForm(request.POST, instance=anamnese, user=request.user)
        if form.is_valid():
            try:
                anamnese_edit = form.save(commit=False)
                anamnese_edit.paciente = paciente
                if clinica_usuario:
                    anamnese_edit.clinica = clinica_usuario
                if request.user.is_authenticated:
                    if created or not anamnese:
                        anamnese_edit.user_create = request.user
                    else:
                        anamnese_edit.user_update = request.user
                anamnese_edit.save()
                return redirect('paciente_list')
            except IntegrityError:
                form.add_error('clinica', 'Já existe uma anamnese para esta clínica. Edite a anamnese existente através do botão abaixo.')
    else:
        form = AnamneseForm(instance=anamnese, user=request.user)
        
    anamneses_existentes = Anamnese.objects.filter(paciente=paciente) if not clinica_usuario else None

    return render(request, 'clinica_core/anamnese_form.html', {
        'form': form, 
        'titulo': f'Anamnese - {paciente.nome}', 
        'btn_texto': 'Salvar Anamnese',
        'paciente': paciente,
        'anamneses_existentes': anamneses_existentes,
        'anamnese_atual': anamnese
    })

@login_required
def documento_paciente_list(request, paciente_id):
    paciente = get_object_or_404(Paciente, pk=paciente_id)
    clinica_usuario = get_user_clinica(request.user)
    
    if clinica_usuario:
        documentos = paciente.documentos.filter(clinica=clinica_usuario).order_by('-date_create')
    else:
        documentos = paciente.documentos.all().order_by('-date_create')
    
    if request.method == 'POST':
        form = DocumentoPacienteForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            doc_novo = form.save(commit=False)
            doc_novo.paciente = paciente
            if clinica_usuario:
                doc_novo.clinica = clinica_usuario
            if request.user.is_authenticated:
                doc_novo.user_create = request.user
            doc_novo.save()
            return redirect('documento_paciente_list', paciente_id=paciente.pk)
    else:
        form = DocumentoPacienteForm(user=request.user)
        
    return render(request, 'clinica_core/documento_paciente.html', {
        'paciente': paciente,
        'documentos': documentos,
        'form': form
    })

@login_required
def documento_paciente_delete(request, paciente_id, documento_id):
    documento = get_object_or_404(DocumentoPaciente, pk=documento_id, paciente_id=paciente_id)
    if request.method == 'POST':
        # Ao deletar o objeto no Django, dependendo do storage pode sobrar o arquivo, 
        # mas por hora o model deletado resolverá o link
        documento.arquivo.delete(save=False)
        documento.delete()
    return redirect('documento_paciente_list', paciente_id=paciente_id)

@login_required
def paciente_prontuario(request, paciente_id):
    paciente = get_object_or_404(Paciente, pk=paciente_id)
    clinica_usuario = get_user_clinica(request.user)
    
    if clinica_usuario:
        evolucoes = paciente.evolucoes.filter(clinica=clinica_usuario).order_by('-date_create')
    else:
        evolucoes = paciente.evolucoes.all().order_by('-date_create')
    
    if request.method == 'POST':
        form = EvolucaoForm(request.POST, user=request.user)
        if form.is_valid():
            nova_evolucao = form.save(commit=False)
            nova_evolucao.paciente = paciente
            if clinica_usuario:
                nova_evolucao.clinica = clinica_usuario
            if request.user.is_authenticated:
                nova_evolucao.user_create = request.user
            nova_evolucao.save()
            return redirect('paciente_prontuario', paciente_id=paciente.pk)
    else:
        form = EvolucaoForm(user=request.user)
        
    return render(request, 'clinica_core/prontuario_paciente.html', {
        'paciente': paciente,
        'evolucoes': evolucoes,
        'form': form
    })

@login_required
def evolucao_delete(request, paciente_id, evolucao_id):
    evolucao = get_object_or_404(Evolucao, pk=evolucao_id, paciente_id=paciente_id)
    # Apenas permite deleção se não foi aprovada
    if evolucao.status != 'APROVADO' and request.method == 'POST':
        evolucao.delete()
    return redirect('paciente_prontuario', paciente_id=paciente_id)

@login_required
def paciente_consultas(request, paciente_id):
    paciente = get_object_or_404(Paciente, pk=paciente_id)
    marcacoes = Marcacao.objects.filter(paciente=paciente).order_by('-data_hora')
    
    return render(request, 'clinica_core/paciente_consultas.html', {
        'paciente': paciente,
        'marcacoes': marcacoes
    })

# --- CRUD ACADEMICOS ---
@login_required
def academico_list(request):
    cadastros = Academico.objects.all().order_by('nome')
    return render(request, 'clinica_core/academico_list.html', {'cadastros': cadastros})

@login_required
def academico_create(request):
    if request.method == 'POST':
        form = AcademicoForm(request.POST)
        if form.is_valid():
            academico = form.save(commit=False)
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            if username:
                # Cria usuario para login
                user, created = User.objects.get_or_create(username=username)
                if password:
                    user.set_password(password)
                user.save()
                academico.usuario = user
                
            if request.user.is_authenticated:
                academico.user_create = request.user
            academico.save()
            return redirect('academico_list')
    else:
        form = AcademicoForm()
    return render(request, 'clinica_core/academico_form.html', {'form': form, 'titulo': 'Novo Aluno (Acadêmico)', 'btn_texto': 'Registrar'})

@login_required
def academico_update(request, pk):
    academico = get_object_or_404(Academico, pk=pk)
    # Prepopulando login
    initial = {}
    if academico.usuario:
        initial['username'] = academico.usuario.username

    if request.method == 'POST':
        form = AcademicoForm(request.POST, instance=academico)
        if form.is_valid():
            academico_edit = form.save(commit=False)
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            
            if username:
                user = academico.usuario
                if not user:
                    user, _ = User.objects.get_or_create(username=username)
                else:
                    user.username = username
                if password:
                    user.set_password(password)
                user.save()
                academico_edit.usuario = user

            if request.user.is_authenticated:
                academico_edit.user_update = request.user
            academico_edit.save()
            return redirect('academico_list')
    else:
        form = AcademicoForm(instance=academico, initial=initial)
    return render(request, 'clinica_core/academico_form.html', {'form': form, 'titulo': 'Editar Aluno', 'btn_texto': 'Salvar Alterações'})

@login_required
def academico_delete(request, pk):
    academico = get_object_or_404(Academico, pk=pk)
    if request.method == 'POST':
        academico.delete()
        return redirect('academico_list')
    return render(request, 'clinica_core/academico_confirm_delete.html', {'academico': academico})


# --- CRUD PROFESSORES ---
@login_required
def professor_list(request):
    cadastros = Professor.objects.all().order_by('nome')
    return render(request, 'clinica_core/professor_list.html', {'cadastros': cadastros})

@login_required
def professor_create(request):
    if request.method == 'POST':
        form = ProfessorForm(request.POST)
        if form.is_valid():
            professor = form.save(commit=False)
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            if username:
                user, created = User.objects.get_or_create(username=username)
                if password:
                    user.set_password(password)
                user.save()
                professor.usuario = user
                
            if request.user.is_authenticated:
                professor.user_create = request.user
            professor.save()
            return redirect('professor_list')
    else:
        form = ProfessorForm()
    return render(request, 'clinica_core/professor_form.html', {'form': form, 'titulo': 'Novo Supervisor (Professor)', 'btn_texto': 'Registrar Professor'})

@login_required
def professor_update(request, pk):
    professor = get_object_or_404(Professor, pk=pk)
    initial = {}
    if professor.usuario:
        initial['username'] = professor.usuario.username

    if request.method == 'POST':
        form = ProfessorForm(request.POST, instance=professor)
        if form.is_valid():
            professor_edit = form.save(commit=False)
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            
            if username:
                user = professor.usuario
                if not user:
                    user, _ = User.objects.get_or_create(username=username)
                else:
                    user.username = username
                if password:
                    user.set_password(password)
                user.save()
                professor_edit.usuario = user

            if request.user.is_authenticated:
                professor_edit.user_update = request.user
            professor_edit.save()
            return redirect('professor_list')
    else:
        form = ProfessorForm(instance=professor, initial=initial)
    return render(request, 'clinica_core/professor_form.html', {'form': form, 'titulo': 'Editar Professor', 'btn_texto': 'Salvar Alterações'})

@login_required
def professor_delete(request, pk):
    professor = get_object_or_404(Professor, pk=pk)
    if request.method == 'POST':
        professor.delete()
        return redirect('professor_list')
    return render(request, 'clinica_core/professor_confirm_delete.html', {'professor': professor})

# --- Colaboradores ---

@login_required
def colaborador_list(request):
    colaboradores = Colaborador.objects.all().order_by('nome')
    return render(request, 'clinica_core/colaborador_list.html', {'colaboradores': colaboradores})

@login_required
def colaborador_create(request):
    if request.method == 'POST':
        form = ColaboradorForm(request.POST)
        if form.is_valid():
            colab = form.save(commit=False)
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            
            if username:
                user, created = User.objects.get_or_create(username=username)
                if password:
                    user.set_password(password)
                
                # Permissões Mágicas
                if colab.cargo == 'ADMINISTRADOR':
                    user.is_superuser = True
                    user.is_staff = True
                else:
                    user.is_superuser = False
                    user.is_staff = False
                    
                user.save()
                colab.usuario = user
            
            if request.user.is_authenticated:
                colab.user_create = request.user
            colab.save()
            return redirect('colaborador_list')
    else:
        form = ColaboradorForm()
    return render(request, 'clinica_core/colaborador_form.html', {'form': form, 'titulo': 'Novo Colaborador', 'btn_texto': 'Registrar Usuário'})

@login_required
def colaborador_update(request, pk):
    colab = get_object_or_404(Colaborador, pk=pk)
    initial = {}
    if colab.usuario:
        initial['username'] = colab.usuario.username

    if request.method == 'POST':
        form = ColaboradorForm(request.POST, instance=colab)
        if form.is_valid():
            colab_edit = form.save(commit=False)
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            
            if username:
                user = colab.usuario
                if not user:
                    user, _ = User.objects.get_or_create(username=username)
                else:
                    user.username = username
                    
                if password:
                    user.set_password(password)
                
                # Permissões Mágicas
                if colab_edit.cargo == 'ADMINISTRADOR':
                    user.is_superuser = True
                    user.is_staff = True
                else:
                    user.is_superuser = False
                    user.is_staff = False
                    
                user.save()
                colab_edit.usuario = user

            if request.user.is_authenticated:
                colab_edit.user_update = request.user
            colab_edit.save()
            return redirect('colaborador_list')
    else:
        form = ColaboradorForm(instance=colab, initial=initial)
    return render(request, 'clinica_core/colaborador_form.html', {'form': form, 'titulo': 'Editar Colaborador', 'btn_texto': 'Salvar Alterações'})

@login_required
def colaborador_delete(request, pk):
    colab = get_object_or_404(Colaborador, pk=pk)
    if request.method == 'POST':
        colab.delete()
        return redirect('colaborador_list')
    return render(request, 'clinica_core/colaborador_confirm_delete.html', {'colaborador': colab})

# --- CRUD CLÍNICAS ---
@login_required
def clinica_list(request):
    clinicas = Clinica.objects.all().order_by('nome')
    # Mapa de ícones e cores por tipo
    CLINICA_META = {
        'OD': {'icon': 'ph-tooth', 'color': 'teal'},
        'PS': {'icon': 'ph-brain', 'color': 'purple'},
        'FI': {'icon': 'ph-activity', 'color': 'orange'},
        'EN': {'icon': 'ph-heartbeat', 'color': 'rose'},
    }
    clinicas_com_meta = [
        {'obj': c, 'meta': CLINICA_META.get(c.nome, {'icon': 'ph-hospital', 'color': 'indigo'})}
        for c in clinicas
    ]
    return render(request, 'clinica_core/clinica_list.html', {
        'clinicas': clinicas_com_meta,
        'total': clinicas.count(),
    })

@login_required
def clinica_create(request):
    if not request.user.is_superuser:
        messages.error(request, 'Acesso negado. Apenas o administrador do sistema pode cadastrar clínicas.')
        return redirect('clinica_list')
    if request.method == 'POST':
        form = ClinicaForm(request.POST)
        if form.is_valid():
            nova = form.save(commit=False)
            nova.user_create = request.user
            nova.save()
            messages.success(request, f'Clínica "{nova.get_nome_display()}" cadastrada com sucesso!')
            return redirect('clinica_list')
    else:
        form = ClinicaForm()
    return render(request, 'clinica_core/clinica_form.html', {
        'form': form, 'titulo': 'Nova Clínica', 'btn_texto': 'Registrar Clínica'
    })

@login_required
def clinica_update(request, pk):
    if not request.user.is_superuser:
        messages.error(request, 'Acesso negado. Apenas o administrador do sistema pode editar clínicas.')
        return redirect('clinica_list')
    clinica = get_object_or_404(Clinica, pk=pk)
    if request.method == 'POST':
        form = ClinicaForm(request.POST, instance=clinica)
        if form.is_valid():
            edit = form.save(commit=False)
            edit.user_update = request.user
            edit.save()
            messages.success(request, 'Clínica atualizada com sucesso!')
            return redirect('clinica_list')
    else:
        form = ClinicaForm(instance=clinica)
    return render(request, 'clinica_core/clinica_form.html', {
        'form': form, 'titulo': 'Editar Clínica', 'btn_texto': 'Salvar Alterações', 'clinica': clinica
    })

@login_required
def clinica_delete(request, pk):
    messages.error(request, 'A exclusão de clínicas não é permitida. As clínicas são registros permanentes do sistema.')
    return redirect('clinica_list')


# --- AREA DO DOCENTE ---
@login_required
def aprovacoes_pendentes(request):
    status_filter = request.GET.get('status', 'AGUARDANDO')
    
    if status_filter == 'APROVADO':
        evolucoes = Evolucao.objects.filter(status='APROVADO').order_by('-date_create')
    elif status_filter == 'TODAS':
        evolucoes = Evolucao.objects.all().order_by('-date_create')
    else:
        # Default fallback
        status_filter = 'AGUARDANDO'
        evolucoes = Evolucao.objects.filter(status='AGUARDANDO').order_by('date_create')

    try:
        professor = Professor.objects.get(usuario=request.user)
    except Professor.DoesNotExist:
        # Se um admin ou secretário acessar a aba, enxerga tudo
        professor = None
        
    return render(request, 'clinica_core/aprovacoes_pendentes.html', {
        'evolucoes': evolucoes, 
        'professor': professor,
        'status_filter': status_filter
    })

@login_required
def evolucao_aprovar(request, evolucao_id):
    evolucao = get_object_or_404(Evolucao, pk=evolucao_id)
    
    try:
        professor = Professor.objects.get(usuario=request.user)
    except Professor.DoesNotExist:
        professor = None
        
    if request.method == 'POST':
        form = AprovacaoEvolucaoForm(request.POST, instance=evolucao)
        if form.is_valid():
            evo = form.save(commit=False)
            evo.status = 'APROVADO'
            if professor:
                evo.avaliador = professor
            evo.save()
            return redirect('aprovacoes_pendentes')
    else:
        form = AprovacaoEvolucaoForm(instance=evolucao)
        
    return render(request, 'clinica_core/evolucao_aprovar.html', {
        'evolucao': evolucao,
        'form': form
    })

@login_required
def evolucao_alterar(request, evolucao_id):
    evolucao = get_object_or_404(Evolucao, pk=evolucao_id)
    
    # Check if user is a Professor
    try:
        professor = Professor.objects.get(usuario=request.user)
    except Professor.DoesNotExist:
        messages.error(request, "Acesso Negado: Apenas contas com perfil de Professor podem alterar uma avaliação já realizada.")
        return redirect('aprovacoes_pendentes')
        
    if evolucao.status != 'APROVADO':
        # Só permite alterar se já foi aprovado
        return redirect('evolucao_aprovar', evolucao_id=evolucao.pk)
        
    if request.method == 'POST':
        form = AlteracaoEvolucaoForm(request.POST, instance=evolucao)
        if form.is_valid():
            senha = form.cleaned_data.get('senha')
            # Verify password
            if not request.user.check_password(senha):
                form.add_error('senha', 'Senha incorreta. Alteração não permitida.')
            else:
                # Log the change
                nota_anterior = evolucao.nota
                observacao_anterior = evolucao.observacao_supervisor
                
                # Para evitar que o save() sobrescreva a instancia atual antes do log, 
                # vamos ler o modelo puro do banco (opcional, pq o instance tá modded)
                evolucao_atual = Evolucao.objects.get(pk=evolucao.pk)
                
                LogAlteracaoEvolucao.objects.create(
                    evolucao=evolucao,
                    professor=professor,
                    nota_anterior=evolucao_atual.nota,
                    nota_nova=form.cleaned_data['nota'],
                    observacao_anterior=evolucao_atual.observacao_supervisor,
                    observacao_nova=form.cleaned_data['observacao_supervisor']
                )
                form.save()
                return redirect('evolucao_aprovar', evolucao_id=evolucao.pk)
    else:
        form = AlteracaoEvolucaoForm(instance=evolucao)
        
    logs = evolucao.logs_alteracao.all().order_by('-data_alteracao')
        
    return render(request, 'clinica_core/evolucao_alterar.html', {
        'evolucao': evolucao,
        'form': form,
        'logs': logs
    })

# --- CRUD DUPLAS ODONTO ---
@login_required
def dupla_list(request):
    cadastros = DuplaOdonto.objects.all().select_related('aluno1', 'aluno2', 'clinica_odonto').order_by('clinica_odonto__nome')
    return render(request, 'clinica_core/dupla_list.html', {'cadastros': cadastros})

@login_required
def dupla_create(request):
    if request.method == 'POST':
        form = DuplaOdontoForm(request.POST)
        if form.is_valid():
            dupla = form.save(commit=False)
            if request.user.is_authenticated:
                dupla.user_create = request.user
            dupla.save()
            return redirect('dupla_list')
    else:
        form = DuplaOdontoForm()
    return render(request, 'clinica_core/dupla_form.html', {'form': form, 'titulo': 'Nova Dupla/Equipe Odonto', 'btn_texto': 'Registrar Dupla'})

@login_required
def dupla_update(request, pk):
    dupla = get_object_or_404(DuplaOdonto, pk=pk)
    if request.method == 'POST':
        form = DuplaOdontoForm(request.POST, instance=dupla)
        if form.is_valid():
            dupla_edit = form.save(commit=False)
            if request.user.is_authenticated:
                dupla_edit.user_update = request.user
            dupla_edit.save()
            return redirect('dupla_list')
    else:
        form = DuplaOdontoForm(instance=dupla)
    return render(request, 'clinica_core/dupla_form.html', {'form': form, 'titulo': 'Editar Dupla/Equipe', 'btn_texto': 'Salvar Alterações'})

@login_required
def dupla_delete(request, pk):
    dupla = get_object_or_404(DuplaOdonto, pk=pk)
    if request.method == 'POST':
        dupla.delete()
        return redirect('dupla_list')
    return render(request, 'clinica_core/dupla_confirm_delete.html', {'dupla': dupla})

# --- AGENDA ---
import re

def get_user_clinica(user):
    if hasattr(user, 'professor_profile'):
        return user.professor_profile.clinica
    if hasattr(user, 'academico_profile'):
        return user.academico_profile.clinica
    return None

@login_required
def agenda_list(request):
    clinica_usuario = get_user_clinica(request.user)
    tab = request.GET.get('tab', 'pendentes')
    
    lista_espera = []
    marcacoes = []
    
    if tab == 'pendentes':
        qs = ListaEspera.objects.filter(status='AGUARDANDO').order_by('data_hora_marcacao')
        if clinica_usuario:
            qs = qs.filter(clinica=clinica_usuario)
        lista_espera = qs
    elif tab == 'agendados':
        qs = Marcacao.objects.exclude(status='CONCLUIDO').order_by('data_hora')
        if clinica_usuario:
            qs = qs.filter(clinica=clinica_usuario)
        marcacoes = qs
    elif tab == 'finalizados':
        qs = Marcacao.objects.filter(status='CONCLUIDO').order_by('-data_hora')
        if clinica_usuario:
            qs = qs.filter(clinica=clinica_usuario)
        marcacoes = qs
        
    return render(request, 'clinica_core/agenda_list.html', {
        'tab': tab,
        'listas': lista_espera, # keep variable name for pending
        'marcacoes': marcacoes,
        'clinica_usuario': clinica_usuario
    })

@login_required
def agenda_agendar(request, pk):
    """Step 1 — Selecionar paciente existente ou criar novo."""
    lista_espera = get_object_or_404(ListaEspera, pk=pk)

    if lista_espera.status != 'AGUARDANDO':
        messages.warning(request, "Esta solicitação já foi processada.")
        return redirect('agenda_list')

    busca = request.GET.get('q', '').strip()
    pacientes = Paciente.objects.all().order_by('nome')
    if busca:
        from django.db.models import Q
        pacientes = pacientes.filter(
            Q(nome__icontains=busca) | Q(cpf__icontains=busca) | Q(celular__icontains=busca)
        )

    return render(request, 'clinica_core/agenda_agendar.html', {
        'lista_espera': lista_espera,
        'pacientes': pacientes,
        'busca': busca,
    })


@login_required
def agenda_agendar_existente(request, pk, paciente_pk):
    """Step 2a — Paciente já existe: mostra apenas form de agendamento."""
    lista_espera = get_object_or_404(ListaEspera, pk=pk)
    paciente = get_object_or_404(Paciente, pk=paciente_pk)

    if lista_espera.status != 'AGUARDANDO':
        messages.warning(request, "Esta solicitação já foi processada.")
        return redirect('agenda_list')

    if request.method == 'POST':
        form_marcacao = MarcacaoForm(request.POST, user=request.user, clinica_espera=lista_espera.clinica)
        if form_marcacao.is_valid():
            marcacao = form_marcacao.save(commit=False)
            marcacao.paciente = paciente
            marcacao.clinica = lista_espera.clinica
            marcacao.lista_espera = lista_espera
            if request.user.is_authenticated:
                marcacao.user_create = request.user
            marcacao.save()

            lista_espera.status = 'AGENDADO'
            lista_espera.agendamento = marcacao
            lista_espera.save()

            messages.success(request, f"Consulta de {paciente.nome} agendada com sucesso!")
            return redirect('agenda_list')
    else:
        form_marcacao = MarcacaoForm(user=request.user, clinica_espera=lista_espera.clinica)

    return render(request, 'clinica_core/agenda_agendar_existente.html', {
        'lista_espera': lista_espera,
        'paciente': paciente,
        'form_marcacao': form_marcacao,
    })


@login_required
def agenda_agendar_novo(request, pk):
    """Step 2b — Novo paciente: form de cadastro + agendamento."""
    lista_espera = get_object_or_404(ListaEspera, pk=pk)

    if lista_espera.status != 'AGUARDANDO':
        messages.warning(request, "Esta solicitação já foi processada.")
        return redirect('agenda_list')

    initial_paciente = {
        'nome': lista_espera.pessoa,
        'celular': lista_espera.celular,
        'observacao': f"Transferido da lista de espera. Observação original: {lista_espera.observacao}" if lista_espera.observacao else "Criado via Agendamento a partir da Lista de Espera."
    }

    if request.method == 'POST':
        form_paciente = PacienteForm(request.POST)
        form_marcacao = MarcacaoForm(request.POST, user=request.user, clinica_espera=lista_espera.clinica)

        if form_paciente.is_valid() and form_marcacao.is_valid():
            paciente = form_paciente.save(commit=False)
            if request.user.is_authenticated:
                paciente.user_create = request.user
            paciente.save()

            marcacao = form_marcacao.save(commit=False)
            marcacao.paciente = paciente
            marcacao.clinica = lista_espera.clinica
            marcacao.lista_espera = lista_espera
            if request.user.is_authenticated:
                marcacao.user_create = request.user
            marcacao.save()

            lista_espera.status = 'AGENDADO'
            lista_espera.agendamento = marcacao
            lista_espera.save()

            messages.success(request, f"Agendamento de {paciente.nome} realizado com sucesso!")
            return redirect('agenda_list')
    else:
        form_paciente = PacienteForm(initial=initial_paciente)
        form_marcacao = MarcacaoForm(user=request.user, clinica_espera=lista_espera.clinica)

    return render(request, 'clinica_core/agenda_agendar_novo.html', {
        'lista_espera': lista_espera,
        'form_paciente': form_paciente,
        'form_marcacao': form_marcacao,
    })

@login_required
def agenda_finalizar(request, pk):
    marcacao = get_object_or_404(Marcacao, pk=pk)
    
    if marcacao.status == 'CONCLUIDO':
        messages.warning(request, "Esta consulta já foi finalizada.")
        return redirect('agenda_list')
        
    if request.method == 'POST':
        form = EvolucaoForm(request.POST, user=request.user, clinica_override=marcacao.clinica)
        if form.is_valid():
            nova_evolucao = form.save(commit=False)
            nova_evolucao.paciente = marcacao.paciente
            nova_evolucao.clinica = marcacao.clinica
            if request.user.is_authenticated:
                nova_evolucao.user_create = request.user
            nova_evolucao.save()
            
            marcacao.status = 'CONCLUIDO'
            marcacao.data_hora_finalizacao = timezone.now()
            marcacao.usuario_finalizacao = request.user
            marcacao.save()

            # Atualiza o status na ListaEspera de origem para refletir no card do dashboard
            if marcacao.lista_espera:
                marcacao.lista_espera.status = 'CONCLUÍDO'
                marcacao.lista_espera.save()
            
            messages.success(request, f"Consulta de {marcacao.paciente.nome} finalizada com sucesso!")
            return redirect('agenda_list')
    else:
        initial_desc = f"Atendimento realizado em {marcacao.data_hora.strftime('%d/%m/%Y às %H:%M')}.\n\nEvolução Clínica:\n"
        form = EvolucaoForm(initial={'descricao': initial_desc}, user=request.user, clinica_override=marcacao.clinica)
        
    return render(request, 'clinica_core/agenda_finalizar.html', {
        'marcacao': marcacao,
        'form': form
    })

@login_required
@require_POST
def marcacao_iniciar_atendimento(request, pk):
    """Muda o status da Marcacao de CONFIRMADO para EM_ATENDIMENTO."""
    marcacao = get_object_or_404(Marcacao, pk=pk)
    if marcacao.status == 'CONFIRMADO':
        marcacao.status = 'EM_ATENDIMENTO'
        marcacao.save(update_fields=['status'])
        messages.success(request, f"Atendimento de {marcacao.paciente.nome} iniciado.")
    else:
        messages.warning(request, "Esta consulta não pode ser iniciada (status atual: %(s)s)." % {'s': marcacao.get_status_display()})
    from django.urls import reverse
    return redirect(reverse('agenda_list') + '?tab=agendados')


# --- CALENDÁRIO INTERATIVO ---

@login_required
def agenda_calendario(request):
    clinica_usuario = get_user_clinica(request.user)

    # Determina a semana a exibir
    semana_param = request.GET.get('semana')
    if semana_param:
        try:
            dia_referencia = datetime.strptime(semana_param, '%Y-%m-%d').date()
        except ValueError:
            dia_referencia = timezone.now().date()
    else:
        dia_referencia = timezone.now().date()

    # Seg a Dom da semana escolhida
    inicio_semana = dia_referencia - timedelta(days=dia_referencia.weekday())  # Segunda-feira
    dias_semana = [inicio_semana + timedelta(days=i) for i in range(7)]

    semana_anterior = (inicio_semana - timedelta(days=7)).strftime('%Y-%m-%d')
    semana_proxima = (inicio_semana + timedelta(days=7)).strftime('%Y-%m-%d')

    # Busca marcações da semana
    fim_semana = inicio_semana + timedelta(days=7)
    qs = Marcacao.objects.filter(
        data_hora__date__gte=inicio_semana,
        data_hora__date__lt=fim_semana
    ).select_related('paciente', 'clinica', 'professor', 'academico').order_by('data_hora')

    if clinica_usuario:
        qs = qs.filter(clinica=clinica_usuario)

    # Estrutura de clínicas
    clinicas_info = [
        {'codigo': 'OD', 'nome': 'Odontologia',  'icone': 'ph-tooth',      'cor': 'teal'},
        {'codigo': 'PS', 'nome': 'Psicologia',    'icone': 'ph-brain',      'cor': 'purple'},
        {'codigo': 'FI', 'nome': 'Fisioterapia',  'icone': 'ph-activity',   'cor': 'orange'},
        {'codigo': 'EN', 'nome': 'Enfermagem',    'icone': 'ph-heartbeat',  'cor': 'rose'},
    ]

    # Monta grade: {clinica_codigo: {data_str: [marcacoes]}}
    grade = {}
    for c in clinicas_info:
        grade[c['codigo']] = {}
        for dia in dias_semana:
            grade[c['codigo']][dia.strftime('%Y-%m-%d')] = []

    for m in qs:
        codigo = m.clinica.nome  # 'OD', 'PS', etc.
        dia_str = m.data_hora.date().strftime('%Y-%m-%d')
        if codigo in grade and dia_str in grade[codigo]:
            grade[codigo][dia_str].append(m)

    return render(request, 'clinica_core/agenda_calendario.html', {
        'dias_semana': dias_semana,
        'clinicas_info': clinicas_info,
        'grade': grade,
        'semana_anterior': semana_anterior,
        'semana_proxima': semana_proxima,
        'inicio_semana': inicio_semana,
        'clinica_usuario': clinica_usuario,
        'hoje': timezone.now().date(),
    })


@login_required
@require_POST
def marcacao_mover(request, pk):
    """Endpoint AJAX para drag & drop — move marcação para nova data/hora."""
    marcacao = get_object_or_404(Marcacao, pk=pk)

    try:
        data = json.loads(request.body)
        nova_data_str = data.get('nova_data')  # 'YYYY-MM-DD'
        novo_horario = marcacao.data_hora.strftime('%H:%M')  # mantém o horário original

        nova_datetime_naive = datetime.strptime(f"{nova_data_str} {novo_horario}", '%Y-%m-%d %H:%M')
        nova_datetime = timezone.make_aware(nova_datetime_naive)

        marcacao.data_hora = nova_datetime
        if request.user.is_authenticated:
            marcacao.user_update = request.user
        marcacao.save()

        return JsonResponse({
            'success': True,
            'nova_data_display': nova_datetime.strftime('%d/%m/%Y'),
            'horario': novo_horario,
        })
    except (ValueError, KeyError, TypeError) as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


# --- CRUD BOXES / SALAS ---
@login_required
def box_list(request):
    boxes = Box.objects.all().select_related('clinica').order_by('clinica', 'nome')
    return render(request, 'clinica_core/box_list.html', {'boxes': boxes})

@login_required
def box_create(request):
    if request.method == 'POST':
        form = BoxForm(request.POST)
        if form.is_valid():
            box = form.save(commit=False)
            if request.user.is_authenticated:
                box.user_create = request.user
            box.save()
            messages.success(request, f"Box '{box.nome}' cadastrado com sucesso!")
            return redirect('box_list')
    else:
        form = BoxForm()
    return render(request, 'clinica_core/box_form.html', {'form': form, 'titulo': 'Novo Box / Sala', 'btn_texto': 'Cadastrar Box'})

@login_required
def box_update(request, pk):
    box = get_object_or_404(Box, pk=pk)
    if request.method == 'POST':
        form = BoxForm(request.POST, instance=box)
        if form.is_valid():
            box_edit = form.save(commit=False)
            if request.user.is_authenticated:
                box_edit.user_update = request.user
            box_edit.save()
            messages.success(request, f"Box '{box_edit.nome}' atualizado com sucesso!")
            return redirect('box_list')
    else:
        form = BoxForm(instance=box)
    return render(request, 'clinica_core/box_form.html', {'form': form, 'titulo': f'Editar: {box.nome}', 'btn_texto': 'Salvar Alterações', 'box': box})

@login_required
def box_delete(request, pk):
    box = get_object_or_404(Box, pk=pk)
    if request.method == 'POST':
        box.delete()
        messages.success(request, "Box removido com sucesso.")
        return redirect('box_list')
    return render(request, 'clinica_core/box_confirm_delete.html', {'box': box})


# ── MÓDULO DE ESTOQUE (ALMOXARIFADO) ─────────────────────────────────────────

@login_required
def estoque_list(request):
    from django.db.models import Q
    busca = request.GET.get('q', '').strip()
    filtro_clinica = request.GET.get('clinica', '')
    filtro_status = request.GET.get('status', '')

    itens = ItemEstoque.objects.select_related('clinica').all()

    if busca:
        itens = itens.filter(Q(nome__icontains=busca) | Q(codigo__icontains=busca))
    if filtro_clinica:
        itens = itens.filter(clinica__nome=filtro_clinica)
    if filtro_status == 'baixo':
        # Filtra itens onde estoque_atual <= estoque_minimo
        from django.db.models import F
        itens = itens.filter(estoque_atual__lte=F('estoque_minimo'))
    elif filtro_status == 'ok':
        from django.db.models import F
        itens = itens.filter(estoque_atual__gt=F('estoque_minimo'))

    total_itens = itens.count()
    from django.db.models import F as Ff
    total_baixo = ItemEstoque.objects.filter(estoque_atual__lte=Ff('estoque_minimo'), ativo=True).count()

    clinicas = Clinica.objects.all()
    return render(request, 'clinica_core/estoque_list.html', {
        'itens': itens,
        'busca': busca,
        'filtro_clinica': filtro_clinica,
        'filtro_status': filtro_status,
        'total_itens': total_itens,
        'total_baixo': total_baixo,
        'clinicas': clinicas,
    })


@login_required
def estoque_create(request):
    if request.method == 'POST':
        form = ItemEstoqueForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.user_create = request.user
            item.save()
            messages.success(request, f'Item "{item.nome}" cadastrado com sucesso!')
            return redirect('estoque_list')
    else:
        form = ItemEstoqueForm()
    return render(request, 'clinica_core/estoque_form.html', {
        'form': form, 'titulo': 'Novo Item de Estoque', 'btn_texto': 'Cadastrar Item'
    })


@login_required
def estoque_update(request, pk):
    item = get_object_or_404(ItemEstoque, pk=pk)
    if request.method == 'POST':
        form = ItemEstoqueForm(request.POST, instance=item)
        if form.is_valid():
            item_edit = form.save(commit=False)
            item_edit.user_update = request.user
            item_edit.save()
            messages.success(request, f'Item "{item_edit.nome}" atualizado.')
            return redirect('estoque_list')
    else:
        form = ItemEstoqueForm(instance=item)
    return render(request, 'clinica_core/estoque_form.html', {
        'form': form, 'titulo': f'Editar: {item.nome}', 'btn_texto': 'Salvar Alterações', 'item': item
    })


@login_required
def estoque_delete(request, pk):
    item = get_object_or_404(ItemEstoque, pk=pk)
    tem_movimentacoes = item.movimentacoes.exists()
    if request.method == 'POST':
        if tem_movimentacoes:
            messages.error(request, 'Não é possível excluir um item que já possui movimentações registradas.')
            return redirect('estoque_list')
        nome = item.nome
        item.delete()
        messages.success(request, f'Item "{nome}" removido.')
        return redirect('estoque_list')
    return render(request, 'clinica_core/estoque_confirm_delete.html', {
        'item': item, 'tem_movimentacoes': tem_movimentacoes
    })


@login_required
def estoque_movimentar(request, pk):
    item = get_object_or_404(ItemEstoque, pk=pk)
    if request.method == 'POST':
        form = MovimentacaoEstoqueForm(request.POST, item=item)
        if form.is_valid():
            mov = form.save(commit=False)
            mov.item = item
            mov.responsavel = request.user
            mov.user_create = request.user
            mov.save()
            tipo_label = 'Entrada' if mov.tipo == 'ENTRADA' else 'Saída'
            messages.success(request, f'{tipo_label} de {mov.quantidade} {item.unidade} registrada. Estoque atual: {item.estoque_atual}.')
            return redirect('estoque_list')
    else:
        form = MovimentacaoEstoqueForm(item=item)
    return render(request, 'clinica_core/estoque_movimentar.html', {
        'form': form, 'item': item
    })


@login_required
def estoque_historico(request, pk):
    item = get_object_or_404(ItemEstoque, pk=pk)
    movimentacoes = item.movimentacoes.select_related('responsavel').order_by('-data', '-date_create')
    return render(request, 'clinica_core/estoque_historico.html', {
        'item': item, 'movimentacoes': movimentacoes
    })
