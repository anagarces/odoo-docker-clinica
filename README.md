#  Módulo Clínica — Odoo 17

Módulo de gestión clínica desarrollado sobre **Odoo 17 Community** como proyecto de portafolio. Implementa un sistema completo de agenda médica con generación automática de slots, gestión de ausencias y control de citas para clínicas privadas.

---

##  Descripción

Este módulo permite gestionar de forma integral el flujo de una clínica privada pequeña: desde la configuración del horario semanal de cada médico hasta el agendamiento de citas por parte de la recepcionista, evitando solapamientos y respetando la disponibilidad real de cada profesional.

---

## ⚙️ Requisitos

| Requisito | Versión |
|---|---|
| Odoo | 17.0 |
| Python | 3.10+ |
| PostgreSQL | 15 |
| Docker | 24+ |

### Dependencias Python
- `pytz`

### Dependencias Odoo
- `base`

---

##  Instalación

### Con Docker (recomendado)

1. Clona el repositorio dentro de tu carpeta de addons:

```bash
git clone <url-repositorio> ./extra-addons/clinica
```

2. Asegúrate de que tu `docker-compose.yml` monta la carpeta correctamente:

```yaml
volumes:
  - ./extra-addons:/mnt/extra-addons
```

3. Instala el módulo:

```bash
docker exec <contenedor_odoo> odoo -i clinica -d <nombre_bd> \
  --db_host db --db_port 5432 \
  --db_user odoo --db_password odoo \
  --stop-after-init
```

4. Reinicia el contenedor:

```bash
docker restart <contenedor_odoo>
```

### Actualizar tras cambios

```bash
docker exec <contenedor_odoo> odoo -u clinica -d <nombre_bd> \
  --db_host db --db_port 5432 \
  --db_user odoo --db_password odoo \
  --stop-after-init
```

---

## Estructura del módulo

```
clinica/
├── __init__.py
├── __manifest__.py
├── models/
│   ├── __init__.py
│   ├── clinica_paciente.py       # Registro de pacientes
│   ├── clinica_medico.py         # Médicos, zona horaria, generación de slots
│   ├── clinica_medico_horario.py # Franjas horarias semanales
│   ├── clinica_slot.py           # Slots de disponibilidad generados
│   ├── clinica_ausencia.py       # Ausencias médicas con bloqueo de slots
│   └── clinica_cita.py           # Citas médicas con máquina de estados
├── data/
│   ├── sequence.xml              # Secuencia para código de cita
│   └── cron.xml                  # Cron semanal de generación de slots
├── security/
│   └── ir.model.access.csv       # Permisos de acceso a modelos
├── views/
│   ├── medico_view.xml
│   ├── medico_horario_view.xml
│   ├── slot_view.xml
│   ├── ausencia_view.xml
│   ├── paciente_view.xml
│   ├── cita_view.xml
│   └── menu.xml
└── demo/
    └── paciente_demo.xml
```

---

##  Modelos

### `clinica.paciente`
Registro de pacientes con datos personales e información médica básica.

| Campo | Tipo | Descripción |
|---|---|---|
| `name` | Char | Nombre completo |
| `fecha_nacimiento` | Date | Fecha de nacimiento |
| `tipo_sangre` | Selection | Grupo sanguíneo |
| `es_alergico` | Boolean | Indicador de alergias |
| `detalles_alergias` | Text | Descripción de alergias |
| `medico_id` | Many2one | Médico de cabecera |
| `cita_ids` | One2many | Historial de citas |

---

### `clinica.medico`
Perfil del médico con configuración de disponibilidad.

| Campo | Tipo | Descripción |
|---|---|---|
| `name` | Char | Nombre del médico |
| `especialidad` | Selection | Especialidad médica |
| `num_colegiado` | Char | Número de colegiado |
| `duracion_cita` | Integer | Duración en minutos por cita |
| `tz` | Selection | Zona horaria (pytz) |
| `horario_ids` | One2many | Franjas horarias semanales |
| `slot_ids` | One2many | Slots generados |
| `ausencia_ids` | One2many | Ausencias registradas |

---

### `clinica.medico.horario`
Franjas horarias semanales abstractas del médico.

| Campo | Tipo | Descripción |
|---|---|---|
| `medico_id` | Many2one | Médico propietario |
| `dia_semana` | Selection | Día (0=Lunes … 6=Domingo) |
| `hora_inicio` | Float | Hora de inicio (9.5 = 09:30) |
| `hora_fin` | Float | Hora de fin |

---

### `clinica.slot`
Hueco de disponibilidad concreto generado a partir del horario semanal.

