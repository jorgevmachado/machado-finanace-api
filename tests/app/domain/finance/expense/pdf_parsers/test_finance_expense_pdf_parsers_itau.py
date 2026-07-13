from datetime import datetime
from uuid import uuid4

from app.domain.finance.allocation.schema import AllocationSchema
from app.domain.finance.expense.pdf_parsers.itau import (
    _extract_categories,
    _extract_expenses_from_section,
    _extract_products_and_services,
    build_parsed_pdf_expenses,
    clean_category,
    parse_expenses,
    parse_header,
    parse_itau,
)


def _allocation_schema() -> AllocationSchema:
    return AllocationSchema(
        id=uuid4(),
        name="Moradia",
        expenses=[],
        name_code="moradia",
        is_active=True,
        account_id=uuid4(),
        description="allocation",
        allocation_contributions=[],
        created_at=datetime(2026, 1, 1, 0, 0, 0),
        updated_at=None,
        deleted_at=None,
    )


def test_parse_header_extracts_fields() -> None:
    lines = [
        "LOTE 05 SUL Total da fatura anterior 3.650,94",
        "71925-000 BRASILIA DF Pagamento efetuado em 10/06/2026 -3.650,94",
        "Vencimento: 15/07/2026 = Total desta fatura 4.022,54",
        "Emissão: 08/07/2026",
        "O total da sua fatura é: Com vencimento em: Limite total de crédito:",
        "R$ 4.022,54 15/07/2026 R$ 47.000,00",
    ]

    result = parse_header(lines)

    assert result["year"] == 2026
    assert result["month"] == 7
    assert float(result["bill_total"]) == 4022.54
    assert float(result["previous_bill_total"]) == 3650.94
    assert result["bill_due_date"].isoformat() == "2026-07-15"
    assert result["previous_bill_due_date"].isoformat() == "2026-06-10"


def test_parse_expenses_maps_categories_in_two_columns() -> None:
    lines = [
        "Lançamentos: compras e saques",
        "11/05 DROGARIA BRASI 02/02 174,94 19/06 AdministradoraBRASILIAB 28,00",
        "saúde BRASILIA outros BRASILIA",
        "12/05 CLINICA DR. GA 02/04 209,02 21/06 IFD*FB COMERCIO DE ALIB 40,39",
        "HEALTH BRASILIA restaurante BRASILIA",
        "21/06 MAMMAMIA PANIFICADORABR 59,90 21/06 CARTERSALEXANI 01/04 110,00",
        "supermercado BRASILIA vestuário ALEXANIA",
        "Lançamentos: produtos e serviços",
        "22/06 Redução Mensalidade - P -31,00",
        "Anuidade Diferenciada",
        "Lançamentos produtos e serviços 0,00",
    ]

    result = parse_expenses(lines)

    assert {
        "date": "11/05",
        "payee": "DROGARIA BRASI",
        "total_of_installments": 2,
        "current_installment": 2,
        "amount": 174.94,
        "category": "saúde BRASILIA",
    } in result
    assert {
        "date": "19/06",
        "payee": "AdministradoraBRASILIAB",
        "total_of_installments": 1,
        "current_installment": 1,
        "amount": 28.0,
        "category": "outros BRASILIA",
    } in result
    assert {
        "date": "21/06",
        "payee": "CARTERSALEXANI",
        "total_of_installments": 4,
        "current_installment": 1,
        "amount": 110.0,
        "category": "vestuário ALEXANIA",
    } in result
    assert {
        "date": "22/06",
        "payee": "Redução Mensalidade - P",
        "total_of_installments": 1,
        "current_installment": 1,
        "amount": -31.0,
        "category": "Anuidade Diferenciada",
    } in result


def test_parse_expenses_cover_cleaning_and_ignored_rows() -> None:
    lines = [
        "Lançamentos: compras e saques",
        "restaurante BRASILIA",
        "10/06 Pagamento via conta 10,00",
        "10/06 PADARIA BRASILIA 20,00 restaurante BRASILIA",
        "08/06 Mensalidade - Plano do 62,00",
        "Lançamentos: produtos e serviços",
        "Lançamentos produtos e serviços 0,00",
    ]

    result = parse_expenses(lines)

    assert {
        "date": "10/06",
        "payee": "PADARIA",
        "total_of_installments": 1,
        "current_installment": 1,
        "amount": 20.0,
        "category": "restaurante BRASILIA",
    } in result
    assert {
        "date": "08/06",
        "payee": "Mensalidade - Plano",
        "total_of_installments": 1,
        "current_installment": 1,
        "amount": 62.0,
        "category": None,
    } in result
    assert all(item["payee"] != "Pagamento via conta" for item in result)


