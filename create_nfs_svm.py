#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NetApp ONTAP NFS SVM Creation and Configuration Script

This script automates the creation and configuration of Storage Virtual Machines (SVMs)
with NFS protocol on NetApp ONTAP systems using the NetApp ONTAP REST API Python Client Library.

Features:
    - SVM creation with custom parameters
    - NFS service configuration (NFSv3, NFSv4, NFSv4.1)
    - Multiple network interfaces (NFS Data LIFs)
    - Management interface creation
    - Export policies and rules configuration
    - Event logging and comprehensive error handling
    - JSON logging for all operations

Requirements:
    - NetApp ONTAP 9.6+
    - Python 3.7+
    - netapp-ontap library
    - PyYAML library

Configuration:
    - Edit config.yaml to set cluster credentials and SVM parameters
    - Define NFS interfaces, export policies, and allowed clients

Author: ONTAP Automation Team
Version: 1.0.0
Last Updated: February 2026
"""

# ============================================================================
# IMPORTS
# ============================================================================
from netapp_ontap import config, HostConnection, NetAppRestError
from netapp_ontap.resources import Cluster, Svm, IpInterface, EmsEvent, NfsService, ExportPolicy, ExportRule
import yaml
import json
import os
from datetime import datetime


# ============================================================================
# SCRIPT INITIALIZATION
# ============================================================================
print("\n" + "="*70)
print("  NetApp ONTAP NFS SVM Creation Script")
print("  Using NetApp ONTAP Python Client Library")
print("="*70)
print("\n[*] Initializing SVM creation workflow...")


# ============================================================================
# YAML CONFIGURATION FUNCTION
# ============================================================================

def config_loader(path="config.yaml"):
    """
    Carga la configuración desde un archivo YAML con validación completa
    
    Lee el archivo de configuración y valida que contenga las secciones
    necesarias para crear una SVM en NetApp ONTAP.
    
    Args:
        path: Ruta al archivo de configuración (por defecto 'config.yaml')
    
    Returns:
        dict: Diccionario con la configuración cargada, o None si falla
    """
    try:
        print(f"[+] Config.yaml loader: {path}")
        
        # Abrir y leer el contenido del archivo YAML
        with open(path, 'r', encoding='utf-8') as file:
            config_data = yaml.safe_load(file)
        
        # VALIDACIONES
        # Validar que el archivo no esté vacío
        if config_data is None:
            print(f"[ERROR] File '{path}' is empty or doen't contain valid YAML")
            return None
        
        # Validar estructura: debe contener seccion 'cluster'
        if 'cluster' not in config_data:
            print(f"[ERROR]Incomplete configuration: missing 'cluster' section")
            return None
        
        # Validar estructura: debe contener seccion 'svm'
        if 'svm' not in config_data:
            print(f"[ERROR] Incomplete configuration: missing 'svm' section")
            return None
        
        print(f"[+] Configuration loaded successfully")

        # Mostrar resumen de la configuración cargada
        print(f"[+] Target cluster: {config_data['cluster'].get('host', 'N/A')}")
        print(f"[+] SVM to create: {config_data['svm'].get('name', 'N/A')}")
        
        return config_data
    
    # CONTROL DE ERRORES
    except FileNotFoundError:
        print(f"[ERROR] File not found: {path}")
        print(f"[ERROR] Please check the path and try again")
        return None
    
    except yaml.YAMLError as e:
        print(f"[ERROR] Invalid YAML format in '{path}'")
        print(f"[ERROR] Detail: {str(e)}")
        return None
    
    except PermissionError:
        print(f"[ERROR] Insufficient permissions to read: {path}")
        return None
    
    except Exception as e:
        print(f"[ERROR] Unexpected failure: {type(e).__name__}")
        print(f"[ERROR] Message: {str(e)}")
        return None


# ============================================================================
# SAVE TO LOG FUNCTION
# ============================================================================

def save_to_log(operation_name, data):
    """
    Guarda datos en un archivo JSON dentro de la carpeta logs/ con timestamp
    
    Args:
        operation_name (str): Nombre de la operación (ej: 'create_svm', 'fcp_create')
        data (dict): Datos a guardar (normalmente el show de la cabina)
    
    Returns:
        str: Ruta del archivo creado
    """
    try:
        # Crear carpeta logs si no existe
        logs_dir = "logs"
        if not os.path.exists(logs_dir):
            os.makedirs(logs_dir)
        
        # Generar timestamp: YYYYMMDD_HHMMSS
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Nombre del archivo: operation_YYYYMMDD_HHMMSS.json
        filename = f"{logs_dir}/{operation_name}_{timestamp}.json"
        
        # Guardar en formato JSON
        with open(filename, 'w', encoding='utf-8') as log_file:
            json.dump(data, log_file, indent=2, ensure_ascii=False)
        
        print(f"[LOG] Saved to: {filename}")
        return filename
    
    except Exception as e:
        print(f"[WARNING] Could not save log: {str(e)}")
        return None


# ============================================================================
# CLUSTER CONNECTION FUNCTION
# ============================================================================

def cluster_connection(cluster_config):
    """
    Establece conexión con la cabina NetApp ONTAP y verifica acceso
    
    Conecta con el cluster usando las credenciales proporcionadas y realiza
    una consulta de prueba para validar que el acceso es correcto.
    
    Args:
        cluster_config: Diccionario con claves 'host', 'username', 'password'
    
    Returns:
        bool: True si conexión exitosa, False si hay errores
    """
    try:
        print(f"\n[*] Establishing connection to cluster: {cluster_config.get('host', 'N/A')}")
        
        # Validar que existan todos los campos necesarios
        required_keys = ['host', 'username', 'password']
        # Itera por cada clave requerida y guarda en una lista las que faltan
        missing_keys = [key for key in required_keys if key not in cluster_config]
        
        if missing_keys:
            print(f"[ERROR] Missing required fields in cluster config: {', '.join(missing_keys)}")
            return False
        
        # Establecer conexión con la cabina
        config.CONNECTION = HostConnection(
            cluster_config['host'],
            username=cluster_config['username'],
            password=cluster_config['password'],
            verify=False 
        )
        
        # Verificar acceso haciendo una consulta al cluster
        cluster_info = Cluster()
        cluster_info.get()
        
        print(f"[+] Connection successful!")
        print(f"[+] Cluster name: {cluster_info.name}")
        print(f"[+] ONTAP version: {cluster_info.version.full}")

        return True
    
    # CONTROL DE ERRORES
    except NetAppRestError as error:
        print(f"[ERROR] NetApp REST API error")
        print(f"[ERROR] HTTP status: {error.status_code}")
        
        # Detallar el tipo de error según el código HTTP
        if error.status_code == 401:
            print(f"[ERROR] Authentication failed")
            print(f"[ERROR] Invalid username or password for user '{cluster_config.get('username')}'")
        elif error.status_code == 403:
            print(f"[ERROR] Forbidden - User lacks required permissions")
        elif error.status_code == 404:
            print(f"[ERROR] Resource not found - Check cluster URL")
        else:
            print(f"[ERROR] Details: {error.http_err_response.http_response.text}")
        
        return False
    
    except KeyError as e:
        print(f"[ERROR] Configuration error - Missing key: {str(e)}")
        return False
    
    except ConnectionError:
        print(f"[ERROR] Cannot reach host '{cluster_config.get('host')}'")
        print(f"[ERROR] Check network connectivity and hostname/IP")
        return False
    
    except TimeoutError:
        print(f"[ERROR] Connection timeout to '{cluster_config.get('host')}'")
        print(f"[ERROR] Cluster is not responding")
        return False
    
    except Exception as e:
        print(f"[ERROR] Unexpected error: {type(e).__name__}")
        print(f"[ERROR] Message: {str(e)}")
        return False


# ============================================================================
# SVM MANAGEMENT FUNCTIONS
# ============================================================================

def create_svm(svm_config):
    """
    Crea una SVM en NetApp ONTAP con los parámetros del config.yaml
    
    Args:
        svm_config: Diccionario con la configuración de la SVM desde config.yaml
    
    Returns:
        bool: True si se creó exitosamente, False si hubo error
    """
    try:
        # Extraer parámetros del config.yaml
        svm_name = svm_config.get('name')
        ipspace = svm_config.get('ipspace')
        language = svm_config.get('language')
        security_style = svm_config.get('security_style')
        rootvolume = svm_config.get('rootvolume')
        aggregate = svm_config.get('aggregate')
        
        # VALIDACIONES
        # Validar que exista el valor obligatorio 'name'
        if not svm_name:
            print(f"[ERROR] 'name' is required in svm configuration")
            return False
        
        print(f"\n[*] Creating SVM: {svm_name}")
        
        # Verificar si la SVM ya existe
        print(f"[*] Checking if SVM already exists...")
        existing_svm = Svm.find(name=svm_name)
        if existing_svm:
            print(f"[ERROR] SVM '{svm_name}' already exists on the cluster")
            return False
        
        # SVM
        # Crear objeto SVM
        new_svm = Svm()
        new_svm.name = svm_name
        
        # DATOS ENVIADOS AL CLÚSTER DESDE EL CONFIG.YAML
        # Configurar IPspace 
        if ipspace:
            new_svm.ipspace = {'name': ipspace}
            print(f"[*] IPspace: {ipspace}")
        
        # Configurar idioma
        if language:
            new_svm.language = language
            print(f"[*] Language: {language}")
        
        # Configurar volumen raíz con security style y nombre
        root_vol = {}
        if rootvolume:
            root_vol['name'] = rootvolume
            print(f"[*] Root Volume Name: {rootvolume}")
        if security_style:
            root_vol['security_style'] = security_style
            print(f"[*] Root Volume Security Style: {security_style}")
        
        if root_vol:
            new_svm.root_volume = root_vol
        
        # Especificar el agregado para el volumen raíz
        new_svm.aggregates = [{'name': aggregate}]
        print(f"[*] Aggregate: {aggregate}")
        
        # Enviar petición de creación al cluster
        print(f"[*] Sending creation request...")
        new_svm.post()
        
        print(f"[+] SVM '{svm_name}' created successfully!")
        
        # SHOW - Obtener y mostrar datos reales de la cabina
        print(f"\n[*] Retrieving SVM details from cluster...")
        svm_created = Svm.find(name=svm_name)
        svm_show = Svm(uuid=svm_created.uuid)
        svm_show.get()
        
        # Preparar datos para guardar en log
        svm_data = {
            'uuid': svm_show.uuid,
            'name': svm_show.name,
            'state': svm_show.state if hasattr(svm_show, 'state') else None,
            'ipspace': svm_show.ipspace.name if hasattr(svm_show, 'ipspace') and svm_show.ipspace else None,
            'language': svm_show.language if hasattr(svm_show, 'language') else None,
            'root_volume_security_style': security_style,
            'aggregates': [
                {'name': aggr.name, 'uuid': aggr.uuid} 
                for aggr in svm_show.aggregates
            ] if hasattr(svm_show, 'aggregates') and svm_show.aggregates else []
        }
        
        # Imprimir show de la SVM
        print(f"\n{'='*60}")
        print(f"  SVM SHOW - Data from NetApp Cluster")
        print(f"{'='*60}")
        print(f"UUID:                    {svm_data['uuid']}")
        print(f"Name:                    {svm_data['name']}")
        print(f"State:                   {svm_data['state'] or 'N/A'}")
        print(f"IPspace:                 {svm_data['ipspace'] or 'N/A'}")
        print(f"Language:                {svm_data['language'] or 'N/A'}")
        print(f"Root Volume Sec. Style:  {svm_data['root_volume_security_style'] or 'N/A'}")
        if svm_data['aggregates']:
            print(f"Aggregates:")
            for aggr in svm_data['aggregates']:
                print(f"  - {aggr['name']} (UUID: {aggr['uuid']})")
        print(f"{'='*60}\n")
        
        # Guardar en log con timestamp
        save_to_log('create_svm', svm_data)
        
        return True
    
    # CONTROL DE ERRORES
    except NetAppRestError as error:
        print(f"[ERROR] NetApp API error during SVM creation")
        print(f"[ERROR] HTTP Status: {error.status_code}")
        
        # Proporcionar información detallada según el error
        if error.status_code == 409:
            print(f"[ERROR] Conflict - SVM may already exist or name is in use")
        elif error.status_code == 400:
            print(f"[ERROR] Bad request - Invalid parameters")
            print(f"[ERROR] Common causes:")
            print(f"[ERROR] - Aggregate 'aggr1' doesn't exist (check aggregate name)")
            print(f"[ERROR] - Invalid ipspace name")
            print(f"[ERROR] - Invalid language code")
            print(f"[ERROR] Response: {error.http_err_response.http_response.text}")
        else:
            print(f"[ERROR] Response: {error.http_err_response.http_response.text}")
        
        return False
    
    except KeyError as e:
        print(f"[ERROR] Missing required configuration key: {str(e)}")
        return False
    
    except Exception as e:
        print(f"[ERROR] Unexpected error during SVM creation: {type(e).__name__}")
        print(f"[ERROR] Details: {str(e)}")
        return False


def modify_svm(svm_config):
    """
    Modifica una SVM configurando parámetros de espacio lógico
    
    Args:
        svm_config: Diccionario con la configuración de la SVM del config.yaml
    
    Returns:
        bool: True si se modificó exitosamente, False si hubo error
    """
    try:
        # Extraer nombre de la SVM del config
        svm_name = svm_config.get('name')
        
        # Extraer lista de agregados del config.yaml
        aggr_list = svm_config.get('aggr_list', [])

        # Extraer valores de espacio lógico del config.yaml
        space_reporting = svm_config.get('is_space_reporting_logical', False)
        space_enforcement = svm_config.get('is_space_enforcement_logical', False)
        
        
        print(f"\n[*] Modifying SVM: {svm_name}")
        
        # Buscar la SVM
        svm = Svm.find(name=svm_name)
        if not svm:
            print(f"[ERROR] SVM '{svm_name}' not found")
            return False
        
        # Configurar lista de agregados desde config.yaml
        if aggr_list:
            svm.aggregates = [{'name': aggr} for aggr in aggr_list]
            print(f"[*] Aggregate list: {', '.join(aggr_list)}")
        
        # Configurar parámetros de espacio lógico desde config.yaml
        svm.is_space_reporting_logical = space_reporting
        svm.is_space_enforcement_logical = space_enforcement
        
        print(f"[*] is_space_reporting_logical: {space_reporting}")
        print(f"[*] is_space_enforcement_logical: {space_enforcement}")
        
        # Aplicar cambios
        print(f"[*] Applying changes...")
        svm.patch()
        
        print(f"[+] SVM '{svm_name}' modified successfully!")
        
        # GET: Obtener datos reales de la SVM desde la cabina
        print(f"[*] Retrieving SVM details from cluster...")
        svm_updated = Svm.find(name=svm_name)
        if svm_updated:
            svm_updated.get(fields='aggregates,is_space_reporting_logical,is_space_enforcement_logical')
            
            # Extraer lista de agregados
            aggr_list_data = []
            if hasattr(svm_updated, 'aggregates') and svm_updated.aggregates:
                aggr_list_data = [{'name': aggr.name, 'uuid': aggr.uuid} for aggr in svm_updated.aggregates]
            
            # Extraer los datos para el show
            svm_data = {
                'vserver_name': svm_name,
                'aggr_list': aggr_list_data,
                'is_space_reporting_logical': svm_updated.is_space_reporting_logical if hasattr(svm_updated, 'is_space_reporting_logical') else False,
                'is_space_enforcement_logical': svm_updated.is_space_enforcement_logical if hasattr(svm_updated, 'is_space_enforcement_logical') else False
            }
            
            # SHOW: Mostrar información de la SVM modificada
            print(f"\n{'='*60}")
            print(f"  SVM Modification Show")
            print(f"{'='*60}")
            print(f"                 Vserver Name: {svm_data['vserver_name']}")
            print(f"is-space-reporting-logical: {svm_data['is_space_reporting_logical']}")
            print(f"is-space-enforcement-logical: {svm_data['is_space_enforcement_logical']}")
            print(f"                   Aggr List:")
            if svm_data['aggr_list']:
                for aggr in svm_data['aggr_list']:
                    print(f"  - {aggr['name']}")
            else:
                print(f"  (No aggregates configured)")
            print(f"{'='*60}\n")
            
            # Guardar en log con timestamp
            save_to_log('modify_svm', svm_data)
        else:
            print(f"[WARNING] Could not retrieve SVM details")
        
        return True
    
    # CONTROL DE ERRORES
    except NetAppRestError as error:
        print(f"[ERROR] NetApp API error")
        print(f"[ERROR] HTTP Status: {error.status_code}")
        print(f"[ERROR] Details: {error.http_err_response.http_response.text}")
        return False
    
    except Exception as e:
        print(f"[ERROR] Unexpected error: {type(e).__name__}")
        print(f"[ERROR] Details: {str(e)}")
        return False

# ============================================================================
# NFS PROTOCOL CONFIGURATION FUNCTION
# ============================================================================

def configure_protocols(svm_config):
    """
    Configura los protocolos permitidos en la SVM (allowed=true/false)
    
    Args:
        svm_config: Diccionario con la configuración de la SVM del config.yaml
                    Debe incluir la sección 'protocols' con cada protocolo y su valor
    
    Returns:
        bool: True si se configuró exitosamente, False si hubo error
    """
    try:
        # Extraer nombre de la SVM del config
        svm_name = svm_config.get('name')
        
        # Extraer diccionario de protocolos del config.yaml
        protocols_config = svm_config.get('protocols', {})
        
        # Validar que haya protocolos para configurar
        if not protocols_config:
            print(f"[WARNING] No protocol configuration found in config.yaml")
            return True
        
        print(f"\n[*] Configuring protocols for SVM: {svm_name}")
        
        # Buscar la SVM
        svm = Svm.find(name=svm_name)
        if not svm:
            print(f"[ERROR] SVM '{svm_name}' not found")
            return False
        
        # Obtener el objeto SVM completo
        svm_obj = Svm(uuid=svm.uuid)
        
        # Configurar cada protocolo según el config.yaml
        for protocol, allowed in protocols_config.items():
            # Convertir el nombre del protocolo a minúsculas por si acaso
            protocol_name = protocol.lower()
            
            # Configurar el protocolo con el valor allowed
            setattr(svm_obj, protocol_name, {'allowed': allowed})
            
            status_text = "enabled" if allowed else "disabled"
            print(f"[*] Protocol {protocol_name.upper()}: {status_text}")
        
        # Aplicar cambios a la SVM
        print(f"[*] Applying protocol changes...")
        svm_obj.patch()
        
        print(f"[+] Protocol configuration applied successfully!")
        
        # GET: Obtener datos reales de la SVM con los protocolos desde la cabina
        print(f"[*] Retrieving protocol configuration from cluster...")
        svm_updated = Svm.find(name=svm_name)
        if svm_updated:
            # Obtener todos los campos de protocolos
            svm_updated.get(fields='nfs,cifs,fcp,iscsi,nvme,s3,ndmp')
            
            # Construir listas de protocolos permitidos y no permitidos
            allowed_protocols = []
            disallowed_protocols = []
            
            # Lista de protocolos conocidos en NetApp ONTAP
            protocol_fields = ['nfs', 'cifs', 'fcp', 'iscsi', 'nvme', 's3', 'ndmp']
            
            for protocol in protocol_fields:
                if hasattr(svm_updated, protocol):
                    protocol_obj = getattr(svm_updated, protocol)
                    if protocol_obj and hasattr(protocol_obj, 'allowed'):
                        if protocol_obj.allowed:
                            allowed_protocols.append(protocol)
                        else:
                            disallowed_protocols.append(protocol)
            
            # Extraer los datos para el show
            svm_data = {
                'vserver_name': svm_name,
                'vserver_uuid': svm_updated.uuid if hasattr(svm_updated, 'uuid') else 'N/A',
                'allowed_protocols': allowed_protocols,
                'disallowed_protocols': disallowed_protocols
            }
            
            # SHOW: Mostrar información como "vserver show -vserver <name> -instance"
            print(f"\n{'='*60}")
            print(f"  Protocol Configuration Show")
            print(f"{'='*60}")
            print(f"                   Vserver: {svm_data['vserver_name']}")
            print(f"              Vserver UUID: {svm_data['vserver_uuid']}")
            print(f"        Allowed Protocols: {', '.join(allowed_protocols) if allowed_protocols else 'none'}")
            print(f"     Disallowed Protocols: {', '.join(disallowed_protocols) if disallowed_protocols else 'none'}")
            print(f"{'='*60}\n")
            
            # Guardar en log con timestamp
            save_to_log('configure_protocols', svm_data)
        else:
            print(f"[WARNING] Could not retrieve protocol configuration")
        
        return True
    
    # CONTROL DE ERRORES
    except NetAppRestError as error:
        print(f"[ERROR] NetApp API error during protocol configuration")
        print(f"[ERROR] HTTP Status: {error.status_code}")
        
        if error.status_code == 400:
            print(f"[ERROR] Bad request - Invalid protocol configuration")
            print(f"[ERROR] Check that protocol names are valid")
        else:
            print(f"[ERROR] Details: {error.http_err_response.http_response.text}")
        
        return False
    
    except Exception as e:
        print(f"[ERROR] Unexpected error during protocol configuration: {type(e).__name__}")
        print(f"[ERROR] Details: {str(e)}")
        return False


def nfs_create(svm_config):
    """
    Crea un servicio NFS en la SVM y lo configura con las versiones de protocolo desde config.yaml
    
    Args:
        svm_config: Diccionario con la configuración de la SVM del config.yaml
    
    Returns:
        bool: True si se creó exitosamente, False si hubo error
    """
    try:
        # Extraer nombre de la SVM del config
        svm_name = svm_config.get('name')
        
        # Extraer parámetros de versiones NFS del config.yaml
        nfs_v3_enabled = svm_config.get('nfs_v3_enabled', True)
        nfs_v40_enabled = svm_config.get('nfs_v40_enabled', True)
        nfs_v41_enabled = svm_config.get('nfs_v41_enabled', True)
        nfs_v41_pnfs_enabled = svm_config.get('nfs_v41_pnfs_enabled', True)
        
        print(f"\n[*] Creating NFS service on SVM: {svm_name}")
        
        # Crear objeto NFS service
        nfs = NfsService()
        nfs.svm = {'name': svm_name}
        nfs.enabled = True
        
        # Configurar el protocolo NFS con las versiones especificadas
        nfs.protocol = {}
        nfs.protocol['v3_enabled'] = nfs_v3_enabled
        nfs.protocol['v40_enabled'] = nfs_v40_enabled
        nfs.protocol['v41_enabled'] = nfs_v41_enabled
        
        # Configurar pNFS (parallel NFS) para v4.1
        if nfs_v41_enabled:
            nfs.protocol['v41_features'] = {}
            nfs.protocol['v41_features']['pnfs_enabled'] = nfs_v41_pnfs_enabled
        
        # Crear el servicio NFS
        print(f"[*] Creating NFS service with the following configuration:")
        print(f"    - NFSv3: {'enabled' if nfs_v3_enabled else 'disabled'}")
        print(f"    - NFSv4.0: {'enabled' if nfs_v40_enabled else 'disabled'}")
        print(f"    - NFSv4.1: {'enabled' if nfs_v41_enabled else 'disabled'}")
        if nfs_v41_enabled:
            print(f"    - NFSv4.1 pNFS: {'enabled' if nfs_v41_pnfs_enabled else 'disabled'}")
        
        nfs.post()
        
        print(f"[+] NFS service created successfully!")
        
        # GET: Obtener datos reales del servicio NFS desde la cabina
        print(f"[*] Retrieving NFS service details from cluster...")
        nfs_service = NfsService.find(svm={'name': svm_name})
        if nfs_service:
            nfs_service.get()
            
            # Extraer los datos para el show
            nfs_data = {
                'vserver_name': svm_name,
                'enabled': nfs_service.enabled if hasattr(nfs_service, 'enabled') else 'N/A',
                'state': nfs_service.state if hasattr(nfs_service, 'state') else 'N/A',
                'svm_uuid': nfs_service.svm.uuid if hasattr(nfs_service.svm, 'uuid') else 'N/A',
                'v3_enabled': 'N/A',
                'v40_enabled': 'N/A',
                'v41_enabled': 'N/A',
                'v41_pnfs_enabled': 'N/A'
            }
            
            # Extraer información del protocolo si está disponible
            if hasattr(nfs_service, 'protocol') and nfs_service.protocol:
                nfs_data['v3_enabled'] = nfs_service.protocol.v3_enabled if hasattr(nfs_service.protocol, 'v3_enabled') else 'N/A'
                nfs_data['v40_enabled'] = nfs_service.protocol.v40_enabled if hasattr(nfs_service.protocol, 'v40_enabled') else 'N/A'
                nfs_data['v41_enabled'] = nfs_service.protocol.v41_enabled if hasattr(nfs_service.protocol, 'v41_enabled') else 'N/A'
                
                if hasattr(nfs_service.protocol, 'v41_features') and nfs_service.protocol.v41_features:
                    nfs_data['v41_pnfs_enabled'] = nfs_service.protocol.v41_features.pnfs_enabled if hasattr(nfs_service.protocol.v41_features, 'pnfs_enabled') else 'N/A'
            
            # SHOW: Mostrar información como "vserver nfs show -vserver <name>"
            print(f"\n{'='*60}")
            print(f"  NFS Service Show")
            print(f"{'='*60}")
            print(f"         Vserver Name: {nfs_data['vserver_name']}")
            print(f"Administrative Status: {'up' if nfs_data['enabled'] else 'down'}")
            print(f"                State: {nfs_data['state']}")
            print(f"             NFSv3: {nfs_data['v3_enabled']}")
            print(f"           NFSv4.0: {nfs_data['v40_enabled']}")
            print(f"           NFSv4.1: {nfs_data['v41_enabled']}")
            print(f"      NFSv4.1 pNFS: {nfs_data['v41_pnfs_enabled']}")
            print(f"{'='*60}\n")
            
            # Guardar en log con timestamp
            save_to_log('nfs_create', nfs_data)
        else:
            print(f"[WARNING] Could not retrieve NFS service details")
        
        return True
    
    # CONTROL DE ERRORES
    except NetAppRestError as error:
        print(f"[ERROR] NetApp API error during NFS creation")
        print(f"[ERROR] HTTP Status: {error.status_code}")
        
        if error.status_code == 409:
            print(f"[ERROR] NFS service may already exist on this SVM")
        elif error.status_code == 400:
            print(f"[ERROR] Bad request - Invalid parameters")
        else:
            print(f"[ERROR] Details: {error.http_err_response.http_response.text}")
        
        return False
    
    except Exception as e:
        print(f"[ERROR] Unexpected error during NFS creation: {type(e).__name__}")
        print(f"[ERROR] Details: {str(e)}")
        return False


# ============================================================================
# EXPORT POLICY CREATION FUNCTION
# ============================================================================

def export_policies(svm_config):
    """
    Crea una export policy en la SVM según config.yaml
    
    Args:
        svm_config: Diccionario con la configuración de la SVM del config.yaml
    
    Returns:
        bool: True si se creó exitosamente, False si hubo error
    """
    try:
        # Extraer nombre de la SVM del config
        svm_name = svm_config.get('name')
        
        # Extraer nombre de la export policy del config.yaml
        policy_name = svm_config.get('export_policy_name', 'default')
        
        print(f"\n[*] Creating export policy on SVM: {svm_name}")
        print(f"[*] Export policy name: {policy_name}")
        
        # Verificar si la export policy ya existe
        existing_policy = ExportPolicy.find(name=policy_name, **{'svm.name': svm_name})
        if existing_policy:
            print(f"[WARNING] Export policy '{policy_name}' already exists on SVM '{svm_name}'")
            print(f"[*] Skipping creation and proceeding with GET...")
        else:
            # Crear objeto Export Policy
            export_policy = ExportPolicy()
            export_policy.name = policy_name
            export_policy.svm = {'name': svm_name}
            
            # Crear la export policy
            print(f"[*] Creating export policy...")
            export_policy.post(hydrate=True)
            
            print(f"[+] Export policy created successfully!")
        
        # GET: Obtener datos reales de las export policies desde la cabina
        print(f"[*] Retrieving export policies from cluster...")
        
        # Obtener todas las export policies de la SVM
        export_policies_list = []
        policies = ExportPolicy.get_collection(**{'svm.name': svm_name})
        
        for policy in policies:
            policy.get()
            policy_data = {
                'policy_name': policy.name if hasattr(policy, 'name') else 'N/A',
                'policy_id': policy.id if hasattr(policy, 'id') else 'N/A',
                'svm_name': svm_name
            }
            export_policies_list.append(policy_data)
        
        # Datos completos para el log
        export_data = {
            'vserver_name': svm_name,
            'total_policies': len(export_policies_list),
            'policies': export_policies_list
        }
        
        # SHOW: Mostrar información como "vserver export-policy show -vserver <name>"
        print(f"\n{'='*60}")
        print(f"  Export Policy Show")
        print(f"{'='*60}")
        print(f"         Vserver Name: {svm_name}")
        print(f"    Total Policies: {len(export_policies_list)}")
        print(f"\n{'Policy Name':<30} {'Policy ID':<15}")
        print(f"{'-'*30} {'-'*15}")
        
        for policy in export_policies_list:
            print(f"{policy['policy_name']:<30} {str(policy['policy_id']):<15}")
        
        print(f"{'='*60}\n")
        
        # Guardar en log con timestamp
        save_to_log('export_policies', export_data)
        
        return True
    
    # CONTROL DE ERRORES
    except NetAppRestError as error:
        print(f"[ERROR] NetApp API error during export policy creation")
        print(f"[ERROR] HTTP Status: {error.status_code}")
        
        if error.status_code == 409:
            print(f"[ERROR] Export policy '{policy_name}' may already exist on this SVM")
        elif error.status_code == 400:
            print(f"[ERROR] Bad request - Invalid parameters")
        else:
            print(f"[ERROR] Details: {error.http_err_response.http_response.text}")
        
        return False
    
    except Exception as e:
        print(f"[ERROR] Unexpected error during export policy creation: {type(e).__name__}")
        print(f"[ERROR] Details: {str(e)}")
        return False


# ============================================================================
# EXPORT POLICY RULES CREATION FUNCTION
# ============================================================================

def export_policy_rules_create(svm_config):
    """
    Crea reglas de export policy para cada política definida en config.yaml
    
    Esta función permite configurar múltiples policies con diferentes reglas.
    Cada policy puede tener atributos completamente diferentes:
    - 'default' puede tener rorule=any, superuser=any, clientmatch=0.0.0.0/0
    - 'rhoso' puede tener rorule=sys, sin superuser, clientmatch=192.168.25.0/24
    
    Args:
        svm_config: Diccionario con la configuración de la SVM del config.yaml
    
    Returns:
        bool: True si todas las reglas se crearon exitosamente, False si hubo error
    """
    try:
        # Extraer nombre de la SVM del config
        svm_name = svm_config.get('name')
        
        # Extraer la configuración de export policy rules del config.yaml
        export_policy_rules_config = svm_config.get('export_policy_rules', [])
        
        if not export_policy_rules_config:
            print(f"[WARNING] No export policy rules defined in config.yaml")
            return True
        
        print(f"\n[*] Creating export policy rules for SVM: {svm_name}")
        
        all_created_rules = []
        
        # PASO 1: ITERAR POR CADA POLICY (default, rhoso, etc.)
        for policy_config in export_policy_rules_config:
            policy_name = policy_config.get('policy_name')
            rules = policy_config.get('rules', [])
            
            print(f"\n[*] Processing policy: {policy_name}")
            
            # PASO 2: ITERAR POR CADA REGLA DE LA POLICY
            # Aquí es donde cada policy puede tener atributos diferentes
            for rule_config in rules:
                # Extraer atributos de la regla (con valores por defecto)
                clientmatch = rule_config.get('clientmatch')
                rorule = rule_config.get('rorule', 'any')  # Default: any
                rwrule = rule_config.get('rwrule', 'any')  # Default: any
                superuser = rule_config.get('superuser')    # Puede ser None
                protocols = rule_config.get('protocols', ['nfs'])
                ruleindex = rule_config.get('ruleindex', 1)
                
                print(f"[*] Creating rule for client: {clientmatch}")
                print(f"    - RO Rule: {rorule}")
                print(f"    - RW Rule: {rwrule}")
                if superuser:
                    print(f"    - Superuser: {superuser}")
                print(f"    - Protocols: {', '.join(protocols)}")
                
                # Buscar el ID de la policy (necesario para crear rules)
                policy = ExportPolicy.find(name=policy_name, **{'svm.name': svm_name})
                if not policy:
                    print(f"[ERROR] Export policy '{policy_name}' not found")
                    return False
                
                # Crear objeto ExportRule
                export_rule = ExportRule(policy.id)  # Requiere policy ID
                export_rule.clients = [{'match': clientmatch}]
                export_rule.ro_rule = [rorule]
                export_rule.rw_rule = [rwrule]
                
                # IMPORTANTE: Solo agregar superuser si está definido
                if superuser:
                    export_rule.superuser = [superuser]
                
                export_rule.protocols = protocols
                export_rule.index = ruleindex
                
                # Crear la regla
                export_rule.post(hydrate=True)
                
                print(f"[+] Rule created successfully!")
                
                # Guardar info de la regla creada
                all_created_rules.append({
                    'policy_name': policy_name,
                    'clientmatch': clientmatch,
                    'rorule': rorule,
                    'rwrule': rwrule,
                    'superuser': superuser if superuser else 'none',
                    'protocols': protocols,
                    'ruleindex': ruleindex
                })
        
        # GET: Obtener todas las reglas creadas desde la cabina
        print(f"\n[*] Retrieving all export policy rules from cluster...")
        
        rules_data = {
            'vserver_name': svm_name,
            'total_policies': len(export_policy_rules_config),
            'policies': []
        }
        
        for policy_config in export_policy_rules_config:
            policy_name = policy_config.get('policy_name')
            
            # Buscar el policy para obtener su ID
            policy = ExportPolicy.find(name=policy_name, **{'svm.name': svm_name})
            if not policy:
                continue
            
            # Obtener reglas de esta policy usando el ID
            rules = ExportRule.get_collection(policy.id)
            
            policy_rules = []
            for rule in rules:
                rule.get()
                
                # Extraer datos de la regla para el show
                policy_rules.append({
                    'index': rule.index if hasattr(rule, 'index') else 'N/A',
                    'clientmatch': rule.clients[0]['match'] if hasattr(rule, 'clients') and rule.clients else 'N/A',
                    'rorule': ', '.join(rule.ro_rule) if hasattr(rule, 'ro_rule') else 'N/A',
                    'rwrule': ', '.join(rule.rw_rule) if hasattr(rule, 'rw_rule') else 'N/A',
                    'superuser': ', '.join(rule.superuser) if hasattr(rule, 'superuser') and rule.superuser else 'none',
                    'protocols': ', '.join(rule.protocols) if hasattr(rule, 'protocols') else 'N/A'
                })
            
            rules_data['policies'].append({
                'policy_name': policy_name,
                'policy_id': policy.id,
                'rules': policy_rules
            })
        
        # SHOW: Mostrar información como "vserver export-policy rule show"
        print(f"\n{'='*90}")
        print(f"  Export Policy Rules Show")
        print(f"{'='*90}")
        
        for policy in rules_data['policies']:
            print(f"\nPolicy: {policy['policy_name']} (ID: {policy['policy_id']})")
            print(f"{'-'*90}")
            print(f"{'Index':<8} {'Client Match':<20} {'RO Rule':<10} {'RW Rule':<10} {'Superuser':<12} {'Protocols':<20}")
            print(f"{'-'*90}")
            
            for rule in policy['rules']:
                print(f"{str(rule['index']):<8} {rule['clientmatch']:<20} {rule['rorule']:<10} {rule['rwrule']:<10} {rule['superuser']:<12} {rule['protocols']:<20}")
        
        print(f"{'='*90}\n")
        
        # Guardar en log con timestamp
        save_to_log('export_policy_rules', rules_data)
        
        return True
    
    # CONTROL DE ERRORES
    except NetAppRestError as error:
        print(f"[ERROR] NetApp API error during export policy rules creation")
        print(f"[ERROR] HTTP Status: {error.status_code}")
        
        if error.status_code == 409:
            print(f"[ERROR] Export rule may already exist at that index")
        elif error.status_code == 400:
            print(f"[ERROR] Bad request - Invalid parameters")
            print(f"[ERROR] Check: policy exists, valid protocols, valid auth methods")
        elif error.status_code == 404:
            print(f"[ERROR] Export policy not found - Create policy first")
        else:
            print(f"[ERROR] Details: {error.http_err_response.http_response.text}")
        
        return False
    
    except Exception as e:
        print(f"[ERROR] Unexpected error during export policy rules creation: {type(e).__name__}")
        print(f"[ERROR] Details: {str(e)}")
        return False


# ============================================================================
# NETWORK INTERFACES CREATION FUNCTION
# ============================================================================

def network_interfaces_create(svm_config):
    """
    Crea network interfaces (LIFs) según config.yaml con total flexibilidad
    
    Permite configurar diferentes tipos de LIFs con atributos específicos:
    - LIF de datos (role=data, data-protocol=nfs)
    - LIF de management (service-policy=default-management)
    - Cada LIF puede tener atributos completamente diferentes
    
    Args:
        svm_config: Diccionario con la configuración de la SVM del config.yaml
    
    Returns:
        bool: True si todas las interfaces se crearon exitosamente, False si hubo error
    """
    try:
        # Extraer nombre de la SVM del config
        svm_name = svm_config.get('name')
        
        # Extraer configuración de network interfaces del config.yaml
        network_interfaces_config = svm_config.get('network_interfaces', [])
        
        if not network_interfaces_config:
            print(f"[WARNING] No network interfaces defined in config.yaml")
            return True
        
        print(f"\n[*] Creating network interfaces for SVM: {svm_name}")
        
        created_lifs = []
        
        # ITERAR POR CADA LIF DEFINIDA EN EL CONFIG
        for lif_config in network_interfaces_config:
            lif_name = lif_config.get('name')
            
            if not lif_name:
                print(f"[ERROR] LIF name is required")
                continue
            
            print(f"\n[*] Creating network interface: {lif_name}")
            
            # Crear objeto IpInterface
            ip_interface = IpInterface()
            ip_interface.name = lif_name
            ip_interface.svm = {'name': svm_name}
            
            # ==============================================================
            # ASIGNACIÓN CONDICIONAL DE ATRIBUTOS
            # Solo se agregan los atributos que existen en el config.yaml
            # ==============================================================
            
            # IP y Subnet (generalmente requeridos)
            if 'address' in lif_config:
                ip_interface.ip = {'address': lif_config['address']}
                print(f"    - Address: {lif_config['address']}")
            
            if 'netmask' in lif_config:
                if not hasattr(ip_interface, 'ip'):
                    ip_interface.ip = {}
                ip_interface.ip['netmask'] = lif_config['netmask']
                print(f"    - Netmask: {lif_config['netmask']}")
            
            # Location (home node y port)
            if 'home_node' in lif_config or 'home_port' in lif_config:
                ip_interface.location = {}
                if 'home_node' in lif_config:
                    ip_interface.location['home_node'] = {'name': lif_config['home_node']}
                    print(f"    - Home Node: {lif_config['home_node']}")
                if 'home_port' in lif_config:
                    ip_interface.location['home_port'] = {'name': lif_config['home_port']}
                    print(f"    - Home Port: {lif_config['home_port']}")
            
            # Broadcast Domain
            if 'broadcast_domain' in lif_config:
                if not hasattr(ip_interface, 'location'):
                    ip_interface.location = {}
                ip_interface.location['broadcast_domain'] = {'name': lif_config['broadcast_domain']}
                print(f"    - Broadcast Domain: {lif_config['broadcast_domain']}")
            
            # Auto Revert
            if 'auto_revert' in lif_config:
                if not hasattr(ip_interface, 'location'):
                    ip_interface.location = {}
                ip_interface.location['auto_revert'] = lif_config['auto_revert']
                print(f"    - Auto Revert: {lif_config['auto_revert']}")
            
            # Service Policy (para LIFs de management)
            # IMPORTANTE: Si se usa service_policy, NO agregar failover manualmente
            if 'service_policy' in lif_config:
                ip_interface.service_policy = {'name': lif_config['service_policy']}
                print(f"    - Service Policy: {lif_config['service_policy']}")
            
            # Failover Policy (SOLO para LIFs sin service_policy)
            # Las LIFs con service_policy gestionan failover automáticamente
            elif 'failover_policy' in lif_config:
                if not hasattr(ip_interface, 'location'):
                    ip_interface.location = {}
                ip_interface.location['failover'] = lif_config['failover_policy']
                print(f"    - Failover Policy: {lif_config['failover_policy']}")
            
            # Scope (solo 'svm' o 'cluster' son válidos)
            # Para LIFs de datos NFS, siempre es 'svm'
            if 'role' in lif_config:
                if lif_config['role'] == 'data':
                    ip_interface.scope = 'svm'
                    print(f"    - Scope: svm (data LIF)")
                else:
                    # Para otros tipos de LIFs
                    ip_interface.scope = 'svm'  # Default
                    print(f"    - Role: {lif_config['role']}")
            
            # Data Protocol (services para LIFs de datos)
            if 'data_protocol' in lif_config:
                # Mapeo de protocolos CLI a services API
                protocol_map = {
                    'nfs': 'data-nfs',
                    'cifs': 'data-cifs',
                    'iscsi': 'data-iscsi',
                    'fcp': 'data-fcp'
                }
                protocol = lif_config['data_protocol']
                service_name = protocol_map.get(protocol, f'data-{protocol}')
                ip_interface.services = [service_name]
                print(f"    - Data Protocol: {protocol} (service: {service_name})")
            
            # Enabled (status-admin)
            if 'status_admin' in lif_config:
                ip_interface.enabled = (lif_config['status_admin'] == 'up')
                print(f"    - Status Admin: {lif_config['status_admin']}")
            
            
            # Crear la LIF
            print(f"\n[*] Creating network interface...")
            ip_interface.post(hydrate=True)
            
            print(f"[+] Network interface '{lif_name}' created successfully!")
            created_lifs.append(lif_name)
        
        # GET: Obtener todas las LIFs desde la cabina
        print(f"\n[*] Retrieving all network interfaces from cluster...")
        
        lifs_data = {
            'vserver_name': svm_name,
            'total_lifs': 0,
            'lifs': []
        }
        
        # Obtener todas las LIFs de la SVM
        lifs = IpInterface.get_collection(**{'svm.name': svm_name})
        
        for lif in lifs:
            lif.get()
            
            lif_info = {
                'name': lif.name if hasattr(lif, 'name') else 'N/A',
                'address': 'N/A',
                'netmask': 'N/A',
                'home_node': 'N/A',
                'home_port': 'N/A',
                'current_node': 'N/A',
                'current_port': 'N/A',
                'status_admin': 'N/A',
                'status_oper': 'N/A',
                'failover': 'N/A',
                'auto_revert': 'N/A',
                'service_policy': 'N/A',
                'services': 'N/A'
            }
            
            # Extraer IP info
            if hasattr(lif, 'ip') and lif.ip:
                if hasattr(lif.ip, 'address'):
                    lif_info['address'] = lif.ip.address
                if hasattr(lif.ip, 'netmask'):
                    lif_info['netmask'] = lif.ip.netmask
            
            # Extraer location info
            if hasattr(lif, 'location') and lif.location:
                if hasattr(lif.location, 'home_node') and lif.location.home_node:
                    lif_info['home_node'] = lif.location.home_node.name
                if hasattr(lif.location, 'home_port') and lif.location.home_port:
                    lif_info['home_port'] = lif.location.home_port.name
                if hasattr(lif.location, 'node') and lif.location.node:
                    lif_info['current_node'] = lif.location.node.name
                if hasattr(lif.location, 'port') and lif.location.port:
                    lif_info['current_port'] = lif.location.port.name
                if hasattr(lif.location, 'failover'):
                    lif_info['failover'] = lif.location.failover
                if hasattr(lif.location, 'auto_revert'):
                    lif_info['auto_revert'] = lif.location.auto_revert
            
            # Extraer status
            if hasattr(lif, 'enabled'):
                lif_info['status_admin'] = 'up' if lif.enabled else 'down'
            if hasattr(lif, 'state'):
                lif_info['status_oper'] = lif.state
            
            # Extraer service policy
            if hasattr(lif, 'service_policy') and lif.service_policy:
                if hasattr(lif.service_policy, 'name'):
                    lif_info['service_policy'] = lif.service_policy.name
            
            # Extraer services
            if hasattr(lif, 'services') and lif.services:
                lif_info['services'] = ', '.join(lif.services)
            
            lifs_data['lifs'].append(lif_info)
        
        lifs_data['total_lifs'] = len(lifs_data['lifs'])
        
        # SHOW: Mostrar información como "network interface show -vserver <name>"
        print(f"\n{'='*120}")
        print(f"  Network Interface Show")
        print(f"{'='*120}")
        print(f"Vserver: {svm_name}")
        print(f"{'='*120}")
        print(f"{'LIF Name':<15} {'Address':<16} {'Home Node':<15} {'Home Port':<12} {'Status':<8} {'Failover':<15} {'Services':<20}")
        print(f"{'-'*120}")
        
        for lif in lifs_data['lifs']:
            print(f"{lif['name']:<15} {lif['address']:<16} {lif['home_node']:<15} {lif['home_port']:<12} {lif['status_admin']:<8} {lif['failover']:<15} {lif['services']:<20}")
        
        print(f"\nTotal LIFs: {lifs_data['total_lifs']}")
        print(f"{'='*120}\n")
        
        # Guardar en log con timestamp
        save_to_log('network_interfaces', lifs_data)
        
        return True
    
    # CONTROL DE ERRORES
    except NetAppRestError as error:
        print(f"[ERROR] NetApp API error during network interface creation")
        print(f"[ERROR] HTTP Status: {error.status_code}")
        
        if error.status_code == 409:
            print(f"[ERROR] Network interface may already exist")
        elif error.status_code == 400:
            print(f"[ERROR] Bad request - Invalid parameters")
            print(f"[ERROR] Check: valid IP, node exists, port exists, broadcast domain")
        elif error.status_code == 404:
            print(f"[ERROR] Resource not found - Check node/port/broadcast-domain names")
        else:
            # Manejar caso donde http_err_response puede ser None (errores de validación)
            if error.http_err_response and hasattr(error.http_err_response, 'http_response'):
                print(f"[ERROR] Details: {error.http_err_response.http_response.text}")
            else:
                print(f"[ERROR] Details: {str(error)}")
        
        return False
    
    except Exception as e:
        print(f"[ERROR] Unexpected error during network interface creation: {type(e).__name__}")
        print(f"[ERROR] Details: {str(e)}")
        return False


# ============================================================================
# EVENT LOG RETRIEVAL FUNCTION
# ============================================================================

def get_event_logs(max_records=100):
    """
    Obtiene los logs de eventos del sistema NetApp ONTAP
    
    Args:
        max_records: Número máximo de eventos a recuperar (default: 100)
    
    Returns:
        bool: True si se obtuvieron exitosamente, False si hubo error
    """
    try:
        print(f"\n[*] Retrieving event logs from cluster...")
        
        # GET: Obtener eventos del sistema desde la cabina
        events_list = []
        ems_events = EmsEvent.get_collection(max_records=max_records)
        
        for event in ems_events:
            event_data = {
                'index': event.index if hasattr(event, 'index') else 'N/A',
                'time': str(event.time) if hasattr(event, 'time') else 'N/A',
                'node': event.node.name if hasattr(event, 'node') and event.node else 'N/A',
                'severity': event.message.severity if hasattr(event, 'message') and hasattr(event.message, 'severity') else 'N/A',
                'event': event.message.name if hasattr(event, 'message') and hasattr(event.message, 'name') else 'N/A'
            }
            events_list.append(event_data)
        
        event_log_data = {
            'total_events': len(events_list),
            'max_records_requested': max_records,
            'events': events_list
        }
        
        # SHOW: Mostrar información como "event log show"
        print(f"\n{'='*110}")
        print(f"  Event Log Show")
        print(f"{'='*110}")
        print(f"{'Index':<8} {'Time':<25} {'Node':<20} {'Severity':<12} {'Event':<40}")
        print(f"{'-'*8} {'-'*25} {'-'*20} {'-'*12} {'-'*40}")
        
        for evt in events_list[:20]:  # Mostrar solo los primeros 20 en pantalla
            print(f"{str(evt['index']):<8} {evt['time']:<25} {evt['node']:<20} {evt['severity']:<12} {evt['event']:<40}")
        
        if len(events_list) > 20:
            print(f"... ({len(events_list) - 20} more events)")
        
        print(f"\nTotal events retrieved: {len(events_list)}")
        print(f"{'='*110}\n")
        
        # Guardar en log con timestamp
        save_to_log('event_logs', event_log_data)
        
        return True
    
    # CONTROL DE ERRORES
    except NetAppRestError as error:
        print(f"[ERROR] NetApp API error during event log retrieval")
        print(f"[ERROR] HTTP Status: {error.status_code}")
        if error.http_err_response and error.http_err_response.http_response:
            print(f"[ERROR] Details: {error.http_err_response.http_response.text}")
        else:
            print(f"[ERROR] Details: {str(error)}")
        return False
    
    except Exception as e:
        print(f"[ERROR] Unexpected error during event log retrieval: {type(e).__name__}")
        print(f"[ERROR] Details: {str(e)}")
        return False

# ============================================================================
# CALLING WORKFLOW
# ============================================================================

# CONFIG YAML LOADER
# Cargar la configuración desde el archivo YAML
config_data = config_loader()

# Verificar que la configuración se cargó exitosamente
if config_data is None:
    print("\n[ERROR] Cannot continue without valid configuration")
    print("[ERROR] Check the config.yaml file and try again")
    exit(1)
else:
    print("\n[SUCCESS] Configuration loaded - Proceeding with pre-checks")

# CLUSTER CONNECTION CHECK
# Establecer conexión y verificar acceso a la cabina NetApp
if not cluster_connection(config_data['cluster']):
    print("\n[ERROR] Failed to connect to NetApp cluster")
    print("[ERROR] Fix connection issues before continuing")
    exit(1)

print("\n[+] All pre-checks passed - Ready to create SVM")

# SVM CREATION STEPS
# Crear la SVM
if create_svm(config_data['svm']):
    print("\n[SUCCESS] SVM creation completed!")
else:
    print("\n[FAILED] SVM creation failed")
    exit(1)

# Modificar la SVM
if modify_svm(config_data['svm']):
    print("\n[SUCCESS] SVM modification completed!")
else:
    print("\n[FAILED] SVM modification failed")
    exit(1)

# NFS SERVICE CREATION STEPS
# Configurar protocolos permitidos en la SVM
if configure_protocols(config_data['svm']):
    print("\n[SUCCESS] Protocol configuration completed!")
else:
    print("\n[FAILED] Protocol configuration failed")
    exit(1)

# Crear el servicio NFS en la SVM
if nfs_create(config_data['svm']):
    print("\n[SUCCESS] NFS service creation completed!")
else:
    print("\n[FAILED] NFS service creation failed")
    exit(1)

# Crear export policy
if export_policies(config_data['svm']):
    print("\n[SUCCESS] Export policy creation completed!")
else:
    print("\n[FAILED] Export policy creation failed")
    exit(1)

# Crear reglas de export policy
if export_policy_rules_create(config_data['svm']):
    print("\n[SUCCESS] Export policy rules creation completed!")
else:
    print("\n[FAILED] Export policy rules creation failed")
    exit(1)

# Crear network interfaces (LIFs)
if network_interfaces_create(config_data['svm']):
    print("\n[SUCCESS] Network interfaces creation completed!")
else:
    print("\n[FAILED] Network interfaces creation failed")
    exit(1)

# LOGS
# Obtener event logs de la cabina como backup
if get_event_logs(max_records=100):
    print("\n[SUCCESS] Event logs backup completed!")
else:
    print("\n[WARNING] Event logs backup failed (non-critical)")
