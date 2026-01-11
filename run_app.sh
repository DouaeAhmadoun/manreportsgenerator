#!/bin/bash
echo "🚀 Démarrage de l'application de génération de rapports"
echo ""
python -m streamlit run main.py --server.port 8501 --server.address 0.0.0.0
