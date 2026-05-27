# clinica_slot.py
from odoo import models, fields, api
from datetime import timedelta, datetime


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
        ('bloqueado', 'Bloqueado'),  
    ], string='Estado', default='libre', required=True)

    cita_id = fields.Many2one(
        'clinica.cita',
        string='Cita Asignada',
        readonly=True
    )

    ausencia_id = fields.Many2one(
        'clinica.ausencia',
        string='Ausencia',
        readonly=True
    )

    name = fields.Char(
        string='Descripción',
        compute='_compute_name',
        store=True
    )

    @api.depends('fecha_inicio', 'medico_id', 'estado')
    def _compute_name(self):
        estado_labels = {'libre': '✅', 'ocupado': '🔴', 'bloqueado': '⛔'}
        for slot in self:
            if slot.fecha_inicio and slot.medico_id:
                icono = estado_labels.get(slot.estado, '')
                slot.name = (
                    f"{icono} {slot.medico_id.name} — "
                    f"{slot.fecha_inicio.strftime('%d/%m/%Y %H:%M')}"
                )

    @api.model
    def generar_slots_medico(self, medico, fecha_inicio, fecha_fin):
        """
        Genera slots para un médico en un rango de fechas.
        No sobreescribe slots ya existentes.
        Retorna el número de slots creados.
        """
        if not medico.horario_ids:
            return 0

        # Obtener días de la semana que trabaja este médico
        # Estructura: {0: [(9.0, 13.0), (16.0, 20.0)], 2: [(9.0, 13.0)], ...}
        horarios_por_dia = {}
        for horario in medico.horario_ids:
            dia = int(horario.dia_semana)
            if dia not in horarios_por_dia:
                horarios_por_dia[dia] = []
            horarios_por_dia[dia].append(
                (horario.hora_inicio, horario.hora_fin)
            )

        duracion = timedelta(minutes=medico.duracion_cita)
        slots_a_crear = []
        fecha_actual = fecha_inicio

        while fecha_actual <= fecha_fin:
            dia_semana = fecha_actual.weekday()  # 0=lunes, 6=domingo

            if dia_semana in horarios_por_dia:
                for hora_inicio, hora_fin in horarios_por_dia[dia_semana]:

                    # Convertir float a horas y minutos
                    # 9.5 → 9 horas, 30 minutos
                    h_ini = int(hora_inicio)
                    m_ini = int(round((hora_inicio - h_ini) * 60))
                    h_fin = int(hora_fin)
                    m_fin = int(round((hora_fin - h_fin) * 60))

                    slot_inicio = fecha_actual.replace(
                        hour=h_ini, minute=m_ini,
                        second=0, microsecond=0
                    )
                    franja_fin = fecha_actual.replace(
                        hour=h_fin, minute=m_fin,
                        second=0, microsecond=0
                    )

                    while slot_inicio + duracion <= franja_fin:
                        slot_fin = slot_inicio + duracion

                        # Verificar que no exista ya este slot
                        existe = self.search_count([
                            ('medico_id', '=', medico.id),
                            ('fecha_inicio', '=', slot_inicio),
                        ])
                        if not existe:
                            slots_a_crear.append({
                                'medico_id': medico.id,
                                'fecha_inicio': slot_inicio,
                                'fecha_fin': slot_fin,
                                'estado': 'libre',
                            })

                        slot_inicio = slot_fin

            fecha_actual += timedelta(days=1)

        if slots_a_crear:
            self.create(slots_a_crear)

        return len(slots_a_crear)