import re
from django import forms
from .models import ListaEspera, ClinicaOdonto, Paciente, Anamnese, DocumentoPaciente, Evolucao, Professor, Academico, DuplaOdonto, Marcacao, Colaborador, Box, Clinica, ItemEstoque, MovimentacaoEstoque

class ListaEsperaForm(forms.ModelForm):
    class Meta:
        model = ListaEspera
        fields = ['pessoa', 'celular', 'clinica', 'clinica_odonto', 'status', 'data_hora_marcacao', 'observacao']
        widgets = {
            'pessoa': forms.TextInput(attrs={
                'class': 'w-full bg-slate-50 dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded-lg px-4 py-3 text-slate-900 dark:text-white focus:outline-none focus:border-indigo-500 transition',
                'placeholder': 'Nome completo do paciente'
            }),
            'celular': forms.TextInput(attrs={
                'class': 'w-full bg-slate-50 dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded-lg px-4 py-3 text-slate-900 dark:text-white focus:outline-none focus:border-indigo-500 transition',
                'placeholder': '(XX) XXXXX-XXXX',
                'pattern': '\\(\\d{2}\\) \\d{4,5}-\\d{4}',
                'title': 'Digite o número no formato (XX) XXXXX-XXXX'
            }),
            'clinica': forms.Select(attrs={
                'class': 'w-full bg-slate-50 dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded-lg px-4 py-3 text-slate-900 dark:text-white focus:outline-none focus:border-indigo-500 transition'
            }),
            'clinica_odonto': forms.Select(attrs={
                'class': 'hidden',
                'id': 'id_clinica_odonto_hidden'
            }),
            'status': forms.Select(attrs={
                'class': 'w-full bg-slate-50 dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded-lg px-4 py-3 text-slate-900 dark:text-white focus:outline-none focus:border-indigo-500 transition'
            }),
            'data_hora_marcacao': forms.DateTimeInput(format='%Y-%m-%dT%H:%M', attrs={
                'class': 'w-full bg-slate-50 dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded-lg px-4 py-3 text-slate-900 dark:text-white focus:outline-none focus:border-indigo-500 transition',
                'type': 'datetime-local'
            }),
            'observacao': forms.Textarea(attrs={
                'class': 'w-full bg-slate-50 dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded-lg px-4 py-3 text-slate-900 dark:text-white focus:outline-none focus:border-indigo-500 transition',
                'placeholder': 'Observações sobre o tratamento do paciente',
                'rows': 3
            })
        }

class ClinicaOdontoForm(forms.ModelForm):
    class Meta:
        model = ClinicaOdonto
        fields = ['nome', 'descricao', 'alunos_periodos']
        widgets = {
            'nome': forms.TextInput(attrs={
                'class': 'w-full bg-slate-50 dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded-lg px-4 py-3 text-slate-900 dark:text-white focus:outline-none focus:border-indigo-500 transition',
                'placeholder': 'Nome da Clínica de Odonto'
            }),
            'descricao': forms.Textarea(attrs={
                'class': 'w-full bg-slate-50 dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded-lg px-4 py-3 text-slate-900 dark:text-white focus:outline-none focus:border-indigo-500 transition',
                'placeholder': 'Descrição ou observações',
                'rows': 3
            }),
            'alunos_periodos': forms.TextInput(attrs={
                'class': 'w-full bg-slate-50 dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded-lg px-4 py-3 text-slate-900 dark:text-white focus:outline-none focus:border-indigo-500 transition',
                'placeholder': 'Ex: 1º ao 3º período'
            })
        }

