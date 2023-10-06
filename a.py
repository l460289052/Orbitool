from typing import Any

from pydantic_core import core_schema
from typing_extensions import Annotated

from pydantic import (
    BaseModel,
    GetCoreSchemaHandler,
    GetJsonSchemaHandler,
    ValidationError,
)
from pydantic.json_schema import JsonSchemaValue


class ThirdPartyType:
    """
    This is meant to represent a type from a third-party library that wasn't designed with Pydantic
    integration in mind, and so doesn't have a `pydantic_core.CoreSchema` or anything.
    """

    x: int

    def __init__(self):
        self.x = 0


class _ThirdPartyTypePydanticAnnotation:
    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        _source_type: Any,
        _handler: GetCoreSchemaHandler,
    ) -> core_schema.CoreSchema:
        """
        We return a pydantic_core.CoreSchema that behaves in the following ways:

        * ints will be parsed as `ThirdPartyType` instances with the int as the x attribute
        * `ThirdPartyType` instances will be parsed as `ThirdPartyType` instances without any changes
        * Nothing else will pass validation
        * Serialization will always return just an int
        """

        def validate_from_int(value: int) -> ThirdPartyType:
            result = ThirdPartyType()
            result.x = value
            return result

        from_int_schema = core_schema.chain_schema(
            [
                core_schema.int_schema(),
                core_schema.no_info_plain_validator_function(validate_from_int),
            ]
        )

        return core_schema.json_or_python_schema(
            json_schema=from_int_schema,
            python_schema=core_schema.union_schema(
                [
                    # check if it's an instance first before doing any further work
                    core_schema.is_instance_schema(ThirdPartyType),
                    from_int_schema,
                ]
            ),
            serialization=core_schema.plain_serializer_function_ser_schema(
                lambda instance: instance.x
            ),
        )

    @classmethod
    def __get_pydantic_json_schema__(
        cls, _core_schema: core_schema.CoreSchema, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        # Use the same schema that would be used for `int`
        return handler(core_schema.int_schema())


# We now create an `Annotated` wrapper that we'll use as the annotation for fields on `BaseModel`s, etc.
PydanticThirdPartyType = Annotated[
    ThirdPartyType, _ThirdPartyTypePydanticAnnotation
]


# Create a model class that uses this annotation as a field
class Model(BaseModel):
    third_party_type: PydanticThirdPartyType


# Demonstrate that this field is handled correctly, that ints are parsed into `ThirdPartyType`, and that
# these instances are also "dumped" directly into ints as expected.
m_int = Model(third_party_type=1)
assert isinstance(m_int.third_party_type, ThirdPartyType)
assert m_int.third_party_type.x == 1
assert m_int.model_dump() == {'third_party_type': 1}

# Do the same thing where an instance of ThirdPartyType is passed in
instance = ThirdPartyType()
assert instance.x == 0
instance.x = 10

m_instance = Model(third_party_type=instance)
assert isinstance(m_instance.third_party_type, ThirdPartyType)
assert m_instance.third_party_type.x == 10
assert m_instance.model_dump() == {'third_party_type': 10}

# Demonstrate that validation errors are raised as expected for invalid inputs
try:
    Model(third_party_type='a')
except ValidationError as e:
    print(e)
    """
    2 validation errors for Model
    third_party_type.is-instance[ThirdPartyType]
      Input should be an instance of ThirdPartyType [type=is_instance_of, input_value='a', input_type=str]
    third_party_type.chain[int,function-plain[validate_from_int()]]
      Input should be a valid integer, unable to parse string as an integer [type=int_parsing, input_value='a', input_type=str]
    """


assert Model.model_json_schema() == {
    'properties': {
        'third_party_type': {'title': 'Third Party Type', 'type': 'integer'}
    },
    'required': ['third_party_type'],
    'title': 'Model',
    'type': 'object',
}
