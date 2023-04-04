from ..base.service import ServiceFactory
from ..models import Product


BaseProductService = ServiceFactory.create_service(Product)


class ProductService(BaseProductService):
    """

    """

    @classmethod
    def register(cls, **kwargs):
        """

        :param kwargs:
        :type kwargs:
        :return:
        :rtype:
        """
        return cls.create(**kwargs)
