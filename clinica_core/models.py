import uuid
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User

class AuditableModel(models.Model):
    user_create = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_%(class)s_set')
    user_update = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='updated_%(class)s_set')
    user_delete = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='deleted_%(class)s_set')
    date_create = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    date_alter = models.DateTimeField(auto_now=True, null=True, blank=True)
    date_delete = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True

class Clinica(AuditableModel):
    NOME_CHOICES = [
        ('OD', 'Odontologia'),
        ('PS', 'Psicologia'),
        ('FI', 'Fisioterapia'),
        ('EN', 'Enfermagem'),
    ]
    nome = models.CharField(max_length=2, choices=NOME_CHOICES)
    
    def __str__(self):
        return self.get_nome_display()

class Academico(AuditableModel):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='academico_profile', null=True, blank=True)
    nome = models.CharField(max_length=100)
    clinica = models.ForeignKey(Clinica, on_delete=models.CASCADE)

    def __str__(self):
        return self.nome

class Professor(AuditableModel):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='professor_profile', null=True, blank=True)
    nome = models.CharField(max_length=100)
    clinica = models.ForeignKey(Clinica, on_delete=models.CASCADE)

    def __str__(self):
        return self.nome

class Colaborador(AuditableModel):
    CARGOS_CHOICES = [
        ('SECRETARIA', 'Secretária(o) / Recepcionista'),
        ('ADMINISTRADOR', 'Administrador(a) do Sistema'),
        ('COLABORADOR', 'Colaborador(a) Geral'),
        ('COORDENADOR', 'Coordenador(a) Geral'),
    ]
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='colaborador_profile', null=True, blank=True)
    nome = models.CharField(max_length=100)
    cargo = models.CharField(max_length=50, choices=CARGOS_CHOICES, default='SECRETARIA')

    def __str__(self):
        return f"{self.nome} - {self.get_cargo_display()}"

class Paciente(AuditableModel):
    nome = models.CharField(max_length=100)
    cpf = models.CharField(max_length=14, unique=True, null=True, blank=True)
    data_nascimento = models.DateField(null=True, blank=True)
    celular = models.CharField(max_length=20, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    endereco = models.TextField(null=True, blank=True)
    observacao = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.nome

class Box(AuditableModel):
    """Representa um espaço físico clínico: cadeira, maca, consultório etc."""
    nome = models.CharField(max_length=100, verbose_name="Nome do Box / Sala")
    clinica = models.ForeignKey(Clinica, on_delete=models.CASCADE, related_name='boxes', verbose_name="Clínica")
    descricao = models.CharField(max_length=255, blank=True, null=True, verbose_name="Descrição")
    ativo = models.BooleanField(default=True, verbose_name="Ativo")

    def __str__(self):
        return f"{self.nome} — {self.clinica.get_nome_display()}"

    class Meta:
        verbose_name = "Box / Sala"
        verbose_name_plural = "Boxes / Salas"
        ordering = ['clinica', 'nome']


class Marcacao(AuditableModel):
    STATUS_CHOICES = [
        ('CONFIRMADO', 'Confirmado'),
        ('EM_ESPERA', 'Em Espera'),
        ('EM_ATENDIMENTO', 'Em Atendimento'),
        ('AGUARDANDO_SUPERVISOR', 'Aguardando Supervisor'),
        ('CONCLUIDO', 'Concluído'),
    ]
    
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE)
    academico = models.ForeignKey(Academico, on_delete=models.CASCADE, null=True, blank=True)
    professor = models.ForeignKey(Professor, on_delete=models.CASCADE, null=True, blank=True, verbose_name="Professor/Responsável")
    clinica = models.ForeignKey(Clinica, on_delete=models.CASCADE)
    box = models.ForeignKey('Box', on_delete=models.SET_NULL, null=True, blank=True, related_name='marcacoes', verbose_name="Box / Sala")
    dupla = models.ForeignKey('DuplaOdonto', on_delete=models.SET_NULL, null=True, blank=True, related_name='marcacoes', verbose_name="Dupla de Alunos (Odonto)")
    data_hora = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=25, choices=STATUS_CHOICES, default='CONFIRMADO')
    
    # Finalização
    data_hora_finalizacao = models.DateTimeField(null=True, blank=True)
    usuario_finalizacao = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='marcacoes_finalizadas')
    lista_espera = models.ForeignKey('ListaEspera', on_delete=models.SET_NULL, null=True, blank=True, related_name='marcacoes', verbose_name="Origem (Lista de Espera)")

    def __str__(self):
        return f"{self.paciente.nome} - {self.data_hora.strftime('%H:%M')}"

