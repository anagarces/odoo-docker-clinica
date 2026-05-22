from odoo import models, fields

class ClinicaCita(models.Model):
    _name = 'clinica.cita'
    _description = 'Cita Médica'

    # Relación con el Paciente (Muchos registros de citas apuntan a UN Paciente)
    paciente_id = fields.Many2one('clinica.paciente', string='Paciente', required=True)
    
    # Relación con el Médico (Muchos registros de citas apuntan a UN Médico)
    medico_id = fields.Many2one('clinica.medico', string='Médico Especialista', required=True)
    
    # Datos propios de la actividad
    fecha_cita = fields.Datetime(string='Fecha y Hora de la Cita', required=True, default=fields.Datetime.now)
    motivo = fields.Text(string='Motivo de la Consulta')
    
    estado = fields.Selection([
        ('borrador', 'Programada'),
        ('concluida', 'Asistió'),
        ('cancelada', 'Cancelada')
    ], string='Estado', default='borrador', required=True)