{
    'name': "Gestión de Clínica",
    'version': '1.0',
    'summary': 'Modulo para gestionar pacientes',
    'category': 'Healthcare',
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        'views/paciente_view.xml',
    ],
    'demo': [
        'demo/paciente_demo.xml',
    ],
    'installable': True,
    'application': True,
}