class DuplaOdontoForm(forms.ModelForm):
    class Meta:
        model = DuplaOdonto
        fields = ['nome', 'clinica_odonto', 'aluno1', 'aluno2']
        widgets = {
            'nome': forms.TextInput(attrs={
                'class': 'w-full bg-slate-50 dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded-lg px-4 py-3 text-slate-900 dark:text-white focus:outline-none focus:border-indigo-500 transition',
                'placeholder': 'Opcional. Ex: Equipe Alpha'
            }),
            'clinica_odonto': forms.Select(attrs={
                'class': 'w-full bg-slate-50 dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded-lg px-4 py-3 text-slate-900 dark:text-white focus:outline-none focus:border-indigo-500 transition'
            }),
            'aluno1': forms.Select(attrs={
                'class': 'w-full bg-slate-50 dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded-lg px-4 py-3 text-slate-900 dark:text-white focus:outline-none focus:border-indigo-500 transition'
            }),
            'aluno2': forms.Select(attrs={
                'class': 'w-full bg-slate-50 dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded-lg px-4 py-3 text-slate-900 dark:text-white focus:outline-none focus:border-indigo-500 transition'
            }),
        }

    def __init__(self, *args, **kwargs):
        super(DuplaOdontoForm, self).__init__(*args, **kwargs)
        # Filtra apenas acadêmicos de odontologia ('OD')
        academicos_odonto = Academico.objects.filter(clinica__nome='OD')
        self.fields['aluno1'].queryset = academicos_odonto
        self.fields['aluno2'].queryset = academicos_odonto
        
    def clean(self):
        cleaned_data = super().clean()
        aluno1 = cleaned_data.get('aluno1')
        aluno2 = cleaned_data.get('aluno2')

        if aluno1 and aluno2 and aluno1 == aluno2:
            self.add_error('aluno2', 'O Aluno 2 não pode ser o mesmo que o Aluno 1.')
        
        return cleaned_data

class PacienteForm(forms.ModelForm):
    class Meta:
        model = Paciente
        fields = ['nome', 'cpf', 'data_nascimento', 'celular', 'email', 'endereco', 'observacao']
        widgets = {
            'nome': forms.TextInput(attrs={
                'class': 'w-full bg-slate-50 dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded-lg px-4 py-3 text-slate-900 dark:text-white focus:outline-none focus:border-indigo-500 transition',
                'placeholder': 'Nome completo'
            }),
            'cpf': forms.TextInput(attrs={
                'class': 'w-full bg-slate-50 dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded-lg px-4 py-3 text-slate-900 dark:text-white focus:outline-none focus:border-indigo-500 transition',
                'placeholder': '000.000.000-00',
                'maxlength': '14'
            }),
            'data_nascimento': forms.DateInput(format='%Y-%m-%d', attrs={
                'class': 'w-full bg-slate-50 dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded-lg px-4 py-3 text-slate-900 dark:text-white focus:outline-none focus:border-indigo-500 transition',
                'type': 'date'
            }),
            'celular': forms.TextInput(attrs={
                'class': 'w-full bg-slate-50 dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded-lg px-4 py-3 text-slate-900 dark:text-white focus:outline-none focus:border-indigo-500 transition',
                'placeholder': '(XX) XXXXX-XXXX'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'w-full bg-slate-50 dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded-lg px-4 py-3 text-slate-900 dark:text-white focus:outline-none focus:border-indigo-500 transition',
                'placeholder': 'email@exemplo.com'
            }),
            'endereco': forms.Textarea(attrs={
                'class': 'w-full bg-slate-50 dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded-lg px-4 py-3 text-slate-900 dark:text-white focus:outline-none focus:border-indigo-500 transition',
                'placeholder': 'Rua, Número, Bairro, Cidade, Estado, CEP',
                'rows': 2
            }),
            'observacao': forms.Textarea(attrs={
                'class': 'w-full bg-slate-50 dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded-lg px-4 py-3 text-slate-900 dark:text-white focus:outline-none focus:border-indigo-500 transition',
                'placeholder': 'Observações gerais, prontuário inicial, etc.',
                'rows': 3
            })
        }

    def clean_cpf(self):
        cpf = self.cleaned_data.get('cpf')
        if not cpf:
            return cpf
            
        cpf = re.sub(r'[^0-9]', '', cpf)
        
        if len(cpf) != 11:
            raise forms.ValidationError('O CPF deve ter 11 dígitos.')
            
        if cpf == cpf[0] * 11:
            raise forms.ValidationError('CPF inválido.')
            
        # Calcula o primeiro dígito verificador
        soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
        resto = (soma * 10) % 11
        if resto == 10:
            resto = 0
        if resto != int(cpf[9]):
            raise forms.ValidationError('CPF inválido.')
            
        # Calcula o segundo dígito verificador
        soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
        resto = (soma * 10) % 11
        if resto == 10:
            resto = 0
        if resto != int(cpf[10]):
            raise forms.ValidationError('CPF inválido.')
            
        return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"

