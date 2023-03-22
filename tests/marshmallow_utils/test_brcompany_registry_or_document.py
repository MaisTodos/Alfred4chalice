import pytest
from marshmallow import ValidationError, fields

from alfred.marshmallow_utils.fields.br_company_registry_or_document import (
    BRCompanyRegistryOrDocumentField,
)


def test_br_company_registry_or_document_is_subclass():
    assert issubclass(BRCompanyRegistryOrDocumentField, fields.String)


def test_br_company_registry_or_document_invalid_default_message():
    field = BRCompanyRegistryOrDocumentField()
    document = "12309845687010"

    with pytest.raises(ValidationError) as err:
        field._deserialize(document, "document", {"document": document})

    assert err.value.args[0] == "Documento inválido"


def test_br_company_registry_or_document_invalid_custom_message():
    document_err_msg = "Some error message"
    field = BRCompanyRegistryOrDocumentField(document_error_msg=document_err_msg)
    document = "12309845687010"

    with pytest.raises(ValidationError) as err:
        field._deserialize(document, "document", {"document": document})

    assert err.value.args[0] == document_err_msg


def test_br_company_registry_or_document_valid_cnpj_without_mask():
    field = BRCompanyRegistryOrDocumentField()
    document = "03492539000101"

    value = field._deserialize(document, "document", {"document": document})

    assert value == document


def test_br_company_registry_or_document_valid_cnpj_with_mask():
    field = BRCompanyRegistryOrDocumentField()
    document = "03.492.539/0001-01"

    value = field._deserialize(document, "document", {"document": document})

    assert value == "03492539000101"


def test_br_company_registry_or_document_valid_cpf_without_mask():
    field = BRCompanyRegistryOrDocumentField()
    document = "99241995025"

    value = field._deserialize(document, "document", {"document": document})

    assert value == document


def test_br_company_registry_or_document_valid_cpf_with_mask():
    field = BRCompanyRegistryOrDocumentField()
    document = "615.179.300-57"

    value = field._deserialize(document, "document", {"document": document})

    assert value == "61517930057"
