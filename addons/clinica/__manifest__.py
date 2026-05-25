{
    'name': "Gestión de Clínica",
    'version': '1.0',
    'summary': 'Modulo para gestionar pacientes',
    'category': 'Healthcare',
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        'data/sequence.xml',
        'views/medico_view.xml',
        'views/paciente_view.xml',
        'views/cita_view.xml',
        'views/menu.xml',
    ],
    'demo': [
        'demo/paciente_demo.xml',
    ],
    'installable': True,
    'application': True,
}