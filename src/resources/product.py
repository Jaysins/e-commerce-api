from src.schemas import ProductRequestSchema, ProductResponseSchema
from src.base.resource import BaseResource


class ProductResource(BaseResource):
    """

    """

    serializers = {"default": ProductRequestSchema,
                   "response": ProductResponseSchema}
