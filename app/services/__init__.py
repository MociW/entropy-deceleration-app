"""Services package — business logic layer.

Each module maps 1-to-1 with an API router domain:

    app/services/research.py  ←→  app/api/routers/research.py
    app/services/config.py    ←→  app/api/routers/config.py

Routers delegate all business logic here.
The service layer orchestrates calls to app/util/* (pipeline, keyword_store).
"""
