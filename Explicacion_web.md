## 1. Objetivo de la aplicación

La aplicación sirve para **controlar que los operarios mantienen sus certificaciones activas**, cumpliendo esta regla:

* Para **cada certificación de cada operario**:

  * Hay periodos consecutivos de **180 días laborables**.
  * En cada periodo deben realizarse **29 inspecciones de producto** asociadas a esa certificación.
  * Cuando se registra la inspección número 29:

    * Ese periodo se marca como **completado**.
    * Se abre automáticamente un **nuevo periodo**, que empieza el día laborable siguiente y vuelve a durar 180 días laborables con el mismo objetivo de 29 inspecciones.
  * Si llega el final del periodo y no se ha alcanzado el número 29:

    * La certificación del operario **caduca**.

El sistema no hace informes sofisticados de momento. El foco del MVP es:

* Dar de alta datos básicos (operarios, certificaciones, auditorías, auditores).
* Registrar inspecciones.
* Mantener correctamente el estado de:

  * Certificaciones de operarios (activa/caducada)
  * Periodos de validación (vigente/completado)

---

## 2. Roles y usuarios

En el MVP, simplificamos:

* **Usuario del sistema**:

  * Hace login con usuario y contraseña.
  * Puede dar de alta y editar:

    * Operarios
    * Auditores
    * Certificaciones
    * Auditorías de producto
    * Asignaciones de certificaciones a operarios
    * Inspecciones de producto
  * No hay gestión avanzada de roles ni permisos.

* **Auditor**:

  * Es una persona que realiza inspecciones.
  * No hace login necesariamente.
  * Se elige desde un desplegable cuando se registra una inspección.

* **Operario**:

  * Nunca hace login.
  * Solo existe como ficha sobre la que se controla el cumplimiento de certificaciones.

---

## 3. Datos que maneja la aplicación

### 3.1. Operarios

Información mínima:

* Nombre y apellidos
* Código interno (opcional)
* Estado: activo / inactivo

Operaciones:

* Crear, editar, desactivar operarios.
* Ver lista de operarios.
* Ver detalle de un operario (sus certificaciones, periodos, inspecciones).

---

### 3.2. Certificaciones

Son tipos genéricos, por ejemplo:

* Certificación de laboratorio
* Certificación de taller

Datos:

* Nombre
* Descripción
* Estado: activa / inactiva (para el catálogo, no para el operario)

Operaciones:

* Crear y editar certificaciones.
* Desactivar una certificación si ya no se usa (pero conservando histórico).

---

### 3.3. Auditorías de producto

Son tipos de auditoría de producto, siempre ligados a una certificación.
Ejemplos:

* Dientes (para certificación de laboratorio)
* Coronas (para certificación de laboratorio)

Datos:

* Certificación a la que pertenecen
* Nombre
* Descripción
* Estado: activa / inactiva

Operaciones:

* Crear y editar tipos de auditoría.
* Desactivar sin borrar histórico.

---

### 3.4. Auditores

Personas que realizan inspecciones.

Datos:

* Nombre
* Apellidos
* Código (opcional)
* Estado: activo / inactivo

Operaciones:

* Crear y editar auditores.
* Seleccionarlos al registrar una inspección.

---

### 3.5. Asignación de certificaciones a operarios

Es la relación “Operario X tiene certificación Y a partir de la fecha Z”.

Datos:

* Operario
* Certificación
* Fecha de asignación
* Estado: activa / no activa
* Fecha de caducidad (si se ha caducado)
* Observaciones

Reglas:

* Cuando se crea una **nueva asignación**:

  * Se crean automáticamente los **datos del primer periodo de validación** (ver siguiente apartado).
* Si una certificación caduca:

  * Se marca como no activa y se establece la fecha de caducidad.
* Si más adelante se quiere reactivar:

  * No se reactiva la misma fila.
  * Se crea una **nueva asignación** con una nueva fecha de asignación.

    * Esto implica un nuevo primer periodo.

---

### 3.6. Periodos de validación de certificación

Para cada asignación de certificación de operario, el sistema mantiene una secuencia de periodos de validación:

* Periodo 1, periodo 2, periodo 3, etc.

Cada periodo contiene:

* Operario + certificación (referencia a la asignación).
* Número de periodo (1, 2, 3…).
* Fecha de inicio del periodo.
* Fecha de fin del periodo.
* Número de días laborables requeridos: 180.
* Inspecciones requeridas: 29.
* Inspecciones realizadas (contador).
* Estado: vigente / completado.
* Fecha de completado (si llega a 29 inspecciones).

Reglas de negocio:

