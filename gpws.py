from ivy.std_api import *
import sys, logging
logger = logging.getLogger('Ivy')
from optparse import OptionParser

bus = "127.255.255.255:2010"

try:
    import pygame
    TEST_SON = True
except ImportError:
    print("Module pygame non installe : impossible de lire les sons")
    TEST_SON = False

class Enveloppe():
    def __init__(self, vertexes, alertlevel, priority, flaps, gear, phase):
        self.vertexes = vertexes
        self.alertlevel = alertlevel
        self.priority = priority
        self.flaps = flaps
        self.gear = gear
        self.phase = phase
        self.sound = "sons/abn2500.wav" # to change
        self.name = "Nom" #to change

    def collision(self,P):
        graphe = self.vertexes
        nbp = len(graphe)
        for i in range(0,nbp):
            A = graphe[i]
            if i == nbp-1:
                B = graphe[0]
            else:
                B = graphe[i+1]
            AB = [0,0]
            AP = [0,0]
            AB[0] = B[0] - A[0]
            AB[1] = B[1] - A[1]
            AP[0] = P[0] - A[0]
            AP[1] = P[1] - A[1]
            d = AB[0]*AP[1] - AB[1]*AP[0]
            if d>0 :
                return False
        return True

    def have_inside(self, point, flaps, gear):
        if (flaps != self.flaps and self.flaps != None) or (gear != self.gear and self.gear != None): # Si la config n'est pas bonne
            return False
        else:
            return self.collision(point)

    def play_sound(self):
        if TEST_SON:
            pygame.init()
            song = pygame.mixer.Sound(self.sound)
            song.play()
            while pygame.mixer.get_busy():
                 pygame.time.delay(100)
            pygame.quit()
        else:
            print("Lecture de ", self.sound)

class Mode():
    def __init__(self, list_enveloppes,phase):
        self.list_enveloppes = list_enveloppes
        self.phase = phase
        self.on = True

    def get_enveloppe(self, point, flaps, gear):
        enveloppe_eff = [] #listes des enveloppes ou se trouve le point
        for env in self.list_enveloppes:
            if env.have_inside(point, flaps, gear):
                enveloppe_eff.append(env)
        if len(enveloppe_eff) == 0:
            return None #Le point n'est dans aucune enveloppe
        else:
            key_sort = lambda env : env.priority
            enveloppe_eff.sort(key=key_sort, reverse=True) #On trie selon la plus grande prioritee
            return enveloppe_eff[0]

class Etat():
    def __init__(self,VerticalSpeed,RadioAltitude,TerrainClosureRate,MSLAltitudeLoss,ComputedAirSpeed,GlideSlopeDeviation,RollAngle,HeightAboveTerrain):
        self.VerticalSpeed = VerticalSpeed
        self.RadioAltitude = RadioAltitude
        self.TerrainClosureRate = TerrainClosureRate
        self.MSLAltitudeLoss = MSLAltitudeLoss
        self.ComputedAirSpeed = ComputedAirSpeed
        self.GlideSlopeDeviation = GlideSlopeDeviation
        self.RollAngle = RollAngle
        self.HeightAboveTerrain = HeightAboveTerrain

    def radio_alt(self, z):
        self.RadioAltitude = z

    def __repr__(self):
        return "Radio_alt = {}".format(self.RadioAltitude)

Etat0 = Etat(0, 0, 0, 0, 0, 0, 0, 0)

#Mode 1
PullUp1 = Enveloppe([[1750,370],[3000,1000],[6225,2075],[8000,2075],[8000,0],[1750,0]],0,1,None,None,1)
SinkRate1 = Enveloppe([[1750,370],[2610,1180],[5150,2450],[8000,2450],[8000,0],[1750,0]],1,1,None,None,1)
Mode1 = Mode([PullUp1,SinkRate1],None)

x1 = Etat0.VerticalSpeed # ft/mn
y1 = Etat0.RadioAltitude # ft

#Mode 2
PullUp2 = Enveloppe([[2277,220],[3000,790],[8000,790],[8000,0],[2277,0]],0,1,None,1,1)
Terrain2 = Enveloppe([[2277,220],[3000,790],[3900,1500],[6000,1800],[8000,1800],[8000,0],[2277,0]],1,1,1,1,1)
Mode2 = Mode([PullUp2,Terrain2],None)

