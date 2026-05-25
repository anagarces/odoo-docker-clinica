from odoo import models, fields, api
from odoo.exceptions import ValidationError


class ClinicaCita(models.Model):
    _name = 'clinica.cita'
    _description = 'Cita Médica'

    name = fields.Char(string="Código", readonly=True, copy=False)

    paciente_id = fields.Many2one(
        'clinica.paciente',
        string='Paciente',
        required=True
    )

    medico_id = fields.Many2one(
        'clinica.medico',
        string='Médico Especialista',
        required=True
    )

    fecha_cita = fields.Datetime(
        string='Fecha y Hora de la Cita',
        required=True,
        default=fields.Datetime.now
    )

    motivo = fields.Text(string='Motivo de la Consulta')

    estado = fields.Selection([
        ('borrador', 'Programada'),
        ('concluida', 'Asistió'),
        ('cancelada', 'Cancelada')
    ], string='Estado', default='borrador', required=True)

    # Generar código automático
    @api.model
    def create(self, vals):
        if vals.get('name', 'Nuevo') == 'Nuevo':
            vals['name'] = self.env['ir.sequence'].next_by_code('clinica.cita') or '/'
        return super().create(vals)

   
    # VALIDACIÓN DE HORARIO
    @api.constrains('medico_id', 'fecha_cita')
    def _check_disponibilidad_medico(self):
        for cita in self:
            citas_duplicadas = self.search([
                ('id', '!=', cita.id),
                ('medico_id', '=', cita.medico_id.id),
                ('fecha_cita', '=', cita.fecha_cita),
                ('estado', '!=', 'cancelada')
            ])

            if citas_duplicadas:
                raise ValidationError(
                    f"¡Conflicto de Horario! El médico {cita.medico_id.name} "
                    f"ya tiene una cita en {cita.fecha_cita}."
                )