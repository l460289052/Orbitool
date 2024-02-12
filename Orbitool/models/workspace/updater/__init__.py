from .base import update, need_update, get_version, register

from . import ver2_0_13
from . import ver2_1_5
from . import ver2_4_0
from . import ver2_5_0
from . import ver2_5_2
from . import ver2_5_3
register("2.0.13", ver2_0_13.update)
register("2.1.5", ver2_1_5.update)
register("2.4.0", ver2_4_0.update)
register("2.5.0", ver2_5_0.update)
register("2.5.2", ver2_5_2.update)
register("2.5.3", ver2_5_3.update)