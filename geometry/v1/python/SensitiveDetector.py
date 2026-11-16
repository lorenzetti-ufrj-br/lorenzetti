

__all__ = [ "SensitiveDetector",]

from GaugiKernel import Logger
from GaugiKernel.macros import MSG_FATAL
from GaugiKernel.constants import um

import numpy as np


def xy_z_to_theta( r_xy, r_z ):
    return np.arctan2(  r_xy , r_z ) if r_z!=0 else np.pi/2
  
def theta_to_eta( theta ):
  try:
    eta = -np.log(np.tan( theta/2. ) )
  except:
    eta = -np.log(np.tan( (theta+np.pi)/2.) )
  return eta

def xy_z_to_eta( r_xy, z ):
  return theta_to_eta( xy_z_to_theta( r_xy, z ) )



#
# Sensitive volume
#
class SensitiveDetector(Logger):

    __allow_keys = [
                      "DeltaPhi",
                      "DeltaEta",
                   ]

    # Hold all granularity information from physical volume in eta x phi plane
    def __init__(self, pv, EtaMin=None, EtaMax=None, Segment=0, **kw):

        Logger.__init__(self)
        for key, value in kw.items():
          if key in self.__allow_keys:
            setattr(self, key, value )
          else:
            MSG_FATAL( self, "Property with name %s is not allow for %s object", key, self.__class__.__name__)

        self.pv = pv
        self.Segment = Segment
        self.PhiBins = np.round( np.arange( -np.pi, np.pi+self.DeltaPhi, step = self.DeltaPhi ), 4 ).tolist()

        # Create eta bins given the detector z position
        if pv.ZMin > 0: # entire in positive side
          eta_min = round(xy_z_to_eta( pv.RMax, pv.ZMin ), 4) if EtaMin is None else EtaMin 
          eta_max = round(xy_z_to_eta( pv.RMin, pv.ZMax ), 4) if EtaMax is None else EtaMax
          self.EtaBins = np.round( np.arange( eta_min, eta_max, step = self.DeltaEta ), 4 ).tolist()
          self.EtaMin = self.EtaBins[0]; self.EtaMax = self.EtaBins[-1]
        elif pv.ZMax < 0: # entire in negative side:
          #etamin=EtaMax;EtaMin=EtaMax;EtaMax=etamin 
          eta_min = round(xy_z_to_eta( pv.RMax, pv.ZMax ), 4) if not EtaMin else EtaMin
          eta_max = round(xy_z_to_eta( pv.RMin, pv.ZMin ), 4) if not EtaMax else EtaMax
          self.EtaBins = np.flip(np.round( np.arange( eta_min, eta_max , step = -1*self.DeltaEta ), 4 )).tolist()
          self.EtaMin = self.EtaBins[-1]; self.EtaMax = self.EtaBins[0]
        else: # The volume cut the zero axis
          eta_min = round(xy_z_to_eta( pv.RMax, 0 ), 4) if EtaMin is None else EtaMin
          eta_max = round(xy_z_to_eta( pv.RMin, pv.ZMax ), 4) if EtaMax is None else EtaMax
          right_eta_bins = np.round( np.arange( eta_min, eta_max  , step = self.DeltaEta ), 4 )
          eta_min = round(xy_z_to_eta( pv.RMax, 0 ), 4) if EtaMin is None else EtaMin
          eta_max = round(xy_z_to_eta( pv.RMin, pv.ZMin ), 4) if EtaMax is None else EtaMax
          left_eta_bins = np.flip(np.round( np.arange( eta_min, eta_max  , step = -1*self.DeltaEta ), 4 ))
          self.EtaBins = np.concatenate( (left_eta_bins, right_eta_bins[1::]) ).tolist()
          self.EtaMin = self.EtaBins[0]; self.EtaMax = self.EtaBins[-1]


    def volume(self):
      return self.pv


