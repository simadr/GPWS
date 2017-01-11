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

#Gear
DOWN = "Down"
UP = "Up"

#Phase
APP = "APPROACH"
CLIMB = "CLIMB"
TO  = "TAKE-OFF"
LDG = "LANDING"

class Enveloppe():
    def __init__(self, vertexes, alertlevel, priority, flaps, gear, name, sound):
        self.vertexes = vertexes
        self.alertlevel = alertlevel
        self.priority = priority
        self.flaps = flaps
        self.gear = gear
        self.sound = sound
        self.name = name

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
        if (flaps not in self.flaps and self.flaps[0] != None) or (gear not in self.gear and self.gear[0] != None): # Si la config n'est pas bonne
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

    def __repr__(self):
        return self.name

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
            enveloppe_eff.sort(key=key_sort) #On trie selon la plus petite prioritee
            return enveloppe_eff[0]

    def disable(self):
        self.on = False

    def enable(self):
        self.on = True

class Etat():
    def __init__(self,VerticalSpeed,RadioAltitude,TerrainClosureRate,MSLAltitudeLoss,ComputedAirSpeed,GlideSlopeDeviation,RollAngle,flaps,gear,phase):
        self.list = [VerticalSpeed, RadioAltitude, TerrainClosureRate, MSLAltitudeLoss, ComputedAirSpeed, GlideSlopeDeviation, RollAngle]
        self.flaps = flaps
        self.gear = gear
        self.phase = phase
        self.da = 0
        self.dh = 0

        # Attribut permettant de savoir si l'etat est correctement initialise
        self.init_ralt = False
        self.init_state = False
        self.init_fms = False
        self.init_config = False


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
        """ Pour les tests uniquement """
        return "RadioAltimeter groundAlt={}\n".format(self.list[RADIOALT] * 0.3048)

    def generate_statevector(self, gamma):
        """ Pour les tests uniquement """
        x = 0
        y = 0
        z = 0
        fpa = gamma
        if gamma !=0 and self.get_VerticalSpeed() != 0 :
            vp = self.get_VerticalSpeed()/math.sin(abs(gamma)) * 0.00508 #Conversion ft/min to m/s
        else: vp = self.get_ComputedAirSpeed() * 0.514444# Conversion kts to m/s
        psi = 0
        phi = self.get_RollAngle()
        return "StateVector x={0} y={1} z={2} Vp={3} fpa={4} psi={5} phi={6}\n".format(x, y, z, vp, fpa, psi, phi)

    def generate_fms(self):
        """ Pour les tests uniquement """
        return "FMS_TO_GPWS PHASE={0} DA={1} DH={2}\n".format(self.phase, self.da, self.dh)

    def generate_config(self):
        """ Pour les tests uniquement """
        return "Config GEAR={} FLAPS={}\n".format(self.gear, self.flaps)

    def get_xy(self, mode):
        x = self.list[mode.abs]
        y = self.list[mode.ord]
        return (x, y)

    def set_xy(self, x, y, mode, gamma=0):
        """  Modifie l'etat de sorte qu'il se trouve aux coord (x,y) dans le mode passe en param  """
        self.list[mode.abs] = x
        self.list[mode.ord] = y
        if mode.abs == VZ and gamma != 0:  #si on change la vz, on change la vp
            self.list[COMPUTED_AIR_SPEED]  =   x/math.sin(abs(gamma))
        elif mode.abs == COMPUTED_AIR_SPEED:
            self.list[VZ] = self.get_ComputedAirSpeed() * math.sin(gamma)


    def change_radio_alt(self, z):
        z = z / 0.3048 #conversion m to ft
        if global_etat.init_ralt: #On met a jour le terrain closure rate si possible
            self.list[TERRAIN_CLOSURE_RATE] = self.get_RadioAltitude() - z
        self.list[RADIOALT] = z

    def change_state(self, x, y, z, vp, fpa, psi, phi):
        self.list[COMPUTED_AIR_SPEED] = vp * 1.94384 #conversion ms to kts
        self.list[VZ] =  - (math.sin(fpa) * vp) * 196.85 #conversion m/s to - ft/min
        self.list[ROLL_ANGLE] = math.degrees(abs(phi))

    def change_fmsinfo(self, phase, da, dh):
        self.phase = phase
        self.da = da
        self.dh = dh

    def change_config(self, flaps, gear):
        self.flaps = flaps
        self.gear = gear

    def is_init(self):
        return self.init_config and self.init_fms and self.init_ralt and self.init_state

    def __copy__(self):
        copy = Etat(self.get_VerticalSpeed(), self.get_RadioAltitude(), self.get_TerrainClosureRate(),
                    self.get_MSLAltitudeLoss(), self.get_ComputedAirSpeed(), self.get_GlideSlopeDeviation(),
                    self.get_RollAngle(), self.flaps, self.gear, self.phase
                    )
        copy.da = self.da
        copy.dh = self.dh
        copy.init_fms = self.init_fms
        copy.init_ralt = self.init_ralt
        copy.init_state = self.init_state
        copy.init_config = self.init_config
        return copy


    def __repr__(self):
        to_print = ""
        to_print +=  "Vertical speed = {}\n".format(self.get_VerticalSpeed())
        to_print +=  "Radio_alt = {}\n".format(self.get_RadioAltitude())
        to_print +=  "Terrain closure rate = {}\n".format(self.get_TerrainClosureRate())
        to_print +=  "MSl altitude loss = {}\n".format(self.get_MSLAltitudeLoss())
        to_print +=  "Computed airspeed = {}\n".format(self.get_ComputedAirSpeed())
        to_print +=  "GlideslopeDeviation = {}\n".format(self.get_GlideSlopeDeviation())
        to_print +=  "Roll angle = {}\n".format(self.get_RollAngle())
        return to_print