class AnamneseForm(forms.ModelForm):
    class Meta:
        model = Anamnese
        fields = ['clinica', 'historico_medico', 'alergias', 'pressao_arterial', 'medicamentos_em_uso', 'queixa_principal']
        widgets = {
            'clinica': forms.Select(attrs={
                'class': 'w-full bg-slate-50 dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded-lg px-4 py-3 text-slate-900 dark:text-white focus:outline-none focus:border-indigo-500 transition mb-4'
            }),
            'historico_medico': forms.Textarea(attrs={
                'class': 'w-full bg-slate-50 dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded-lg px-4 py-3 text-slate-900 dark:text-white focus:outline-none focus:border-indigo-500 transition',
                'placeholder': 'Descreva o histórico de doenças e cirurgias do paciente',
                'rows': 4
            }),
            'alergias': forms.Textarea(attrs={
                'class': 'w-full bg-slate-50 dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded-lg px-4 py-3 text-slate-900 dark:text-white focus:outline-none focus:border-indigo-500 transition',
                'placeholder': 'Descreva reações alérgicas conhecidas a substâncias, medicamentos ou alimentos',
                'rows': 3
            }),
            'pressao_arterial': forms.TextInput(attrs={
                'class': 'w-full bg-slate-50 dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded-lg px-4 py-3 text-slate-900 dark:text-white focus:outline-none focus:border-indigo-500 transition',
                'placeholder': 'Ex: 120/80 mmHg'
            }),
            'medicamentos_em_uso': forms.Textarea(attrs={
                'class': 'w-full bg-slate-50 dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded-lg px-4 py-3 text-slate-900 dark:text-white focus:outline-none focus:border-indigo-500 transition',
                'placeholder': 'Descreva os medicamentos que o paciente faz uso atualmente',
                'rows': 3
            }),
            'queixa_principal': forms.Textarea(attrs={
                'class': 'w-full bg-slate-50 dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded-lg px-4 py-3 text-slate-900 dark:text-white focus:outline-none focus:border-indigo-500 transition',
                'placeholder': 'Motivo principal da busca pelo atendimento',
                'rows': 3
            })
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user and (hasattr(user, 'professor_profile') or hasattr(user, 'academico_profile')):
            if 'clinica' in self.fields:
                self.fields.pop('clinica', None)
        elif 'clinica' in self.fields:
            self.fields['clinica'].required = True

class DocumentoPacienteForm(forms.ModelForm):
    class Meta:
        model = DocumentoPaciente
        fields = ['clinica', 'arquivo', 'descricao']
        widgets = {
            'clinica': forms.Select(attrs={
                'class': 'w-full bg-slate-50 dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded-lg px-4 py-3 text-slate-900 dark:text-white focus:outline-none focus:border-indigo-500 transition mb-4'
            }),
            'arquivo': forms.FileInput(attrs={
                'class': 'w-full bg-slate-50 dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded-lg px-4 py-3 text-slate-900 dark:text-white focus:outline-none focus:border-indigo-500 transition file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100 dark:file:bg-indigo-900/50 dark:file:text-indigo-300',
                'accept': 'image/*,application/pdf'
            }),
            'descricao': forms.TextInput(attrs={
                'class': 'w-full bg-slate-50 dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded-lg px-4 py-3 text-slate-900 dark:text-white focus:outline-none focus:border-indigo-500 transition',
                'placeholder': 'Descrição curta (ex: Raio-X, Atestado...)'
            })
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user and (hasattr(user, 'professor_profile') or hasattr(user, 'academico_profile')):
            if 'clinica' in self.fields:
                self.fields.pop('clinica', None)
        elif 'clinica' in self.fields:
            self.fields['clinica'].required = True

class EvolucaoForm(forms.ModelForm):
    class Meta:
        model = Evolucao
        fields = ['clinica', 'descricao']
        widgets = {
            'clinica': forms.Select(attrs={
                'class': 'w-full bg-slate-50 dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded-lg px-4 py-3 text-slate-900 dark:text-white focus:outline-none focus:border-indigo-500 transition mb-4'
            }),
            'descricao': forms.Textarea(attrs={
                'class': 'w-full bg-slate-50 dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded-lg px-4 py-3 text-slate-900 dark:text-white focus:outline-none focus:border-indigo-500 transition',
                'placeholder': 'Descreva detalhadamente o que foi realizado clinicamente neste momento...',
                'rows': 4
            })
        }

    def __init__(self, *args, user=None, clinica_override=None, **kwargs):
        super().__init__(*args, **kwargs)
        # Se a clínica já é conhecida externamente (ex: finalizar consulta da agenda), remove o campo
        if clinica_override or (user and (hasattr(user, 'professor_profile') or hasattr(user, 'academico_profile'))):
            self.fields.pop('clinica', None)
        elif 'clinica' in self.fields:
            self.fields['clinica'].required = True

class ProfessorForm(forms.ModelForm):
    username = forms.CharField(max_length=150, widget=forms.TextInput(attrs={
        'class': 'w-full bg-slate-50 dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded-lg px-4 py-3 text-slate-900 dark:text-white focus:outline-none focus:border-indigo-500 transition', 'placeholder': 'Matrícula / Usuário de Login'
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'w-full bg-slate-50 dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded-lg px-4 py-3 text-slate-900 dark:text-white focus:outline-none focus:border-indigo-500 transition', 'placeholder': 'Senha (deixe em branco se for editar)'
    }), required=False)

    class Meta:
        model = Professor
        fields = ['nome', 'clinica']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'w-full bg-slate-50 dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded-lg px-4 py-3 text-slate-900 dark:text-white focus:outline-none focus:border-indigo-500 transition', 'placeholder': 'Nome Completo'}),
            'clinica': forms.Select(attrs={'class': 'w-full bg-slate-50 dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded-lg px-4 py-3 text-slate-900 dark:text-white focus:outline-none focus:border-indigo-500 transition'})
        }

