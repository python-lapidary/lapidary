class Absent:
    __singleton = None

    def __new__(cls):
        if cls.__singleton is None:
            cls.__singleton = super().__new__(cls)
        return cls.__singleton

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
