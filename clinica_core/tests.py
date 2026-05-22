from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from clinica_core.models import Paciente, ListaEspera, Clinica, Marcacao
from clinica_core.forms import PacienteForm
import datetime
from django.utils import timezone

class PacienteUniquenessTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password')
        self.clinica = Clinica.objects.create(nome='OD')
        self.paciente_existente = Paciente.objects.create(
            nome="Paciente Existente",
            cpf="123.456.789-09",
            data_nascimento="1990-01-01"
        )
        self.lista_espera = ListaEspera.objects.create(
            pessoa="Novo Paciente",
            celular="(11) 99999-9999",
            atendente=self.user,
            clinica=self.clinica,
            data_hora_marcacao=timezone.now()
        )

    def test_form_validation_duplicate_cpf(self):
        # Test that PacienteForm rejects a duplicate CPF
        form_data = {
            'nome': "Outro Paciente",
            'cpf': "12345678909",  # Same CPF, unformatted (which is formatted by clean_cpf)
            'data_nascimento': "1995-05-05",
            'celular': "(11) 88888-8888"
        }
        form = PacienteForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('cpf', form.errors)

    def test_agenda_agendar_novo_view_duplicate_cpf(self):
        # Log in
        self.client.login(username='testuser', password='password')
        
        # Post request to agenda_agendar_novo with a duplicate CPF
        url = reverse('agenda_agendar_novo', kwargs={'pk': self.lista_espera.pk})
        
        post_data = {
            'nome': "Outro Paciente",
            'cpf': "123.456.789-09",  # Duplicate CPF
            'data_nascimento': "1995-05-05",
            'celular': "(11) 88888-8888",
            'data_hora': "2026-05-25T10:00",
            'professor': '',
            'box': '',
            'dupla': ''
        }
        
        response = self.client.post(url, data=post_data)
        
        # The form should fail validation (is_valid = False), so we remain on the same page with form errors
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Paciente com este Cpf")
        
        # Verify that no new patient was created (we only have the one from setUp)
        self.assertEqual(Paciente.objects.count(), 1)
