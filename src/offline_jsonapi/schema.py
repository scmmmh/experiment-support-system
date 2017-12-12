import marshmallow as ma

from marshmallow.schema import ValidationError, POST_LOAD, PRE_LOAD

from .fields import Relationship

class Schema(ma.Schema):

    def __init__(self, include_schemas=None, *args, **kwargs):
        super(Schema, self).__init__(*args, **kwargs)
        self.include_schemas = dict([(s.Meta.type_, s()) for s in include_schemas]) if include_schemas else {}
        self.include_schemas[self.Meta.type_] = self

    def _unwrap_single(self, data):
        """Unwraps a single JSONAPI object into the flatter structure expected
        by marshmallow.
        """
        if data is not None:
            unwrapped = {}
            unwrapped['id'] = data['id']
            unwrapped['type'] = data['type']
            if 'attributes' in data:
                unwrapped.update(data['attributes'])
            if 'relationships' in data:
                for key, value in data['relationships'].items():
                    unwrapped[key] = self._unwrap(value, isinstance(value['data'], list))
            return unwrapped
        else:
            return None

    def _unwrap(self, data, many):
        """Unwraps a single JSONAPI object or JSONAPI collection into the flatter
        structure expected by marshmallow."""
        if many:
            return [self._unwrap_single(part) for part in data['data']]
        else:
            return self._unwrap_single(data['data'])

    def _get_original_data(self, obj):
        """Returns the original source data that has been attached to an object
        during pre-/post-processing.

        :param obj: The object to get the original data from"""
        if isinstance(obj, dict):
            return obj['__original_data']
        else:
            return obj.__original_data

    def _set_original_data(self, obj, original_data):
        """Sets the original source data as an attribute of the ``obj`` object.
        Distinguishes between ``dict`` instances, where it is set on the key
        ``__original_data`` and other object where it is set on the property
        ``__original_data``.

        :param obj: The object to attach the original source data to
        :param original_data: The original source data
        :type original_data: ``dict``
        """
        if isinstance(obj, dict):
            obj['__original_data'] = original_data
        else:
            obj.__original_data = original_data

    def _load_relationships(self, result, many, included):
        """Loads and sets the relationships between main objects and included objects.

        :param result: The main object being loaded
        :param many: Whether the ``result`` is a collection or not
        :type many: ``bool``
        :param included: The included data that is being loaded"""
        loaded = {}
        if many:
            for part in result:
                loaded[(self._get_original_data(part)['type'], self._get_original_data(part)['id'])] = part
        else:
            loaded[(self._get_original_data(result)['type'], self._get_original_data(result)['id'])] = result
        for part in included:
            loaded[(self._get_original_data(part)['type'], self._get_original_data(part)['id'])] = part
        for key, item in loaded.items():
            schema = self.include_schemas[key[0]]
            if isinstance(item, dict):
                original_data = item['__original_data']
            else:
                original_data = item.__original_data
            for field_name, validator in schema.fields.items():
                if isinstance(validator, Relationship):
                    values = validator.deserialize(original_data[field_name] if field_name in original_data else None)
                    if values:
                        if isinstance(values, list):
                            values = [loaded[key] for key in values]
                        else:
                            values = loaded[values]
                    if isinstance(item, dict):
                        item[field_name] = values
                    else:
                        setattr(item, field_name, values)

    def _invoke_load_processors(self, tag_name, data, many, original_data=None):
        """Overrides the :class:`~marshmallow.schema.Schema` in order to enable the
        pre-/post-load processors to be called for both the main and included data.
        Where ``many`` is ``True``, the individual data items will be grouped by
        the type in the original data to ensure that all data items with the same
        type are pre-processed together. This ensures that pre-/post-load processors
        with ``pass_many=True`` will be called correctly.
        """
        if many:
            groups = {}
            for data_part, original_part in zip(data, original_data):
                if original_part['type'] not in groups:
                    groups[original_part['type']] = [[], []]
                groups[original_part['type']][0].append(data_part)
                groups[original_part['type']][1].append(original_part)
            result = []
            for data_parts, original_parts in groups.values():
                group_result = super(Schema, self.include_schemas[original_parts[0]['type']])._invoke_load_processors(tag_name, data_parts, many, original_data=original_parts)
                for result_part, original_part in zip(group_result, original_parts):
                    self._set_original_data(result_part, original_part)
                result.extend(group_result)
        else:
            result = super(Schema, self.include_schemas[original_data['type']])._invoke_load_processors(tag_name, data, many, original_data=original_data)
            self._set_original_data(result, original_data)
        return result

    def _do_load(self, data, many=None, partial=None, postprocess=True):
        """Fully override the :class:`~marshmallow.schema.Schema` in order to
        correctly handle included data. Pre- and post-load processors will be called
        on both the main and any included data. Post-load processors will be called
        before relationships between the objects have been loaded. Finally relationships
        will be loaded."""
        errors = {}
        many = self.many if many is None else bool(many)
        included = self._unwrap({'data': data['included']}, True) if 'included' in data else []
        data = self._unwrap(data, many)
        if partial is None:
            partial = self.partial
        try:
            processed_data = self._invoke_load_processors(
                PRE_LOAD,
                data,
                many,
                original_data=data)
            processed_included = self._invoke_load_processors(
                PRE_LOAD,
                included,
                many=True,
                original_data=included)
        except ValidationError as err:
            errors = err.normalized_messages()
            result = None
        if not errors:
            try:
                result = self._unmarshal(
                    processed_data,
                    self.fields,
                    many=many,
                    partial=partial,
                    dict_class=self.dict_class,
                    index_errors=self.opts.index_errors,
                )
                result_included = []
                for included_part in processed_included:
                    schema = self.include_schemas[included_part['type']]
                    result_included.append(schema._unmarshal(included_part,
                                                             schema.fields,
                                                             many=False,
                                                             dict_class=self.dict_class,
                                                             index_errors=self.opts.index_errors))
            except ValidationError as err:
                result = err.data
            self._invoke_field_validators(data=result, many=many)
            errors = self._unmarshal.errors
            field_errors = bool(errors)
            # Run schema-level migration
            try:
                self._invoke_validators(pass_many=True, data=result, original_data=data, many=many,
                                        field_errors=field_errors)
            except ValidationError as err:
                errors.update(err.messages)
            try:
                self._invoke_validators(pass_many=False, data=result, original_data=data, many=many,
                                        field_errors=field_errors)
            except ValidationError as err:
                errors.update(err.messages)
        # Run post processors
        if not errors and postprocess:
            try:
                result = self._invoke_load_processors(
                    POST_LOAD,
                    result,
                    many,
                    original_data=data)
                result_included = self._invoke_load_processors(
                    POST_LOAD,
                    result_included,
                    many=True,
                    original_data=included)
                self._load_relationships(result, many, result_included)
            except ValidationError as err:
                errors = err.normalized_messages()
        if errors:
            exc = ValidationError(
                errors,
                field_names=self._unmarshal.error_field_names,
                fields=self._unmarshal.error_fields,
                data=data,
                valid_data=result,
                **self._unmarshal.error_kwargs
            )
            self.handle_error(exc, data)
            if self.strict:
                raise exc
        return result, errors
