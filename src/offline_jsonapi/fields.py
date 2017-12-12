import marshmallow as ma

class Relationship(ma.fields.Field):

    def __init__(self, many=False, **kwargs):
        super(Relationship, self).__init__(**kwargs)
        self.many = many

    def _deserialize(self, value, attr=None, data=None):
        if value is None:
            return None
        else:
            if self.many:
                return [(v['type'], v['id']) for v in value]
            else:
                return (value['type'], value['id'])