def test_itau_internal_extract_helpers_edge_cases() -> None:
    assert _extract_expenses_from_section([], start_index=-1, end_index=0) == []
    assert _extract_products_and_services(["sem secao"]) == []
    assert _extract_categories("restaurante BRASILIA 15,00") == ["restaurante BRASILIA"]
    assert _extract_categories("outros Rio de Janeir Centro Sul Extra") == [
        "outros Rio de Janeir Centro"
    ]


def test_clean_category_returns_others_when_category_is_none() -> None:
    assert clean_category(None) == "OTHERS"


def test_clean_category_uppercases_and_strips_without_city_suffix() -> None:
    assert clean_category("  supermercado premium  ") == "SUPERMARKET PREMIUM"


def test_clean_category_removes_city_suffix_and_maps_outros_to_others() -> None:
    assert clean_category("outros BRASILIA") == "OTHERS"


def test_clean_category_removes_city_suffix_and_keeps_non_outros_value() -> None:
    assert clean_category("restaurante OSASCO") == "RESTAURANT"


def test_build_parsed_pdf_expenses_fallback_date() -> None:
    result = build_parsed_pdf_expenses(
        year=2026,
        month=7,
        expenses=[
            {
                "date": "XX/YY",
                "payee": "TESTE",
                "amount": 10.0,
                "category": None,
                "current_installment": 1,
                "total_of_installments": 1,
            }
        ],
    )

    assert len(result) == 1
    assert result[0].date.isoformat() == "2026-07-01"
    assert result[0].reference_month == 7


def test_parse_itau_marks_reference_mismatch() -> None:
    allocation = _allocation_schema()
    lines = [
        "LOTE 05 SUL Total da fatura anterior 3.650,94",
        "71925-000 BRASILIA DF Pagamento efetuado em 10/06/2026 -3.650,94",
        "Vencimento: 15/07/2026 = Total desta fatura 4.022,54",
        "Emissão: 08/07/2026",
        "O total da sua fatura é: Com vencimento em: Limite total de crédito:",
        "R$ 4.022,54 15/07/2026 R$ 47.000,00",
        "Lançamentos: compras e saques",
        "07/07 DOG DO RAFILDSBRASILIAB 70,00",
        "supermercado BRASILIA",
        "Lançamentos: produtos e serviços",
        "Lançamentos produtos e serviços 0,00",
    ]

    result = parse_itau(
        lines=lines,
        allocation=allocation,
        reference_year=2025,
        reference_month=7,
    )

    assert result.error is True
    assert result.message == "Reference year is different from document"
    assert result.allocation.id == allocation.id


def test_parse_itau_marks_reference_month_mismatch() -> None:
    allocation = _allocation_schema()
    lines = [
        "Vencimento: 15/07/2026 = Total desta fatura 4.022,54",
        "Emissão: 08/07/2026",
        "Lançamentos: compras e saques",
        "07/07 DOG DO RAFILDSBRASILIAB 70,00",
        "supermercado BRASILIA",
        "Lançamentos: produtos e serviços",
        "Lançamentos produtos e serviços 0,00",
    ]

    result = parse_itau(
        lines=lines,
        allocation=allocation,
        reference_year=2026,
        reference_month=6,
    )

    assert result.error is True
    assert result.message == "Reference month is different from document"

def test_parse_itau_with_error_when_expense_list_is_empty() -> None:
    allocation = _allocation_schema()
    lines = [
        "Vencimento: 15/07/2026 = Total desta fatura 4.022,54",
        "Emissão: 08/07/2026",
        "Lançamentos: compras e saques",
        "supermercado BRASILIA",
        "Lançamentos: produtos e serviços",
        "Lançamentos produtos e serviços 0,00",
    ]

    result = parse_itau(
        lines=lines,
        allocation=allocation,
        reference_year=2026,
        reference_month=7,
    )

    assert result.error is True
    assert result.message == "No expenses found in the document"
