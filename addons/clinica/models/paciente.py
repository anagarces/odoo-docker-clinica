from odoo import models, fields

class ClinicaPaciente(models.Model):
    _name = 'clinica.paciente'
    _description = 'Registro de Pacientes de la Clínica'

    name = fields.Char(string='Nombre Completo', required=True)
    fecha_nacimiento = fields.Date(string='Fecha de Nacimiento')
    telefono = fields.Char(string='Teléfono')
    email = fields.Char(string='Correo electrónico')
    es_alergico = fields.Boolean(string='¿Es alérgico?', default = False)
    detalles_alergias = fields.Text(string='Detalles de Alergias')
    tipo_sangre = fields.Selection(
        [
            ('a_plus', 'A+'),
            ('a_minus', 'A-'),
            ('b_plus', 'B+'),
            ('b_minus', 'B-'),
            ('ab_plus', 'AB+'),
            ('ab_minus', 'AB-'),
            ('o_plus', 'O+'),
            ('o_minus', 'O-'),
        ],
        string='Tipo de Sangre'
    )