x2 = Etat0.TerrainClosureRate # ft/mn
y2 = Etat0.RadioAltitude # ft


#Mode 3
DontSink = Enveloppe([[0,0],[143,1500],[400,1500],[400,0]],1,1,1,1,1)
Mode3 = Mode([DontSink],"Takeoff")

x3 = Etat0.MSLAltitudeLoss # ft
y3 = Etat0.RadioAltitude # ft


#Mode 4
TooLowTerrain4 = Enveloppe([[190,0],[190,500],[250,1000],[400,1000],[400,0],[190,0]],1,1,1,1,1)
TooLowFlaps4 = Enveloppe([[0,0],[0,245],[190,245],[190,0]],1,1,1,1,1)
TooLowGear4 = Enveloppe([[0,0],[0,500],[190,500],[190,0]],1,1,1,1,1)
Mode4 = Mode([TooLowTerrain4,TooLowFlaps4,TooLowGear4],None)

x4 = Etat0.ComputedAirSpeed # kts
y4 = Etat0.RadioAltitude # ft

#Mode 5
GlideSlopeReduced5 = Enveloppe([[1.3,1000],[4,1000],[4,0],[2.98,0],[1.3,150]],1,1,1,1,1)
GlideSlope5 = Enveloppe([[2,300],[4,300],[4,0],[3.68,0],[2,150]],1,1,1,1,1)

x5 = Etat0.GlideSlopeDeviation# dots
y5 = Etat0.RadioAltitude # ft

Mode5 = Mode([GlideSlopeReduced5,GlideSlope5],"Approach")

#Mode 6
ExRollAngle6 = Enveloppe([[10,30],[40,150],[40,500],[90,500],[-90,500],[-40,500],[-40,150],[-10,30]],1,1,1,1,1)
Mode6 = Mode([ExRollAngle6],0)

x6 = Etat0.RollAngle # degrees
y6 = Etat0.HeightAboveTerrain # ft


global_etat = Etat(0, 0, 0, 0, 0, 0, 0, 0)
#parse
usage = "usage: %prog [options]"
parser = OptionParser(usage=usage)
parser.set_defaults(ivy_bus="127.255.255.255:2010", interval=5, verbose=False, app_name="GPWS")
parser.add_option('-v', '--verbose', action='store_true', dest='verbose',
                  help='Be verbose.')
parser.add_option('-i', '--interval', type='int', dest='interval',
                  help='Interval between messages (in seconds)')
parser.add_option('-b', '--ivybus', type='string', dest='ivy_bus',
                  help='Bus id (format @IP:port, default to 127.255.255.255:2010)')
parser.add_option('-a', '--appname', type='string', dest='app_name',
                  help='Application Name')
(options, args) = parser.parse_args()

# init log
level = logging.INFO
if options.verbose: # update logging level
    level = logging.DEBUG
logger.setLevel(level)

#### IVY ####
def on_cx_proc(agent, connected):
    if connected == IvyApplicationDisconnected:
        logger.error('Ivy application %r was disconnected', agent)
    else:
        logger.info('Ivy application %r was connected', agent)


def on_die_proc(agent, _id):
    logger.info('received the order to die from %r with id = %d', agent, _id)


def connect(app_name, ivy_bus):
    IvyInit(app_name,                   # application name for Ivy
            "[%s ready]" % app_name,    # ready message
            0,                          # main loop is local (ie. using IvyMainloop)
            on_cx_proc,                 # handler called on connection/disconnection
            on_die_proc)
    IvyStart(ivy_bus)

def on_time(agent, *larg):
    logger.info("Receive time : %s" % larg[0])
    print ("t=", larg[0])

def on_radioalt(agent, *larg):
    z = larg[0]
    logger.info("Receive radio allitude : %s" % z)
    global_etat.radio_alt(z)
    print global_etat

def on_statevector(agent, *larg):
    pass

connect(options.app_name, options.ivy_bus)
IvyBindMsg(on_time, '^Time t=(\S+)')
IvyBindMsg(on_radioalt, '^RadioAltimeter groundAlt=(\S+)')
IvyMainLoop()