def Creation_Modes():

    PullUp1 = Enveloppe([[1750,370],[3000,1000],[6225,2075],[8000,2075],[8000,0],[1750,0]],'W',2,[None],[None], "Pullup", "sons/nabpullup.wav")
    SinkRate1 = Enveloppe([[1750,370],[2610,1180],[5150,2450],[8000,2450],[8000,0],[1750,0]],'C',17,[None],[None], "Sink rate", "sons/nabsinkrate.wav")
    PullUp2 = Enveloppe([[2277,220],[3000,790],[8000,790],[8000,0],[2277,0]],'W',3,[None],[None], "terrain Pull up", "sons/nabterrainaheadpullup.wav")
    Terrain2 = Enveloppe([[2277,220],[3000,790],[3900,1500],[6000,1800],[8000,1800],[8000,0],[2277,0]],'C',9,[None],[None], "Terrain", "sons/nabglideslope2.wav")
    DontSink3 = Enveloppe([[0,0],[143,1500],[400,1500],[400,0]],'C',18,[None],[None], "Don't sink", "sons/ndontsink.wav")
    TooLowTerrain4 = Enveloppe([[190,0],[190,500],[250,1000],[400,1000],[400,0],[190,0]],'W',4,[None],[None], "Too low terrain", "sons/TooLowTerrain.wav")
    TooLowFlaps4 = Enveloppe([[0,0],[0,245],[190,245],[190,0]],'C',16,[0],[None], "Too low flaps", "sons/nabtoolowflaps.wav")
    TooLowGear4 = Enveloppe([[0,0],[0,500],[190,500],[190,0]],'C',15,[None],[UP], "Too low gear", "sons/nabtoolowgear.wav")
    GlideSlope5 = Enveloppe([[2,300],[4,300],[4,0],[3.68,0],[2,150]],'C',19,[None],[DOWN], "GLIDESLOPE", "sons/nabglideslope2.wav")
    GlideSlopeReduced5 = Enveloppe([[1.3,1000],[4,1000],[4,0],[2.98,0],[1.3,150]],'C',19.5,[None],[DOWN],"Glideslope (reduced)", "sons/nabglideslope.wav")
    #ExRollAngle6 = Enveloppe([[10,30],[40,150],[40,500],[180,500],[180,0], [10, 0]],'C',22,[None],[None], "Bank angle", "sons/nbankangle.wav")
    ExRollAngle_16 = Enveloppe([[10,30],[40,150],[40,0],[10,0]],'C',22,[None],[None], "Bank angle", "sons/nbankangle.wav")
    ExRollAngle_26 = Enveloppe([[40,0],[40,5000],[180,5000],[180,0]],'C',22,[None],[None], "Bank angle", "sons/nbankangle.wav")


    Mode1 = Mode([PullUp1,SinkRate1],[None],VZ,RADIOALT)
    Mode2 = Mode([PullUp2,Terrain2], [None],TERRAIN_CLOSURE_RATE,RADIOALT)
    Mode3 = Mode([DontSink3],[CLIMB],MSL_ALT_LOSS,RADIOALT)
    Mode3.disable()
    Mode4 = Mode([TooLowTerrain4,TooLowFlaps4,TooLowGear4],[APP,LDG,TO],COMPUTED_AIR_SPEED,RADIOALT)
    Mode5 = Mode([GlideSlopeReduced5,GlideSlope5],[APP],GLIDE_SLOPE_DEVIATION,RADIOALT)
    Mode5.disable()
    Mode6 = Mode([ExRollAngle_16, ExRollAngle_26],[None],ROLL_ANGLE,RADIOALT)

    return [Mode1,Mode2,Mode3,Mode4,Mode5,Mode6]

