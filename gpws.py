from ivy.std_api import *
import sys, logging, math
logger = logging.getLogger('Ivy')
from optparse import OptionParser

bus = "127.255.255.255:2010"

try:
    import pygame
    TEST_SON = True
except ImportError:
    print("Module pygame non installe : impossible de lire les sons")
    TEST_SON = False

# Abcsisses/Ordornnees des modes
VZ = 0
RADIOALT = 1
TERRAIN_CLOSURE_RATE = 2
MSL_ALT_LOSS = 3
COMPUTED_AIR_SPEED = 4
GLIDE_SLOPE_DEVIATION = 5
ROLL_ANGLE = 6

class Enveloppe():
    def __init__(self, vertexes, alertlevel, priority, flaps, gear):
        self.vertexes = vertexes
        self.alertlevel = alertlevel
        self.priority = priority
        self.flaps = flaps
        self.gear = gear
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
        if (flaps not in self.flaps and self.flaps[0] != 0) or (gear not in self.gear and self.flaps[0] !=0): # Si la config n'est pas bonne
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
    def __init__(self, list_enveloppes,phase,abs,ord):
        self.list_enveloppes = list_enveloppes
        self.phase = phase
        self.on = True
        self.ord = ord
        self.abs = abs

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
    def __init__(self,VerticalSpeed,RadioAltitude,TerrainClosureRate,MSLAltitudeLoss,ComputedAirSpeed,GlideSlopeDeviation,RollAngle,flaps,gear,phase):
        self.list = [VerticalSpeed, RadioAltitude, TerrainClosureRate, MSLAltitudeLoss, ComputedAirSpeed, GlideSlopeDeviation, RollAngle]
        self.flaps = flaps
        self.gear = gear
        self.phase = phase

    def get_VerticalSpeed(self):
        return self.list[VZ]

    def get_RadioAltitude(self):
        return self.list[RADIOALT]

    def get_TerrainClosureRate(self):
        return self.list[TERRAIN_CLOSURE_RATE]

    def get_MSLAltitudeLoss(self):
        return self.list[MSL_ALT_LOSS]

    def get_ComputedAirSpeed(self):
        return self.list[COMPUTED_AIR_SPEED]

    def get_GlideSlopeDeviation(self):
        return self.list[GLIDE_SLOPE_DEVIATION]

    def get_RollAngle(self):
        return self.list[ROLL_ANGLE]

    def generate_radioalt(self):
        return "RadioAltimeter groundAlt={}\n".format(self.list[RADIOALT] * 0.3048)

    def generate_statevector(self, gamma):
        """ Pour les tests uniquement """
        x = 0
        y = 0
        z = 0
        fpa = gamma
        if gamma !=0 and self.get_VerticalSpeed() != 0 :
            vp = self.get_VerticalSpeed()/math.sin(gamma) * 0.00508 #Conversion ft/min to m/s
        else: vp = self.get_ComputedAirSpeed() * 0.514444# Conversion kts to m/s
        psi = 0
        phi = self.get_RollAngle()
        return "StateVector x={0} y={1} z={2} Vp={3} fpa={4} psi={5} phi={6}\n".format(x, y, z, vp, fpa, psi, phi)

    def get_xy(self, mode):
        return (self.list[mode.abs], self.list[mode.ord])

    def set_xy(self, x, y, mode, gamma=0):
        """  Modifie l'etat de sorte qu'il se trouve aux coord (x,y) dans le mode passe en param  """
        self.list[mode.abs] = x
        self.list[mode.ord] = y
        if mode.abs == VZ and gamma != 0:  #si on change la vz, on change la vp
            self.list[COMPUTED_AIR_SPEED]  = x/math.sin(gamma)
        elif mode.abs == COMPUTED_AIR_SPEED:
            self.list[VZ] = self.get_ComputedAirSpeed() * math.sin(gamma)


    def change_radio_alt(self, z):
        self.list[RADIOALT] = z

    def change_state(self, x, y, z, vp, fpa, psi, phi):
        self.list[COMPUTED_AIR_SPEED] = vp  * 1,94384 #conversion ms to kts
        self.list[VZ] = (math.sin(fpa) * vp) * 196,85 #conversion m/s to ft/min
        self.list[ROLL_ANGLE] = math.degrees(phi)

    def change_fmsinfo(self, phase, da, dh):
        self.phase = phase

    def __repr__(self):
        return "Radio_alt = {}".format(self.list[RADIOALT])

