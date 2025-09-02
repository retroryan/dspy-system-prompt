"""
Configuration management endpoints.

Handles system configuration retrieval and updates.
"""

import logging
from datetime import datetime

from fastapi import APIRouter, HTTPException, status, Depends
from api.core.config_models import ConfigResponse, ConfigUpdateRequest
from api.core.config_manager import ConfigManager
from api.core.dependencies import get_config_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/config", tags=["Configuration"])


@router.get("/{section}", response_model=ConfigResponse)
def get_config(
    section: str,
    config_manager: ConfigManager = Depends(get_config_manager)
):
    """
    Get configuration for a section.
    
    Retrieves the current configuration settings for the specified
    section (llm, agent, tools, api).
    
    Args:
        section: Configuration section name
        
    Returns:
        Configuration values for the section
        
    Raises:
        404: Unknown configuration section
    """
    valid_sections = ["llm", "agent", "tools", "api"]
    
    if section not in valid_sections:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unknown configuration section: {section}. Valid sections: {valid_sections}"
        )
    
    try:
        config = config_manager.get_config(section)
        
        return ConfigResponse(
            section=section,
            config=config,
            updated_at=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Failed to get config for section {section}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve configuration: {str(e)}"
        )


@router.post("/{section}", response_model=ConfigResponse)
def update_config(
    section: str,
    request: ConfigUpdateRequest,
    config_manager: ConfigManager = Depends(get_config_manager)
):
    """
    Update configuration for a section.
    
    Updates the configuration settings for the specified section.
    The configuration is validated against the section's schema
    before being saved.
    
    Args:
        section: Configuration section name
        request: Configuration update data
        
    Returns:
        Updated configuration values
        
    Raises:
        400: Invalid configuration data
        404: Unknown configuration section
    """
    valid_sections = ["llm", "agent", "tools", "api"]
    
    if section not in valid_sections:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unknown configuration section: {section}. Valid sections: {valid_sections}"
        )
    
    # Validate that section in request matches URL
    if request.section != section:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Section mismatch: URL section '{section}' != request section '{request.section}'"
        )
    
    try:
        updated_config = config_manager.update_config(section, request.config)
        
        logger.info(f"Configuration updated for section: {section}")
        
        return ConfigResponse(
            section=section,
            config=updated_config,
            updated_at=datetime.now().isoformat()
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to update config for section {section}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update configuration: {str(e)}"
        )