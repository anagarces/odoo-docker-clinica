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
    fecha_inicio = fields.Datetime(
        related='slot_id.fecha_inicio',
        string='Fecha y Hora',
        store=True,
        readonly=True
    )
    fecha_fin = fields.Datetime(
        related='slot_id.fecha_fin',
        string='Fin de Consulta',
        store=True,
        readonly=True
    )
    motivo = fields.Text(string='Motivo de la Consulta')
    estado = fields.Selection([
        ('borrador', 'Programada'),
        ('concluida', 'Asistió'),
        ('cancelada', 'Cancelada')
    ], string='Estado', default='borrador', required=True)

    @api.onchange('medico_id')
    def _onchange_medico_id(self):
        """
    Al cambiar el médico, limpiar el slot seleccionado.
        Evita que quede un slot de un médico anterior
        mientras se muestra la lista del nuevo médico.
        """
        self.slot_id = False

    @api.model
    def create(self, vals):
        if not vals.get('name') or vals.get('name', 'Nuevo') == 'Nuevo':
            vals['name'] = (
                self.env['ir.sequence'].next_by_code('clinica.cita') or '/'
            )
        res = super().create(vals)
        # Marcar el slot como ocupado al crear la cita
        if res.slot_id:
            res.slot_id.write({
                'estado': 'ocupado',
                'cita_id': res.id,
            })
        return res

    def write(self, vals):
        res = super().write(vals)
        if vals.get('estado') == 'cancelada':
            for cita in self:
                if cita.slot_id:
                    cita.slot_id.write({
                        'estado': 'libre',
                        'cita_id': False,
                    })
        return res

    def action_cancelar(self):
        """
    Cancela la cita y libera el slot asociado.
    """
        for cita in self:
            if cita.estado == 'cancelada':
                raise ValidationError(
                    "Esta cita ya está cancelada."
            )
            if cita.estado == 'concluida':
                raise ValidationError(
                    "No se puede cancelar una cita que ya fue atendida."
            )
            cita.estado = 'cancelada'

    def action_concluir(self):
        """
    Marca la cita como concluida.
    """
        for cita in self:
            if cita.estado == 'concluida':
                raise ValidationError(
                    "Esta cita ya fue marcada como asistida."
            )
            if cita.estado == 'cancelada':
                raise ValidationError(
                    "No se puede concluir una cita cancelada."
            )
            cita.estado = 'concluida'

    @api.constrains('slot_id', 'paciente_id', 'estado')
    def _check_disponibilidad_paciente(self):
        """El slot ya protege al médico.
        Solo necesitamos validar que el paciente
        no tenga otra cita solapada con otro médico.
        """
        for cita in self:
            if cita.estado == 'cancelada' or not cita.slot_id:
                continue
            solapadas = self.search([
                ('id', '!=', cita.id),
                ('paciente_id', '=', cita.paciente_id.id),
                ('estado', '!=', 'cancelada'),
                ('slot_id.fecha_inicio', '<', cita.slot_id.fecha_fin),
                ('slot_id.fecha_fin', '>', cita.slot_id.fecha_inicio),
            ])
            if solapadas:
                raise ValidationError(
                    f"El paciente {cita.paciente_id.name} ya tiene una cita "
                    f"en ese horario con otro médico."
                )