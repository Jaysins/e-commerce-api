"""
models.py

Data model file for application. This will connect to the mongo database and provide a source for storage
for the application service

"""

import settings
import pymongo

from pymongo.write_concern import WriteConcern
from pymongo.operations import IndexModel
from pymodm import connect, fields, MongoModel, EmbeddedMongoModel
from datetime import datetime, timedelta
from pymodm.common import _import as common_import
import bcrypt
import json
import jwt
from pprint import pprint

# Must always be run before any other database calls can follow
connect(settings.MONGO_DB_URI, connect=False, maxPoolSize=None)
print(settings.MONGO_DB_URI)


class ReferenceField(fields.ReferenceField):
    """
    ReferenceField
    """

    def dereference_if_needed(self, value):
        """

        :param value:
        :type value:
        :return:
        :rtype:
        """

        if isinstance(value, self.related_model):
            return value
        if self.model._mongometa._auto_dereference:
            dereference_id = common_import('pymodm.dereference.dereference_id')
            return dereference_id(self.related_model, value)
        value_stick = self.related_model._mongometa.pk.to_python(value)
        if not isinstance(value_stick, self.related_model):
            # print(type(value_stick))
            # value_stick = value_stick if value_stick and len(value_stick) > 10 else ObjectId(value_stick)
            check = self.related_model.objects.raw({"_id": value_stick})
            # print(check.count(), "dondnoenxe")
            if check.count() < 1:
                return self.related_model._mongometa.pk.to_python(value)
            return check.first()
        return self.related_model._mongometa.pk.to_python(value)


class AppMixin:
    """ App mixin will hold special methods and field parameters to map to all model classes"""

    def to_dict(self, exclude=None, do_dump=False):
        """

        @param exclude:
        @param do_dump:
        @return:
        """
        if isinstance(self, (MongoModel, EmbeddedMongoModel)):
            d = self.to_custom_son(exclude=exclude).to_dict()
            # [d.pop(i, None) for i in exclude]
            return json.loads(json.dumps(d, default=str)) if do_dump else d
        return self.__dict__


