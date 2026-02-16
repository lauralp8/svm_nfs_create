# NetApp ONTAP RBAC User Management Script

Script automatizado para la creación y gestión de usuarios RBAC (Role-Based Access Control) en NetApp ONTAP usando la API REST oficial.

## Descripción

Este script de Python automatiza todo el proceso de gestión de usuarios RBAC en Storage Virtual Machines (SVMs) de NetApp ONTAP, incluyendo:

- Creación de usuarios RBAC con configuración personalizada
- Soporte para múltiples aplicaciones (HTTP, SSH, ONTAPI)
- Configuración de métodos de autenticación (password, domain, nsswitch, cert, publickey)
- Asignación de roles personalizados o predefinidos
- Consulta y visualización de todos los usuarios de la SVM (security login show)
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
pip install -r requirements.txt
```

**Bibliotecas requeridas:**
- `netapp-ontap` - NetApp ONTAP REST API Python Client Library
- `PyYAML` - Parser YAML para archivos de configuración

## Estructura del Proyecto

```
rbac/
├── rbac.py            # Script principal
├── config.yaml        # Archivo de configuración
├── requirements.txt   # Dependencias Python
├── README.md          # Esta documentación
└── logs/              # Logs JSON generados automáticamente
    ├── security_login_show_<svm_name>_YYYYMMDD_HHMMSS.json
    └── event_logs_YYYYMMDD_HHMMSS.json
```

## Configuración

Edita el archivo `config.yaml` con los parámetros de tu entorno. El archivo incluye las siguientes secciones:

### cluster
Configuración de conexión al cluster NetApp:
- `host`: Hostname o IP del cluster
- `username`: Usuario administrador
- `password`: Contraseña

```yaml
cluster:
  host: cluster1.demo.netapp.com
  username: admin
  password: Netapp1!
```

### svm
Configuración de la Storage Virtual Machine donde se crearán los usuarios:
- `name`: Nombre de la SVM existente donde se crearán los usuarios RBAC

```yaml
svm:
  name: svm_1_cluster
```

### rbac_user
Configuración del usuario RBAC a crear:
- `name`: Nombre del usuario a crear
- `applications`: Lista de aplicaciones permitidas (http, ssh, ontapi, console, service-processor)
- `authentication_method`: Método de autenticación (password, domain, nsswitch, cert, publickey, usm, community)
- `role`: Rol RBAC asignado (admin, vsadmin, vsadmin-readonly, vsadmin-backup, vsadmin-snaplock, vsadmin-protocol, o roles personalizados)
- `password`: Contraseña del usuario (requerida para authentication_method: password)

```yaml
rbac_user:
  name: api_user
  applications:
    - http
    - ssh
    - ontapi
  authentication_method: password
  role: vsadmin
  password: SecurePass123!
```

Para ver ejemplos de configuración, consulta el archivo `config.yaml` incluido en el proyecto.

## Sistema de Logging

El script implementa un sistema de logging automático que captura datos REALES de la cabina NetApp después de cada operación:

### Características
- **Timestamp automático**: Formato YYYYMMDD_HHMMSS (ej: 20260211_143025)
- **Formato JSON**: Datos estructurados y fáciles de procesar
- **Datos de cabina**: GET real desde ONTAP, no configuración enviada
- **Directorio logs/**: Se crea automáticamente si no existe

### Logs Generados

1. **security_login_show_<svm_name>_YYYYMMDD_HHMMSS.json**
   - Operación: security_login_show
   - Nombre y UUID de la SVM
   - Total de usuarios en la SVM
   - Lista completa de usuarios con:
     - Nombre de usuario
     - Rol asignado
     - Estado de bloqueo (locked)
     - Comentarios
     - Aplicaciones configuradas
     - Métodos de autenticación por aplicación
   - Usuario recién creado (marcado)

2. **event_logs_YYYYMMDD_HHMMSS.json**
   - Backup de eventos del cluster (últimos 100)
   - Total de eventos recuperados
   - Lista de eventos con:
     - Index
     - Timestamp
     - Nodo
     - Severidad
     - Nombre del evento

## Uso

### Ejecución Básica
```bash
python rbac.py
```

### Flujo de Ejecución

1. **Carga de configuración** - Lee y valida `config.yaml`
2. **Conexión al cluster** - Establece conexión y verifica credenciales
3. **Creación de usuario RBAC** - Crea el usuario con múltiples aplicaciones → Guarda log
4. **Consulta de usuarios** - Obtiene lista completa de usuarios de la SVM (security login show)
5. **Event Logs Backup** - Obtiene logs de eventos del cluster → Guarda log
6. **Finalización** - Todos los logs disponibles en directorio `logs/`

### Ejemplo de Salida
```
======================================================================
  NetApp ONTAP RBAC User Management Script
  Using NetApp ONTAP Python Client Library
