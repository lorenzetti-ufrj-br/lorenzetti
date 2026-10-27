__all__ = ["ComponentAccumulator"]

from GaugiKernel import Logger, Configurable
from GaugiKernel.macros import MSG_WARNING
from typing import List, Union
import numpy as np
import os

#
# Componenent 
#
class ComponentAccumulator( Logger ):

  def __init__(self, 
               name            : str, 
               output          : str, 
               reader          : Configurable,
              ):
    
    Logger.__init__(self)
    import ROOT
    ROOT.gSystem.Load('liblorenzetti')
    from ROOT import RunManager
    from ROOT import Gaugi as GK
    self.__acc = GK.ComponentAccumulator( name )
    from ROOT import SG
    self.__ctx = SG.EventContext("EventContext")
    self.__store = SG.StoreGate(output)
    self.__ctx.setStoreGateSvc(self.__store)
    self.__reader = reader
    self.__acc.push_back(reader.c_ptr())

  def __add__( self, algs ):
    if type(algs) is not list:
      algs = [algs]
    for alg in algs:
      self.__acc.push_back(alg.c_ptr())
    return self

  def GetEntries(self):
    reader = self.__reader.c_ptr() if hasattr(self.__reader, 'c_ptr') else self.__reader
    if hasattr(reader, "GetEntries"):
      return reader.GetEntries()
    elif hasattr(reader, "entries"):
      return reader.entries()
    return 0

  def configure(self):
    self.__acc.initialize()
    self.__acc.bookHistograms(self.__ctx)

 
  def run( self , events : Union[List[int], int] = -1 ):
    self.configure()
    if isinstance(events, int):
      total = self.GetEntries()
      if events > 0:
        total = min(events, total)
      events = list(range(max(0, total)))

    for evt in events:
        self.__acc.run(self.__ctx, evt)
      
    self.__acc.finalize()
    self.__ctx.getStoreGateSvc().save()
 