class ListaEspera(AuditableModel):
    STATUS_CHOICES = [
        ('AGUARDANDO', 'Aguardando'),
        ('AGENDADO', 'Agendado'),
        ('CONCLUÍDO', 'Concluído'),
        ('CANCELADO', 'Cancelado')
    ]
    
    id_marcacao = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    pessoa = models.CharField(max_length=255)
    celular = models.CharField(max_length=20)
    atendente = models.ForeignKey(User, on_delete=models.CASCADE, related_name='atendimentos_lista_espera')
    clinica = models.ForeignKey(Clinica, on_delete=models.CASCADE)
    clinica_odonto = models.ForeignKey('ClinicaOdonto', on_delete=models.SET_NULL, null=True, blank=True, related_name='agendamentos')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='AGUARDANDO')
    data_hora_marcacao = models.DateTimeField()
    observacao = models.TextField(null=True, blank=True)
    agendamento = models.OneToOneField(
        'Marcacao',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='origem_lista_espera',
        verbose_name="Agendamento gerado"
    )

    def __str__(self):
        return f"{self.pessoa} - {self.clinica.get_nome_display()}"

class ClinicaOdonto(AuditableModel):
    nome = models.CharField(max_length=255)
    descricao = models.TextField(blank=True, null=True, verbose_name="Descrição")
    alunos_periodos = models.CharField(max_length=255, verbose_name="Alunos dos Períodos")

    def __str__(self):
        return self.nome

class DuplaOdonto(AuditableModel):
    nome = models.CharField(max_length=255, blank=True, null=True, verbose_name="Sufixo ou Identificador (Opcional)")
    aluno1 = models.ForeignKey(Academico, on_delete=models.CASCADE, related_name='duplas_primarias', verbose_name="Aluno/Acadêmico 1 (Titular)")
    aluno2 = models.ForeignKey(Academico, on_delete=models.SET_NULL, null=True, blank=True, related_name='duplas_secundarias', verbose_name="Aluno/Acadêmico 2 (Opcional)")
    clinica_odonto = models.ForeignKey(ClinicaOdonto, on_delete=models.CASCADE, related_name='duplas', verbose_name="Sub-Clínica/Turma")

    def __str__(self):
        nome_aluno1 = self.aluno1.nome.split()[0] if self.aluno1 else "Sem Aluno"
        
        if self.nome:
            return f"{self.nome} - {self.clinica_odonto.nome}"
        if self.aluno2:
            nome_aluno2 = self.aluno2.nome.split()[0]
            return f"Dupla: {nome_aluno1} & {nome_aluno2} - {self.clinica_odonto.nome}"
        return f"Individual: {nome_aluno1} - {self.clinica_odonto.nome}"

class Anamnese(AuditableModel):
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE, related_name='anamneses')
    clinica = models.ForeignKey(Clinica, on_delete=models.CASCADE, related_name='anamneses', null=True, blank=True)
    historico_medico = models.TextField(blank=True, null=True, verbose_name="Histórico Médico")
    alergias = models.TextField(blank=True, null=True, verbose_name="Alergias")
    pressao_arterial = models.CharField(max_length=50, blank=True, null=True, verbose_name="Pressão Arterial")
    medicamentos_em_uso = models.TextField(blank=True, null=True, verbose_name="Medicamentos em Uso")
    queixa_principal = models.TextField(blank=True, null=True, verbose_name="Queixa Principal")

    class Meta:
        unique_together = ('paciente', 'clinica')

    def __str__(self):
        return f"Anamnese - {self.paciente.nome}"

class DocumentoPaciente(AuditableModel):
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE, related_name='documentos')
    clinica = models.ForeignKey(Clinica, on_delete=models.CASCADE, related_name='documentos', null=True, blank=True)
    arquivo = models.FileField(upload_to='documentos_pacientes/')
    descricao = models.CharField(max_length=255, blank=True, null=True, verbose_name="Descrição do Arquivo")

    def __str__(self):
        return f"{self.descricao or 'Documento'} - {self.paciente.nome}"

