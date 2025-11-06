"""
Manejo personalizado de excepciones para la API REST de AeroEFI

Este módulo contiene manejadores de excepciones personalizados que proporcionan
respuestas HTTP adecuadas y mensajes de error consistentes.
"""
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import Http404
from django.db import IntegrityError
import logging

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Manejador personalizado de excepciones que proporciona respuestas
    HTTP consistentes y mensajes de error detallados.
    """
    # Llamar al manejador por defecto de DRF primero
    response = exception_handler(exc, context)
    
    # Si DRF no pudo manejar la excepción, manejamos casos específicos
    if response is None:
        if isinstance(exc, Http404):
            custom_response_data = {
                'error': 'Not Found',
                'message': 'El recurso solicitado no fue encontrado.',
                'status_code': 404
            }
            return Response(custom_response_data, status=status.HTTP_404_NOT_FOUND)
        
        elif isinstance(exc, DjangoValidationError):
            custom_response_data = {
                'error': 'Validation Error',
                'message': 'Los datos proporcionados no son válidos.',
                'details': exc.messages if hasattr(exc, 'messages') else str(exc),
                'status_code': 400
            }
            return Response(custom_response_data, status=status.HTTP_400_BAD_REQUEST)
        
        elif isinstance(exc, IntegrityError):
            custom_response_data = {
                'error': 'Integrity Error',
                'message': 'Error de integridad en la base de datos. Posible duplicación de datos.',
                'status_code': 400
            }
            return Response(custom_response_data, status=status.HTTP_400_BAD_REQUEST)
        
        else:
            # Para otras excepciones no manejadas, devolver error 500
            logger.exception('Unhandled exception in API')
            custom_response_data = {
                'error': 'Internal Server Error',
                'message': 'Ocurrió un error interno del servidor. Por favor, inténtelo más tarde.',
                'status_code': 500
            }
            return Response(custom_response_data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    # Personalizar la respuesta de DRF para hacerla más consistente
    if response is not None:
        custom_response_data = {
            'error': get_error_type(response.status_code),
            'message': get_error_message(response.status_code),
            'status_code': response.status_code
        }
        
        # Agregar detalles específicos si están disponibles
        if hasattr(response, 'data') and response.data:
            if isinstance(response.data, dict):
                # Para errores de validación, incluir detalles específicos
                if 'non_field_errors' in response.data:
                    custom_response_data['details'] = response.data['non_field_errors']
                else:
                    custom_response_data['field_errors'] = response.data
            elif isinstance(response.data, list):
                custom_response_data['details'] = response.data
            else:
                custom_response_data['details'] = str(response.data)
        
        response.data = custom_response_data
    
    return response


def get_error_type(status_code):
    """Obtiene el tipo de error basado en el código de estado HTTP"""
    error_types = {
        400: 'Bad Request',
        401: 'Unauthorized',
        403: 'Forbidden',
        404: 'Not Found',
        405: 'Method Not Allowed',
        406: 'Not Acceptable',
        409: 'Conflict',
        410: 'Gone',
        422: 'Unprocessable Entity',
        429: 'Too Many Requests',
        500: 'Internal Server Error',
        502: 'Bad Gateway',
        503: 'Service Unavailable',
        504: 'Gateway Timeout',
    }
    return error_types.get(status_code, 'Unknown Error')


def get_error_message(status_code):
    """Obtiene un mensaje de error descriptivo basado en el código de estado HTTP"""
    messages = {
        400: 'La solicitud contiene datos inválidos o malformados.',
        401: 'Credenciales de autenticación no proporcionadas o inválidas.',
        403: 'No tienes permisos suficientes para realizar esta acción.',
        404: 'El recurso solicitado no fue encontrado.',
        405: 'Método HTTP no permitido para este endpoint.',
        406: 'El formato solicitado no es aceptable.',
        409: 'Conflicto con el estado actual del recurso.',
        410: 'El recurso ya no está disponible.',
        422: 'Los datos son válidos pero no pueden ser procesados.',
        429: 'Demasiadas solicitudes. Por favor, inténtalo más tarde.',
        500: 'Error interno del servidor.',
        502: 'Error en el servidor upstream.',
        503: 'El servicio no está disponible temporalmente.',
        504: 'Timeout del servidor upstream.',
    }
    return messages.get(status_code, 'Ha ocurrido un error desconocido.')


class APIException(Exception):
    """Excepción personalizada para la API"""
    
    def __init__(self, message, status_code=400, error_type=None):
        self.message = message
        self.status_code = status_code
        self.error_type = error_type or get_error_type(status_code)
        super().__init__(self.message)


class BusinessLogicError(APIException):
    """Excepción para errores de lógica de negocio"""
    
    def __init__(self, message, status_code=422):
        super().__init__(message, status_code, 'Business Logic Error')


class ResourceNotFoundError(APIException):
    """Excepción para recursos no encontrados"""
    
    def __init__(self, message="Recurso no encontrado", status_code=404):
        super().__init__(message, status_code, 'Resource Not Found')


class ValidationError(APIException):
    """Excepción para errores de validación"""
    
    def __init__(self, message, field_errors=None, status_code=400):
        super().__init__(message, status_code, 'Validation Error')
        self.field_errors = field_errors or {}


class PermissionDeniedError(APIException):
    """Excepción para errores de permisos"""
    
    def __init__(self, message="Permisos insuficientes", status_code=403):
        super().__init__(message, status_code, 'Permission Denied')