======================================================================

[*] Initializing RBAC user creation workflow...
[+] Config.yaml loader: config.yaml
[+] Configuration loaded successfully
[+] Target cluster: cluster1.demo.netapp.com
[+] SVM to create: svm_1_cluster

[*] Establishing connection to cluster: cluster1.demo.netapp.com
[+] Connection successful!
[+] Cluster name: cluster1
[+] ONTAP version: 9.14.1

[+] All pre-checks passed - Ready to create RBAC users

[*] Creating RBAC user account (rbac_user)...
[*] Looking up SVM UUID for: svm_1_cluster
[+] SVM found - UUID: 12345678-1234-1234-1234-123456789abc
[*] Creating user 'api_user' with applications [http, ssh, ontapi] in SVM 'svm_1_cluster'...
[+] User account created successfully!

[*] Retrieving all user accounts from SVM 'svm_1_cluster'...

==================================================================================================================================
  Security Login Show - Vserver: svm_1_cluster
==================================================================================================================================
User/Group           Application     Authentication       Role            Locked     Comment                       
-------------------- --------------- -------------------- --------------- ---------- ------------------------------
api_user             http            password             vsadmin         false                                    
                     ssh             password                                                                       
                     ontapi          password                                                                       
vsadmin              http            password             vsadmin         false                                    
==================================================================================================================================

[+] Total users in SVM 'svm_1_cluster': 2
[LOG] Saved to: logs/security_login_show_svm_1_cluster_20260211_143025.json

[SUCCESS] RBAC user created successfully with all applications!

[*] Retrieving event logs from cluster...
[LOG] Saved to: logs/event_logs_20260211_143026.json

