# clinica_slot.py
from odoo import models, fields


class ClinicaSlot(models.Model):
    _name = 'clinica.slot'
    _description = 'Slot de Disponibilidad Médica'
    _order = 'fecha_inicio asc'

    medico_id = fields.Many2one(
        'clinica.medico',
        string='Médico',
        required=True,
        ondelete='cascade'
    )
    fecha_inicio = fields.Datetime(string='Inicio', required=True)
    fecha_fin = fields.Datetime(string='Fin', required=True)

    estado = fields.Selection([
        ('libre', 'Libre'),
        ('ocupado', 'Ocupado'),
        ('bloqueado', 'Bloqueado'),  # excepción manual
    ], string='Estado', default='libre', required=True)

    cita_id = fields.Many2one(
        'clinica.cita',
        string='Cita Asignada',
        readonly=True
    )

    name = fields.Char(
        string='Descripción',
        compute='_compute_name',
        store=True
    )

    @api.depends('fecha_inicio', 'fecha_fin', 'medico_id')
    def _compute_name(self):
        for slot in self:
            if slot.fecha_inicio and slot.medico_id:
                slot.name = (
                    f"{slot.medico_id.name} — "
                    f"{slot.fecha_inicio.strftime('%d/%m/%Y %H:%M')}"
                )