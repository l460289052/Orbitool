from datetime import datetime, timedelta

from .. import H5File, BaseStructure


def test_structure():
    class Child(BaseStructure):
        value: int

    class Father(BaseStructure):
        flt: float = 1.
        bl: bool = False
        s: str = "123"
        dt: datetime = datetime.now()
        c1: Child
        c2: Child

    f = H5File()

    c1 = Child(value=1)
    c2 = Child(value=2)
    father = Father(
        c1=c1, c2=c2,
        flt=2., bl=True, s="321",
        dt=datetime.now() + timedelta(1)
    )
    f.write("father", father)

    t: Father = f.read("father", Father)

    assert t.c1.value == 1
    assert t.c2.value == 2
    assert father == t
