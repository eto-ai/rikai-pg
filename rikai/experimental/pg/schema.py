#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.


from rikai.spark.sql.generated.RikaiModelSchemaParser import RikaiModelSchemaParser
from rikai.spark.sql.generated.RikaiModelSchemaVisitor import RikaiModelSchemaVisitor
from rikai.spark.sql.schema import SchemaError, parse_schema as rikai_parse_schema

__all__ = ["parse_schema"]


_POSTGRESQL_TYPE_MAPPING = {
    "int": "INT",
    "long": "BIGINT",
    "float": "REAL",
    "double": "REAL",
    "string": "TEXT",
    "str": "TEXT",
    "binary": "BYTEA",
    "box2d": "BOX",
    "image": "image",
    "bool": "BOOLEAN",
    "polygon": "polygon",
    "point": "point",
}


class PostgresTypeVisitor(RikaiModelSchemaVisitor):
    def visitStructType(self, ctx: RikaiModelSchemaParser.StructTypeContext) -> str:
        # Only support detection type for now
        fields = [self.visitStructField(field) for field in ctx.field()]
        if set(fields) == set(["label TEXT", "label_id INT", "box BOX", "score REAL"]):
            return "detection"
        raise ValueError(f"Dont know how to supported yet: {fields}")

    def visitStructField(self, ctx: RikaiModelSchemaParser.StructFieldContext) -> str:
        name = self.visit(ctx.identifier())
        dataType = self.visit(ctx.fieldType())
        return f"{name} {dataType}"

    def visitArrayType(self, ctx: RikaiModelSchemaParser.ArrayTypeContext) -> str:
        return f"{self.visit(ctx.fieldType())}[]"

    def visitUnquotedIdentifier(
        self, ctx: RikaiModelSchemaParser.UnquotedIdentifierContext
    ) -> str:
        identifer = ctx.IDENTIFIER().getText()
        if identifer[0].isnumeric():
            raise SchemaError(f'Identifier can not start with a digit: "{identifer}"')
        return identifer

    def visitPlainFieldType(
        self, ctx: RikaiModelSchemaParser.PlainFieldTypeContext
    ) -> str:
        name = self.visit(ctx.identifier())
        try:
            return _POSTGRESQL_TYPE_MAPPING[name]
        except KeyError as e:
            raise SchemaError(f'Can not recognize type: "{name}"') from e


def parse_schema(schema: str) -> str:
    """Parse ModelType schema and returns Postgres types"""
    return rikai_parse_schema(schema_str=schema, visitor=PostgresTypeVisitor())
