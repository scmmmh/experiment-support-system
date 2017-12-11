import marshmallow as ma

class Relationship(ma.fields.Field):

    def _deserialize(self, value, attr=None, data=None):
        if value:
            return (value['type'], value['id'])
        else:
            return None
