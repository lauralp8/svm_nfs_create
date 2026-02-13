# NetApp ONTAP NFS SVM Creation Script

Script automatizado para la creación y configuración completa de Storage Virtual Machines (SVMs) con protocolo NFS en NetApp ONTAP usando la API REST oficial.

## Descripción

Este script de Python automatiza todo el proceso de creación de una SVM configurada para protocolo NFS (Network File System) en NetApp ONTAP, incluyendo:

- Creación de la SVM con configuración básica
- Modificación de parámetros de espacio lógico
- Configuración de protocolos permitidos (CIFS, NFS, FCP, iSCSI, etc.)
- Creación de servicio NFS (NFSv3, NFSv4.0, NFSv4.1, pNFS)
- Creación de export policies y reglas de acceso
- Creación de interfaces de red NFS (múltiples LIFs)
- Creación de interfaz de management
- Backup automático de event logs del cluster
- Sistema de logging con timestamp para todas las operaciones

## Requisitos

### Software
- Python 3.7 o superior
- NetApp ONTAP 9.6 o superior
- Acceso de red al cluster NetApp
- Credenciales de administrador del cluster

### Dependencias Python
```bash
pip install -r requirements
```

## Estructura del Proyecto

```
svm_nfs_create/
├── create_nfs_svm.py  # Script principal
├── config.yaml        # Archivo de configuración
├── requirements       # Dependencias Python
├── README.md          # Esta documentación
└── logs/              # Logs JSON generados automáticamente
```

## Configuración

Edita el archivo `config.yaml` con los parámetros de tu entorno. El archivo incluye las siguientes secciones:

### cluster
Configuración de conexión al cluster NetApp:
- `host`: Hostname o IP del cluster
- `username`: Usuario administrador
- `password`: Contraseña

### svm
Configuración de la Storage Virtual Machine:
- `name`: Nombre de la SVM a crear
- `ipspace`: IPspace (default: Default)
- `aggregate`: Agregado para volumen raíz
- `language`: Código de idioma (default: c.utf_8)
- `security_style`: Estilo de seguridad (unix/ntfs/mixed)
- `aggr_list`: Lista de agregados permitidos
- `is_space_reporting_logical`: Reporte de espacio lógico (true/false)
- `is_space_enforcement_logical`: Enforcement de espacio lógico (true/false)
- `protocols`: Diccionario de protocolos permitidos (cifs, nfs, fcp, iscsi, etc.)

### Configuración del servicio NFS
- `nfs_v3_enabled`: Habilitar NFSv3 (true/false)
- `nfs_v40_enabled`: Habilitar NFSv4.0 (true/false)
- `nfs_v41_enabled`: Habilitar NFSv4.1 (true/false)
- `nfs_v41_pnfs_enabled`: Habilitar pNFS para NFSv4.1 (true/false)

### Export Policies
- `export_policy_name`: Nombre de la export policy principal
- `export_policy_rules`: Lista de policies con sus reglas de acceso

Cada regla de export policy incluye:
- `policy_name`: Nombre de la policy (default, rhoso, etc.)
- `clientmatch`: Rango de IPs o hostname permitidos
- `rorule`: Regla de lectura (any, sys, krb5, none)
- `rwrule`: Regla de escritura (any, sys, krb5, none)
- `superuser`: Acceso superuser (any, sys, krb5, none) - opcional
- `protocols`: Lista de protocolos (nfs, nfs3, nfs4)
- `ruleindex`: Índice de la regla (orden de evaluación) - opcional

### network_interfaces
Lista de interfaces de red NFS. Cada interfaz puede incluir:
- `name`: Nombre de la interfaz lógica
- `role`: Rol de la interfaz (data)
- `data_protocol`: Protocolo de datos (nfs)
- `home_node`: Nodo home
- `home_port`: Puerto home (ejemplo: e0c, e0d)
- `address`: Dirección IP
- `netmask`: Máscara de red
- `auto_revert`: Auto-revert a home port (true/false)
- `service_policy`: Service policy para LIFs de management (default-management)
- `broadcast_domain`: Broadcast domain
- `status_admin`: Estado administrativo (up/down)

Para ver ejemplos de configuración, consulta el archivo `config.yaml` incluido en el proyecto.

## Funciones del Script

