from odoo import models, fields, api
from odoo.exceptions import ValidationError


class ClinicaAusencia(models.Model):
    _name = 'clinica.ausencia'
    _description = 'Ausencia de Médico'
    _order = 'fecha_inicio desc'

    medico_id = fields.Many2one(
        'clinica.medico',
        string='Médico',
        required=True,
        ondelete='cascade'
    )
    fecha_inicio = fields.Date(string='Fecha de Inicio', required=True)
    fecha_fin = fields.Date(string='Fecha de Fin', required=True)
    motivo = fields.Selection([
        ('vacaciones', 'Vacaciones'),
        ('enfermedad', 'Enfermedad'),
        ('congreso', 'Congreso / Formación'),
        ('permiso', 'Permiso Personal'),
        ('otro', 'Otro'),
    ], string='Motivo', required=True)
    notas = fields.Text(string='Notas')
    estado = fields.Selection([
        ('pendiente', 'Pendiente'),
        ('confirmada', 'Confirmada'),
        ('cancelada', 'Cancelada'),
    ], string='Estado', default='pendiente', required=True)
    slot_ids = fields.One2many(
        'clinica.slot',
        'ausencia_id',
        string='Slots Bloqueados'
    )
    name = fields.Char(
        string='Descripción',
        compute='_compute_name',
        store=True
)

    @api.depends('medico_id', 'motivo', 'fecha_inicio', 'fecha_fin')
    def _compute_name(self):
        for ausencia in self:
            if ausencia.medico_id and ausencia.fecha_inicio:
                motivo_label = dict(
                    self._fields['motivo'].selection
                ).get(ausencia.motivo, '')
                ausencia.name = (
                    f"{ausencia.medico_id.name} — "
                    f"{motivo_label} "
                    f"({ausencia.fecha_inicio} / {ausencia.fecha_fin})"
                )

    @api.constrains('fecha_inicio', 'fecha_fin')
    def _check_fechas(self):
        for ausencia in self:
            if ausencia.fecha_inicio > ausencia.fecha_fin:
                raise ValidationError(
                    "La fecha de inicio debe ser anterior o igual a la fecha de fin."
                )

    def action_confirmar(self):
        """Al confirmar, bloquea todos los slots del médico en ese rango."""
        for ausencia in self:
            slots = self.env['clinica.slot'].search([
                ('medico_id', '=', ausencia.medico_id.id),
                ('fecha_inicio', '>=', f"{ausencia.fecha_inicio} 00:00:00"),
                ('fecha_inicio', '<=', f"{ausencia.fecha_fin} 23:59:59"),
                ('estado', '=', 'libre'),
            ])
            slots.write({
                'estado': 'bloqueado',
                'ausencia_id': ausencia.id,
            })
            ausencia.estado = 'confirmada'

    def action_cancelar(self):
        """Al cancelar, libera los slots que bloqueó esta ausencia."""
        for ausencia in self:
            ausencia.slot_ids.write({
                'estado': 'libre',
                'ausencia_id': False,
            })
            ausencia.estado = 'cancelada'