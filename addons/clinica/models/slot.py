# clinica_slot.py
from odoo import models, fields, api
from datetime import timedelta, datetime, date
import pytz


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
        for slot in self:
            if slot.fecha_inicio and slot.medico_id:
                #   Convertir UTC a timezone local del médico para mostrar
                tz_name = slot.medico_id.tz or 'Europe/Madrid'
                tz = pytz.timezone(tz_name)
                fecha_local = pytz.utc.localize(
                    slot.fecha_inicio
                ).astimezone(tz)
                slot.name = (
                    f"{slot.medico_id.name} — "
                    f"{fecha_local.strftime('%d/%m/%Y %H:%M')}"
            )

    @api.model
    def generar_slots_medico(self, medico, fecha_inicio, fecha_fin):
        if not medico.horario_ids:
            return 0

        # Obtener timezone del usuario o usar UTC por defecto
        tz_name = self.env.user.tz or 'UTC'
        import pytz
        tz = pytz.timezone(tz_name)

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
            dia_semana = fecha_actual.weekday()

            if dia_semana in horarios_por_dia:
                for hora_inicio, hora_fin in horarios_por_dia[dia_semana]:

                    h_ini = int(hora_inicio)
                    m_ini = int(round((hora_inicio - h_ini) * 60))
                    h_fin = int(hora_fin)
                    m_fin = int(round((hora_fin - h_fin) * 60))

                    # Construir datetime en hora local y convertir a UTC
                    slot_inicio_local = tz.localize(datetime(
                        fecha_actual.year, fecha_actual.month, fecha_actual.day,
                        h_ini, m_ini, 0
                    ))
                    franja_fin_local = tz.localize(datetime(
                        fecha_actual.year, fecha_actual.month, fecha_actual.day,
                        h_fin, m_fin, 0
                    ))

                    # Convertir a UTC para almacenar en Odoo
                    slot_inicio = slot_inicio_local.astimezone(pytz.utc).replace(tzinfo=None)
                    franja_fin = franja_fin_local.astimezone(pytz.utc).replace(tzinfo=None)

                    while slot_inicio + duracion <= franja_fin:
                        slot_fin = slot_inicio + duracion

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

                        slot_inicio = slot_inicio + duracion

            fecha_actual += timedelta(days=1)

        if slots_a_crear:
            self.create(slots_a_crear)

        return len(slots_a_crear)