### `config_loader`
Esta función carga la configuración desde un archivo YAML y valida que contenga las secciones necesarias para crear una SVM en NetApp ONTAP. 

- **Parámetros**: 
  - `path` (str): Ruta al archivo de configuración (por defecto `config.yaml`).
- **Retorno**: 
  - Diccionario con la configuración cargada o `None` si ocurre un error.
- **Errores manejados**: 
  - Archivo no encontrado, formato YAML inválido, permisos insuficientes, entre otros.

### `save_to_log`
Guarda datos en un archivo JSON dentro de la carpeta `logs/` con un timestamp automático.

- **Parámetros**: 
  - `operation_name` (str): Nombre de la operación (ejemplo: `create_svm`).
  - `data` (dict): Datos a guardar.
- **Retorno**: 
  - Ruta del archivo creado.
- **Características**: 
  - Crea automáticamente la carpeta `logs/` si no existe.
  - Genera nombres de archivo con el formato `operation_YYYYMMDD_HHMMSS.json`.

## Ejemplo de Configuración

### Reglas de Exportación (`export_policy_rules`)
```yaml
export_policy_rules:
  - policy_name: default
    rules:
      - clientmatch: 0.0.0.0/0
        rorule: any
        rwrule: any
        superuser: any
        protocols:
          - nfs
          - nfs3
          - nfs4
        ruleindex: 1
  - policy_name: rhoso
    rules:
      - clientmatch: 192.168.25.0/24
        rorule: sys
        rwrule: any
        protocols:
          - nfs
          - nfs3
          - nfs4
```

### Interfaces de Red (`network_interfaces`)
```yaml
network_interfaces:
  - name: lif1
    role: data
    data_protocol: nfs
    home_node: cluster1-01
    home_port: e0c
    address: 192.168.0.141
    netmask: 255.255.255.0
    auto_revert: false
  - name: UFCREATEYA
    service_policy: default-management
    address: 192.168.0.142
    netmask: 255.255.255.0
    home_node: cluster1-01
    home_port: e0d
    broadcast_domain: Default
    status_admin: up
    auto_revert: false
```

## Sistema de Logging

### Formato de Logs
Los logs se generan en formato JSON con la siguiente estructura:

- **create_svm_YYYYMMDD_HHMMSS.json**:
  ```json
  {
    "uuid": "<UUID de la SVM>",
    "name": "<Nombre de la SVM>",
    "state": "<Estado>",
    "ipspace": "<IPSpace>",
    "aggregates": ["<Agregado1>", "<Agregado2>"]
  }
  ```

- **modify_svm_YYYYMMDD_HHMMSS.json**:
  ```json
  {
    "aggregates": ["<Agregado1>", "<Agregado2>"]
  }
  ```

## Uso

### Ejecución Básica
```bash
python create_nfs_svm.py
```

### Flujo de Ejecución

1. **Carga de configuración** - Lee y valida `config.yaml`
2. **Conexión al cluster** - Establece conexión y verifica credenciales
3. **Creación de SVM** - Crea la SVM con parámetros básicos → Guarda log
4. **Modificación de SVM** - Configura agregados y espacio lógico → Guarda log
5. **Protocolos** - Configura protocolos permitidos/no permitidos → Guarda log
6. **Servicio NFS** - Crea y configura servicio NFS con versiones → Guarda log
7. **Export Policies** - Crea export policies → Guarda log
8. **Export Policy Rules** - Crea reglas de acceso para cada policy → Guarda log
9. **Interfaces de Red** - Crea todas las interfaces NFS y management → Guarda log
10. **Event Logs Backup** - Obtiene logs de eventos del cluster → Guarda log
11. **Finalización** - Todos los logs disponibles en directorio `logs/`


## API REST de NetApp

Este script utiliza la **API REST oficial de NetApp ONTAP**:

### Endpoints POST (Creación)
- **POST** `/api/svm/svms` - Creación de SVM
- **POST** `/api/protocols/nfs/services` - Creación servicio NFS
- **POST** `/api/protocols/nfs/export-policies` - Creación export policies
- **POST** `/api/protocols/nfs/export-policies/{policy.id}/rules` - Creación export rules
- **POST** `/api/network/ip/interfaces` - Creación interfaces de red

