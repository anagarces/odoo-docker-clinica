from odoo import models, fields, api
from odoo.exceptions import ValidationError

class ClinicaMedico(models.Model):
    _name = 'clinica.medico'
    _description = 'Médico de la Clínica'

    name = fields.Char(string='Nombre del Médico', required=True)
    especialidad = fields.Selection([
        ('general', 'Medicina General'),
        ('pediatria', 'Pediatría'),
        ('cardiologia', 'Cardiología'),
        ('dermatologia', 'Dermatología')
    ], string='Especialidad', default='general', required=True)
    num_colegiado = fields.Char(string='Número de Colegiado', required=True)
    duracion_cita = fields.Integer(
        string='Duración de Cita (minutos)',
        default=40,
        required=True
    )
    horario_ids = fields.One2many(
        'clinica.medico.horario',
        'medico_id',
        string='Horarios de Atención'
    )
    slot_ids = fields.One2many(
        'clinica.slot',
        'medico_id',
        string='Slots Generados'
    )
    ausencia_ids = fields.One2many(
        'clinica.ausencia',
        'medico_id',
        string='Ausencias'
    )


    @api.constrains('duracion_cita')
    def _check_duracion(self):
        for medico in self:
            if medico.duracion_cita <= 0:
                raise ValidationError(
                    "La duración de la cita debe ser mayor a 0 minutos."
                )
            if medico.duracion_cita > 120:
                raise ValidationError(
                    "La duración de la cita no puede superar las 2 horas."
                )

     def action_generar_slots(self):
        """
        Botón manual: genera slots para las próximas 4 semanas
        desde hoy para el médico seleccionado.
        """
        hoy = date.today()
        fecha_fin = hoy + timedelta(weeks=4)

        for medico in self:
            creados = self.env['clinica.slot'].generar_slots_medico(
                medico=medico,
                fecha_inicio=hoy,
                fecha_fin=fecha_fin,
            )
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Slots Generados',
                    'message': f'Se generaron {creados} slots para {medico.name}.',
                    'type': 'success',
                    'sticky': False,
                }
            }

    @api.model
    def _cron_generar_slots(self):
        """
        Llamado por el cron semanal.
        Para cada médico activo, genera slots de la semana +4
        manteniendo siempre un horizonte de 4 semanas disponibles.
        """
        hoy = date.today()
        # El cron genera solo la semana que está a 4 semanas vista
        # para no duplicar trabajo ya hecho
        fecha_inicio = hoy + timedelta(weeks=4)
        fecha_fin = fecha_inicio + timedelta(weeks=1)

        medicos = self.search([])  # todos los médicos
        for medico in medicos:
            if medico.horario_ids:
                self.env['clinica.slot'].generar_slots_medico(
                    medico=medico,
                    fecha_inicio=fecha_inicio,
                    fecha_fin=fecha_fin,
                )