class AcademicoForm(forms.ModelForm):
    username = forms.CharField(max_length=150, widget=forms.TextInput(attrs={
        'class': 'w-full bg-slate-50 dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded-lg px-4 py-3 text-slate-900 dark:text-white focus:outline-none focus:border-indigo-500 transition', 'placeholder': 'Matrícula / Usuário de Login'
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'w-full bg-slate-50 dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded-lg px-4 py-3 text-slate-900 dark:text-white focus:outline-none focus:border-indigo-500 transition', 'placeholder': 'Senha (deixe em branco se for editar)'
    }), required=False)

    class Meta:
        model = Academico
        fields = ['nome', 'clinica']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'w-full bg-slate-50 dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded-lg px-4 py-3 text-slate-900 dark:text-white focus:outline-none focus:border-indigo-500 transition', 'placeholder': 'Nome Acâdemico'}),
            'clinica': forms.Select(attrs={'class': 'w-full bg-slate-50 dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded-lg px-4 py-3 text-slate-900 dark:text-white focus:outline-none focus:border-indigo-500 transition'})
        }

class ColaboradorForm(forms.ModelForm):
    username = forms.CharField(max_length=150, widget=forms.TextInput(attrs={
        'class': 'w-full bg-slate-50 dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded-lg px-4 py-3 text-slate-900 dark:text-white focus:outline-none focus:border-indigo-500 transition', 'placeholder': 'Matrícula / Login'
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'w-full bg-slate-50 dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded-lg px-4 py-3 text-slate-900 dark:text-white focus:outline-none focus:border-indigo-500 transition', 'placeholder': 'Senha (deixe em branco se for editar)'
    }), required=False)

    class Meta:
        model = Colaborador
        fields = ['nome', 'cargo']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'w-full bg-slate-50 dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded-lg px-4 py-3 text-slate-900 dark:text-white focus:outline-none focus:border-indigo-500 transition', 'placeholder': 'Nome Completo'}),
            'cargo': forms.Select(attrs={'class': 'w-full bg-slate-50 dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded-lg px-4 py-3 text-slate-900 dark:text-white focus:outline-none focus:border-indigo-500 transition'})
        }

