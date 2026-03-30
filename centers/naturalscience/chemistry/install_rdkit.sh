#!/bin/bash
# Install RDKit for ChemistryAI4S | Γ
# Memory-efficient installation for 4GB RAM system

echo "Installing RDKit (lightweight)..."

# Option 1: pip (memory efficient)
pip install rdkit-pypi --quiet

# Verify installation
python3 -c "from rdkit import Chem; print('RDKit version:', Chem.__version__)" && \
    echo "✓ RDKit installed successfully" || \
    echo "✗ Installation failed"