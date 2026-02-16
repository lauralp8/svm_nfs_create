#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NetApp ONTAP SVM Creation and Configuration Script

This script automates the creation and configuration of Storage Virtual Machines (SVMs)
on NetApp ONTAP systems using the NetApp ONTAP REST API Python Client Library.

Features:
    - SVM creation with custom parameters
    - FCP service configuration
    - Multiple network interfaces (FCP LIFs)
    - Management interface creation
    - Protocol configuration
    - Comprehensive error handling and validation

Requirements:
    - NetApp ONTAP 9.6+
    - Python 3.7+
    - netapp-ontap library
    - PyYAML library

Author: NetApp ONTAP Automation
Version: 1.0.0
"""

# ============================================================================
# IMPORTS
# ============================================================================
from netapp_ontap import config, HostConnection, NetAppRestError
from netapp_ontap.resources import Cluster, Svm, FcpService, FcInterface, IpInterface, EmsEvent, Account
import yaml
import json
import os
from datetime import datetime


# ============================================================================
# SCRIPT INITIALIZATION
# ============================================================================
print("\n" + "="*70)
print("  NetApp ONTAP FCP SVM Creation Script")
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
# RBAC MANAGEMENT FUNCTIONS
# ============================================================================

def login_create(config_data, user_config_key='rbac_user'):
    """
    Crea un usuario RBAC en la SVM especificada usando la API REST de NetApp ONTAP
    con soporte para múltiples aplicaciones (http, ssh, ontapi)
        
    Args:
        config_data: Diccionario con la configuración completa del archivo YAML
                    Debe contener:
                    - config_data['svm']['name']: Nombre de la SVM
                    - config_data[user_config_key]['name']: Nombre del usuario
                    - config_data[user_config_key]['applications']: Lista de aplicaciones (http, ssh, ontapi, etc.)
                    - config_data[user_config_key]['authentication_method']: Método de autenticación
                    - config_data[user_config_key]['role']: Rol RBAC
                    - config_data[user_config_key]['password']: Contraseña del usuario
        user_config_key: Clave del diccionario config_data que contiene la configuración del usuario
                        Por defecto 'rbac_user'
    
    Returns:
        bool: True si el usuario se creó exitosamente, False si hubo error
    """
    try:
        print(f"\n[*] Creating RBAC user account ({user_config_key})...")
        
        # Extraer configuración del usuario RBAC
        user_config = config_data.get(user_config_key, {})
        svm_name = config_data.get('svm', {}).get('name')
        
        # Validar que existan todos los campos necesarios
        required_fields = ['name', 'applications', 'authentication_method', 'role', 'password']
        missing_fields = [field for field in required_fields if field not in user_config]
        
        if missing_fields:
            print(f"[ERROR] Missing required fields in {user_config_key} config: {', '.join(missing_fields)}")
            return False
        
        # Validar que applications sea una lista
        if not isinstance(user_config['applications'], list) or len(user_config['applications']) == 0:
            print(f"[ERROR] 'applications' must be a non-empty list")
            return False
        
        if not svm_name:
            print(f"[ERROR] SVM name not found in configuration")
            return False
        
        # Obtener UUID de la SVM
        print(f"[*] Looking up SVM UUID for: {svm_name}")
        svm = Svm.find(name=svm_name)
        
        if not svm:
            print(f"[ERROR] SVM '{svm_name}' not found in cluster")
            return False
        
        print(f"[+] SVM found - UUID: {svm.uuid}")
        
        # Crear objeto Account con los parámetros del config.yaml
        apps_str = ', '.join(user_config['applications'])
        print(f"[*] Creating user '{user_config['name']}' with applications [{apps_str}] in SVM '{svm_name}'...")
        
        account = Account()
        account.name = user_config['name']
        account.owner = {"uuid": svm.uuid}
        
        # Crear lista de aplicaciones - cada aplicación con el mismo método de autenticación
        account.applications = [
            {
                "application": app,
                "authentication_methods": [user_config['authentication_method']]
            }
            for app in user_config['applications']
        ]
        
        account.role = {"name": user_config['role']}
        account.password = user_config['password']
        
        # POST: Crear el usuario en la cabina NetApp con todas las aplicaciones
        account.post()
        
        print(f"[+] User account created successfully!")
        
        # OBTENER TODOS LOS USUARIOS DE LA SVM (security login show -vserver svm_1_cluster)
        print(f"\n[*] Retrieving all user accounts from SVM '{svm_name}'...")
        
        # GET: Obtener todos los usuarios de la SVM
        all_accounts = Account.get_collection(**{"owner.uuid": svm.uuid})
        
        users_list = []
        for account in all_accounts:
            account.get()  # Obtener detalles completos de cada cuenta
            
            user_info = {
                'name': account.name,
                'role': account.role.name if hasattr(account, 'role') else 'N/A',
                'locked': account.locked if hasattr(account, 'locked') else False,
                'comment': account.comment if hasattr(account, 'comment') else None,
                'applications': []
            }
            
            # Obtener cada aplicación y método de autenticación
            if hasattr(account, 'applications') and account.applications:
                for app in account.applications:
                    user_info['applications'].append({
                        'application': app.application if hasattr(app, 'application') else 'N/A',
                        'authentication_methods': list(app.authentication_methods) if hasattr(app, 'authentication_methods') else []
                    })
            
            users_list.append(user_info)
        
        # SHOW: Mostrar información como "security login show -vserver svm_1_cluster"
        print(f"\n{'='*130}")
        print(f"  Security Login Show - Vserver: {svm_name}")
        print(f"{'='*130}")
        print(f"{'User/Group':<20} {'Application':<15} {'Authentication':<20} {'Role':<15} {'Locked':<10} {'Comment':<30}")
        print(f"{'-'*20} {'-'*15} {'-'*20} {'-'*15} {'-'*10} {'-'*30}")
        
        for user in users_list:
            if user['applications']:
                # Mostrar cada aplicación en una línea separada
                for i, app in enumerate(user['applications']):
                    user_name = user['name'] if i == 0 else ''
                    role_name = user['role'] if i == 0 else ''
                    locked_status = str(user['locked']).lower() if i == 0 else ''
                    comment = user['comment'] if i == 0 and user['comment'] else ''
                    
                    app_name = app['application']
                    auth_method = ', '.join(app['authentication_methods'])
                    
                    print(f"{user_name:<20} {app_name:<15} {auth_method:<20} {role_name:<15} {locked_status:<10} {comment:<30}")
            else:
                # Usuario sin aplicaciones
                print(f"{user['name']:<20} {'N/A':<15} {'N/A':<20} {user['role']:<15} {str(user['locked']).lower():<10} {user['comment'] if user['comment'] else '':<30}")
        
        print(f"{'='*130}\n")
        print(f"[+] Total users in SVM '{svm_name}': {len(users_list)}")
        
        # Preparar datos para guardar en log con el show completo de la SVM
        security_login_data = {
            'operation': 'security_login_show',
            'svm_name': svm_name,
            'svm_uuid': svm.uuid,
            'total_users': len(users_list),
            'users': users_list,
            'created_user': user_config['name']  # Marcar cuál fue el usuario recién creado
        }
        
        # Guardar en log con timestamp
        log_name = f"security_login_show_{svm_name}"
        save_to_log(log_name, security_login_data)
        
        return True
    
    # CONTROL DE ERRORES
    except NetAppRestError as error:
        print(f"[ERROR] NetApp API error during user creation")
        print(f"[ERROR] HTTP Status: {error.status_code}")
        
        # Detallar el tipo de error según el código HTTP
        if error.status_code == 409:
            print(f"[ERROR] User '{user_config.get('name', 'N/A')}' already exists")
        elif error.status_code == 400:
            print(f"[ERROR] Invalid parameters")
        elif error.status_code == 403:
            print(f"[ERROR] Forbidden - Insufficient permissions")
        
        if error.http_err_response and error.http_err_response.http_response:
            print(f"[ERROR] Details: {error.http_err_response.http_response.text}")
        else:
            print(f"[ERROR] Details: {str(error)}")
        return False
    
    except Exception as e:
        print(f"[ERROR] Unexpected error during user creation: {type(e).__name__}")
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

print("\n[+] All pre-checks passed - Ready to create RBAC users")

# RBAC CREATION STEPS
# Crear usuario RBAC con múltiples aplicaciones (http, ssh, ontapi)
if login_create(config_data, 'rbac_user'):
    print("\n[SUCCESS] RBAC user created successfully with all applications!")
else:
    print("\n[ERROR] Failed to create RBAC user")
    print("[ERROR] Check the error messages above for details")
    exit(1)

# LOGS BACKUP
# Obtener event logs de la cabina como backup
if get_event_logs(max_records=100):
    print("\n[SUCCESS] Event logs backup completed!")
else:
    print("\n[WARNING] Event logs backup failed (non-critical)")