class AprovacaoEvolucaoForm(forms.ModelForm):
    class Meta:
        model = Evolucao
        fields = ['nota', 'observacao_supervisor']
        widgets = {
            'nota': forms.NumberInput(attrs={'class': 'w-full bg-slate-50 dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded-lg px-4 py-3 text-slate-900 dark:text-white focus:outline-none focus:border-indigo-500 transition', 'step': '0.1', 'min': '0', 'max': '10', 'placeholder': 'Ex: 9.5'}),
            'observacao_supervisor': forms.Textarea(attrs={'class': 'w-full bg-slate-50 dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded-lg px-4 py-3 text-slate-900 dark:text-white focus:outline-none focus:border-indigo-500 transition', 'rows': 3, 'placeholder': 'Feedback avaliativo para o prontuário preenchido...'})
        }

class AlteracaoEvolucaoForm(forms.ModelForm):
    senha = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full bg-slate-50 dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded-lg px-4 py-3 text-slate-900 dark:text-white focus:outline-none focus:border-indigo-500 transition',
            'placeholder': 'Digite sua senha para confirmar'
        }),
        required=True,
        label='Senha de Confirmação'
    )

    class Meta:
        model = Evolucao
        fields = ['nota', 'observacao_supervisor']
        widgets = {
            'nota': forms.NumberInput(attrs={'class': 'w-full bg-slate-50 dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded-lg px-4 py-3 text-slate-900 dark:text-white focus:outline-none focus:border-indigo-500 transition', 'step': '0.1', 'min': '0', 'max': '10', 'placeholder': 'Ex: 9.5'}),
            'observacao_supervisor': forms.Textarea(attrs={'class': 'w-full bg-slate-50 dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded-lg px-4 py-3 text-slate-900 dark:text-white focus:outline-none focus:border-indigo-500 transition', 'rows': 3, 'placeholder': 'Novo comentário / feedback do professor...'})
        }