[SUCCESS] Event logs backup completed!
```

## API REST de NetApp

Este script utiliza la **API REST oficial de NetApp ONTAP** a través de la Python Client Library:

### Endpoints POST (Creación)
- **POST** `/api/security/accounts` - Creación de usuarios RBAC

### Endpoints GET (Consulta)
- **GET** `/api/svm/svms` - Consulta de SVMs y obtención de UUID
- **GET** `/api/security/accounts` - Consulta de usuarios RBAC por SVM
- **GET** `/api/support/ems/events` - Consulta de event logs
- **GET** `/api/cluster` - Consulta de información del cluster

**Documentación oficial**: [NetApp ONTAP REST API](https://library.netapp.com/ecmdocs/ECMLP3351667/html/)

## Registro de Funciones

### Funciones de Configuración y Utilidades

#### config_loader(path="config.yaml")
Carga y valida el archivo de configuración YAML.
- **Entrada**: Ruta al archivo config.yaml
- **Salida**: Diccionario con configuración o None si falla
- **Validaciones**: Verifica estructura y secciones obligatorias (cluster, svm, rbac_user)
- **Errores capturados**: FileNotFoundError, yaml.YAMLError, PermissionError

#### save_to_log(operation_name, data)
Guarda datos en archivo JSON con timestamp en carpeta logs/.
- **Entrada**: Nombre de operación y diccionario de datos
- **Salida**: Ruta del archivo creado
- **Formato**: `logs/operacion_YYYYMMDD_HHMMSS.json`
- **Comportamiento**: Crea directorio logs/ si no existe

#### cluster_connection(cluster_config)
Establece y verifica conexión con el cluster NetApp ONTAP.
- **Entrada**: Diccionario con host, username, password
- **Salida**: True si conexión exitosa, False si falla
- **Validaciones**: Prueba acceso consultando información del cluster
- **Muestra**: Nombre del cluster y versión de ONTAP
- **Errores capturados**: NetAppRestError (401, 403, 404), ConnectionError, TimeoutError

### Funciones de Gestión RBAC

#### login_create(config_data, user_config_key='rbac_user')
Crea un usuario RBAC en la SVM especificada con soporte para múltiples aplicaciones.
- **Entrada**: Configuración completa del YAML y clave del usuario a crear
- **Salida**: True si se creó, False si error
- **POST**: `/api/security/accounts`
- **GET**: `/api/svm/svms` (para obtener UUID de SVM)
- **GET**: `/api/security/accounts` (para obtener lista completa de usuarios)
- **Funcionalidad**:
  - Valida campos obligatorios (name, applications, authentication_method, role, password)
  - Busca UUID de la SVM especificada
  - Crea usuario con múltiples aplicaciones simultáneamente
  - Obtiene lista completa de usuarios de la SVM (equivalente a `security login show`)
  - Muestra tabla formateada con todos los usuarios y sus aplicaciones
- **Log**: `security_login_show_<svm_name>_YYYYMMDD_HHMMSS.json`
- **Equivalente CLI**:
  ```bash
  security login create -user-or-group-name <name> -application http \
    -authentication-method password -vserver <svm> -role <role>
  security login create -user-or-group-name <name> -application ssh \
    -authentication-method password -vserver <svm> -role <role>
  security login create -user-or-group-name <name> -application ontapi \
    -authentication-method password -vserver <svm> -role <role>
  security login show -vserver <svm>
  ```

### Funciones de Monitoreo

#### get_event_logs(max_records=100)
Obtiene y respalda los logs de eventos del cluster.
- **Entrada**: Número máximo de registros (default: 100)
- **Salida**: True si se obtuvieron, False si error
- **GET**: `/api/support/ems/events`
- **Funcionalidad**:
  - Recupera eventos del sistema EMS (Event Management System)
  - Extrae index, timestamp, nodo, severidad y nombre del evento
  - Muestra tabla formateada con los primeros 20 eventos
- **Log**: `event_logs_YYYYMMDD_HHMMSS.json`
- **Equivalente CLI**: `event log show -max-records 100`

## Registro de Errores

### Errores de Configuración

#### ERR-001: Archivo de configuración no encontrado
```
[ERROR] File not found: config.yaml
[ERROR] Please check the path and try again
```
**Causa**: El archivo config.yaml no existe en el directorio actual  
**Solución**: Verificar que config.yaml existe en la misma carpeta que el script

#### ERR-002: YAML inválido
```
[ERROR] Invalid YAML format in 'config.yaml'
[ERROR] Detail: <detalle del error>
```
**Causa**: Sintaxis YAML incorrecta (indentación, formato)  
**Solución**: Validar sintaxis YAML, verificar espacios e indentación

#### ERR-003: Configuración incompleta
```
[ERROR] Incomplete configuration: missing 'cluster' section
[ERROR] Incomplete configuration: missing 'svm' section
```
**Causa**: Faltan secciones obligatorias en config.yaml  
**Solución**: Asegurar que config.yaml contenga secciones 'cluster', 'svm' y 'rbac_user'

#### ERR-004: Archivo vacío
```
[ERROR] File 'config.yaml' is empty or doesn't contain valid YAML
```
**Causa**: Archivo config.yaml vacío o solo contiene comentarios  
**Solución**: Añadir configuración válida al archivo

#### ERR-005: Permisos insuficientes
```
[ERROR] Insufficient permissions to read: config.yaml
```
**Causa**: Sin permisos de lectura en el archivo  
**Solución**: Verificar y ajustar permisos del archivo

### Errores de Conexión

#### ERR-101: Error de autenticación
```
[ERROR] HTTP status: 401
[ERROR] Authentication failed
[ERROR] Invalid username or password for user '<username>'
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
[ERROR] Cannot reach host '<hostname>'
[ERROR] Check network connectivity and hostname/IP
```
**Causa**: Problemas de red o hostname incorrecto  
**Solución**: Verificar conectividad de red y hostname/IP del cluster

#### ERR-104: Timeout de conexión
```
[ERROR] Connection timeout to '<hostname>'
[ERROR] Cluster is not responding
```
**Causa**: Cluster no responde  
**Solución**: Verificar que el cluster esté encendido y accesible

#### ERR-105: Recurso no encontrado
```
[ERROR] HTTP status: 404
[ERROR] Resource not found - Check cluster URL
```
**Causa**: URL del cluster incorrecta o API no disponible  
**Solución**: Verificar hostname y versión de ONTAP (requiere 9.6+)

#### ERR-106: Campos obligatorios faltantes
```
[ERROR] Missing required fields in cluster config: host, username
```
**Causa**: Faltan campos obligatorios en la configuración del cluster  
**Solución**: Completar todos los campos requeridos (host, username, password)

### Errores de Creación de Usuario RBAC

#### ERR-201: Usuario ya existe
```
[ERROR] User '<username>' already exists
```
**Causa**: Ya existe un usuario con ese nombre en la SVM  
**Solución**: Cambiar nombre en config.yaml o eliminar usuario existente con `security login delete`

#### ERR-202: SVM no encontrada
```
[ERROR] SVM '<svm_name>' not found in cluster
```
**Causa**: Nombre de SVM incorrecto o SVM no existe  
**Solución**: Ejecutar `vserver show` para ver SVMs disponibles y verificar nombre

#### ERR-203: Campos obligatorios faltantes
```
[ERROR] Missing required fields in rbac_user config: name, applications
```
**Causa**: Faltan campos obligatorios en la configuración del usuario  
**Solución**: Completar todos los campos: name, applications, authentication_method, role, password

#### ERR-204: Lista de aplicaciones vacía
```
[ERROR] 'applications' must be a non-empty list
```
**Causa**: Campo applications vacío o no es una lista  
**Solución**: Especificar al menos una aplicación (http, ssh, ontapi, console, service-processor)

#### ERR-205: Parámetros inválidos
```
[ERROR] HTTP Status: 400
[ERROR] Invalid parameters
```
**Causa**: Parámetros de creación inválidos (rol inexistente, método de autenticación no válido, etc.)  
**Solución**: Verificar que:
- El rol exista (`security login role show`)
- El authentication_method sea válido (password, domain, nsswitch, cert, publickey, usm, community)
- Las aplicaciones sean válidas (http, ssh, ontapi, console, service-processor)

#### ERR-206: Rol no existe
```
[ERROR] Role '<role_name>' not found
```
**Causa**: Rol especificado no existe en la SVM  
**Solución**: Usar roles predefinidos (admin, vsadmin, vsadmin-readonly, etc.) o crear rol personalizado primero

### Errores de Event Logs

#### ERR-601: No se pueden obtener event logs
```
[WARNING] Event logs backup failed (non-critical)
```
**Causa**: Error al consultar API de eventos  
**Solución**: No crítico, verificar permisos de lectura de eventos. El script continúa normalmente

### Códigos de Estado HTTP Comunes

- **400 Bad Request**: Parámetros inválidos en la solicitud
- **401 Unauthorized**: Credenciales incorrectas
- **403 Forbidden**: Sin permisos suficientes
- **404 Not Found**: Recurso no existe (SVM, cluster API endpoint)
- **409 Conflict**: Recurso ya existe (usuario duplicado)
- **500 Internal Server Error**: Error interno del servidor ONTAP

## Seguridad

- **IMPORTANTE**: NO compartas el archivo `config.yaml` con credenciales
- Considera usar variables de entorno para credenciales sensibles
- El script desactiva verificación SSL (`verify=False`) - úsalo solo en entornos de desarrollo/pruebas
- Los logs pueden contener información sensible (nombres de usuarios, roles) - protege el directorio `logs/`
- Las contraseñas de usuarios RBAC deben cumplir con las políticas de seguridad de ONTAP
- Recomendación: usar contraseñas fuertes con al menos 8 caracteres (mayúsculas, minúsculas, números, símbolos)

## Licencia

Este script es para uso interno y educativo.

## Soporte

Para problemas relacionados con la API de NetApp, consulta:
- [Documentación API REST](https://library.netapp.com/ecmdocs/ECMLP3351667/html/)
- [NetApp Community](https://community.netapp.com/)
- [Python Client Library](https://pypi.org/project/netapp-ontap/)

---

**Versión**: 1.0  
**Última actualización**: Febrero 2026  
**Compatible con**: ONTAP 9.6+
esto es del read me