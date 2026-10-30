__all__ = ["Configurable", "PropertyList"]

import ROOT
from GaugiKernel import Logger
from GaugiKernel.macros import MSG_FATAL
from GaugiKernel import list2stdvector


class PropertyList(list):
    """
    List wrapper that supports both `+= item` and `+= [item]`
    for intuitive accumulation of tools and vector properties.
    """
    def __init__(self, owner=None, prop_name=None, iterable=None):
        super().__init__(iterable if iterable is not None else [])
        self._owner = owner
        self._prop_name = prop_name

    def _sync(self):
        if self._owner is not None and self._prop_name is not None:
            setattr(self._owner, self._prop_name, self)

    def __iadd__(self, other):
        if isinstance(other, list):
            self.extend(other)
        else:
            self.append(other)
        self._sync()
        return self

    def __add__(self, other):
        res = PropertyList(self._owner, self._prop_name, self)
        if isinstance(other, list):
            res.extend(other)
        else:
            res.append(other)
        return res


def treatPropertyValue(value):
    if hasattr(value, "c_ptr"):
        return value.c_ptr()

    if isinstance(value, list):
        if len(value) == 0:
            return value
        if hasattr(value[0], "c_ptr"):
            from ROOT.std import vector
            vec = vector("Gaugi::Tool*")()
            for tool in value:
                vec.push_back(tool.c_ptr())
            return vec
        if isinstance(value[0], str):
            return list2stdvector('string', value)
        elif isinstance(value[0], int):
            return list2stdvector('int', value)
        elif isinstance(value[0], float):
            return list2stdvector('float', value)
        elif isinstance(value[0], bool):
            return list2stdvector('bool', value)
        elif isinstance(value[0], list) and len(value[0]) > 0 and isinstance(value[0][0], int):
            from ROOT.std import vector
            vec = vector("vector<int>")()
            for v in value:
                vec.push_back(list2stdvector('int', v))
            return vec
    return value


class Configurable(Logger):
    """
    Base class for configurable algorithms in the Gaugi Kernel.
    Inherits from Logger for message service integration.
    Provides automatic C++ property synchronization via attribute access.
    """

    def __init__(self, core_class, name, *args, **kwargs):
        Logger.__init__(self, name)
        c_args = [treatPropertyValue(a) for a in args]
        try:
            self._c_ptr = core_class(name, *c_args)
        except TypeError:
            if not args:
                try:
                    self._c_ptr = core_class()
                except TypeError:
                    self._c_ptr = core_class(name)
            else:
                try:
                    self._c_ptr = core_class(name, *args)
                except TypeError:
                    raise

        self._name = name

        properties = [str(p) for p in self._c_ptr.getProperties()] if hasattr(self._c_ptr, "getProperties") else []
        self._properties = set(properties)

        # Apply keyword arguments directly via setattr
        for key, val in kwargs.items():
            setattr(self, key, val)

    def __del__(self):
        del self._c_ptr

    def c_ptr(self):
        return self._c_ptr

    def name(self) -> str:
        if hasattr(self, '_c_ptr') and hasattr(self._c_ptr, 'name'):
            return self._c_ptr.name()
        return getattr(self, '_name', self.__class__.__name__)

    def getTypeName(self) -> str:
        """Returns the C++ class name or Python Configurable class name."""
        if hasattr(self, '_c_ptr') and self._c_ptr:
            return self._c_ptr.__class__.__name__
        return self.__class__.__name__

    def getPropertiesDict(self) -> dict:
        """
        Returns a dictionary of all declared algorithm properties and their current values,
        filtering out internal pointers and private attributes.
        """
        props = {}
        if hasattr(self, '_properties'):
            for prop_name in sorted(self._properties):
                if prop_name.startswith('_'):
                    continue
                try:
                    val = getattr(self, prop_name)
                    if hasattr(val, '__iter__') and not isinstance(val, (str, bytes, dict)):
                        val = list(val)
                    props[prop_name] = val
                except Exception:
                    pass
        for k, v in sorted(self.__dict__.items()):
            if k.startswith('_') or k in props or k == 'level':
                continue
            if hasattr(v, '__iter__') and not isinstance(v, (str, bytes, dict)):
                props[k] = list(v)
            else:
                props[k] = v
        return props

    def getInputContainers(self) -> list:
        """
        Automatically identifies input (consumed) container keys from properties.
        Recognizes Input*Key, Input*Keys, and ItemList entries.
        """
        inputs = []
        props = self.getPropertiesDict()
        for key, val in props.items():
            if not val:
                continue
            if key.startswith("Input") and key.endswith("Key") and isinstance(val, str):
                inputs.append(val)
            elif key.startswith("Input") and key.endswith("Keys") and isinstance(val, list):
                inputs.extend([str(item) for item in val if item])
            elif key == "ItemList" and isinstance(val, list):
                for item in val:
                    if "#" in item:
                        inputs.append(item.split("#")[1])
        return sorted(list(set(inputs)))

    def getOutputContainers(self) -> list:
        """
        Automatically identifies output (produced) container keys from properties.
        Recognizes Output*Key and Output*Keys.
        """
        outputs = []
        props = self.getPropertiesDict()
        for key, val in props.items():
            if not val:
                continue
            if key.startswith("Output") and key.endswith("Key") and isinstance(val, str):
                outputs.append(val)
            elif key.startswith("Output") and key.endswith("Keys") and isinstance(val, list):
                outputs.extend([str(item) for item in val if item])
        return sorted(list(set(outputs)))

    def setProperty(self, key, value):
        setattr(self, key, value)

    def getProperty(self, key):
        return getattr(self, key)

    def merge(self, acc):
        """Merges this configurable into a ComponentAccumulator."""
        acc += self

    def __setattr__(self, name, value):
        if name in ('_properties', '_c_ptr', '_name'):
            super().__setattr__(name, value)
            return

        if isinstance(value, list) and not isinstance(value, PropertyList):
            value = PropertyList(self, name, value)
        elif isinstance(value, PropertyList):
            value._owner = self
            value._prop_name = name

        self.__dict__[name] = value

        if hasattr(self, '_c_ptr') and self._c_ptr.hasProperty(name):
            try:
                self._c_ptr.setProperty(name, treatPropertyValue(value))
            except Exception as e:
                MSG_FATAL(self, f"Exception setting property '{name}' with value '{value}': {e}")

    def __getattr__(self, name):
        if name in ('_properties', '_c_ptr'):
            raise AttributeError(name)

        if hasattr(self, '_properties') and name in self._properties:
            is_vector = (
                self._c_ptr.isVectorProperty(name)
                if hasattr(self, '_c_ptr') and hasattr(self._c_ptr, 'isVectorProperty')
                else ("tool" in name.lower() or name.endswith("s"))
            )
            if is_vector:
                prop_list = PropertyList(self, name)
                self.__dict__[name] = prop_list
                return prop_list
            return None

        if hasattr(self, '_c_ptr') and hasattr(self._c_ptr, name):
            return getattr(self._c_ptr, name)

        try:
            return super().__getattr__(name)
        except AttributeError:
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")

