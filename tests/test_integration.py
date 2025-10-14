# -*- coding: utf-8 -*-
"""
Integration Test - Complete NF-e Validation Pipeline

Tests the entire flow:
CSV → Parse → Validate (Federal + State) → Report (JSON + Markdown)
"""

import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'src'))

from nfe_validator.infrastructure.parsers.csv_parser import NFeCSVParser
from nfe_validator.domain.services.federal_validators import (
    NCMValidator,
    PISCOFINSValidator,
    CFOPValidator,
    TotalsValidator
)
from nfe_validator.domain.services.state_validators import (
    SPValidator,
    PEValidator
)
from nfe_validator.infrastructure.validators.report_generator import ReportGenerator
from repositories.fiscal_repository import FiscalRepository


def test_csv(csv_path: str, test_name: str):
    """
    Test a single CSV file through the complete pipeline

    Args:
        csv_path: Path to CSV file
        test_name: Name of the test for reporting
    """
    print(f"\n{'=' * 80}")
    print(f"TEST: {test_name}")
    print(f"CSV: {csv_path}")
    print(f"{'=' * 80}\n")

    # Step 1: Initialize Repository
    print("[1/5] Initializing Fiscal Repository...")
    repo = FiscalRepository()
    print(f"      Database version: {repo.get_database_version()}")
    print(f"      Last population: {repo.get_last_population_date()}")
    stats = repo.get_statistics()
    print(f"      Statistics: {stats}")

    # Step 2: Parse CSV
    print("\n[2/5] Parsing CSV...")
    parser = NFeCSVParser()
    try:
        nfes = parser.parse_csv(csv_path)
        print(f"      Parsed {len(nfes)} NF-e(s)")

        if not nfes:
            print("      [ERROR] No NF-e found in CSV")
            return False

        nfe = nfes[0]  # Get first NF-e
        print(f"      Chave: {nfe.chave_acesso}")
        print(f"      Número: {nfe.numero}")
        print(f"      Emitente: {nfe.emitente.razao_social} ({nfe.emitente.uf})")
        print(f"      Destinatário: {nfe.destinatario.razao_social} ({nfe.destinatario.uf})")
        print(f"      Items: {len(nfe.items)}")

    except Exception as e:
        print(f"      [ERROR] Parse failed: {e}")
        return False

    # Step 3: Federal Validators
    print("\n[3/5] Running Federal Validators...")

    item_validators = [
        ('NCM', NCMValidator(repo)),
        ('PIS/COFINS', PISCOFINSValidator(repo)),
        ('CFOP', CFOPValidator(repo))
    ]

    # Run item validators
    for validator_name, validator in item_validators:
        print(f"      - {validator_name} Validator...")
        for item in nfe.items:
            errors = validator.validate(item, nfe)
            if errors:
                print(f"        -> Item {item.numero_item}: {len(errors)} error(s)")
                nfe.validation_errors.extend(errors)
            else:
                print(f"        -> Item {item.numero_item}: OK")

    # Run totals validator (validates entire NF-e)
    print(f"      - Totals Validator...")
    totals_validator = TotalsValidator(repo)
    totals_errors = totals_validator.validate(nfe)
    if totals_errors:
        print(f"        -> {len(totals_errors)} error(s)")
        nfe.validation_errors.extend(totals_errors)
    else:
        print(f"        -> OK")

    # Step 4: State Validators (SP + PE)
    print("\n[4/5] Running State Validators...")

    state_validators = []

    if nfe.emitente.uf == 'SP' or nfe.destinatario.uf == 'SP':
        state_validators.append(('SP', SPValidator(repo)))

    if nfe.emitente.uf == 'PE' or nfe.destinatario.uf == 'PE':
        state_validators.append(('PE', PEValidator(repo)))

    if not state_validators:
        print("      - No state validators applicable")
    else:
        for validator_name, validator in state_validators:
            print(f"      - {validator_name} Validator...")
            for item in nfe.items:
                errors = validator.validate(item, nfe)
                if errors:
                    print(f"        -> Item {item.numero_item}: {len(errors)} warning(s)")
                    nfe.validation_errors.extend(errors)
                else:
                    print(f"        -> Item {item.numero_item}: OK")

    # Step 5: Generate Reports
    print("\n[5/5] Generating Reports...")

    generator = ReportGenerator()

    # Count errors by severity
    from nfe_validator.domain.entities.nfe_entity import Severity

    critical = sum(1 for e in nfe.validation_errors if e.severity == Severity.CRITICAL)
    error = sum(1 for e in nfe.validation_errors if e.severity == Severity.ERROR)
    warning = sum(1 for e in nfe.validation_errors if e.severity == Severity.WARNING)
    info = sum(1 for e in nfe.validation_errors if e.severity == Severity.INFO)

    print(f"      Total errors: {len(nfe.validation_errors)}")
    print(f"      - CRITICAL: {critical}")
    print(f"      - ERROR: {error}")
    print(f"      - WARNING: {warning}")
    print(f"      - INFO: {info}")

    # Financial impact
    impact = nfe.get_total_financial_impact()
    print(f"      Financial impact: R$ {impact:,.2f}")

    # Generate reports
    output_dir = Path(__file__).parent / 'output'
    output_dir.mkdir(exist_ok=True)

    # JSON Report
    json_report = generator.generate_json_report(nfe)
    json_path = output_dir / f'{test_name}_report.json'

    import json
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(json_report, f, ensure_ascii=False, indent=2)
    print(f"      JSON Report: {json_path}")

    # Markdown Report
    md_report = generator.generate_markdown_report(nfe)
    md_path = output_dir / f'{test_name}_report.md'

    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(md_report)
    print(f"      Markdown Report: {md_path}")

    # Validation Status
    if critical > 0 or error > 0:
        status = "INVALID"
    elif warning > 0:
        status = "VALID_WITH_WARNINGS"
    else:
        status = "VALID"

    print(f"\n      VALIDATION STATUS: {status}")

    # Close repository
    repo.close()

    return True


def main():
    """
    Run all integration tests
    """
    print("\n" + "=" * 80)
    print("NF-e VALIDATOR - INTEGRATION TESTS")
    print("MVP Sucroalcooleiro - Açúcar (SP + PE)")
    print("=" * 80)

    tests_dir = Path(__file__).parent / 'data'

    test_cases = [
        ('nfe_valid.csv', 'test_01_valid'),
        ('nfe_erro_ncm.csv', 'test_02_ncm_error'),
        ('nfe_erro_pis_cofins.csv', 'test_03_pis_cofins_error'),
        ('nfe_erro_cfop.csv', 'test_04_cfop_error'),
        ('nfe_erro_totais.csv', 'test_05_totals_error')
    ]

    results = []

    for csv_file, test_name in test_cases:
        csv_path = tests_dir / csv_file

        if not csv_path.exists():
            print(f"\n[WARNING] CSV not found: {csv_path}")
            results.append((test_name, False))
            continue

        try:
            success = test_csv(str(csv_path), test_name)
            results.append((test_name, success))
        except Exception as e:
            print(f"\n[ERROR] Test failed with exception: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))

    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)

    for test_name, success in results:
        status = "[OK]" if success else "[FAILED]"
        print(f"{status} {test_name}")

    passed = sum(1 for _, s in results if s)
    total = len(results)

    print(f"\nPassed: {passed}/{total}")

    if passed == total:
        print("\n[SUCCESS] All tests passed!")
        return 0
    else:
        print(f"\n[FAILURE] {total - passed} test(s) failed")
        return 1


if __name__ == '__main__':
    exit(main())
