# clinica_medico_horario.py
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class ClinicaMedicoHorario(models.Model):
    _name = 'clinica.medico.horario'
    _description = 'Horario Semanal del Médico'

    medico_id = fields.Many2one(
        'clinica.medico',
        string='Médico',
        required=True,
        ondelete='cascade' 
    )
    dia_semana = fields.Selection([
        ('0', 'Lunes'),
        ('1', 'Martes'),
        ('2', 'Miércoles'),
        ('3', 'Jueves'),
        ('4', 'Viernes'),
        ('5', 'Sábado'),
        ('6', 'Domingo'),
    ], string='Día de la Semana', required=True)

    hora_inicio = fields.Float(string='Hora de Inicio', required=True)
    hora_fin = fields.Float(string='Hora de Fin', required=True)

    @api.constrains('hora_inicio', 'hora_fin')
    def _check_horas(self):
        for horario in self:
            if horario.hora_inicio >= horario.hora_fin:
                raise ValidationError(
                    "La hora de inicio debe ser anterior a la hora de fin."
                )
            if horario.hora_inicio < 0 or horario.hora_fin > 24:
                raise ValidationError(
                    "Las horas deben estar entre 0 y 24."
                )