L_Modes = Creation_Modes()

def test_mode(Etat):
    active_mode = [mode for mode in L_Modes if mode.on]
    flaps = Etat.flaps
    gear = Etat.gear
    L = []
    for Mode in active_mode:
        if Etat.phase in Mode.phase or Mode.phase[0] == None:
            x,y = Etat.get_xy(Mode)
            L.append(Mode.get_enveloppe([x,y],flaps,gear))
    L = [e for e in L if e!= None]
    key_sort = lambda env : env.priority
    L.sort(key=key_sort) #On trie selon la plus petite prioritee
    return (L[0] if len(L)!=0 else None)


## Variables globals
global_etat = Etat(6000,500,2611, 200, 140, 3.5, 60,0,"UP","LANDING")


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
        if global_etat.is_init():
            env = test_mode(global_etat)
            if env != None:
                env.play_sound()
        else:
            print("GPWS NOT INITIALIZED")
        print global_etat


    def on_radioalt(agent, *larg):
        z = float(larg[0])
        logger.info("Receive radio altitude : %s" % z)
        global_etat.change_radio_alt(z)
        global_etat.init_ralt = True

    def on_statevector(agent, *larg):
        x = float(larg[0])
        y = float(larg[1])
        z = float(larg[2])
        vp = float(larg[3])
        fpa = float(larg[4])
        psi = float(larg[5])
        phi = float(larg[6])
        global_etat.change_state(x, y, z, vp, fpa, psi, phi)
        global_etat.init_state = True

    def on_fms(agent, *larg):
        phase = larg[0]
        da = float(larg[1])
        dh = float(larg[2])
        global_etat.change_fmsinfo(phase, da, dh)
        global_etat.init_fms = True

    def on_config(agent, *larg):
        gear = larg[0]
        flaps = larg[1]
        global_etat.change_config(flaps, gear)
        global_etat.init_config = True


    connect(options.app_name, options.ivy_bus)
    IvyBindMsg(on_time, '^Time t=(\S+)')
    IvyBindMsg(on_radioalt, '^RadioAltimeter groundAlt=(\S+)')
    IvyBindMsg(on_statevector, 'StateVector\s+x=(\S+)\s+y=(\S+)\sz=(\S+)\sVp=(\S+)\sfpa=(\S+)\spsi=(\S+)\sphi=(\S+)')
    IvyBindMsg(on_fms, '^FMS_TO_GPWS\sPHASE=(\S+)\sDA=(\S+)\sDH=(\S+)')
    IvyBindMsg(on_config, 'Config\s+GEAR=(\S+)\s+FLAPS=(\S+)')
    IvyMainLoop()