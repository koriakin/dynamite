# Copyright 2017 CodiLime
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from .field import IsaSwitch, MatchError
from .st import IsaSTInsn
from .sema import SemaUnkOp, SemaList, SemaReadArg, SemaWriteArg


class BaseInsn:
    """
    The base class for instruction templates.  Converts instruction fields
    to/from an instruction syntax tree.
    """

    def parse(self, state):
        """
        Parses this argument from disassembly state, generating an instruction
        syntax tree.
        """
        raise NotImplementedError


class Insn(BaseInsn):
    """
    A single instruction template.  Once parsing gets here, the instruction
    is known, and it's just a matter of parsing its arguments.
    """

    def __init__(self, name, sema, *args, mods=[]):
        self.name = name
        if not isinstance(sema, SemaList):
            assert isinstance(sema, list)
            sema = SemaList(sema)
        self.sema = sema
        self.args = args
        self.mods = mods

    def parse(self, state):
        args = [arg.parse(state) for arg in self.args]
        mods = []
        for mod in self.mods:
            mods += mod.parse(state)
        def rebuilder_arg(cls, *args):
            if cls is SemaReadArg:
                dst, arg = args
                return self.args[arg].sema_read(state, dst)
            elif cls is SemaWriteArg:
                arg, src = args
                return self.args[arg].sema_write(state, src)
            else:
                return cls(*args)
        sema = self.sema.rebuild(rebuilder_arg)
        return IsaSTInsn(self.name, args, mods), sema


class InsnSwitch(BaseInsn, IsaSwitch):
    """
    Selects an instruction based on the value of a field - see IsaSwitch
    and IsaMatch for how the matching is done.
    """
    def parse(self, state):
        try:
            i = self.find(state)
        except MatchError as e:
            state.errors.append(e)
            return IsaSTInsn(None), [SemaUnkOp()]
        return i.parse(state)
