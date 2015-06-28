# -*- coding: utf-8 -*-
import inspect
from functools import partial

import marshmallow as ma
from marshmallow.compat import with_metaclass
from marshmallow_mongoengine.convert import ModelConverter


class SchemaOpts(ma.SchemaOpts):
    """Options class for `ModelSchema`.
    Adds the following options:

    - ``model``: The Mongoengine Document model to generate the `Schema`
        from (required).
    - ``model_fields_kwargs``: Dict of {field: kwargs} to provide as
        additionals argument during fields creation.
    - ``model_converter``: `ModelConverter` class to use for converting the
        Mongoengine Document model to marshmallow fields.
    """

    def __init__(self, meta):
        super(SchemaOpts, self).__init__(meta)
        self.model = getattr(meta, 'model', None)
        self.model_fields_kwargs = getattr(meta, 'model_fields_kwargs', {})
        self.model_converter = getattr(meta, 'model_converter', ModelConverter)


class SchemaMeta(ma.schema.SchemaMeta):
    """Metaclass for `ModelSchema`."""

    # override SchemaMeta
    @classmethod
    def get_declared_fields(mcs, klass, *args, **kwargs):
        """Updates declared fields with fields converted from the
        Mongoengine model passed as the `model` class Meta option.
        """
        declared_fields = kwargs.get('dict_class', dict)()
        # inheriting from base classes
        for base in inspect.getmro(klass):
            opts = klass.opts
            if opts.model:
                Converter = opts.model_converter
                converter = Converter()
                declared_fields = converter.fields_for_model(
                    opts.model,
                    fields=opts.fields,
                    fields_kwargs=opts.model_fields_kwargs
                )
                break
        base_fields = super(SchemaMeta, mcs).get_declared_fields(
            klass, *args, **kwargs
        )
        declared_fields.update(base_fields)
        return declared_fields


class ModelSchema(with_metaclass(SchemaMeta, ma.Schema)):
    """Base class for Mongoengine model-based Schemas.

    Example: ::

        from marshmallow_mongoengine import ModelSchema
        from mymodels import User

        class UserSchema(ModelSchema):
            class Meta:
                model = User
    """
    OPTIONS_CLASS = SchemaOpts

    def make_object(self, data):
        return self.opts.model(**data)