class User(MongoModel, AppMixin):
    """ Model for storing information about an entity or user who owns an account or set of accounts.
    _id will be equivalent to either the user_id or the entity_id
    """

    email = fields.CharField(required=False, blank=True)
    first_name = fields.CharField(required=False, blank=True)
    password = fields.CharField(required=False, blank=True)
    last_name = fields.CharField(required=False, blank=True)
    date_created = fields.DateTimeField(required=True, blank=False, default=datetime.utcnow)
    last_updated = fields.DateTimeField(required=True, blank=False, default=datetime.utcnow)

    class Meta:
        """
        Meta class
        """

        write_concern = WriteConcern(j=True)
        ignore_unknown_fields = True
        indexes = [
            IndexModel([("_cls", pymongo.DESCENDING), ("email", pymongo.ASCENDING), ("first_name", pymongo.ASCENDING),
                        ("last_name", pymongo.ASCENDING), ("date_created", pymongo.DESCENDING), ])]

    def set_password(self, password):
        """
        Password hashing logic for each model.
        This will be run on every user object when it is created.

        Arguments:
            password {str or unidecode} -- The password, in clear text, to be hashed and set on the model
        """

        if not password or not isinstance(password, (str, bytes)):
            raise ValueError("Password must be non-empty string or bytes value")

        self.password = (bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())).decode()
        # set last updated.
        self.last_updated = datetime.utcnow()

        return self.save()

    def check_password(self, password):
        """
        Password checking logic.
        This will be used whenever a user attempts to authenticate.

        Arguments:
            password {str or bytes} -- The password to be compared, in clear text.

        Raises:
            ValueError -- Raised if there is an empty value in password

        Returns:
            bool -- True if password is equal to hashed password, False if not.
        """

        if not password or not isinstance(password, (str, bytes)):
            raise ValueError("Password must be non-empty string or bytes value")

        # both password and hashed password need to be encrypted.
        return bcrypt.checkpw(password.encode('utf-8'), self.password.encode('utf-8'))

    @property
    def auth_token(self):
        """ Generate the auth token for this user from the current data embedded within the application """

        if not self.pk:
            raise ValueError("Cannot generate token for unsaved object")

        expires_in = datetime.now() + timedelta(hours=int(settings.JWT_EXPIRES_IN_HOURS))

        payload = dict(first_name=self.first_name, last_name=self.last_name, id=str(self.pk), exp=expires_in)
        # print(payload, "token the payload")
        encoded = jwt.encode(payload, key=settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
        return encoded


class Address(EmbeddedMongoModel, AppMixin):
    street = fields.CharField(required=True, blank=False)
    street_line_2 = fields.CharField(required=False, blank=True)
    state = fields.CharField(required=True, blank=False)
    country = fields.CharField(required=True, blank=False)


class Person(EmbeddedMongoModel, AppMixin):
    name = fields.CharField(required=True, blank=False)
    email = fields.CharField(required=True, blank=False)
    phone = fields.CharField(required=True, blank=False)


class Currency(MongoModel, AppMixin):
    code = fields.CharField(primary_key=True)
    name = fields.CharField()
    symbol = fields.CharField()
    date_created = fields.DateTimeField(required=True, blank=False, default=datetime.utcnow)
    last_updated = fields.DateTimeField(required=True, blank=False, default=datetime.utcnow)


class Price(EmbeddedMongoModel, AppMixin):
    """
    Price
    """
    value = fields.FloatField(required=True, blank=False)
    cost_value = fields.FloatField(required=False, blank=True)
    selling_value = fields.FloatField(required=False, blank=True)
    discount_value = fields.FloatField(required=False, blank=True)
    currency = ReferenceField(Currency, required=True, blank=False)
    mrsp_value = fields.FloatField(required=False, blank=True)
    profit_margin = fields.FloatField(required=False, blank=True)

    class Meta:
        """
        Meta
        """
        write_concern = WriteConcern(j=True)
        ignore_unknown_fields = True


class Category(MongoModel, AppMixin):
    """
    Model to hold product categories
    """

    code = fields.CharField(required=True, blank=False)
    name = fields.CharField(required=True, blank=False)
    description = fields.CharField(required=False, blank=True)
    instance_id = fields.CharField(required=True)
    entity_id = fields.CharField(required=False, blank=True)
    visible = fields.BooleanField(blank=True, default=True)
    eligible = fields.BooleanField(blank=True, default=True)
    relevance = fields.IntegerField(required=False, blank=True)
    commission = fields.FloatField(required=False, default=None, blank=True)
    date_created = fields.DateTimeField(required=True, blank=False, default=datetime.utcnow)
    last_updated = fields.DateTimeField(required=True, blank=False, default=datetime.utcnow)

    @property
    def sub_categories(self):
        """
        All subcategories tied to this category
        @return: sub categoriees
        @rtype: MongoModel
        """
        return SubCategory.objects.raw({"category": self.pk})

    @property
    def product_count(self):
        """

        @return:
        """
        return Product.objects.raw({"category_code": self.code,
                                    "instance_id": self.instance_id}).only("_id").count()


class SubCategory(MongoModel, AppMixin):
    """
    Model to hold product Sub categories

    """
    code = fields.CharField(required=True, blank=False)
    name = fields.CharField(required=True, blank=False)
    description = fields.CharField()
    category = ReferenceField(Category, required=True, blank=False)
    instance_id = fields.CharField(required=True)
    entity_id = fields.CharField(required=False, blank=True)
    category_code = fields.CharField(required=False, blank=True)
    visible = fields.BooleanField(blank=True, default=True)
    eligible = fields.BooleanField(blank=True, default=True)
    date_created = fields.DateTimeField(required=True, blank=False, default=datetime.utcnow)
    last_updated = fields.DateTimeField(required=True, blank=False, default=datetime.utcnow)


class Country(MongoModel, AppMixin):
    code = fields.CharField(primary_key=True)
    name = fields.CharField(required=True, blank=False)
    slug = fields.CharField(required=False, blank=True)
    phone_code = fields.BooleanField(default=False)
    enabled = fields.BooleanField(default=False)
    requires_post_code = fields.BooleanField(default=False)
    date_created = fields.DateTimeField(required=True, blank=False, default=datetime.utcnow)
    last_updated = fields.DateTimeField(required=True, blank=False, default=datetime.utcnow)


class Location(MongoModel, AppMixin):
    """
    Holds the Location
    """
    first_name = fields.CharField(required=False, blank=False)
    last_name = fields.CharField(required=False, blank=False)
    name = fields.CharField(required=False, blank=False)
    phone = fields.CharField(required=True, blank=False)
    email = fields.CharField(required=False, blank=True)
    city = fields.CharField(required=False, blank=True)
    state = fields.CharField(required=False, blank=True)
    domain = fields.CharField(required=False, blank=True)
    country = ReferenceField(Country, required=False, blank=True)
    street = fields.CharField(required=False, blank=True)
    street_line_2 = fields.CharField(required=False, blank=True)
    post_code = fields.CharField(required=False, blank=True)
    lat = fields.FloatField(required=False, blank=True)
    lng = fields.FloatField(required=False, blank=True)
    default = fields.BooleanField(blank=True, default=False)
    user_id = fields.CharField(required=False, blank=True)
    user = fields.ReferenceField(User, required=True, blank=False)
    date_created = fields.DateTimeField(required=True, blank=False, default=datetime.utcnow)
    last_updated = fields.DateTimeField(required=True, blank=False, default=datetime.utcnow)

    class Meta:
        """
        Meta
        """
        write_concern = WriteConcern(j=True)
        ignore_unknown_fields = True

        indexes = [
            IndexModel([('domain', pymongo.ASCENDING), ('email', pymongo.ASCENDING),
                        ('instance_id', pymongo.ASCENDING), ('phone', pymongo.ASCENDING),
                        ("date_created", pymongo.DESCENDING)]),
            IndexModel([('domain', pymongo.ASCENDING), ('instance_id', pymongo.ASCENDING)],
                       partialFilterExpression={"domain": {"$type": "string"}},
                       unique=True)
        ]

    @property
    def product_count(self):
        """

        @return:
        """
        return Product.objects.raw({"location": self.pk}).count()


class ProductStat(EmbeddedMongoModel):
    """
    Defines the model for product Stats
    """
    units_sold = fields.IntegerField(required=False, blank=True)
    total_amount = fields.FloatField(required=False, blank=True)
    likes = fields.IntegerField(required=False, blank=True)
    views = fields.IntegerField(required=False, blank=True)
    first_sale_date = fields.DateTimeField(required=True, blank=False, default=datetime.utcnow)
    last_sale_date = fields.DateTimeField(required=True, blank=False, default=datetime.utcnow)


class EmbeddedAttribute(EmbeddedMongoModel, AppMixin):
    """

    Model that holds the attributes
    E.g name: Size code: size values:[ 41, 42, 43]
    """

    name = fields.CharField(required=True, blank=False)
    code = fields.CharField(required=False, blank=True)
    category = ReferenceField(Category, required=True, blank=False)
    sub_category = ReferenceField(SubCategory, required=False, blank=True)
    values = fields.ListField(required=False, blank=True)
    instance_id = fields.CharField(required=True, blank=False)
    date_created = fields.DateTimeField(required=True, blank=False, default=datetime.utcnow)
    last_updated = fields.DateTimeField(required=True, blank=False, default=datetime.utcnow)

    class Meta:
        """
        Meta
        """
        write_concern = WriteConcern(j=True)
        ignore_unknown_fields = True


class ProductVariant(EmbeddedMongoModel, AppMixin):
    """
    Model that holds the product variant
    """
    id = fields.CharField()
    name = fields.CharField(required=False, blank=True)  # 44-red-regular
    sku = fields.CharField(required=False, blank=True)  # sku-001
    prices = fields.EmbeddedDocumentListField(Price, required=False)
    quantity = fields.IntegerField(required=True, blank=False)
    attributes = fields.ListField(required=False,
                                  blank=True)  # {'size': '44', 'color': 'red', 'fit': 'slim|regular|skinny'}
    available = fields.BooleanField(required=False, blank=True)
    default_currency = ReferenceField(Currency, required=False, blank=True)

    class Meta:
        """
        Meta Class
        """
        write_concern = WriteConcern(j=True)
        ignore_unknown_fields = True

    def __hash__(self):
        """ custom hashing method so that comparison will work on an object level """
        return hash(self.sku)

    def __eq__(self, other):
        """ custom equality function to ensure object can be compared using either a string or object value """

        # compare permission with another permission object
        if isinstance(other, ProductVariant):
            return hash(self.sku) == other.__hash__()

        # compare permission with another string matching the domain
        if isinstance(other, (str, bytes)):
            return str(self.sku) == other

    @property
    def pk(self):
        """

        @return:
        @rtype:
        """
        return self.id

    @property
    def price(self):
        """
        Price
        """
        default_currency = self.default_currency
        for price in self.prices:
            if price.currency.code == default_currency.code:
                return price
        return self.price


class Product(AppMixin, MongoModel):
    name = fields.CharField(required=True, blank=False)
    sku = fields.CharField(required=False, blank=True)  # sku for the product
    code = fields.CharField(required=False, blank=True)  # sku for the product
    description = fields.CharField(required=False, blank=True)
    caption = fields.CharField(required=False, blank=True)
    category = ReferenceField(Category, required=False, blank=True)
    sub_category = ReferenceField(SubCategory, required=False, blank=True)
    discount_price = fields.EmbeddedDocumentField(Price, required=False, blank=True)
    images = fields.ListField(required=False, blank=True)
    price = fields.EmbeddedDocumentField(Price, required=False, blank=True)
    location = ReferenceField(Location, required=False, blank=True)
    quantity = fields.IntegerField(required=True, blank=False, default=1)
    unlimited_stock = fields.BooleanField(blank=True, default=False)
    user = fields.ReferenceField(User, required=True, blank=False)
    tags = fields.ListField(fields.CharField(), required=False, blank=True, default=[])
    attributes = fields.EmbeddedDocumentListField(EmbeddedAttribute, required=False, blank=True)
    variants = fields.EmbeddedDocumentListField(ProductVariant, required=False, blank=True)
    options = fields.ListField(required=False, blank=True)
    stats = fields.EmbeddedDocumentField(ProductStat, required=False, blank=True)
    allow_modification = fields.BooleanField(blank=True)
    visible = fields.BooleanField(blank=True, default=True)
    has_variations = fields.BooleanField(blank=True, default=False)
    supplier = fields.DictField(required=False, blank=True)
    date_created = fields.DateTimeField(required=True, blank=False, default=datetime.utcnow)
    last_updated = fields.DateTimeField(required=True, blank=False, default=datetime.utcnow)