class Evolucao(AuditableModel):
    STATUS_APROVACAO = [
        ('AGUARDANDO', 'Aguardando Supervisor'),
        ('APROVADO', 'Aprovado')
    ]
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE, related_name='evolucoes')
    clinica = models.ForeignKey(Clinica, on_delete=models.CASCADE, related_name='evolucoes', null=True, blank=True)
    descricao = models.TextField(verbose_name="Evolução Clínica")
    
    # Supervisão
    status = models.CharField(max_length=20, choices=STATUS_APROVACAO, default='AGUARDANDO')
    nota = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    avaliador = models.ForeignKey(Professor, on_delete=models.SET_NULL, null=True, blank=True)
    observacao_supervisor = models.TextField(blank=True, null=True)

    class Meta:
        permissions = [
            ("can_approve_evolucao", "Can approve evolucao")
        ]

    def __str__(self):
        return f"Evolução - {self.paciente.nome}"

class LogAlteracaoEvolucao(models.Model):
    evolucao = models.ForeignKey(Evolucao, on_delete=models.CASCADE, related_name='logs_alteracao')
    professor = models.ForeignKey(Professor, on_delete=models.SET_NULL, null=True, blank=True)
    data_alteracao = models.DateTimeField(auto_now_add=True)
    nota_anterior = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    nota_nova = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    observacao_anterior = models.TextField(blank=True, null=True)
    observacao_nova = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Alteração na Evolução {self.evolucao.id} em {self.data_alteracao.strftime('%d/%m/%Y')}"


# ── MÓDULO DE ESTOQUE (ALMOXARIFADO) ─────────────────────────────────────────

class ItemEstoque(AuditableModel):
    """Catálogo de insumos clínicos controlados pelo almoxarifado."""
    nome = models.CharField(max_length=200, verbose_name="Nome do Item")
    codigo = models.CharField(max_length=50, blank=True, null=True, verbose_name="Código / SKU")
    unidade = models.CharField(max_length=50, default="Unidade", verbose_name="Unidade de Medida")
    clinica = models.ForeignKey(
        Clinica, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='itens_estoque', verbose_name="Clínica (opcional)"
    )
    estoque_minimo = models.PositiveIntegerField(default=0, verbose_name="Estoque Mínimo (alerta)")
    estoque_atual = models.PositiveIntegerField(default=0, verbose_name="Estoque Atual")
    descricao = models.TextField(blank=True, null=True, verbose_name="Descrição / Observações")
    ativo = models.BooleanField(default=True, verbose_name="Ativo")

    class Meta:
        verbose_name = "Item de Estoque"
        verbose_name_plural = "Itens de Estoque"
        ordering = ['nome']

    def __str__(self):
        return self.nome

    @property
    def estoque_baixo(self):
        return self.estoque_atual <= self.estoque_minimo


class MovimentacaoEstoque(AuditableModel):
    """Registro de entrada ou saída de um insumo."""
    TIPO_CHOICES = [
        ('ENTRADA', 'Entrada'),
        ('SAIDA', 'Saída'),
    ]
    item = models.ForeignKey(
        ItemEstoque, on_delete=models.CASCADE,
        related_name='movimentacoes', verbose_name="Item"
    )
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES, verbose_name="Tipo")
    quantidade = models.PositiveIntegerField(verbose_name="Quantidade")
    data = models.DateField(default=timezone.now, verbose_name="Data")
    responsavel = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='movimentacoes_estoque', verbose_name="Responsável"
    )
    motivo = models.CharField(max_length=255, blank=True, null=True, verbose_name="Motivo / Referência")
    observacao = models.TextField(blank=True, null=True, verbose_name="Observação")

    class Meta:
        verbose_name = "Movimentação de Estoque"
        verbose_name_plural = "Movimentações de Estoque"
        ordering = ['-data', '-date_create']

    def __str__(self):
        return f"{self.get_tipo_display()} — {self.item.nome} ({self.quantidade} {self.item.unidade})"

    def save(self, *args, **kwargs):
        # Atualiza estoque_atual do item
        item = self.item
        if self.tipo == 'ENTRADA':
            item.estoque_atual += self.quantidade
        elif self.tipo == 'SAIDA':
            item.estoque_atual = max(0, item.estoque_atual - self.quantidade)
        item.save(update_fields=['estoque_atual'])
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # Reverte o efeito da movimentação ao deletar
        item = self.item
        if self.tipo == 'ENTRADA':
            item.estoque_atual = max(0, item.estoque_atual - self.quantidade)
        elif self.tipo == 'SAIDA':
            item.estoque_atual += self.quantidade
        item.save(update_fields=['estoque_atual'])
        super().delete(*args, **kwargs)