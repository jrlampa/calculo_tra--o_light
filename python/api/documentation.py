"""API documentation configuration and enhancements."""
from __future__ import annotations

from typing import Dict, Any
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi


def custom_openapi_schema(app: FastAPI) -> Dict[str, Any]:
    """Generate custom OpenAPI schema with enhanced documentation."""
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="Cálculo de Tração API",
        version="2.0.0",
        description="""
        ## API para Cálculo de Tração de Redes Elétricas
        
        Esta API fornece endpoints para:
        - **Gerenciamento de Projetos**: CRUD de projetos e pontos
        - **Cálculos**: Processamento de tração e tensões
        - **Autenticação**: Login, registro e sessões
        - **Administração**: Operações administrativas
        - **Dados Públicos**: Lookup de cabos, postes e estruturas
        
        ### Autenticação
        A maioria dos endpoints requer autenticação via token JWT.
        
        ### Rate Limiting
        - 60 requisições por minuto
        - 1000 requisições por hora
        
        ### Formato de Resposta
        Todas as respostas seguem o formato:
        ```json
        {
            "data": { ... },
            "error": null,
            "message": "Success"
        }
        ```
        """,
        routes=app.routes,
    )
    
    # Add custom schemas
    openapi_schema["components"]["schemas"]["ErrorResponse"] = {
        "type": "object",
        "properties": {
            "error": {
                "type": "string",
                "description": "Error code"
            },
            "message": {
                "type": "string", 
                "description": "Error description"
            },
            "type": {
                "type": "string",
                "description": "Error type"
            }
        },
        "required": ["error", "message"]
    }
    
    openapi_schema["components"]["schemas"]["SuccessResponse"] = {
        "type": "object",
        "properties": {
            "data": {
                "type": "object",
                "description": "Response data"
            },
            "message": {
                "type": "string",
                "description": "Success message"
            }
        },
        "required": ["data"]
    }
    
    # Add security schemes
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "JWT authentication token"
        }
    }
    
    # Add global security
    openapi_schema["security"] = [{"BearerAuth": []}]
    
    # Add tags descriptions
    openapi_schema["tags"] = [
        {
            "name": "Projetos",
            "description": "Gerenciamento de projetos de cálculo de tração"
        },
        {
            "name": "Cálculo",
            "description": "Endpoints para processamento de cálculos"
        },
        {
            "name": "Public",
            "description": "Endpoints públicos para lookup de dados"
        },
        {
            "name": "Admin",
            "description": "Endpoints administrativos"
        },
        {
            "name": "Health",
            "description": "Verificação de saúde do sistema"
        },
        {
            "name": "Authentication",
            "description": "Autenticação e gerenciamento de usuários"
        }
    ]
    
    # Add servers
    openapi_schema["servers"] = [
        {
            "url": "http://localhost:8000",
            "description": "Development server"
        },
        {
            "url": "https://api.calculo-tracao.com",
            "description": "Production server"
        }
    ]
    
    # Add contact and license info
    openapi_schema["info"]["contact"] = {
        "name": "API Support",
        "email": "support@calculo-tracao.com",
        "url": "https://calculo-tracao.com/support"
    }
    
    openapi_schema["info"]["license"] = {
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT"
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema


def setup_api_documentation(app: FastAPI) -> None:
    """Setup enhanced API documentation."""
    app.openapi = lambda: custom_openapi_schema(app)
    
    # Add custom documentation endpoints
    @app.get("/docs", include_in_schema=False)
    async def custom_swagger_ui_html():
        """Custom Swagger UI."""
        from fastapi.responses import HTMLResponse
        
        return HTMLResponse("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Cálculo de Tração API - Documentation</title>
            <link rel="stylesheet" type="text/css" href="https://unpkg.com/swagger-ui-dist@3.52.5/swagger-ui.css" >
            <style>
                html { box-sizing: border-box; overflow: -moz-scrollbars-vertical; overflow-y: scroll; }
                *, *:before, *:after { box-sizing: inherit; }
                body { margin:0; background: #fafafa; }
            </style>
        </head>
        <body>
            <div id="swagger-ui"></div>
            <script src="https://unpkg.com/swagger-ui-dist@3.52.5/swagger-ui-bundle.js"></script>
            <script src="https://unpkg.com/swagger-ui-dist@3.52.5/swagger-ui-standalone-preset.js"></script>
            <script>
                window.onload = function() {
                    const ui = SwaggerUIBundle({
                        url: '/openapi.json',
                        dom_id: '#swagger-ui',
                        deepLinking: true,
                        presets: [
                            SwaggerUIBundle.presets.apis,
                            SwaggerUIStandalonePreset
                        ],
                        plugins: [
                            SwaggerUIBundle.plugins.DownloadUrl
                        ],
                        layout: "StandaloneLayout",
                        defaultModelsExpandDepth: 2,
                        defaultModelExpandDepth: 2,
                        displayRequestDuration: true,
                        filter: true,
                        showExtensions: true,
                        showCommonExtensions: true,
                        docExpansion: "none",
                        tryItOutEnabled: true
                    });
                };
            </script>
        </body>
        </html>
        """)
    
    @app.get("/redoc", include_in_schema=False)
    async def redoc_html():
        """ReDoc documentation."""
        from fastapi.responses import HTMLResponse
        
        return HTMLResponse("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Cálculo de Tração API - ReDoc</title>
            <meta charset="utf-8"/>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <link href="https://fonts.googleapis.com/css?family=Montserrat:300,400,700|Roboto:300,400,700" rel="stylesheet">
            <style>
                body { margin: 0; padding: 0; }
            </style>
        </head>
        <body>
            <redoc spec-url='/openapi.json'></redoc>
            <script src="https://cdn.jsdelivr.net/npm/redoc@2.0.0/bundles/redoc.standalone.js"></script>
        </body>
        </html>
        """)
