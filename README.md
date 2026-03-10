# NetApp ONTAP NFS SVM Creation Script

Script automatizado para la creación y configuración completa de Storage Virtual Machines (SVMs) con protocolo NFS en NetApp ONTAP usando la API REST oficial.

## Índice

- [Inicio Rápido](#inicio-rápido)
- [Descripción](#descripción)
- [Requisitos](#requisitos)
  - [Software](#software)
  - [Dependencias Python](#dependencias-python)
- [Estructura del Proyecto](#estructura-del-proyecto)
- [Configuración Inicial](#configuración-inicial)
  - [Crear config.yaml desde Cero](#crear-configyaml-desde-cero)
- [Configuración](#configuración)
  - [cluster](#cluster)
  - [svm](#svm)
  - [Configuración del servicio NFS](#configuración-del-servicio-nfs)
  - [Export Policies](#export-policies)
  - [network_interfaces](#network_interfaces)
- [Funciones del Script](#funciones-del-script)
  - [config_loader](#config_loader)
  - [save_to_log](#save_to_log)
- [Ejemplo de Configuración](#ejemplo-de-configuración)
  - [Reglas de Exportación (export_policy_rules)](#reglas-de-exportación-export_policy_rules)
  - [Interfaces de Red (network_interfaces)](#interfaces-de-red-network_interfaces)
- [Sistema de Logging](#sistema-de-logging)
  - [Formato de Logs](#formato-de-logs)
- [Uso](#uso)
  - [Ejecución Básica](#ejecución-básica)
  - [Flujo de Ejecución](#flujo-de-ejecución)
- [API REST de NetApp](#api-rest-de-netapp)
  - [Endpoints POST (Creación)](#endpoints-post-creación)
  - [Endpoints PATCH (Modificación)](#endpoints-patch-modificación)
  - [Endpoints GET (Consulta)](#endpoints-get-consulta)
- [Registro de Funciones](#registro-de-funciones)
  - [Funciones de Configuración y Utilidades](#funciones-de-configuración-y-utilidades)
  - [Funciones de Gestión de SVM](#funciones-de-gestión-de-svm)
  - [Funciones de Configuración NFS](#funciones-de-configuración-nfs)
  - [Funciones de Interfaces de Red](#funciones-de-interfaces-de-red)
  - [Funciones de Monitoreo](#funciones-de-monitoreo)
- [Registro de Errores](#registro-de-errores)
  - [Errores de Configuración](#errores-de-configuración)
  - [Errores de Conexión](#errores-de-conexión)
  - [Errores de Creación de SVM](#errores-de-creación-de-svm)
  - [Errores de Servicio NFS](#errores-de-servicio-nfs)
  - [Errores de Export Policies](#errores-de-export-policies)
  - [Errores de Interfaces de Red](#errores-de-interfaces-de-red)
  - [Errores de Protocolos](#errores-de-protocolos)
  - [Errores de Event Logs](#errores-de-event-logs)
  - [Códigos de Estado HTTP Comunes](#códigos-de-estado-http-comunes)
- [Seguridad](#seguridad)

## Inicio Rápido

¿Primera vez usando este script? Sigue estos pasos:

### 1. Clonar el repositorio
```bash
git clone <repository-url>
cd svm_nfs_create
```

### 2. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 3. Crear tu archivo de configuración
```bash
# Copiar la plantilla
copy config.yaml.example config.yaml   # Windows
cp config.yaml.example config.yaml     # Linux/macOS

# Editar con tus valores
notepad config.yaml                    # Windows
nano config.yaml                       # Linux/macOS
```

### 4. Configurar valores mínimos requeridos

Edita `config.yaml` y configura al menos:
- `cluster.host` - IP o hostname de tu cluster NetApp
- `cluster.username` - Usuario admin
- `cluster.password` - Contraseña
- `svm.name` - Nombre único para tu SVM
- `svm.aggregate` - Agregado existente (verifica con `storage aggregate show`)
- `network_interfaces[0].address` - IP libre para la LIF NFS
- `network_interfaces[0].home_node` - Nodo del cluster (verifica con `cluster show`)
- `network_interfaces[0].home_port` - Puerto de red (ej: e0c, e0d)

### 5. Ejecutar el script
```bash
python create_nfs_svm.py
```

### 6. Verificar logs

Los resultados se guardan automáticamente en la carpeta `logs/` con timestamp.

```bash
# Ver logs generados
dir logs                # Windows
ls logs                 # Linux/macOS
```

Para configuración detallada, consulta la sección [Configuración Inicial](#configuración-inicial).

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
- Python: 3.11.4
- NetApp ONTAP: 9.15.1 o superior
- YAML: 6.0 o superior
- NetApp ONTAP Python Client Library: 9.14.0 o superior
- Git
- Acceso de red al cluster NetApp
- Credenciales de administrador del cluster

### Dependencias Python
```bash
pip install -r requirements.txt
```

## Estructura del Proyecto

```
svm_nfs_create/
├── create_nfs_svm.py    # Script principal
├── config.yaml.example  # Plantilla de configuración (versionada)
├── config.yaml          # Tu configuración (NO versionada, crear manualmente)
├── .gitignore           # Excluye config.yaml del repositorio
├── requirements.txt     # Dependencias Python
├── README.md            # Esta documentación
└── logs/                # Logs JSON generados automáticamente
```

**Nota**: El archivo `config.yaml` NO está incluido en el repositorio por seguridad. Usa `config.yaml.example` como plantilla.

## Configuración Inicial

### Crear config.yaml desde Cero

**IMPORTANTE**: El archivo `config.yaml` contiene credenciales sensibles y está excluido del repositorio Git por seguridad. Debes crearlo manualmente antes de ejecutar el script.

#### Opción 1: Usar la plantilla incluida (Recomendado)

El proyecto incluye un archivo `config.yaml.example` que puedes usar como punto de partida:

```bash
# En Windows PowerShell
Copy-Item config.yaml.example config.yaml

# En Linux/macOS
cp config.yaml.example config.yaml
```

Luego edita `config.yaml` con tus valores específicos.

#### Opción 2: Crear desde cero

#### Paso 1: Crear el archivo

Crea un archivo llamado `config.yaml` en el directorio raíz del proyecto (mismo directorio donde está `create_nfs_svm.py`).

#### Paso 2: Estructura básica

Copia la siguiente plantilla completa en tu archivo `config.yaml`:

```yaml
# ============================================================================
# CONFIGURACIÓN PARA CREAR SVM CON SERVICIO NFS USANDO API REST DE ONTAP
# ============================================================================

# CONFIGURACIÓN DE CONEXIÓN AL CLUSTER
cluster:
  host: cluster.demo.netapp.com         # Hostname o IP del cluster NetApp
  username: admin                        # Usuario con permisos de administrador
  password: YourPassword123!             # Contraseña del usuario admin

# CONFIGURACIÓN DE LA SVM NFS
svm: 
  name: SVM_NFS_01                       # Nombre único de la SVM a crear
  ipspace: Default                       # IPspace (usar 'Default' si no hay uno específico)
  aggregate: aggr0_cluster_01            # Agregado para el volumen raíz de la SVM
  language: c.utf_8                      # Código de idioma (c.utf_8, es.utf_8, en_us.utf_8)
  security_style: unix                   # Estilo de seguridad: unix, ntfs, o mixed
  rootvolume: SVM_NFS_01_root            # Nombre del volumen raíz de la SVM

  # Parámetros de modificación
  aggr_list:                             # Lista de agregados que la SVM puede usar
    - aggr0_cluster_01
    - aggr0_cluster_02
  is_space_reporting_logical: true       # Reportar espacio lógico en lugar de físico
  is_space_enforcement_logical: true     # Aplicar límites de espacio lógico

  # Protocolos permitidos
  protocols:
    cifs: false                          # CIFS/SMB - Protocolo de Windows
    nfs: true                            # NFS - Protocolo de Unix/Linux
    ndmp: true                           # NDMP - Protocolo de backup
    s3: false                            # S3 - Object storage
    fcp: false                           # FCP - Fibre Channel Protocol
    iscsi: false                         # iSCSI - Block protocol

  # Configuración del servicio NFS
  nfs_v3_enabled: true                   # Habilitar NFSv3
  nfs_v40_enabled: true                  # Habilitar NFSv4.0
  nfs_v41_enabled: true                  # Habilitar NFSv4.1
  nfs_v41_pnfs_enabled: true             # Habilitar pNFS (parallel NFS) para NFSv4.1

  # Configuración de export policy
  export_policy_name: default            # Nombre de la export policy principal

  # Configuración de export policy rules
  export_policy_rules:
    # Policy 1: default - Acceso completo desde cualquier origen
    - policy_name: default
      rules:
        - clientmatch: 0.0.0.0/0         # Rango de IPs permitidas (0.0.0.0/0 = todas)
          rorule: any                    # Regla de lectura: any, sys, krb5, none
          rwrule: any                    # Regla de escritura: any, sys, krb5, none
          superuser: any                 # Acceso superuser: any, sys, krb5, none
          protocols:                     # Protocolos permitidos
            - nfs
            - nfs3
            - nfs4
          ruleindex: 1                   # Índice de la regla (orden de evaluación)
    
    # Policy 2: custom - Ejemplo de policy personalizada
    - policy_name: custom_policy
      rules:
        - clientmatch: 192.168.1.0/24    # Solo red 192.168.1.x
          rorule: sys                    # Solo lectura con autenticación de sistema
          rwrule: sys                    # Lectura/escritura con autenticación
          superuser: sys                 # Superuser con autenticación
          protocols:
            - nfs3
            - nfs4
          ruleindex: 1

  # CONFIGURACIÓN NETWORK INTERFACES (LIFs)
  network_interfaces:
    # LIF 1: Interfaz de datos NFS
    - name: nfs_data_lif_01              # Nombre único de la interfaz
      role: data                         # Rol: data (para tráfico de datos)
      data_protocol: nfs                 # Protocolo: nfs, cifs, iscsi, fcp
      home_node: cluster-01              # Nodo home (usar 'cluster show' para ver nodos)
      home_port: e0c                     # Puerto home (ej: e0c, e0d, a0a)
      address: 192.168.1.100             # Dirección IP de la interfaz
      netmask: 255.255.255.0             # Máscara de red
      auto_revert: false                 # Auto-revert a home node/port (true/false)

    # LIF 2: Segunda interfaz de datos NFS (opcional - para alta disponibilidad)
    - name: nfs_data_lif_02
      role: data
      data_protocol: nfs
      home_node: cluster-02              # Usar otro nodo para balanceo
      home_port: e0c
      address: 192.168.1.101
      netmask: 255.255.255.0
      auto_revert: false
  
    # LIF 3: Interfaz de management (opcional - para administración)
    - name: svm_mgmt_lif
      service_policy: default-management # Service policy para LIFs de management
      address: 192.168.1.102
      netmask: 255.255.255.0
      home_node: cluster-01
      home_port: e0d                     # Usar puerto diferente al de datos
      broadcast_domain: Default          # Broadcast domain (usar 'network port broadcast-domain show')
      status_admin: up                   # Estado administrativo: up o down
      auto_revert: false
```

#### Paso 3: Personalizar valores

Reemplaza los valores de ejemplo con los de tu entorno:

**Sección `cluster`** (obligatoria):
- `host`: IP o hostname de tu cluster NetApp ONTAP
- `username`: Tu usuario administrador del cluster
- `password`: Tu contraseña (mantén este archivo seguro)

**Sección `svm`** (obligatoria):
- `name`: Nombre único para tu SVM (no debe existir ya en el cluster)
- `aggregate`: Usa `storage aggregate show` en ONTAP CLI para ver agregados disponibles
- `rootvolume`: Nombre del volumen raíz (generalmente `<svm_name>_root`)

**Sección `aggr_list`**:
- Lista todos los agregados que la SVM puede usar para crear volúmenes
- Usa `storage aggregate show` para ver los disponibles

**Sección `export_policy_rules`**:
- `clientmatch`: Define qué clientes pueden acceder (ejemplos):
  - `0.0.0.0/0` - Todos los clientes
  - `192.168.1.0/24` - Red específica
  - `192.168.1.100` - IP específica
  - `client1.domain.com` - Hostname específico
- `rorule` / `rwrule`: Reglas de acceso:
  - `any` - Cualquier método de autenticación
  - `sys` - Solo autenticación de sistema Unix/Linux
  - `krb5` - Kerberos 5
  - `none` - Sin acceso

**Sección `network_interfaces`**:
- `home_node`: Usa `cluster show` para ver nodos disponibles
- `home_port`: Usa `network port show -node <node>` para ver puertos disponibles
- `address`: IP libre en tu red que no esté en uso
- `netmask`: Máscara de red de tu subnet
- `broadcast_domain`: Usa `network port broadcast-domain show` para ver dominios disponibles

#### Paso 4: Validar sintaxis YAML

**IMPORTANTE**: YAML es sensible a la indentación. Usa **espacios, NO tabs**.

Reglas básicas:
- Usa **2 espacios** para cada nivel de indentación
- Los items de lista comienzan con `- ` (guión y espacio)
- Los valores se separan con `: ` (dos puntos y espacio)
- Los comentarios comienzan con `#`

#### Paso 5: Verificar antes de ejecutar

Antes de ejecutar el script, verifica:

- El archivo se llama exactamente `config.yaml`  
- Está en el mismo directorio que `create_nfs_svm.py`  
- No tiene tabs, solo espacios  
- Los valores de `host`, `username`, `password` son correctos  
- El nombre de la SVM no existe en el cluster  
- Los nombres de nodos, puertos y agregados existen en tu cluster  
- Las direcciones IP están libres y son válidas  

#### Ejemplo Mínimo

Si solo necesitas una configuración básica para pruebas, este es el mínimo requerido:

```yaml
cluster:
  host: 192.168.1.50
  username: admin
  password: NetApp123!

svm: 
  name: test_svm
  aggregate: aggr0_cluster_01
  rootvolume: test_svm_root
  
  aggr_list:
    - aggr0_cluster_01
  
  protocols:
    nfs: true
  
  nfs_v3_enabled: true
  
  export_policy_name: default
  
  export_policy_rules:
    - policy_name: default
      rules:
        - clientmatch: 0.0.0.0/0
          rorule: any
          rwrule: any
          protocols:
            - nfs3
  
  network_interfaces:
    - name: test_lif
      role: data
      data_protocol: nfs
      home_node: cluster-01
      home_port: e0c
      address: 192.168.1.200
      netmask: 255.255.255.0
      auto_revert: false
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

### Protección de Credenciales

- **IMPORTANTE**: NO compartas el archivo `config.yaml` con credenciales
- El archivo `.gitignore` está configurado para excluir `config.yaml` del repositorio
- Usa `config.yaml.example` como plantilla (sin credenciales reales)
- Considera usar variables de entorno para credenciales sensibles en producción
- El script desactiva verificación SSL (`verify=False`) - úsalo solo en entornos de desarrollo/pruebas
- Los logs pueden contener información sensible - protege el directorio `logs/`

### Buenas Prácticas

1. **Nunca versiones config.yaml**: El `.gitignore` ya lo excluye, pero verifica antes de hacer commits
2. **Permisos restrictivos**: En Linux/Unix, usa `chmod 600 config.yaml` para que solo el propietario pueda leerlo
3. **Rotación de contraseñas**: Cambia las contraseñas periódicamente y actualiza `config.yaml`
4. **Logs de auditoría**: Revisa regularmente los logs en el directorio `logs/` para auditar operaciones
5. **Backup seguro**: Si haces backup de `config.yaml`, asegúrate de que esté encriptado

### Uso en Producción

Para entornos de producción, considera:

```python
# Usar variables de entorno en lugar de config.yaml
import os

cluster_config = {
    'host': os.getenv('ONTAP_HOST'),
    'username': os.getenv('ONTAP_USERNAME'),
    'password': os.getenv('ONTAP_PASSWORD')
}
```

---
