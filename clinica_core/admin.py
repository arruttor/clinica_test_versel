from django.contrib import admin
from .models import Clinica, Academico, Paciente, Marcacao, ListaEspera

class BaseAdmin(admin.ModelAdmin):
    readonly_fields = ('user_create', 'user_update', 'user_delete', 'date_create', 'date_alter', 'date_delete')

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.user_create = request.user
        else:
            obj.user_update = request.user
        super().save_model(request, obj, form, change)

@admin.register(Clinica)
class ClinicaAdmin(BaseAdmin):
    pass

@admin.register(Academico)
class AcademicoAdmin(BaseAdmin):
    pass

@admin.register(Paciente)
class PacienteAdmin(BaseAdmin):
    pass

@admin.register(Marcacao)
class MarcacaoAdmin(BaseAdmin):
    pass

@admin.register(ListaEspera)
class ListaEsperaAdmin(BaseAdmin):
    pass
