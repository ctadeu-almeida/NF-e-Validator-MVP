# -*- coding: utf-8 -*-
"""
Test Agent - Verificar se Agente IA funciona

Usage:
    python tests/test_agent.py
"""

import sys
from pathlib import Path
import os

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'src'))

from repositories.fiscal_repository import FiscalRepository
from agents.ncm_agent import create_ncm_agent


def test_agent():
    """Test LangChain ReAct Agent"""

    print("\n" + "=" * 80)
    print("TESTE DO AGENTE IA - NCM CLASSIFICATION")
    print("=" * 80 + "\n")

    # Check API key
    api_key = os.getenv('GOOGLE_API_KEY')

    if not api_key:
        print("[ERROR] GOOGLE_API_KEY não configurada!")
        print("\nPara configurar:")
        print("Windows PowerShell: $env:GOOGLE_API_KEY = 'your-key'")
        print("Linux/Mac: export GOOGLE_API_KEY='your-key'")
        return False

    print(f"[OK] API Key encontrada: {api_key[:10]}...")

    # Initialize repository
    print("\n[1/3] Inicializando Repository...")
    try:
        repo = FiscalRepository()
        print(f"      Database version: {repo.get_database_version()}")
    except Exception as e:
        print(f"[ERROR] Erro ao carregar repository: {e}")
        return False

    # Initialize agent
    print("\n[2/3] Inicializando Agente IA (Gemini 2.5)...")
    try:
        agent = create_ncm_agent(repo, api_key)
        print("      [OK] Agente criado com sucesso")
    except Exception as e:
        print(f"[ERROR] Erro ao criar agente: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Test classifications
    print("\n[3/3] Testando Classificações...")

    test_cases = [
        {
            'description': 'Açúcar cristal tipo 1 - saco 50kg',
            'current_ncm': '17019900',
            'expected_correct': True
        },
        {
            'description': 'Açúcar refinado especial',
            'current_ncm': '17019100',
            'expected_correct': True
        },
        {
            'description': 'Computador desktop Intel i7',
            'current_ncm': '17019900',
            'expected_correct': False  # Wrong NCM!
        }
    ]

    success_count = 0
    total_count = len(test_cases)

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n   Test {i}/{total_count}: {test_case['description']}")
        print(f"   NCM Atual: {test_case['current_ncm']}")

        try:
            result = agent.classify_ncm(
                test_case['description'],
                test_case['current_ncm']
            )

            print(f"   NCM Sugerido: {result.get('suggested_ncm', 'N/A')}")
            print(f"   Confiança: {result.get('confidence', 0)}%")
            print(f"   Correto: {result.get('is_correct', 'N/A')}")

            # Check if result makes sense
            if result.get('is_correct') == test_case['expected_correct']:
                print("   [OK] Classificação correta!")
                success_count += 1
            else:
                print(f"   [WARNING] Esperado: {test_case['expected_correct']}, Obtido: {result.get('is_correct')}")

        except Exception as e:
            print(f"   [ERROR] Erro ao classificar: {e}")
            import traceback
            traceback.print_exc()

    # Summary
    print("\n" + "=" * 80)
    print("RESUMO")
    print("=" * 80)
    print(f"Sucesso: {success_count}/{total_count}")

    if success_count == total_count:
        print("\n[SUCCESS] Todos os testes passaram! ✅")
        return True
    else:
        print(f"\n[WARNING] {total_count - success_count} teste(s) falharam ⚠️")
        return False


if __name__ == '__main__':
    try:
        success = test_agent()
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n[INFO] Teste interrompido pelo usuário")
        exit(1)
    except Exception as e:
        print(f"\n[ERROR] Erro inesperado: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
