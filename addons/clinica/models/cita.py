# clinica_cita.py
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class ClinicaCita(models.Model):
    _name = 'clinica.cita'
    _description = 'Cita Médica'

    name = fields.Char(
        string="Código",
        readonly=True,
        copy=False,
        default='Nuevo'
    )
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
    slot_id = fields.Many2one(
        'clinica.slot',
        string='Horario Disponible',
        required=True,
        domain="[('medico_id', '=', medico_id), ('estado', '=', 'libre')]"
    )

    # Campos informativos derivados del slot
    fecha_inicio = fields.Datetime(
        related='slot_id.fecha_inicio',
        string='Fecha y Hora',
        store=True,
        readonly=True
    )
    motivo = fields.Text(string='Motivo de la Consulta')
    estado = fields.Selection([
        ('borrador', 'Programada'),
        ('concluida', 'Asistió'),
        ('cancelada', 'Cancelada')
    ], string='Estado', default='borrador', required=True)

    @api.model
    def create(self, vals):
        if not vals.get('name') or vals.get('name', 'Nuevo') == 'Nuevo':
            vals['name'] = (
                self.env['ir.sequence'].next_by_code('clinica.cita') or '/'
            )
        return super().create(vals)

    def write(self, vals):
        res = super().write(vals)
        # Si la cita se cancela, liberar el slot
        if vals.get('estado') == 'cancelada':
            for cita in self:
                if cita.slot_id:
                    cita.slot_id.write({
                        'estado': 'libre',
                        'cita_id': False
                    })
        return res

    @api.constrains('slot_id', 'paciente_id', 'estado')
    def _check_disponibilidad(self):
        for cita in self:
            if cita.estado == 'cancelada':
                continue
            # Verificar que el paciente no tenga otra cita en el mismo slot horario
            if cita.slot_id:
                citas_solapadas = self.search([
                    ('id', '!=', cita.id),
                    ('paciente_id', '=', cita.paciente_id.id),
                    ('estado', '!=', 'cancelada'),
                    ('slot_id.fecha_inicio', '<', cita.slot_id.fecha_fin),
                    ('slot_id.fecha_fin', '>', cita.slot_id.fecha_inicio),
                ])
                if citas_solapadas:
                    raise ValidationError(
                        f"El paciente {cita.paciente_id.name} ya tiene "
                        f"una cita en ese horario con otro médico."
                    )