class MarcacaoForm(forms.ModelForm):
    class Meta:
        model = Marcacao
        fields = ['data_hora', 'professor', 'box', 'dupla']
        widgets = {
            'data_hora': forms.DateTimeInput(format='%Y-%m-%dT%H:%M', attrs={
                'class': 'w-full bg-slate-50 dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded-lg px-4 py-3 text-slate-900 dark:text-white focus:outline-none focus:border-indigo-500 transition',
                'type': 'datetime-local'
            }),
            'professor': forms.Select(attrs={
                'class': 'w-full bg-slate-50 dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded-lg px-4 py-3 text-slate-900 dark:text-white focus:outline-none focus:border-indigo-500 transition'
            }),
            'box': forms.Select(attrs={
                'class': 'w-full bg-slate-50 dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded-lg px-4 py-3 text-slate-900 dark:text-white focus:outline-none focus:border-indigo-500 transition'
            }),
            'dupla': forms.Select(attrs={
                'class': 'w-full bg-slate-50 dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded-lg px-4 py-3 text-slate-900 dark:text-white focus:outline-none focus:border-indigo-500 transition',
                'id': 'id_dupla_odonto'
            }),
        }

    def __init__(self, *args, user=None, clinica_espera=None, **kwargs):
        super(MarcacaoForm, self).__init__(*args, **kwargs)
        if user:
            # Se for superuser ou não tiver perfil (secretária), traz todos
            if user.is_superuser or (not hasattr(user, 'professor_profile') and not hasattr(user, 'academico_profile')):
                self.fields['professor'].queryset = Professor.objects.all().order_by('nome')
            # Se for professor, traz da mesma clínica dele
            elif hasattr(user, 'professor_profile'):
                self.fields['professor'].queryset = Professor.objects.filter(clinica=user.professor_profile.clinica).order_by('nome')
            # Se for acadêmico, traz da mesma clínica também
            elif hasattr(user, 'academico_profile'):
                self.fields['professor'].queryset = Professor.objects.filter(clinica=user.academico_profile.clinica).order_by('nome')
        elif clinica_espera:
            self.fields['professor'].queryset = Professor.objects.filter(clinica=clinica_espera).order_by('nome')

        # Filtra boxes pela clínica da lista de espera (se fornecida)
        if clinica_espera:
            self.fields['box'].queryset = Box.objects.filter(clinica=clinica_espera, ativo=True).order_by('nome')
        else:
            self.fields['box'].queryset = Box.objects.filter(ativo=True).order_by('clinica', 'nome')
        self.fields['box'].required = False
        self.fields['box'].empty_label = '— Nenhum box / sem reserva —'

        # Campo de dupla: só relevante para Odontologia
        self.fields['dupla'].required = False
        self.fields['dupla'].empty_label = '— Nenhuma dupla selecionada —'
        if clinica_espera and clinica_espera.nome == 'OD':
            # Filtra duplas vinculadas à sub-clínica de odonto da lista de espera
            self._is_odonto = True
            self.fields['dupla'].queryset = DuplaOdonto.objects.select_related('aluno1', 'aluno2', 'clinica_odonto').order_by('clinica_odonto__nome', 'aluno1__nome')
        else:
            self._is_odonto = False
            self.fields['dupla'].queryset = DuplaOdonto.objects.none()

    def clean(self):
        cleaned_data = super().clean()
        box = cleaned_data.get('box')
        data_hora = cleaned_data.get('data_hora')

        if box and data_hora:
            from datetime import timedelta
            janela_inicio = data_hora - timedelta(minutes=59)
            janela_fim    = data_hora + timedelta(minutes=59)

            conflitos = Marcacao.objects.filter(
                box=box,
                data_hora__gte=janela_inicio,
                data_hora__lte=janela_fim,
                status__in=['CONFIRMADO', 'EM_ESPERA', 'EM_ATENDIMENTO', 'AGUARDANDO_SUPERVISOR'],
            )
            # Exclui a própria instância em caso de edição
            if self.instance and self.instance.pk:
                conflitos = conflitos.exclude(pk=self.instance.pk)

            if conflitos.exists():
                conflito = conflitos.first()
                raise forms.ValidationError(
                    f"⚠️ Overbooking detectado! O {box.nome} já está reservado às "
                    f"{conflito.data_hora.strftime('%H:%M')} para {conflito.paciente.nome}. "
                    f"Escolha outro box ou outro horário."
                )
        return cleaned_data


class BoxForm(forms.ModelForm):
    class Meta:
        model = Box
        fields = ['nome', 'clinica', 'descricao', 'ativo']
        widgets = {
            'nome': forms.TextInput(attrs={
                'class': 'w-full bg-slate-50 dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded-lg px-4 py-3 text-slate-900 dark:text-white focus:outline-none focus:border-indigo-500 transition',
                'placeholder': 'Ex: Box 01, Maca 02, Consultório A'
            }),
            'clinica': forms.Select(attrs={
                'class': 'w-full bg-slate-50 dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded-lg px-4 py-3 text-slate-900 dark:text-white focus:outline-none focus:border-indigo-500 transition'
            }),
            'descricao': forms.TextInput(attrs={
                'class': 'w-full bg-slate-50 dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded-lg px-4 py-3 text-slate-900 dark:text-white focus:outline-none focus:border-indigo-500 transition',
                'placeholder': 'Observações opcionais sobre o espaço'
            }),
            'ativo': forms.CheckboxInput(attrs={
                'class': 'w-5 h-5 rounded border-slate-300 dark:border-slate-600 text-indigo-600 focus:ring-indigo-500'
            }),
        }

