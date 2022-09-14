class Absent:
    @classmethod
    def __get_validators__(cls):
        yield Absent._validate

    @staticmethod
    def _validate(obj: 'Absent'):
        if obj is not ABSENT:
            raise ValueError()
        else:
            return obj

    def __repr__(self):
        return '-ABSENT-'


ABSENT = Absent()
