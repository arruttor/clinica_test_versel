import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "clinica_edu_una.settings")
django.setup()

from clinica_core.models import Clinica, Anamnese, DocumentoPaciente, Evolucao

clinica_fisio = Clinica.objects.filter(nome='FI').first()

if clinica_fisio:
    Anamnese.objects.filter(clinica__isnull=True).update(clinica=clinica_fisio)
    DocumentoPaciente.objects.filter(clinica__isnull=True).update(clinica=clinica_fisio)
    Evolucao.objects.filter(clinica__isnull=True).update(clinica=clinica_fisio)
    print("Dados atualizados para Fisioterapia")
else:
    print("Clínica de Fisioterapia não encontrada. Nenhuma alteração feita.")