class ClinicaForm(forms.ModelForm):
    class Meta:
        model = Clinica
        fields = ['nome']
        widgets = {
            'nome': forms.Select(attrs={
                'class': 'w-full bg-slate-50 dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded-lg px-4 py-3 text-slate-900 dark:text-white focus:outline-none focus:border-indigo-500 transition'
            }),
        }

    def clean_nome(self):
        nome = self.cleaned_data.get('nome')
        qs = Clinica.objects.filter(nome=nome)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError('Já existe uma clínica cadastrada com este tipo.')
        return nome


# ── MÓDULO DE ESTOQUE ─────────────────────────────────────────────────────────

CLASS_INPUT = 'w-full bg-slate-50 dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded-lg px-4 py-3 text-slate-900 dark:text-white focus:outline-none focus:border-indigo-500 transition'

class ItemEstoqueForm(forms.ModelForm):
    class Meta:
        model = ItemEstoque
        fields = ['nome', 'codigo', 'unidade', 'clinica', 'estoque_minimo', 'descricao', 'ativo']
        widgets = {
            'nome': forms.TextInput(attrs={'class': CLASS_INPUT, 'placeholder': 'Ex: Luvas de nitrilo (caixa 100un)'}),
            'codigo': forms.TextInput(attrs={'class': CLASS_INPUT, 'placeholder': 'Código interno / SKU (opcional)'}),
            'unidade': forms.TextInput(attrs={'class': CLASS_INPUT, 'placeholder': 'Ex: Caixa, Frasco, Unidade, Par'}),
            'clinica': forms.Select(attrs={'class': CLASS_INPUT}),
            'estoque_minimo': forms.NumberInput(attrs={'class': CLASS_INPUT, 'min': '0', 'placeholder': '0'}),
            'descricao': forms.Textarea(attrs={'class': CLASS_INPUT, 'rows': 3, 'placeholder': 'Observações adicionais (opcional)'}),
            'ativo': forms.CheckboxInput(attrs={'class': 'w-5 h-5 rounded border-slate-300 dark:border-slate-600 text-indigo-600 focus:ring-indigo-500'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['clinica'].required = False
        self.fields['clinica'].empty_label = '— Todas as clínicas —'


class MovimentacaoEstoqueForm(forms.ModelForm):
    class Meta:
        model = MovimentacaoEstoque
        fields = ['tipo', 'quantidade', 'data', 'motivo', 'observacao']
        widgets = {
            'tipo': forms.Select(attrs={'class': CLASS_INPUT}),
            'quantidade': forms.NumberInput(attrs={'class': CLASS_INPUT, 'min': '1', 'placeholder': '1'}),
            'data': forms.DateInput(format='%Y-%m-%d', attrs={'class': CLASS_INPUT, 'type': 'date'}),
            'motivo': forms.TextInput(attrs={'class': CLASS_INPUT, 'placeholder': 'Ex: Compra NF 1234, Uso em atendimento, Doação'}),
            'observacao': forms.Textarea(attrs={'class': CLASS_INPUT, 'rows': 2, 'placeholder': 'Detalhes opcionais'}),
        }

    def __init__(self, *args, item=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._item = item

    def clean(self):
        cleaned = super().clean()
        tipo = cleaned.get('tipo')
        quantidade = cleaned.get('quantidade')
        if tipo == 'SAIDA' and self._item and quantidade:
            if quantidade > self._item.estoque_atual:
                raise forms.ValidationError(
                    f'Quantidade insuficiente em estoque. '
                    f'Disponível: {self._item.estoque_atual} {self._item.unidade}.'
                )
        return cleaned