def Creation_Modes():

    PullUp1 = Enveloppe([[1750,370],[3000,1000],[6225,2075],[8000,2075],[8000,0],[1750,0]],'W',2,[None],[None])
    SinkRate1 = Enveloppe([[1750,370],[2610,1180],[5150,2450],[8000,2450],[8000,0],[1750,0]],'C',17,[None],[None])
    PullUp2 = Enveloppe([[2277,220],[3000,790],[8000,790],[8000,0],[2277,0]],'W',3,[None],[None])
    Terrain2 = Enveloppe([[2277,220],[3000,790],[3900,1500],[6000,1800],[8000,1800],[8000,0],[2277,0]],'C',9,[None],[None])
    DontSink3 = Enveloppe([[0,0],[143,1500],[400,1500],[400,0]],'C',18,[None],[None])
    TooLowTerrain4 = Enveloppe([[190,0],[190,500],[250,1000],[400,1000],[400,0],[190,0]],'W',4,[None],[None])
    TooLowFlaps4 = Enveloppe([[0,0],[0,245],[190,245],[190,0]],'C',16,[0],[None])
    TooLowGear4 = Enveloppe([[0,0],[0,500],[190,500],[190,0]],'C',15,[None],["UP"])
    GlideSlope5 = Enveloppe([[2,300],[4,300],[4,0],[3.68,0],[2,150]],'C',19,[None],"DOWN")
    GlideSlopeReduced5 = Enveloppe([[1.3,1000],[4,1000],[4,0],[2.98,0],[1.3,150]],'C',18.5,[None],["DOWN"])
    ExRollAngle6 = Enveloppe([[10,30],[40,150],[40,500],[90,500],[-90,500],[-40,500],[-40,150],[-10,30]],'C',22,[None],[None])

    Mode1 = Mode([PullUp1,SinkRate1],[None],VZ,RADIOALT)
    Mode2 = Mode([PullUp2,Terrain2], [None],TERRAIN_CLOSURE_RATE,RADIOALT)
    Mode3 = Mode([DontSink3],["CLIMB"],MSL_ALT_LOSS,RADIOALT)
    Mode4 = Mode([TooLowTerrain4,TooLowFlaps4,TooLowGear4],["APPROACH","LANDING","TAKE-OFF"],COMPUTED_AIR_SPEED,RADIOALT)
    Mode5 = Mode([GlideSlopeReduced5,GlideSlope5],["APPROACH"],GLIDE_SLOPE_DEVIATION,RADIOALT)
    Mode6 = Mode([ExRollAngle6],[None],ROLL_ANGLE,RADIOALT)

    return [Mode1,Mode2,Mode3,Mode4,Mode5,Mode6]

L_Modes = Creation_Modes()

def test_mode(Etat):
    flaps = Etat.flaps
    gear = Etat.gear
    L = []
    for Mode in L_Modes:
        if Etat.phase in Mode.phase:
            x,y = Etat.get_xy(Mode)
            L.append(Mode.get_enveloppe([x,y],flaps,gear))

    L = [e for e in L if e!= None]
    key_sort = lambda env : env.priority
    L.sort(key=key_sort, reverse=True) #On trie selon la plus grande prioritee
    return (L[0] if len(L)!=0 else [])


global_etat = Etat(2000, 100, 2000, 2000, 300, 3.5, 60,0,"UP","LANDING")
print(test_mode(global_etat))


if __name__ == '__main__':
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
        logger.info("Receive radio altitude : %s" % z)
        global_etat.change_radio_alt(z)

    def on_statevector(agent, *larg):
        x = larg[0]
        y = larg[1]
        z = larg[2]
        vp = larg[3]
        fpa = larg[4]
        psi = larg[5]
        phi = larg[6]
        global_etat.change_state(x, y, z, vp, fpa, psi, phi)

    def on_fms(agent, *larg):
        pass


    connect(options.app_name, options.ivy_bus)
    IvyBindMsg(on_time, '^Time t=(\S+)')
    IvyBindMsg(on_radioalt, '^RadioAltimeter groundAlt=(\S+)')
    IvyBindMsg(on_statevector, 'StateVector\s+x=(\S+)\s+y=(\S+)\sz=(\S+)\sVp=(\S+)\sfpa=(\S+)\spsi=(\S+)\sphi=(\S+)')
    IvyMainLoop()