__all__ = ["Configurable"]

import ROOT
from GaugiKernel import Logger
from GaugiKernel.Cpp import treatPropertyValue
from GaugiKernel.macros import MSG_FATAL

from GaugiKernel import list2stdvector



def treatPropertyValue( value ):

  if hasattr(value, "core"):
    return value.core()

  if type(value) is list:
    if len(value) == 0:
      return value
    if hasattr(value[0], "core"):
      from ROOT.std import vector
      vec = vector("Gaugi::AlgTool*")()
      for tool in value:
        vec.push_back(tool.core())
      return vec
    if type(value[0]) is str:
      return list2stdvector('string', value)
    elif type(value[0]) is int:
      return list2stdvector('int', value)
    elif type(value[0]) is float:
      return list2stdvector('float', value)
    elif type(value[0]) is bool:
      return list2stdvector('bool', value)
    # list of list with ints, should be vector<vector<int>>
    elif (type(value[0]) is list) and (type(value[0][0]) is int) :
      from ROOT.std import vector
      vec = vector("vector<int>")()
      for v in value:
        vec.push_back( list2stdvector('int', v) )
      return vec
  else:
    return value



class Configurable(Logger):
    """
    Base class for configurable algorithms in the Gaugi Kernel.
    Inherits from Logger for message service integration.
    Provides property management and tool attachment interface.
    """
    
    def __init__(self, core_class, name, **kwargs):
        Logger.__init__(self, name)
        self._c_ptr = core_class(name)
        
        properties = [str(p) for p in self._c_ptr.getProperties()] if hasattr(self._c_ptr, "getProperties") else []
        self._properties = set(properties)
        
        # Initialize properties in __dict__ to None by default
        for prop in properties:
            self.__dict__[prop] = None

        self._ext_adds = {}
        self._ext_sets = {}

        # Scan for __func__add__ methods in C++ core
        for attr in dir(self._c_ptr):
            if attr.startswith("__func__add__"):
                func_name = attr[len("__func__add__"):]
                self._ext_adds[func_name] = attr

        # Scan for __func__set__ methods in C++ core
        for attr in dir(self._c_ptr):
            if attr.startswith("__func__set__"):
                func_name = attr[len("__func__set__"):]
                self._ext_sets[func_name] = attr
                # Initialize key in dict if it's not set
                if func_name not in self.__dict__:
                    self.__dict__[func_name] = None

        # Apply keyword arguments
        for key, val in kwargs.items():
            self.setProperty(key, val)

    def __del__(self):
        del self._c_ptr

    def core(self):
        return self._c_ptr

    def setProperty(self, key, value):
        if self._c_ptr.hasProperty(key):
            self.__dict__[key] = value
            try:
                self._c_ptr.setProperty(key, treatPropertyValue(value))
            except Exception as e:
                MSG_FATAL(self, f"Exception in property with name {key} and value: {value}. Error: {e}")
        else:
            self.__dict__[key] = value

    def getProperty(self, key):
        if hasattr(self, key):
            return getattr(self, key)
        else:
            MSG_FATAL(self, "Property with name %s is not allowed for %s object", key, self.__class__.__name__)

    def __getattr__(self, name):
        # Prevent infinite recursion for internal attributes
        if name in ('_properties', '_ext_adds', '_ext_sets', '_c_ptr'):
            raise AttributeError(name)

        # Dynamic getter/setter method for C++ properties
        if name.startswith("get_"):
            prop_name = name[4:]
            if prop_name in self._properties:
                return lambda: self.getProperty(prop_name)
        elif name.startswith("set_"):
            prop_name = name[4:]
            if prop_name in self._properties:
                return lambda val: self.setProperty(prop_name, val)
        elif name.startswith("get") and len(name) > 3:
            prop_name = name[3:]
            for p in self._properties:
                cap_p = p[0].upper() + p[1:] if p else p
                if cap_p == prop_name:
                    return lambda: self.getProperty(p)
        elif name.startswith("set") and len(name) > 3:
            prop_name = name[3:]
            for p in self._properties:
                cap_p = p[0].upper() + p[1:] if p else p
                if cap_p == prop_name:
                    return lambda val: self.setProperty(p, val)

        # Dynamic ext__prop__add_ method
        if name in self._ext_adds:
            method_name = self._ext_adds[name]
            def ext_prop_method(alg):
                func = getattr(self._c_ptr, method_name)
                if isinstance(alg, list):
                    for item in alg:
                        c_item = item.core() if hasattr(item, "core") else item
                        func(c_item)
                else:
                    c_alg = alg.core() if hasattr(alg, "core") else alg
                    func(c_alg)
                return self
            return ext_prop_method

        # Delegate to parent class (Logger)'s __getattr__ if not resolved here
        try:
            return super().__getattr__(name)
        except AttributeError:
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")

    def __setattr__(self, name, value):
        # Avoid recursion on internal attributes during initialization
        if name in ('_properties', '_ext_adds', '_ext_sets', '_c_ptr'):
            super().__setattr__(name, value)
            return

        if hasattr(self, '_properties') and name in self._properties:
            self.setProperty(name, value)
        elif hasattr(self, '_ext_sets') and name in self._ext_sets:
            method_name = self._ext_sets[name]
            func = getattr(self._c_ptr, method_name)
            c_val = value.core() if hasattr(value, "core") else value
            func(c_val)
            self.__dict__[name] = value
        else:
            super().__setattr__(name, value)