1. Al crear una asignación operador-certificación:

   * Se crea el periodo nº1:

     * Fecha inicio = fecha de asignación.
     * Fecha fin = fecha calculada a 180 días laborables.
     * Inspecciones requeridas = 29.
     * Inspecciones realizadas = 0.
     * Vigente = true.

2. Cuando se registra una inspección:

   * Se busca el **periodo vigente** para esa certificación de ese operario.
   * Se verifica que la fecha de inspección está dentro del intervalo.
   * Se incrementa el contador de “inspecciones realizadas”.
   * Si después de incrementarlo se llega a 29:

     * El periodo se marca como:

       * Completado = true.
       * Vigente = false.
       * Fecha completado = fecha inspección.
     * Se crea un nuevo periodo:

       * Número periodo = anterior + 1.
       * Fecha inicio = día laborable siguiente a la fecha de la inspección nº 29.
       * Fecha fin = 180 días laborables a partir de esa fecha inicio.
       * Inspecciones realizadas = 0.
       * Vigente = true.

3. Caducidad por no cumplimiento:

   * Si se alcanza la fecha fin de un periodo y no está completado:

     * La certificación del operario se marca como **no activa**.
     * Se establece la **fecha de caducidad** en la asignación.
     * No se crean nuevos periodos para esa asignación.

4. Restricciones:

   * En cada momento, para una misma asignación de certificación de operario:

     * Solo puede existir **un periodo vigente**.
   * No puede haber solapamiento de periodos.

---

### 3.7. Inspecciones de producto

Son los eventos concretos que cuentan para las certificaciones.

Datos que se registran:

* Operario + certificación (seleccionando la asignación).
* Periodo de validación al que pertenece.
* Tipo de auditoría de producto (ej.: dientes, coronas).
* Auditor que la ha realizado.
* Fecha de inspección.
* Número de piezas auditadas.
* Resultado de la inspección (campo libre o catálogo simple: OK / NO OK).
* Observaciones.

Reglas:

* La fecha de inspección debe estar dentro del periodo vigente para esa asignación.
* No se pueden borrar inspecciones:

  * Si se quiere “anular” una, el MVP puede simplemente no contemplarlo, o más adelante añadir un estado de “anulada”.
* No se registran inspecciones fuera de periodo ni “extra” una vez completado el periodo (la 29ª inspección provoca el cierre inmediato del periodo actual y la apertura del siguiente).

---

### 3.8. Configuración de reglas

Aunque ahora mismo las reglas están “fijas”, la app debe apoyarse en parámetros que puedan venir de configuración:

* Días laborables requeridos por periodo: 180.
* Inspecciones mínimas por periodo: 29.

En el MVP puedes:

* Tener estos valores en una tabla de configuración con una sola fila activa.
* O tenerlos como constantes en la lógica de negocio.

---

## 4. Funcionalidades mínimas del MVP

Desde el punto de vista de la interfaz y flujos:

1. **Autenticación simple**

   * Formulario de login con usuario y contraseña.
   * No hace falta gestión avanzada de roles.

2. **Gestión de catálogos**

   * CRUD básico de:

     * Operarios
     * Certificaciones
     * Auditorías de producto
     * Auditores

3. **Asignación de certificaciones**

   * Pantalla para:

     * Elegir operario.
     * Elegir certificación.
     * Indicar fecha de asignación.
   * Al guardar:

     * Crear la asignación.
     * Crear el periodo de validación nº 1.

4. **Registro de inspecciones**

   * Pantalla para:

     * Elegir operario.
     * Elegir certificación activa de ese operario.
     * El sistema determina el periodo vigente.
     * Seleccionar tipo de auditoría de producto.
     * Seleccionar auditor.
     * Indicar fecha de inspección.
     * Indicar número de piezas auditadas.
     * Resultado y observaciones.
   * Al guardar:

     * Validar que la fecha está en el periodo vigente.
     * Vincular la inspección con ese periodo.
     * Actualizar el contador de inspecciones del periodo.
     * Si se alcanza la nº 29:

       * Marcar periodo como completado.
       * Crear nuevo periodo (día laborable siguiente, 180 días).
     * Si el periodo ha vencido sin llegar a 29:

       * Marcar certificación de operario como caducada.

5. **Consulta básica del estado**

   * Para cada operario:

     * Lista de certificaciones activas y caducadas.
     * Para cada certificación:

       * Periodo vigente: fechas y número de inspecciones realizadas / requeridas.
       * Historial de periodos anteriores.
       * Lista de inspecciones.

No hace falta en el MVP:

* Informes avanzados.
* Alertas automáticas por correo.
* Paneles gráficos.
