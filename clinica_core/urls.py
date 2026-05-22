from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('login/', auth_views.LoginView.as_view(template_name='clinica_core/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('', views.dashboard, name='dashboard'),
    path('lista-espera/', views.lista_espera_list, name='lista_espera_list'),
    path('lista-espera/novo/', views.lista_espera_create, name='lista_espera_create'),
    path('lista-espera/editar/<uuid:pk>/', views.lista_espera_update, name='lista_espera_update'),
    
    path('agenda/', views.agenda_list, name='agenda_list'),
    path('agenda/calendario/', views.agenda_calendario, name='agenda_calendario'),
    path('agenda/agendar/<uuid:pk>/', views.agenda_agendar, name='agenda_agendar'),
    path('agenda/agendar/<uuid:pk>/novo/', views.agenda_agendar_novo, name='agenda_agendar_novo'),
    path('agenda/agendar/<uuid:pk>/selecionar/<int:paciente_pk>/', views.agenda_agendar_existente, name='agenda_agendar_existente'),
    path('agenda/finalizar/<int:pk>/', views.agenda_finalizar, name='agenda_finalizar'),
    path('agenda/iniciar/<int:pk>/', views.marcacao_iniciar_atendimento, name='marcacao_iniciar_atendimento'),
    path('agenda/mover/<int:pk>/', views.marcacao_mover, name='marcacao_mover'),
    
    path('cadastros/clinicas-odonto/', views.clinica_odonto_list, name='clinica_odonto_list'),
    path('cadastros/clinicas-odonto/nova/', views.clinica_odonto_create, name='clinica_odonto_create'),
    path('cadastros/clinicas-odonto/editar/<int:pk>/', views.clinica_odonto_update, name='clinica_odonto_update'),
    path('cadastros/clinicas-odonto/excluir/<int:pk>/', views.clinica_odonto_delete, name='clinica_odonto_delete'),
    
    path('cadastros/pacientes/', views.paciente_list, name='paciente_list'),
    path('cadastros/pacientes/checar-cpf/', views.paciente_check_cpf, name='paciente_check_cpf'),
    path('cadastros/pacientes/novo/', views.paciente_create, name='paciente_create'),
    path('cadastros/pacientes/editar/<int:pk>/', views.paciente_update, name='paciente_update'),
    path('cadastros/pacientes/excluir/<int:pk>/', views.paciente_delete, name='paciente_delete'),
    path('cadastros/pacientes/<int:paciente_id>/anamnese/', views.anamnese_update, name='anamnese_update'),
    path('cadastros/pacientes/<int:paciente_id>/arquivos/', views.documento_paciente_list, name='documento_paciente_list'),
    path('cadastros/pacientes/<int:paciente_id>/arquivos/<int:documento_id>/apagar/', views.documento_paciente_delete, name='documento_paciente_delete'),
    path('cadastros/pacientes/<int:paciente_id>/prontuario/', views.paciente_prontuario, name='paciente_prontuario'),
    path('cadastros/pacientes/<int:paciente_id>/prontuario/<int:evolucao_id>/apagar/', views.evolucao_delete, name='evolucao_delete'),
    path('cadastros/pacientes/<int:paciente_id>/consultas/', views.paciente_consultas, name='paciente_consultas'),
    
    path('cadastros/academicos/', views.academico_list, name='academico_list'),
    path('cadastros/academicos/novo/', views.academico_create, name='academico_create'),
    path('cadastros/academicos/editar/<int:pk>/', views.academico_update, name='academico_update'),
    path('cadastros/academicos/excluir/<int:pk>/', views.academico_delete, name='academico_delete'),
    
    path('cadastros/professores/', views.professor_list, name='professor_list'),
    path('cadastros/professores/novo/', views.professor_create, name='professor_create'),
    path('cadastros/professores/editar/<int:pk>/', views.professor_update, name='professor_update'),
    path('cadastros/professores/excluir/<int:pk>/', views.professor_delete, name='professor_delete'),
    
    path('cadastros/colaboradores/', views.colaborador_list, name='colaborador_list'),
    path('cadastros/colaboradores/novo/', views.colaborador_create, name='colaborador_create'),
    path('cadastros/colaboradores/editar/<int:pk>/', views.colaborador_update, name='colaborador_update'),
    path('cadastros/colaboradores/excluir/<int:pk>/', views.colaborador_delete, name='colaborador_delete'),
    
    path('supervisao/aprovacoes/', views.aprovacoes_pendentes, name='aprovacoes_pendentes'),
    path('supervisao/aprovacao/<int:evolucao_id>/', views.evolucao_aprovar, name='evolucao_aprovar'),
    path('supervisao/aprovacao/<int:evolucao_id>/alterar/', views.evolucao_alterar, name='evolucao_alterar'),
    
    path('cadastros/duplas/', views.dupla_list, name='dupla_list'),
    path('cadastros/duplas/nova/', views.dupla_create, name='dupla_create'),
    path('cadastros/duplas/editar/<int:pk>/', views.dupla_update, name='dupla_update'),
    path('cadastros/duplas/excluir/<int:pk>/', views.dupla_delete, name='dupla_delete'),

    path('cadastros/boxes/', views.box_list, name='box_list'),
    path('cadastros/boxes/novo/', views.box_create, name='box_create'),
    path('cadastros/boxes/editar/<int:pk>/', views.box_update, name='box_update'),
    path('cadastros/boxes/excluir/<int:pk>/', views.box_delete, name='box_delete'),

    path('cadastros/clinicas/', views.clinica_list, name='clinica_list'),
    path('cadastros/clinicas/nova/', views.clinica_create, name='clinica_create'),
    path('cadastros/clinicas/editar/<int:pk>/', views.clinica_update, name='clinica_update'),
    path('cadastros/clinicas/excluir/<int:pk>/', views.clinica_delete, name='clinica_delete'),

    # ── Almoxarifado (módulo opcional) ────────────────────────────────────────
    path('estoque/', views.estoque_list, name='estoque_list'),
    path('estoque/novo/', views.estoque_create, name='estoque_create'),
    path('estoque/editar/<int:pk>/', views.estoque_update, name='estoque_update'),
    path('estoque/excluir/<int:pk>/', views.estoque_delete, name='estoque_delete'),
    path('estoque/<int:pk>/movimentar/', views.estoque_movimentar, name='estoque_movimentar'),
    path('estoque/<int:pk>/historico/', views.estoque_historico, name='estoque_historico'),
]
