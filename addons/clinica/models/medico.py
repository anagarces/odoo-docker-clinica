from odoo import models, fields

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