### Endpoints PATCH (Modificación)
- **PATCH** `/api/svm/svms/{uuid}` - Modificación de SVM y protocolos

### Endpoints GET (Consulta)
- **GET** `/api/svm/svms` - Consulta de SVMs
- **GET** `/api/protocols/nfs/services` - Consulta servicio NFS
- **GET** `/api/protocols/nfs/export-policies` - Consulta export policies
- **GET** `/api/protocols/nfs/export-policies/{policy.id}/rules` - Consulta export rules
- **GET** `/api/network/ip/interfaces` - Consulta de interfaces IP
- **GET** `/api/support/ems/events` - Consulta de event logs

**Documentación oficial**: [NetApp ONTAP REST API](https://library.netapp.com/ecmdocs/ECMLP3351667/html/)


## Registro de Funciones

### Funciones de Configuración y Utilidades

#### config_loader(path="config.yaml")
Carga y valida el archivo de configuración YAML.
- **Entrada**: Ruta al archivo config.yaml
- **Salida**: Diccionario con configuración o None si falla
- **Validaciones**: Verifica estructura y secciones obligatorias (cluster, svm)

#### save_to_log(operation_name, data)
Guarda datos en archivo JSON con timestamp en carpeta logs/.
- **Entrada**: Nombre de operación y diccionario de datos
- **Salida**: Ruta del archivo creado
- **Formato**: `logs/operacion_YYYYMMDD_HHMMSS.json`

#### cluster_connection(cluster_config)
Establece y verifica conexión con el cluster NetApp ONTAP.
- **Entrada**: Diccionario con host, username, password
- **Salida**: True si conexión exitosa, False si falla
- **Validaciones**: Prueba acceso con consulta al cluster

### Funciones de Gestión de SVM

#### create_svm(svm_config)
Crea una Storage Virtual Machine con parámetros básicos.
- **Entrada**: Configuración de SVM desde config.yaml
- **Salida**: True si se creó, False si error
- **POST**: `/api/svm/svms`
- **Log**: `create_svm_YYYYMMDD_HHMMSS.json`

#### modify_svm(svm_config)
Modifica parámetros de espacio lógico y lista de agregados.
- **Entrada**: Configuración de SVM con aggr_list y parámetros de espacio
- **Salida**: True si modificación exitosa, False si error
- **PATCH**: `/api/svm/svms/{uuid}`
- **Log**: `modify_svm_YYYYMMDD_HHMMSS.json`

### Funciones de Configuración NFS

#### configure_protocols(svm_config)
Configura protocolos permitidos y no permitidos en la SVM.
- **Entrada**: Configuración de SVM con diccionario de protocolos
- **Salida**: True si configuración exitosa, False si error
- **PATCH**: `/api/svm/svms/{uuid}`
- **Log**: `configure_protocols_YYYYMMDD_HHMMSS.json`

#### nfs_create(svm_config)
Crea y habilita el servicio NFS en la SVM con versiones específicas.
- **Entrada**: Configuración de SVM con versiones NFS (v3, v4.0, v4.1, pNFS)
- **Salida**: True si se creó, False si error
- **POST**: `/api/protocols/nfs/services`
- **Log**: `nfs_create_YYYYMMDD_HHMMSS.json`

#### export_policies(svm_config)
Crea export policies para control de acceso NFS.
- **Entrada**: Configuración de SVM con nombre de policy
- **Salida**: True si se creó, False si error
- **POST**: `/api/protocols/nfs/export-policies`
- **Log**: `export_policies_YYYYMMDD_HHMMSS.json`

#### export_policy_rules_create(svm_config)
Crea reglas de acceso para las export policies configuradas.
- **Entrada**: Configuración con lista de policies y sus reglas
- **Salida**: True si todas se crearon, False si error
- **POST**: `/api/protocols/nfs/export-policies/{policy.id}/rules`
- **Log**: `export_policy_rules_YYYYMMDD_HHMMSS.json`
- **Características**: Soporta múltiples policies con reglas diferentes

### Funciones de Interfaces de Red

#### network_interfaces_create(svm_config)
Crea interfaces de red IP (LIFs) para datos NFS y management.
- **Entrada**: Configuración de SVM con lista de interfaces
- **Salida**: True si todas se crearon, False si error
- **POST**: `/api/network/ip/interfaces`
- **Log**: `network_interfaces_YYYYMMDD_HHMMSS.json`
- **Tipos soportados**: LIFs de datos NFS y LIFs de management

### Funciones de Monitoreo

#### get_event_logs(max_records=100)
Obtiene y respalda los logs de eventos del cluster.
- **Entrada**: Número máximo de registros (default: 100)
- **Salida**: True si se obtuvieron, False si error
- **GET**: `/api/support/ems/events`
- **Log**: `event_logs_YYYYMMDD_HHMMSS.json`

## Registro de Errores

### Errores de Configuración

#### ERR-001: Archivo de configuración no encontrado
```
[ERROR] File not found: config.yaml
```
**Causa**: El archivo config.yaml no existe en el directorio actual  
**Solución**: Verificar que config.yaml existe en la misma carpeta que el script

#### ERR-002: YAML inválido
```
[ERROR] Invalid YAML format in 'config.yaml'
```
**Causa**: Sintaxis YAML incorrecta (indentación, formato)  
**Solución**: Validar sintaxis YAML, verificar espacios e indentación

#### ERR-003: Configuración incompleta
```
[ERROR] Incomplete configuration: missing 'cluster' section
[ERROR] Incomplete configuration: missing 'svm' section
```
**Causa**: Faltan secciones obligatorias en config.yaml  
**Solución**: Asegurar que config.yaml contenga secciones 'cluster' y 'svm'

#### ERR-004: Campos obligatorios faltantes
```
[ERROR] Missing required fields in cluster config: host, username
```
**Causa**: Faltan campos obligatorios en la configuración del cluster  
**Solución**: Completar todos los campos requeridos (host, username, password)

### Errores de Conexión

#### ERR-101: Error de autenticación
```
[ERROR] HTTP status: 401
[ERROR] Authentication failed
[ERROR] Invalid username or password
```
**Causa**: Credenciales incorrectas  
**Solución**: Verificar username y password en config.yaml

#### ERR-102: Acceso denegado
```
[ERROR] HTTP status: 403
[ERROR] Forbidden - User lacks required permissions
```
**Causa**: Usuario sin permisos de administrador  
**Solución**: Usar cuenta con rol admin o vsadmin

#### ERR-103: Host no alcanzable
```
[ERROR] Cannot reach host 'cluster1.demo.netapp.com'
```
**Causa**: Problemas de red o hostname incorrecto  
**Solución**: Verificar conectividad de red y hostname/IP del cluster

#### ERR-104: Timeout de conexión
```
[ERROR] Connection timeout to 'cluster1.demo.netapp.com'
```
**Causa**: Cluster no responde  
**Solución**: Verificar que el cluster esté encendido y accesible

### Errores de Creación de SVM

#### ERR-201: SVM ya existe
```
[ERROR] SVM 'svm_name' already exists on the cluster
```
**Causa**: Ya existe una SVM con ese nombre  
**Solución**: Cambiar nombre en config.yaml o eliminar SVM existente

#### ERR-202: Agregado no existe
```
[ERROR] Aggregate 'aggr1' doesn't exist (check aggregate name)
```
**Causa**: Nombre de agregado incorrecto o no existe  
**Solución**: Ejecutar `storage aggregate show` para ver agregados disponibles

#### ERR-203: IPspace inválido
```
[ERROR] Bad request - Invalid ipspace name
```
**Causa**: IPspace especificado no existe  
**Solución**: Verificar IPspaces con `network ipspace show`

#### ERR-204: Código de idioma inválido
```
[ERROR] Bad request - Invalid language code
```
**Causa**: Código de idioma no soportado  
**Solución**: Usar códigos válidos: c.utf_8, en_us.utf_8, etc.

### Errores de Servicio NFS

#### ERR-301: Servicio NFS ya existe
```
[ERROR] NFS service may already exist on this SVM
```
**Causa**: La SVM ya tiene servicio NFS configurado  
**Solución**: Verificar con `vserver nfs show -vserver <name>`

#### ERR-302: Parámetros NFS inválidos
```
[ERROR] Bad request - Invalid parameters
```
**Causa**: Combinación inválida de versiones NFS o parámetros  
**Solución**: Verificar que las versiones NFS sean compatibles

### Errores de Export Policies

#### ERR-401: Export policy no encontrada
```
[ERROR] Export policy not found - Create policy first
```
**Causa**: Intentar crear reglas en una policy que no existe  
**Solución**: Crear la export policy antes de agregar reglas

#### ERR-402: Export rule ya existe
```
[ERROR] Export rule may already exist at that index
```
**Causa**: Ya existe una regla con ese índice en la policy  
**Solución**: Usar un ruleindex diferente o eliminar la regla existente

#### ERR-403: Parámetros de export rule inválidos
```
[ERROR] Bad request - Invalid parameters
[ERROR] Check: policy exists, valid protocols, valid auth methods
```
**Causa**: Parámetros inválidos en las reglas (clientmatch, rorule, rwrule)  
**Solución**: 
- Verificar sintaxis de clientmatch (IP/subnet correcta: 192.168.1.0/24)
- Usar auth methods válidos: any, sys, krb5, krb5i, krb5p, none
- Verificar protocolos válidos: nfs, nfs3, nfs4

### Errores de Interfaces de Red

#### ERR-501: Interfaz ya existe
```
[ERROR] Network interface may already exist
```
**Causa**: Ya existe una LIF con ese nombre  
**Solución**: Cambiar nombre de LIF en config.yaml

#### ERR-502: Dirección IP inválida
```
[ERROR] Bad request - Invalid IP
```
**Causa**: Dirección IP inválida o ya en uso  
**Solución**: Verificar que la IP sea válida y no esté en uso

#### ERR-503: Puerto no existe
```
[ERROR] Resource not found - Check node/port/broadcast-domain names
```
**Causa**: Nodo, puerto o broadcast domain no existen  
**Solución**: 
- Verificar nodos: `cluster show`
- Verificar puertos: `network port show -node <node>`
- Verificar broadcast domain: `network port broadcast-domain show`

#### ERR-504: Parámetros de red inválidos
```
[ERROR] Bad request - Invalid parameters
[ERROR] Check: valid IP, node exists, port exists, broadcast domain
```
**Causa**: Combinación inválida de parámetros de red  
**Solución**: Verificar que todos los recursos de red existan y sean compatibles

#### ERR-505: Service policy no existe
```
[ERROR] Service policy 'invalid-policy' not found
```
**Causa**: Service policy especificado no existe  
**Solución**: Usar policies predefinidos: default-management, default-data-files, default-data-blocks

### Errores de Protocolos

#### ERR-601: Protocolo no soportado
```
[ERROR] Bad request - Invalid protocol configuration
```
**Causa**: Nombre de protocolo inválido  
**Solución**: Usar protocolos válidos: nfs, cifs, fcp, iscsi, nvme, s3, ndmp

#### ERR-602: Conflicto de protocolos
```
[ERROR] Cannot enable both NFS and CIFS without proper configuration
```
**Causa**: Configuración de protocolos incompatible  
**Solución**: Configurar security-style adecuado para multiprotocolo

### Errores de Event Logs

#### ERR-701: No se pueden obtener event logs
```
[WARNING] Event logs backup failed (non-critical)
```
**Causa**: Error al consultar API de eventos  
**Solución**: No crítico, verificar permisos de lectura de eventos

### Códigos de Estado HTTP Comunes

- **400 Bad Request**: Parámetros inválidos en la solicitud
- **401 Unauthorized**: Credenciales incorrectas
- **403 Forbidden**: Sin permisos suficientes
- **404 Not Found**: Recurso no existe
- **409 Conflict**: Recurso ya existe o conflicto de estado
- **500 Internal Server Error**: Error interno del servidor ONTAP

## Seguridad

- **IMPORTANTE**: NO compartas el archivo `config.yaml` con credenciales
- Considera usar variables de entorno para credenciales sensibles
- El script desactiva verificación SSL (`verify=False`) - úsalo solo en entornos de desarrollo/pruebas
- Los logs pueden contener información sensible - protege el directorio `logs/`


## Soporte

Para problemas relacionados con la API de NetApp, consulta:
- [Documentación API REST](https://library.netapp.com/ecmdocs/ECMLP3351667/html/)
- [NetApp Community](https://community.netapp.com/)
- [Python Client Library](https://pypi.org/project/netapp-ontap/)

---