| Campo | Tipo | Descripción |
|---|---|---|
| `medico_id` | Many2one | Médico asignado |
| `fecha_inicio` | Datetime | Inicio del slot (UTC) |
| `fecha_fin` | Datetime | Fin del slot (UTC) |
| `estado` | Selection | `libre / ocupado / bloqueado` |
| `cita_id` | Many2one | Cita asignada (si ocupado) |
| `ausencia_id` | Many2one | Ausencia que lo bloquea |

---

### `clinica.ausencia`
Ausencia de un médico en un rango de fechas.

| Campo | Tipo | Descripción |
|---|---|---|
| `medico_id` | Many2one | Médico ausente |
| `fecha_inicio` | Date | Inicio de la ausencia |
| `fecha_fin` | Date | Fin de la ausencia |
| `motivo` | Selection | Vacaciones / Enfermedad / Congreso / Permiso / Otro |
| `estado` | Selection | `pendiente / confirmada / cancelada` |
| `slot_ids` | One2many | Slots bloqueados por esta ausencia |

> Al **confirmar** una ausencia se bloquean automáticamente todos los slots libres del médico en ese rango. Al **cancelar** se liberan.

---

### `clinica.cita`
Cita médica asignada a un slot disponible.

| Campo | Tipo | Descripción |
|---|---|---|
| `name` | Char | Código autogenerado (ej. CITA/2026/0001) |
| `paciente_id` | Many2one | Paciente |
| `medico_id` | Many2one | Médico |
| `slot_id` | Many2one | Slot elegido (filtrado: libre + mismo médico) |
| `fecha_inicio` | Datetime | Calculado del slot (readonly) |
| `fecha_fin` | Datetime | Calculado del slot (readonly) |
| `motivo` | Text | Motivo de la consulta |
| `estado` | Selection | `borrador / concluida / cancelada` |

---

## Flujo de uso

```
1. Administrador crea el médico
   └─ Define especialidad, duración de cita y zona horaria

2. Administrador configura horario semanal
   └─ Ejemplo: Lunes 09:00-13:00, Miércoles 09:00-13:00

3. Administrador genera slots
   └─ Botón "Generar Slots (4 semanas)" en la ficha del médico
   └─ El cron semanal mantiene siempre un horizonte de 4 semanas

4. Recepcionista registra ausencia (si aplica)
   └─ Confirma ausencia → slots del rango pasan a "Bloqueado"

5. Recepcionista crea la cita
   └─ Elige paciente y médico
   └─ El campo Horario Disponible muestra solo slots libres
   └─ Al guardar el slot pasa a "Ocupado"

6. Gestión posterior
   └─ "Marcar como Asistida" → estado Asistió
   └─ "Cancelar Cita" → estado Cancelada + slot vuelve a Libre
```

---

## Menú y accesos

```
Clínica
├── Citas
│   └── Todas las Citas
├── Planificación
│   ├── Slots Disponibles
│   └── Ausencias de Médicos
└── Configuración
    ├── Médicos
    └── Pacientes
```

---

## 🔧 Decisiones técnicas destacadas

**Zona horaria en el médico, no en el usuario**
Los slots se generan usando la zona horaria definida en la ficha del médico (`tz`), no la del usuario que pulsa el botón. Esto garantiza consistencia independientemente de quién ejecute la acción.

**Slots como entidad propia**
En lugar de validar solapamientos con búsquedas en `clinica.cita`, cada hueco horario es un registro independiente con estado propio. Esto simplifica la lógica de validación y hace el sistema más robusto.

**Generación idempotente**
El método `generar_slots_medico` verifica existencia antes de crear cada slot. Puede ejecutarse múltiples veces sin generar duplicados.

**Máquina de estados en citas**
Las transiciones de estado se controlan mediante métodos explícitos (`action_cancelar`, `action_concluir`) con validaciones, evitando transiciones inválidas como concluir una cita cancelada.

**Float para horas abstractas**
El horario semanal almacena horas como `Float` (`9.5 = 09:30`), siguiendo la convención de Odoo RRHH. La conversión a `Datetime` concreto ocurre solo en el momento de generar slots.

---

##  Estado del proyecto

| Funcionalidad 
|---|---|
| Gestión de pacientes 
| Gestión de médicos y horarios 
| Generación automática de slots 
| Cron semanal 
| Gestión de ausencias
| Agendamiento de citas con slots
| Máquina de estados en citas 
| Seguridad por grupos de usuario
| Datos demo actualizados 

---

## 👩‍💻 Desarrollado con

- [Odoo 17 Community](https://www.odoo.com)
- Python 3.10
- PostgreSQL 15
- Docker
- Visual Studio Code
